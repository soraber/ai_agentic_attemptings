# Authenticated MCP Resource Server

The gateway supports real MCP SDK 2.3.0 Streamable HTTP in addition to trusted-launch
stdio. It is an OAuth **resource server**, not an identity provider or OAuth login
client. Test-only tokens are generated in memory; no signing key is shipped.

## Trust Boundary

- Only configured public RSA signing keys with explicit `RS256`, unique `kid`,
  and at least 2048 bits are accepted. Private JWKS parameters are rejected.
- Tokens require the expected issuer and a single exact resource audience,
  `typ=at+jwt`, subject, client ID, expiry, issue time, and not-before. Lifetime
  defaults to at most 15 minutes. Unknown keys/subject-client pairs fail closed.
- Configured subject/client bindings determine the role. Model-supplied sender,
  recipient, and card fields cannot create authentication or reviewer approval.
  Each HTTP actor is the hash of issuer, subject, and client ID.
- Both tools require `policy:read`; procurement also requires `procurement:submit`.
  A trusted operator must independently provision an unexpired, operation-bound
  approval for that exact actor. A caller with the same role cannot borrow it.

## Operator Setup

Use the repository's isolated CPU/API environment. Obtain issuer public JWKS
through your identity provider's trusted administrative/discovery channel, verify
the issuer out of band, and save only **public** keys in an operator-managed file.
Never accept a JWKS URL or key supplied by a model or bearer token. Keep operational
config, access tokens, and approval ledgers out of the repository.

Example config structure (replace the domains and synthetic subjects):

```json
{
  "issuer": "https://identity.example.com/",
  "resource": "https://gateway.example.com/mcp",
  "bindings": [{"subject": "employee-123", "client_id": "approved-client", "role": "procurement-requester"}],
  "max_token_lifetime_seconds": 900,
  "allow_loopback_http": false
}
```

Use the exact role constants in `src/project7_agent/contracts.py`; unrecognized
roles are rejected. The tests use an explicitly permitted loopback HTTP issuer
for transport validation, not a production identity provider.

```sh
export PROJECT7_TRANSPORT=streamable-http
export PROJECT7_AUTH_CONFIG=/runtime/config/auth.json
export PROJECT7_PUBLIC_JWKS=/runtime/config/public-jwks.json
export PROJECT7_LEDGER=/runtime/state/synthetic-ledger.sqlite
export PROJECT7_PORT=8000
PYTHONPATH=project7/src .venv-notebook/bin/python -m project7_agent.mcp_server
```

Run from the repository root. These `/runtime/...` paths are deployment placeholders,
not real user directories. The listener binds only to `127.0.0.1`; deploy behind
a separately managed TLS proxy matching the configured resource. Access logging
is disabled. Do not expose the listener directly. DNS-rebinding Host/Origin checks
and a 64 KiB body limit remain enabled. Never pass tokens as command-line arguments.

## Verification And Limits

```sh
PYTHONPATH=project7/src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-notebook/bin/python -m pytest -q -p no:cacheprovider project7/tests/test_http_auth.py
```

Eighteen tests cover signature/issuer/audience/time checks, scope failures,
actor-bound approval, sender spoofing, restart deduplication, legacy-approval
isolation, request limits, and a real client/server exchange over a local socket.
Auth failures remain separate from model-generated attack outcomes.

The service loads keys and bindings at startup. The verifier's trusted-operator
`revoke_binding(subject, client_id)` method removes authority immediately for new
checks, including a second binding check just before a tool call. It is not an
unauthenticated network endpoint. Key rotation and persisted configuration changes
still require controlled restart; in-memory revocations must also be reflected in
the operator's configuration before restarting. No browser login, PKCE client flow, issuer-side token issuance, external TLS
deployment, rate limiter, or multi-tenant production ledger is implemented here.
HTTP authorization does not establish general prompt-injection
resistance or A2A conformance.

## Request Lifecycle

SDK middleware enforces a server tool deadline (15 seconds by default), propagates
cancellation, and optionally writes payload-free correlation traces to
`PROJECT7_TRACE_FILE`. Trace IDs use `_meta["project7/trace_id"]` or a server UUID;
logs contain method, status, timing, and IDs, not tool arguments/results or tokens.
The model harness uses AsyncOpenAI with no hidden retries and 60-second model,
10-second client tool, and 180-second case limits. Timed-out calls reserve their
unknown cost against the budget rather than assuming they were free.

Local tests cover real stdio cancellation/deadline notifications, matching
client/server trace IDs, revoked HTTP identity, and a hostile tool result trying
to change an approved amount. The amount remains bound by deterministic policy.
These authored tests do not establish general model injection resistance.
Cancellation is cooperative, not rollback: a synchronous committed effect can
outlive a disconnect. Treat an uncertain outcome as unknown and reconcile the
persistent idempotency ledger before retrying. Provider-side compute may continue
after client cancellation; external billing is not controlled by this harness.

Sources: [MCP SDK authorization](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/authorization.md),
[MCP authorization specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization),
[PyJWT validation API](https://pyjwt.readthedocs.io/en/stable/api.html).
