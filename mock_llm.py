"""
IReckon 3.0 模拟大模型服务
用于测试 - 接收任务请求，返回模拟响应
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import random
import time

app = FastAPI()

class TaskRequest(BaseModel):
    user_request: str
    scheduler_cap_id: Optional[str] = None
    context: Optional[dict] = None

# 模拟的不同角色
ROLES = {
    "scheduler": "我理解了你的请求，正在分析...",
    "executor": "我正在执行任务...",
    "reviewer_efficiency": "我正在优化代码效率...",
    "reviewer_correctness": "我正在检查代码正确性...",
    "learner": "我正在学习新的知识...",
    "tool_manager": "我正在管理工具...",
    "content_filter": "我正在检查内容安全性...",
    "creative": "我正在生成创意内容...",
    "deliverer": "我正在整理输出...",
}

@app.post("/api/tasks")
async def create_task(task: TaskRequest):
    task_id = f"task-{int(time.time())}"
    return {
        "task_id": task_id,
        "status": "created",
        "user_request": task.user_request
    }

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    return {
        "task_id": task_id,
        "status": random.choice(["planning", "executing", "reviewing", "completed"]),
        "progress": random.random()
    }

@app.post("/api/tasks/{task_id}/execute")
async def execute_task(task_id: str, task: TaskRequest):
    # 模拟执行
    responses = []
    for role, msg in ROLES.items():
        responses.append({
            "role": role,
            "content": f"[{role}] {msg}\n\n处理: {task.user_request[:50]}..."
        })
    
    return {
        "task_id": task_id,
        "status": "completed",
        "responses": responses,
        "tokens_input": random.randint(100, 1000),
        "tokens_output": random.randint(200, 2000),
        "cache_hit": random.random() > 0.5,
        "latency_ms": random.randint(100, 2000)
    }

@app.get("/api/config")
async def get_config():
    return {
        "theme": "dark",
        "language": "zh-CN",
        "api_timeout": 30,
        "roles": {
            "scheduler": {"enabled": True, "model": "gpt-4"},
            "executor": {"enabled": True, "model": "gpt-4"},
            "reviewer_efficiency": {"enabled": True, "model": "gpt-4"},
            "reviewer_correctness": {"enabled": True, "model": "gpt-4"},
        },
        "show_in_public": True,  # 角色发言是否在公共区显示
    }

@app.post("/api/config/update")
async def update_config(updates: dict):
    return {"status": "updated", "config": updates}

@app.get("/api/roles")
async def get_roles():
    return {
        "roles": [
            {"id": r, "name": r.replace("_", " ").title(), "enabled": True}
            for r in ROLES.keys()
        ]
    }

@app.post("/api/roles/{role_id}/enable")
async def enable_role(role_id: str, enabled: bool = True):
    return {"role_id": role_id, "enabled": enabled}

@app.get("/api/diagnostics")
async def get_diagnostics():
    return {
        "status": "ok",
        "checks": {
            "api": "ok",
            "mock_llm": "ok",  # 模拟LLM服务
            "roles": "ok",
            "cache": "ok" if random.random() > 0.3 else "miss",
        },
        "stats": {
            "requests_total": random.randint(100, 1000),
            "cache_hit_rate": random.random(),
            "avg_latency_ms": random.randint(100, 500),
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "mock": True}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Mock LLM Server running on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)