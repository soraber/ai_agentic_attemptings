import asyncio
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient

from project7_agent.gateway import SecureGateway
from project7_agent.http_auth import HTTPAuthConfig, JWTVerifier, actor_id
from project7_agent.mcp_server import build_http_app, make_task


@pytest.fixture
def credentials():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key()))
    public.update(kid='ephemeral-test-key', alg='RS256', use='sig')
    config = HTTPAuthConfig(issuer='https://issuer.example.invalid', resource='https://gateway.example.invalid/mcp',
        bindings=[{'subject': name, 'client_id': 'test-client'} for name in ('alice', 'bob')])
    verifier = JWTVerifier(config, {'keys': [public]})

    def issue(subject='alice', changes=None, headers=None, key=None):
        now = int(time.time())
        claims = dict(iss=config.issuer, aud=config.resource, sub=subject, client_id='test-client',
                      iat=now, nbf=now-1, exp=now+300, scope='policy:read procurement:submit')
        claims.update(changes or {})
        return jwt.encode(claims, key or private, algorithm='RS256',
                          headers={'kid': public['kid'], 'typ': 'at+jwt', **(headers or {})})
    return verifier, issue, public


def post(client, token=None, name='policy_search', arguments=None):
    headers = {'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-06-18'}
    if token is not None:
        headers['Authorization'] = 'Bearer ' + token
    return client.post('/mcp', headers=headers, json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': name, 'arguments': arguments or {'query': 'policy'}}})


def app(ledger, verifier):
    return build_http_app(ledger, verifier)


@pytest.mark.parametrize('changes,headers', [
    ({'aud': 'https://other.example.invalid/mcp'}, {}),
    ({'iss': 'https://other.example.invalid'}, {}),
    ({'exp': 1}, {}), ({'nbf': int(time.time())+3600}, {}),
    ({'sub': 'unknown'}, {}), ({'client_id': 'other-client'}, {}),
    ({'exp': int(time.time())+7200}, {}), ({'scope': ['policy:read']}, {}),
    ({'iat': '123'}, {}), ({}, {'kid': 'unknown'}), ({}, {'typ': 'JWT'}),
])
def test_invalid_access_tokens_are_rejected(credentials, tmp_path, changes, headers):
    verifier, issue, _ = credentials
    with TestClient(app(tmp_path/'ledger.sqlite', verifier), base_url='http://127.0.0.1:8000') as client:
        assert post(client, issue(changes=changes, headers=headers)).status_code == 401


def test_http_discovery_scopes_and_signature(credentials, tmp_path):
    verifier, issue, _ = credentials
    with TestClient(app(tmp_path/'ledger.sqlite', verifier), base_url='http://127.0.0.1:8000') as client:
        anonymous = post(client)
        assert anonymous.status_code == 401
        assert 'resource_metadata=' in anonymous.headers['www-authenticate']
        discovery = client.get('/.well-known/oauth-protected-resource/mcp').json()
        assert discovery['resource'] == verifier.config.resource
        assert post(client, issue(changes={'scope': ''})).status_code == 403
        wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        assert post(client, issue(key=wrong_key)).status_code == 401
        result = post(client, issue())
        assert result.status_code == 200
        assert result.json()['result']['structuredContent']['matches']
        denied = post(client, issue(changes={'scope': 'policy:read'}), 'review_request',
                      {'task_id': 't', 'request_id': 'R', 'amount': 50})
        assert denied.json()['result']['isError']


def test_approval_is_actor_bound_and_survives_http_restart(credentials, tmp_path):
    verifier, issue, _ = credentials
    ledger = tmp_path/'ledger.sqlite'
    authority = SecureGateway(ledger, actor_id=actor_id(verifier.config.issuer, 'alice', 'test-client'))
    authority.register_approval(make_task('approved', 'R', 50.0), 'compliance-reviewer', time.time()+300)
    authority.close()
    arguments = {'task_id': 'approved', 'request_id': 'R', 'amount': 50.0}
    with TestClient(app(ledger, verifier), base_url='http://127.0.0.1:8000') as client:
        other = post(client, issue('bob'), 'review_request', arguments).json()['result']['structuredContent']
        assert other['effects_created'] == 0
        assert 'approval_id' not in other['artifact']
        own = post(client, issue(), 'review_request', arguments).json()['result']['structuredContent']
        assert own['effects_created'] == 1
        spoof = post(client, issue('bob'), 'review_request', {**arguments, 'sender': 'alice'}).json()['result']
        # SDK ignores extra function arguments; they must never become identity.
        assert spoof['structuredContent']['effects_created'] == 0
        assert 'approval_id' not in spoof['structuredContent']['artifact']
    with TestClient(app(ledger, verifier), base_url='http://127.0.0.1:8000') as client:
        replay = post(client, issue(), 'review_request', arguments).json()['result']['structuredContent']
        assert replay['effects_created'] == 0


def test_invalid_config_and_private_jwks_fail_closed(credentials):
    verifier, _, public = credentials
    with pytest.raises(ValueError):
        HTTPAuthConfig(issuer='http://public.example.com', resource=verifier.config.resource,
                       bindings=verifier.config.bindings)
    with pytest.raises(ValueError):
        JWTVerifier(verifier.config, {'keys': [{**public, 'd': 'not-a-public-key'}]})
    assert asyncio.run(verifier.verify_token('malformed')) is None


def test_legacy_local_approval_is_not_remote_authority(credentials, tmp_path):
    verifier, _, _ = credentials
    ledger = tmp_path/'ledger.sqlite'
    local = SecureGateway(ledger)
    local.register_approval(make_task('old', 'R', 50.0), 'compliance-reviewer', time.time()+300)
    local.close()
    remote = SecureGateway(ledger, actor_id=actor_id(verifier.config.issuer, 'alice', 'test-client'))
    result = remote.process_request(make_task('old', 'R', 50.0))
    remote.close()
    assert 'approval_id' not in result.artifact


def test_revoked_binding_rejects_existing_unexpired_token(credentials, tmp_path):
    verifier, issue, _ = credentials
    token=issue()
    with TestClient(app(tmp_path/'ledger.sqlite', verifier), base_url='http://127.0.0.1:8000') as client:
        assert post(client,token).status_code==200
        verifier.revoke_binding('alice','test-client')
        assert post(client,token).status_code==401


def test_host_origin_and_size_limits(credentials, tmp_path):
    verifier, issue, _ = credentials
    with TestClient(app(tmp_path/'ledger.sqlite', verifier), base_url='http://127.0.0.1:8000') as client:
        client.headers['Host'] = 'attacker.example.invalid'
        assert post(client, issue()).status_code == 421
        client.headers['Host'] = '127.0.0.1:8000'
        client.headers['Origin'] = 'https://attacker.example.invalid'
        assert post(client, issue()).status_code == 403
        del client.headers['Origin']
        assert post(client, issue(), arguments={'query': 'x'*70000}).status_code == 413


def test_real_tcp_mcp_client_authentication(credentials, tmp_path):
    import socket
    import threading
    import httpx2
    import uvicorn
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    verifier, issue, _ = credentials
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(build_http_app(tmp_path/'tcp.sqlite', verifier, port),
        log_level='critical', access_log=False, lifespan='on'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic()+5
        while not server.started and thread.is_alive() and time.monotonic()<deadline:
            time.sleep(.02)
        assert server.started

        async def check():
            async with httpx2.AsyncClient(headers={'Authorization': 'Bearer '+issue()}, timeout=5) as http:
                async with Client(streamable_http_client(f'http://127.0.0.1:{port}/mcp', http_client=http),
                                  read_timeout_seconds=5) as client:
                    assert len((await client.list_tools()).tools) == 2
                    result = await client.call_tool('policy_search', {'query': 'policy'})
                    assert not result.is_error and result.structured_content['matches']
        asyncio.run(check())
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
        assert not thread.is_alive()
