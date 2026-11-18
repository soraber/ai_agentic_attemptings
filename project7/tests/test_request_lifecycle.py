import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp import Client, StdioServerParameters
from project7_agent.request_lifecycle import RequestLifecycle


def test_timeout_cancellation_and_payload_free_correlated_trace(tmp_path):
    path=tmp_path/'traces.jsonl'
    ctx=SimpleNamespace(meta={'project7/trace_id':'a'*32}, request_id=7, method='tools/call')
    stopped=[]
    async def slow(context):
        try: await asyncio.sleep(10)
        finally: stopped.append(True)
    with pytest.raises(TimeoutError):
        asyncio.run(RequestLifecycle(path,.02)(ctx,slow))
    row=json.loads(path.read_text())
    assert row['status']=='timeout' and row['trace_id']=='a'*32 and stopped
    assert 'arguments' not in row and 'token' not in row


@pytest.mark.parametrize('mode',['server_deadline','client_cancel'])
def test_real_stdio_timeout_cancels_cooperative_tool(tmp_path, mode):
    server=tmp_path/'fixture_server.py'
    trace=tmp_path/'trace.jsonl'
    server.write_text('''import asyncio,sys
from mcp.server import MCPServer
from project7_agent.request_lifecycle import RequestLifecycle
s=MCPServer("lifecycle-fixture",middleware=[RequestLifecycle(sys.argv[1],float(sys.argv[2]))])
@s.tool()
async def slow() -> str:
    await asyncio.sleep(20)
    return "must not complete"
s.run(transport="stdio")
''')
    params=StdioServerParameters(command=sys.executable,args=[str(server),str(trace),'5' if mode=='client_cancel' else '.05'],
        env={'PATH':os.defpath,'PYTHONPATH':str(Path(__file__).parents[1]/'src'),'PYTHONDONTWRITEBYTECODE':'1'})
    async def check():
        async with Client(params,read_timeout_seconds=2) as client:
            await client.list_tools()
            if mode=='client_cancel':
                task=asyncio.create_task(client.call_tool('slow',{},meta={'project7/trace_id':'b'*32}))
                await asyncio.sleep(.05)
                task.cancel()
                with pytest.raises(asyncio.CancelledError): await task
                await asyncio.sleep(.1)
                return
            try:
                result=await client.call_tool('slow',{},meta={'project7/trace_id':'b'*32})
                assert result.is_error
            except Exception as exc:
                # A server-side timeout may be surfaced as a protocol error.
                assert type(exc).__name__ in {'MCPError', 'TimeoutError'}
    asyncio.run(check())
    rows=[json.loads(line) for line in trace.read_text().splitlines()]
    timed=[row for row in rows if row['method']=='tools/call']
    assert len(timed)==1 and timed[0]['status']==('cancelled' if mode=='client_cancel' else 'timeout')
    assert timed[0]['trace_id']=='b'*32


def test_explicit_cancellation_records_cancelled_status(tmp_path):
    path=tmp_path/'cancelled.jsonl'
    ctx=SimpleNamespace(meta={},request_id=1,method='tools/call')
    async def exercise():
        started=asyncio.Event()
        async def slow(context):
            started.set()
            await asyncio.sleep(10)
        task=asyncio.create_task(RequestLifecycle(path,5)(ctx,slow))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    asyncio.run(exercise())
    assert json.loads(path.read_text())['status']=='cancelled'
