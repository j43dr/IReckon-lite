from loguru import logger
import asyncio
from typing import Dict, Any


class WebSocket:
    def __init__(self):
        self.connections = []

    async def connect(self, ws):
        self.connections.append(ws)

    async def broadcast(self, message: str):
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            await self.disconnect(ws)

    async def disconnect(self, ws):
        if ws in self.connections:
            self.connections.remove(ws)


ws_manager = WebSocket()

async def log_consumer():
    logger.info("Log consumer started")
    from app.core.logger import _log_queue
    loop = asyncio.get_running_loop()
    while True:
        try:
            msg = await loop.run_in_executor(None, _log_queue.get)
            await ws_manager.broadcast(msg)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(0.1)