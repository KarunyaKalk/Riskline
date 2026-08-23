import asyncio
import json
import logging
from collections import defaultdict
from typing import AsyncGenerator, Dict, List, Set
from uuid import UUID

logger = logging.getLogger("events")


class EventBroadcaster:
    """
    Tenant-isolated real-time event publisher and subscriber manager using Server-Sent Events (SSE).
    Guarantees event broadcasts are strictly scoped to the target organization (org_id).
    """

    def __init__(self):
        # Maps org_id string -> set of asyncio queues for connected subscribers
        self.subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)

    async def subscribe(self, org_id: UUID) -> AsyncGenerator[str, None]:
        org_id_str = str(org_id)
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers[org_id_str].add(queue)
        logger.info(f"New SSE client subscribed to org {org_id_str} (Total: {len(self.subscribers[org_id_str])})")

        try:
            # Yield initial connection confirmation message
            init_event = json.dumps({"type": "CONNECTED", "org_id": org_id_str})
            yield f"data: {init_event}\n\n"

            while True:
                data = await queue.get()
                event_str = json.dumps(data)
                yield f"data: {event_str}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.subscribers[org_id_str].discard(queue)
            if not self.subscribers[org_id_str]:
                del self.subscribers[org_id_str]
            logger.info(f"SSE client disconnected from org {org_id_str}")

    async def publish_async(self, org_id: UUID, event_type: str, payload: dict) -> int:
        org_id_str = str(org_id)
        queues = self.subscribers.get(org_id_str, set())
        event_data = {"type": event_type, "org_id": org_id_str, "payload": payload}

        count = 0
        for q in list(queues):
            try:
                q.put_nowait(event_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to publish event to queue: {e}")

        logger.info(f"Published event {event_type} to {count} subscribers in org {org_id_str}")
        return count

    def publish_sync(self, org_id: UUID, event_type: str, payload: dict) -> int:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.publish_async(org_id, event_type, payload), loop)
                return len(self.subscribers.get(str(org_id), set()))
        except Exception:
            pass
        return 0


event_broadcaster = EventBroadcaster()
