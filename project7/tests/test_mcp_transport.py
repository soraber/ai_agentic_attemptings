import asyncio
import os
import sys
import time
from pathlib import Path

from mcp import Client, StdioServerParameters

from project7_agent.gateway import SecureGateway
from project7_agent.mcp_server import make_task


def test_real_stdio_discovery_schema_approval_and_restart(tmp_path):
    ledger = tmp_path / "ledger.sqlite"
    authority = SecureGateway(ledger)
    authority.register_approval(make_task("approved", "REQ-1", 50.0), "compliance-reviewer", time.time() + 60)
    authority.close()
    params = StdioServerParameters(command=sys.executable, args=["-m", "project7_agent.mcp_server"],
        env={"PATH": os.defpath, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
             "PYTHONDONTWRITEBYTECODE": "1", "PROJECT7_LEDGER": str(ledger)})

    async def check():
        async with Client(params, read_timeout_seconds=10) as client:
            listed = await client.list_tools()
            assert {tool.name for tool in listed.tools} == {"policy_search", "review_request"}
            invalid = await client.call_tool("review_request", {"task_id": "invalid"})
            assert invalid.is_error
            result = await client.call_tool("review_request", {"task_id": "unapproved", "request_id": "REQ-2", "amount": 60})
            assert result.structured_content["effects_created"] == 0
            first = await client.call_tool("review_request", {"task_id": "approved", "request_id": "REQ-1", "amount": 50.0})
            assert first.structured_content["effects_created"] == 1
        async with Client(params, read_timeout_seconds=10) as client:
            repeated = await client.call_tool("review_request", {"task_id": "approved", "request_id": "REQ-1", "amount": 50.0})
            assert repeated.structured_content["effects_created"] == 0
    asyncio.run(check())
