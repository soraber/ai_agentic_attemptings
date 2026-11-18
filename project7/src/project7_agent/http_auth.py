"""OAuth resource-server verification. This module never issues tokens or logs them."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import jwt
from mcp.server.auth.provider import AccessToken
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts import REQUESTER_CARD, REVIEWER_CARD


class PrincipalBinding(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    subject: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    role: str = REQUESTER_CARD.name


class HTTPAuthConfig(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    issuer: str
    resource: str
    bindings: list[PrincipalBinding] = Field(min_length=1)
    max_token_lifetime_seconds: int = Field(default=900, ge=1, le=3600)
    allow_loopback_http: bool = False

    @model_validator(mode='after')
    def validate_boundary(self):
        for url in (self.issuer, self.resource):
            parts = urlsplit(url)
            local_http = self.allow_loopback_http and parts.scheme == 'http' and parts.hostname in {'127.0.0.1', 'localhost', '::1'}
            if (not parts.hostname or parts.username or parts.password or parts.query or parts.fragment
                    or not (parts.scheme == 'https' or local_http)):
                raise ValueError('Trusted issuer/resource must use HTTPS; explicit loopback tests only')
        pairs = {(b.subject, b.client_id) for b in self.bindings}
        if len(pairs) != len(self.bindings) or any(b.role not in {REQUESTER_CARD.name, REVIEWER_CARD.name} for b in self.bindings):
            raise ValueError('Bindings must have unique subject/client pairs and known roles')
        return self


def actor_id(issuer: str, subject: str, client_id: str) -> str:
    return 'oauth:' + hashlib.sha256(json.dumps([issuer, subject, client_id], separators=(',', ':')).encode()).hexdigest()


class JWTVerifier:
    def __init__(self, config: HTTPAuthConfig, public_jwks: dict):
        self.config = config
        self.keys = {}
        for key in public_jwks.get('keys', []):
            if (key.get('kty') != 'RSA' or key.get('alg') != 'RS256' or key.get('use') != 'sig'
                    or not key.get('kid') or key['kid'] in self.keys
                    or any(k in key for k in ('d', 'p', 'q', 'dp', 'dq', 'qi', 'oth'))):
                raise ValueError('Expected unique public RSA signing keys, explicitly RS256')
            parsed = jwt.PyJWK.from_dict(key, algorithm='RS256')
            if parsed.key.key_size < 2048:
                raise ValueError('RSA key must contain at least 2048 bits')
            self.keys[key['kid']] = parsed.key
        if not self.keys:
            raise ValueError('At least one trusted public key is required')
        self.bindings = {(b.subject, b.client_id): b.role for b in config.bindings}

    def revoke_binding(self, subject, client_id):
        """Trusted operator control; no model-facing revocation endpoint is exposed."""
        self.bindings = {key:role for key,role in self.bindings.items() if key != (subject,client_id)}

    def current_role(self, subject, client_id):
        return self.bindings.get((subject, client_id))

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token or len(token) > 16384:
            return None
        try:
            header = jwt.get_unverified_header(token)
            if header.get('alg') != 'RS256' or header.get('typ') != 'at+jwt' or header.get('crit'):
                return None
            key = self.keys.get(header.get('kid'))
            if key is None:
                return None
            claims = jwt.decode(token, key, algorithms=['RS256'], issuer=self.config.issuer,
                                audience=self.config.resource, options={
                                    'require': ['iss', 'aud', 'sub', 'client_id', 'exp', 'iat', 'nbf'],
                                    'strict_aud': True})
            if any(type(claims[name]) is not int for name in ('exp', 'iat', 'nbf')):
                return None
            if not 0 < claims['exp'] - claims['iat'] <= self.config.max_token_lifetime_seconds:
                return None
            subject, client_id = claims['sub'], claims['client_id']
            if not isinstance(subject, str) or not isinstance(client_id, str):
                return None
            role = self.bindings.get((subject, client_id))
            scope = claims.get('scope', '')
            if role is None or not isinstance(scope, str):
                return None
            return AccessToken(token=token, client_id=client_id, subject=subject,
                               scopes=scope.split(), expires_at=claims['exp'], resource=self.config.resource,
                               claims={'iss': self.config.issuer, 'role': role,
                                       'actor_id': actor_id(self.config.issuer, subject, client_id)})
        except (jwt.PyJWTError, ValueError, TypeError, KeyError):
            return None


def load_verifier(config_path: str | Path, jwks_path: str | Path) -> JWTVerifier:
    return JWTVerifier(HTTPAuthConfig.model_validate_json(Path(config_path).read_text()),
                       json.loads(Path(jwks_path).read_text()))
