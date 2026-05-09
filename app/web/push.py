from loguru import logger
from typing import Dict, Any


class PushNotification:
    def __init__(self):
        self.subscribers = []

    async def send(self, title: str, message: str) -> Dict[str, Any]:
        logger.info(f"Push: {title}")
        return {"status": "sent", "title": title}

    def subscribe(self, endpoint: str):
        self.subscribers.append(endpoint)


push_notification = PushNotification()