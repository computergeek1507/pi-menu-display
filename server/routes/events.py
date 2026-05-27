import asyncio
import json
import time

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

_subscribers: list[asyncio.Queue] = []
_lock = asyncio.Lock()


async def broadcast(event: dict):
    async with _lock:
        dead = []
        for q in _subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            _subscribers.remove(q)


@router.get("/events/{screen_id}")
async def event_stream(screen_id: str, request: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    async with _lock:
        _subscribers.append(q)

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
                    continue

                target = event.get("screen", "")
                event_type = event.get("type", "refresh")

                if target == screen_id or target == "specials":
                    yield {"event": event_type, "data": json.dumps(event)}
        finally:
            async with _lock:
                if q in _subscribers:
                    _subscribers.remove(q)

    return EventSourceResponse(generate())
