from loguru import logger
import asyncio
from typing import Dict, Any


class WebSocket:
    def __init__(self):
        self.connections = []

    async def connect(self, ws):
        self.connections.append(ws)

    async def broadcast(self, message: str):
        for ws in self.connections:
            await ws.send(message)

    async def disconnect(self, ws):
        if ws in self.connections:
            self.connections.remove(ws)


ws_manager = WebSocket()

async def log_consumer():
    logger.info("Log consumer started")
    while True:
        await asyncio.sleep(1)