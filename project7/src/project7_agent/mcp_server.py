"""MCP boundary with separate trusted-launch stdio and authenticated HTTP modes.

No A2A conformance is claimed. Approval is provisioned
out-of-band in the ledger by a trusted operator, never by a model tool argument.
"""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict
from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings

from .contracts import REQUESTER_CARD
from .gateway import SecureGateway
from .request_lifecycle import RequestLifecycle


class PolicyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    matches: list[str]


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    artifact: dict[str, Any]
    effects_created: int


def make_task(task_id: str, request_id: str, amount: float, sender: str = REQUESTER_CARD.name) -> dict:
    return {"task_id": task_id, "correlation_id": task_id, "sender": sender,
            "recipient": "compliance-reviewer", "action": "review_request",
            "payload": {"request_id": request_id, "amount": amount}}


def build_server(database_path: str, *, verifier=None, trace_path=None, timeout_seconds=15):
    auth = None if verifier is None else AuthSettings(issuer_url=verifier.config.issuer,
        resource_server_url=verifier.config.resource, required_scopes=['policy:read'], validate_token_resource=True)
    server = MCPServer("project7-policy-gateway", token_verifier=verifier, auth=auth,
                       middleware=[RequestLifecycle(trace_path, timeout_seconds)])

    def identity(scope):
        if verifier is None:
            return REQUESTER_CARD.name, REQUESTER_CARD.name
        token = get_access_token()
        if token is None or scope not in token.scopes:
            raise PermissionError('Authenticated request with required tool scope is mandatory')
        if verifier.current_role(token.subject, token.client_id) != token.claims['role']:
            raise PermissionError('Principal binding was revoked or changed')
        return token.claims['role'], token.claims['actor_id']

    @server.tool(structured_output=True)
    def policy_search(query: str) -> PolicyResponse:
        """Read the synthetic procurement policy; no side effects."""
        identity('policy:read')
        return PolicyResponse(matches=["An operation-bound, unexpired reviewer approval is required."])

    @server.tool(structured_output=True)
    def review_request(task_id: str, request_id: str, amount: float) -> ReviewResponse:
        """Review a synthetic purchase. Approval cannot be supplied through tool arguments."""
        # Sync SDK tools run in worker threads; keep each SQLite connection thread-local.
        role, actor = identity('procurement:submit')
        gateway = SecureGateway(database_path, principal=role, actor_id=actor)
        try:
            result = gateway.process_request(make_task(task_id, request_id, amount, sender=role))
        finally:
            gateway.close()
        return ReviewResponse(status=result.status, artifact=result.artifact,
            effects_created=sum(event["event"] == "tool.call" and event.get("tool") == "approve_procurement" for event in result.trace))

    return server


def build_http_app(database_path, verifier, port=8000, trace_path=None, timeout_seconds=15):
    resource = urlsplit(verifier.config.resource)
    security = TransportSecuritySettings(enable_dns_rebinding_protection=True,
        allowed_hosts=[resource.netloc, f'127.0.0.1:{port}'],
        allowed_origins=[f'{resource.scheme}://{resource.netloc}', f'http://127.0.0.1:{port}'])
    return build_server(str(database_path), verifier=verifier, trace_path=trace_path,
                        timeout_seconds=timeout_seconds).streamable_http_app(
        stateless_http=True, json_response=True, max_request_body_size=65536,
        streamable_http_path=resource.path or '/mcp', transport_security=security)


if __name__ == "__main__":
    path = os.environ.get("PROJECT7_LEDGER")
    if not path:
        raise RuntimeError("PROJECT7_LEDGER must point to a dedicated synthetic execution ledger")
    transport = os.environ.get('PROJECT7_TRANSPORT', 'stdio')
    trace_path = os.environ.get('PROJECT7_TRACE_FILE')
    if transport == 'stdio':
        build_server(path, trace_path=trace_path).run(transport='stdio')
    elif transport == 'streamable-http':
        from .http_auth import load_verifier
        verifier = load_verifier(os.environ['PROJECT7_AUTH_CONFIG'], os.environ['PROJECT7_PUBLIC_JWKS'])
        import uvicorn
        port = int(os.environ.get('PROJECT7_PORT', '8000'))
        app = build_http_app(path, verifier, port, trace_path=trace_path)
        # Only a loopback listener; use a separately managed TLS reverse proxy for deployment.
        uvicorn.run(app, host='127.0.0.1', port=port, access_log=False)
    else:
        raise ValueError('Unsupported transport')
