import asyncio
from typing import Optional
from enum import Enum
from loguru import logger
from app.core.config import config_manager
from app.core.database import db


class MessageLayer(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class MeetingRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.participants = []
        self.messages = []

    async def join(self, participant: str):
        self.participants.append(participant)

    async def leave(self, participant: str):
        if participant in self.participants:
            self.participants.remove(participant)

    async def send_message(self, sender: str, message: str):
        self.messages.append({"sender": sender, "message": message})


class MeetingRoomManager:
    def __init__(self):
        self.rooms = {}
        
    async def get_room(self, room_id: str) -> MeetingRoom:
        if room_id not in self.rooms:
            self.rooms[room_id] = MeetingRoom(room_id)
        return self.rooms[room_id]
        
    async def create_room(self, room_id: str):
        room = MeetingRoom(room_id)
        self.rooms[room_id] = room
        return room
        
    async def close_room(self, room_id: str):
        if room_id in self.rooms:
            del self.rooms[room_id]


meeting_room_manager = MeetingRoomManager()
