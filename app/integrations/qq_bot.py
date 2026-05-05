from loguru import logger
from typing import Dict, Any


class QQBot:
    def __init__(self):
        self.qq = None

    async def send_message(self, group: str, message: str):
        logger.info(f"QQ: {message}")

    async def send_private(self, user: str, message: str):
        logger.info(f"QQ private: {message}")


qq_bot = QQBot()