"""Bounded MCP request lifetime and payload-free correlated traces."""
import asyncio
import json
import re
import time
import uuid
from pathlib import Path


class RequestLifecycle:
    def __init__(self, trace_path=None, timeout_seconds=15):
        if not 0 < timeout_seconds <= 300:
            raise ValueError('Tool timeout must be positive and at most 300 seconds')
        self.trace_path = Path(trace_path) if trace_path else None
        self.timeout_seconds = timeout_seconds
        if self.trace_path:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)

    async def __call__(self, ctx, call_next):
        proposed = (ctx.meta or {}).get('project7/trace_id', '')
        trace_id = proposed if isinstance(proposed,str) and re.fullmatch(r'[a-f0-9]{32}', proposed) else uuid.uuid4().hex
        started = time.perf_counter()
        record = {'trace_id':trace_id, 'request_id':str(ctx.request_id), 'method':ctx.method,
                  'status':'running', 'timeout_seconds':self.timeout_seconds}
        try:
            if ctx.method == 'tools/call':
                async with asyncio.timeout(self.timeout_seconds):
                    result = await call_next(ctx)
            else:
                result = await call_next(ctx)
            record['status'] = 'complete'
            return result
        except TimeoutError:
            record['status'] = 'timeout'
            raise
        except asyncio.CancelledError:
            record['status'] = 'cancelled'
            raise
        except Exception as exc:
            record.update(status='failed', error_type=type(exc).__name__)
            raise
        finally:
            record['seconds'] = time.perf_counter()-started
            if self.trace_path:
                # One compact line, no bearer tokens, request arguments, or tool contents.
                with self.trace_path.open('a') as handle:
                    handle.write(json.dumps(record)+'\n')
