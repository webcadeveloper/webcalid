# utils/async_context.py
import asyncio
import contextlib

@contextlib.contextmanager
def async_context():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()