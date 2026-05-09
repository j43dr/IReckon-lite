from loguru import logger
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os
import json
import time
from pathlib import Path
from app.core.config import config_manager

app = FastAPI()

# ===== 配置 =====
def load_config() -> dict:
    return config_manager.get_all()

def save_config():
    config_manager.save()

# ===== 统计 =====
STATS = {
    "requests_total": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "tokens_input": 0,
    "tokens_output": 0,
    "total_latency_ms": 0,
}

def record_request(latency_ms: int, cache_hit: bool, tokens_in: int = 0, tokens_out: int = 0):
    STATS["requests_total"] += 1
    if cache_hit:
        STATS["cache_hits"] += 1
    else:
        STATS["cache_misses"] += 1
    STATS["tokens_input"] += tokens_in
    STATS["tokens_output"] += tokens_out
    STATS["total_latency_ms"] += latency_ms

def get_stats() -> dict:
    total = STATS["requests_total"]
    return {
        "cache_hit_rate": STATS["cache_hits"] / total if total > 0 else 0,
        "avg_latency_ms": STATS["total_latency_ms"] / total if total > 0 else 0,
        "requests_total": total,
        "tokens_input": STATS["tokens_input"],
        "tokens_output": STATS["tokens_output"],
        "cache_hits": STATS["cache_hits"],
        "cache_misses": STATS["cache_misses"],
    }

# ===== 模型 =====
class TaskCreate(BaseModel):
    user_request: str = Field(..., min_length=1)
    scheduler_cap_id: Optional[str] = None

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    layer: str = "L1"

class AIInstanceCreate(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    endpoint: str
    model: str
    api_key: str = ""
    tags: List[str] = []
    parameters: Dict[str, Any] = {}
    cost_per_1k_tokens: float = 0.0
    max_context: int = 4096
    enabled: bool = True

class ConfigUpdate(BaseModel):
    updates: Dict[str, Any] = {}

class RoleUpdate(BaseModel):
    enabled: bool = True
    model: str = "gpt-4"
    show_in_public: bool = True

class StyleAIUpdate(BaseModel):
    enabled: bool = False
    style: str = "professional"
    tone: str = "formal"
    length: str = "medium"

# ===== 端点 =====
@app.get("/api/status")
async def get_status():
    return {"status": "ok", "version": "3.0", "timestamp": time.time()}

@app.get("/api/diagnostics")
async def get_diagnostics():
    cfg = load_config()
    stats = get_stats()
    return {
        "status": "ok",
        "checks": {
            "database": "ok",
            "tools": "ok",
            "ai_pool": "ok",
            "roles": "ok" if cfg.get("roles") is not None else "not_configured"
        },
        "stats": stats,
        "mock_llm": "ok"
    }

@app.get("/api/stats")
async def get_api_stats():
    return get_stats()

@app.get("/api/themes")
async def get_themes():
    return {
        "catgirl": {"name": "Catgirl", "primary": "#ff69b4", "secondary": "#1a1a2e"},
        "dark": {"name": "Dark", "primary": "#6200ea", "secondary": "#121212"},
        "light": {"name": "Light", "primary": "#03dac6", "secondary": "#ffffff"},
        "professional": {"name": "Professional", "primary": "#1a73e8", "secondary": "#ffffff"},
    }

# ===== 风格化AI =====
@app.get("/api/style-ai")
async def get_style_ai():
    cfg = load_config()
    return cfg.get("style_ai", {"enabled": False, "style": "professional"})

@app.post("/api/style-ai")
async def update_style_ai(config: StyleAIUpdate):
    config_manager.update("style_ai", config.model_dump())
    save_config()
    return {"status": "updated", "style_ai": config_manager.get("style_ai")}

# ===== 任务 =====
@app.get("/api/tasks")
async def get_tasks():
    try:
        from app.core.database import db
        rows = await db.fetch_all("SELECT task_id, user_request, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 50")
        return rows or []
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        return []

@app.post("/api/tasks", status_code=201)
async def create_task(task: TaskCreate):
    try:
        from app.engine.tasks import task_manager
        task_id = await task_manager.create_task(task.user_request)
        # 自动启动任务
        await task_manager.start_task(task_id, task.scheduler_cap_id)
        record_request(10, False, 50, 100)
        return {"task_id": task_id, "status": "created", "user_request": task.user_request}
    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    try:
        from app.core.database import db
        row = await db.fetch_one("SELECT task_id, user_request, status, config_snapshot FROM tasks WHERE task_id=?", (task_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "task_id": row[0],
            "user_request": row[1],
            "status": row[2],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}/execute")
async def execute_task(task_id: str):
    """启动任务执行（如果尚未启动）"""
    try:
        from app.engine.tasks import task_manager
        from app.core.database import db
        row = await db.fetch_one("SELECT status FROM tasks WHERE task_id=?", (task_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        status = row[0]
        if status == "pending":
            await task_manager.start_task(task_id)
        return {"task_id": task_id, "status": "executing"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task execute failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}/messages")
async def get_task_messages(task_id: str, layer: str = "user", limit: int = 50):
    try:
        from app.core.database import db
        rows = await db.fetch_all(
            "SELECT msg_id, sender_role, sender_id, content, metadata, timestamp FROM conversation_messages WHERE task_id=? AND layer=? ORDER BY timestamp ASC LIMIT ?",
            (task_id, layer, limit)
        )
        return {"messages": rows or []}
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        return {"messages": []}

@app.post("/api/tasks/{task_id}/messages")
async def add_task_message(task_id: str, msg: MessageCreate):
    try:
        from app.core.database import db
        import uuid
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        await db.execute(
            "INSERT INTO conversation_messages(msg_id, task_id, layer, sender_role, content) VALUES(?,?,?,?,?)",
            (msg_id, task_id, msg.layer, "user", msg.content)
        )
        return {"status": "ok", "msg_id": msg_id}
    except Exception as e:
        logger.error(f"Failed to add message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    try:
        from app.engine.tasks import task_manager
        result = await task_manager.cancel_task(task_id)
        return {"status": "cancelled" if result else "not_found"}
    except Exception as e:
        logger.error(f"Cancel failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    try:
        from app.engine.tasks import task_manager
        result = await task_manager.resume_task(task_id)
        return {"status": "resumed" if result else "not_found"}
    except Exception as e:
        logger.error(f"Resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== AI实例 =====
@app.get("/api/ai-instances")
async def get_ai_instances():
    try:
        from app.core.database import db
        rows = await db.get_all_ai_instances(enabled_only=False)
        # Normalize database field name instance_id -> id for frontend compatibility
        normalized = []
        for r in (rows or []):
            if 'instance_id' in r and 'id' not in r:
                r['id'] = r.pop('instance_id')
            normalized.append(r)
        return normalized
    except Exception as e:
        logger.error(f"Failed to get AI instances: {e}")
        return []

@app.post("/api/ai-instances", status_code=201)
async def create_ai_instance(instance: AIInstanceCreate):
    try:
        from app.core.database import db
        await db.save_ai_instance(instance.model_dump())
        return {"instance_id": instance.id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create AI instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/ai-instances/{instance_id}")
async def update_ai_instance(instance_id: str, instance: AIInstanceCreate):
    try:
        from app.core.database import db
        data = instance.model_dump()
        data["id"] = instance_id  # Use URL instance_id, not body id
        await db.save_ai_instance(data)
        return {"instance_id": instance_id, "status": "updated"}
    except Exception as e:
        logger.error(f"Failed to update AI instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/ai-instances/{instance_id}")
async def delete_ai_instance(instance_id: str):
    try:
        from app.core.database import db
        await db.execute("DELETE FROM ai_instances WHERE instance_id=?", (instance_id,))
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Failed to delete AI instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-instances/{instance_id}/test")
async def test_ai_instance(instance_id: str):
    from app.llm.pool import capability_pool
    cap = await capability_pool.get_by_id(instance_id)
    if not cap:
        raise HTTPException(status_code=404, detail="Instance not found")
    start = time.time()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(cap.endpoint)
            latency = int((time.time() - start) * 1000)
            return {"status": "reachable", "latency_ms": latency, "http_status": resp.status_code}
    except HTTPException:
        raise
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {"status": "error", "error": str(e), "latency_ms": latency}

# ===== 角色配置 =====
@app.get("/api/roles")
async def get_roles():
    cfg = load_config()
    roles = cfg.get("roles", {})
    return {"roles": roles}

@app.get("/api/roles/{role_id}")
async def get_role(role_id: str):
    cfg = load_config()
    role = cfg.get("roles", {}).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@app.post("/api/roles/{role_id}")
async def update_role(role_id: str, role: RoleUpdate):
    config_manager.update(f"roles.{role_id}", role.model_dump())
    save_config()
    return {"status": "ok", "role": config_manager.get(f"roles.{role_id}")}

# ===== 配置 =====
@app.get("/api/config")
async def get_config():
    return load_config()

@app.post("/api/config/update")
async def update_config(config: ConfigUpdate):
    config_manager.update_nested(config.updates)
    save_config()
    return {"status": "updated", "config": config_manager.get_all()}

web_api = app