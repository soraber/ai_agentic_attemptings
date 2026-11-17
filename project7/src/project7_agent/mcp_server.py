"""Local stdio MCP boundary; parent-process launch is the identity trust boundary.

No HTTP authentication or A2A conformance is claimed. Approval is provisioned
out-of-band in the ledger by a trusted operator, never by a model tool argument.
"""
from __future__ import annotations

import os
from typing import Any
from pydantic import BaseModel, ConfigDict
from mcp.server import MCPServer

from .contracts import REQUESTER_CARD
from .gateway import SecureGateway


class PolicyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    matches: list[str]


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    artifact: dict[str, Any]
    effects_created: int


def make_task(task_id: str, request_id: str, amount: float) -> dict:
    return {"task_id": task_id, "correlation_id": task_id, "sender": REQUESTER_CARD.name,
            "recipient": "compliance-reviewer", "action": "review_request",
            "payload": {"request_id": request_id, "amount": amount}}


def build_server(database_path: str):
    server = MCPServer("project7-policy-gateway")

    @server.tool(structured_output=True)
    def policy_search(query: str) -> PolicyResponse:
        """Read the synthetic procurement policy; no side effects."""
        return PolicyResponse(matches=["An operation-bound, unexpired reviewer approval is required."])

    @server.tool(structured_output=True)
    def review_request(task_id: str, request_id: str, amount: float) -> ReviewResponse:
        """Review a synthetic purchase. Approval cannot be supplied through tool arguments."""
        # Sync SDK tools run in worker threads; keep each SQLite connection thread-local.
        gateway = SecureGateway(database_path, principal=REQUESTER_CARD.name)
        try:
            result = gateway.process_request(make_task(task_id, request_id, amount))
        finally:
            gateway.close()
        return ReviewResponse(status=result.status, artifact=result.artifact,
            effects_created=sum(event["event"] == "tool.call" and event.get("tool") == "approve_procurement" for event in result.trace))

    return server


if __name__ == "__main__":
    path = os.environ.get("PROJECT7_LEDGER")
    if not path:
        raise RuntimeError("PROJECT7_LEDGER must point to a dedicated synthetic execution ledger")
    build_server(path).run(transport="stdio")
