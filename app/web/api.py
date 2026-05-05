from loguru import logger
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()


class TaskCreate(BaseModel):
    user_request: str
    scheduler_cap_id: str = None


class MessageCreate(BaseModel):
    content: str
    layer: str = "user"


class AIInstanceCreate(BaseModel):
    id: str
    name: str
    endpoint: str
    model: str
    api_key: str = ""
    tags: List[str] = []


class ConfigUpdate(BaseModel):
    updates: Dict[str, Any]


@app.get("/api/status")
async def get_status():
    return {"status": "ok", "version": "3.0"}


@app.get("/api/diagnostics")
async def get_diagnostics():
    return {"status": "ok", "checks": {"database": "ok", "tools": "ok", "ai_pool": "ok"}}


@app.get("/api/themes")
async def get_themes():
    return {
        "catgirl": {"name": "Catgirl", "primary": "#ff69b4", "secondary": "#1a1a2e"},
        "dark": {"name": "Dark", "primary": "#6200ea", "secondary": "#121212"},
        "light": {"name": "Light", "primary": "#03dac6", "secondary": "#ffffff"},
    }


@app.get("/api/tasks")
async def get_tasks():
    return []


@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    return {"task_id": f"task-{hash(task.user_request)[:8]}", "status": "created"}


@app.get("/api/tasks/{task_id}/messages")
async def get_task_messages(task_id: str, layer: str = "user", limit: int = 50):
    return {"messages": []}


@app.post("/api/tasks/{task_id}/messages")
async def add_task_message(task_id: str, msg: MessageCreate):
    return {"status": "ok"}


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    return {"status": "cancelled"}


@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    return {"status": "resumed"}


@app.get("/api/ai-instances")
async def get_ai_instances():
    return []


@app.post("/api/ai-instances")
async def create_ai_instance(instance: AIInstanceCreate):
    return {"instance_id": instance.id, "status": "created"}


@app.put("/api/ai-instances/{instance_id}")
async def update_ai_instance(instance_id: str, instance: AIInstanceCreate):
    return {"instance_id": instance_id, "status": "updated"}


@app.delete("/api/ai-instances/{instance_id}")
async def delete_ai_instance(instance_id: str):
    return {"status": "deleted"}


@app.post("/api/ai-instances/{instance_id}/test")
async def test_ai_instance(instance_id: str):
    return {"status": "ok", "latency_ms": 100}


@app.get("/api/config")
async def get_config():
    return {
        "theme": "catgirl",
        "language": "zh-CN",
        "api_timeout": 10,
    }


@app.post("/api/config/update")
async def update_config(config: ConfigUpdate):
    return {"status": "updated"}


web_api = app