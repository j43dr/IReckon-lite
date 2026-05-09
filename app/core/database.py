import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite
from cryptography.fernet import Fernet, InvalidToken
from loguru import logger
from .config import config_manager


class Database:
    _instance: Optional["Database"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_init") and self._init:
            return
        self._init = True
        self._conn = None
        self._fernet = None
        self._write_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        data_dir = Path(config_manager.get("system.data_dir", "./data"))
        db_dir = data_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_dir / "ireckon.db"

    async def _get_cipher(self):
        if self._fernet is None:
            key_path = Path(config_manager.get("system.data_dir", "./data")) / ".key"
            key_path.parent.mkdir(parents=True, exist_ok=True)
            if key_path.exists():
                with open(key_path, "rb") as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_path, "wb") as f:
                    f.write(key)
                if os.name == "posix":
                    try:
                        await asyncio.to_thread(key_path.chmod, 0o600)
                    except Exception:
                        pass
            self._fernet = Fernet(key)
        return self._fernet

    async def connect(self):
        async with self._connect_lock:
            if self._conn is not None:
                return
            # Normalize and validate journal mode
            journal = (config_manager.get("database.journal_mode", "DELETE") or "DELETE").upper()
            ALLOWED_JOURNALS = {"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL"}
            if journal not in ALLOWED_JOURNALS:
                journal = "DELETE"
            timeout = config_manager.get("database.timeout", 5.0)
            self._conn = await aiosqlite.connect(str(self.db_path), timeout=timeout, isolation_level=None)
            # Apply the validated journal mode
            try:
                await self._conn.execute(f"PRAGMA journal_mode={journal}")
            except Exception as e:
                logger.warning(f"Failed to set PRAGMA journal_mode to {journal}: {e}")
            await self._conn.execute("PRAGMA foreign_keys = ON")
            await self._create_tables()
            logger.info(f"DB connected {self.db_path} (journal={journal})")

    async def _create_tables(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, user_request TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, config_snapshot TEXT, output_dir TEXT);
            CREATE TABLE IF NOT EXISTS ai_instances (instance_id TEXT PRIMARY KEY, name TEXT, endpoint TEXT, model TEXT, api_key_encrypted TEXT, parameters TEXT, tags TEXT, cost_per_1k REAL, max_context INTEGER, enabled INTEGER);
            CREATE TABLE IF NOT EXISTS tool_parts (part_id TEXT PRIMARY KEY, name TEXT, description TEXT, language TEXT, code TEXT, input_schema TEXT, output_schema TEXT, tags TEXT, model_path TEXT, created_by TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS knowledge_entries (entry_id TEXT PRIMARY KEY, type TEXT, title TEXT, content TEXT, source TEXT, vector_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS conversation_messages (msg_id TEXT PRIMARY KEY, task_id TEXT, layer TEXT, sender_role TEXT, sender_id TEXT, content TEXT, metadata TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (task_id) REFERENCES tasks(task_id));
            CREATE TABLE IF NOT EXISTS task_board_states (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT UNIQUE NOT NULL, state_json TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS token_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, role TEXT, model TEXT, prompt_tokens INTEGER, completion_tokens INTEGER, total_tokens INTEGER, cost REAL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_task_board_task_id ON task_board_states (task_id);
        """)
        await self._conn.commit()
        await self._migrate_task_board()

    async def _migrate_task_board(self):
        try:
            row = await self.fetch_one("SELECT sql FROM sqlite_master WHERE type='table' AND name='task_board_states'")
            if row and "UNIQUE" not in (row[0] or ""):
                await self._conn.executescript("""
                    BEGIN TRANSACTION;
                    ALTER TABLE task_board_states RENAME TO task_board_states_old;
                    CREATE TABLE task_board_states (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT UNIQUE NOT NULL, state_json TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                    INSERT OR IGNORE INTO task_board_states (task_id, state_json, updated_at) SELECT task_id, state_json, updated_at FROM task_board_states_old;
                    DROP TABLE task_board_states_old;
                    COMMIT;
                """)
                await self._conn.commit()
        except Exception as e:
            logger.debug(f"Task board migration skipped: {e}")

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def execute(self, sql, params=()):
        if self._conn is None:
            await self.connect()
        async with self._write_lock:
            async with self._conn.cursor() as cur:
                await cur.execute(sql, params)
                await self._conn.commit()
                return cur.lastrowid or 0

    async def fetch_one(self, sql, params=()):
        if self._conn is None:
            await self.connect()
        async with self._conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()

    async def fetch_all(self, sql, params=()):
        if self._conn is None:
            await self.connect()
        async with self._conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            if not rows:
                return []
            cols = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(cols, r)) for r in rows]

    async def save_ai_instance(self, instance: Dict):
        cipher = await self._get_cipher()
        enc = cipher.encrypt(instance.get("api_key", "").encode()).decode() if instance.get("api_key") else ""
        iid = instance.get("id") or instance.get("instance_id")
        if not iid:
            raise ValueError("AI instance must have 'id' or 'instance_id'")
        await self.execute(
            "INSERT OR REPLACE INTO ai_instances(instance_id, name, endpoint, model, api_key_encrypted, parameters, tags, cost_per_1k, max_context, enabled) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (iid, instance.get("name", ""), instance.get("endpoint", ""), instance.get("model", ""), enc,
             json.dumps(instance.get("parameters", {})), json.dumps(instance.get("tags", [])),
             instance.get("cost_per_1k_tokens", 0.0), instance.get("max_context", 4096),
             1 if instance.get("enabled", True) else 0)
        )

    async def get_ai_instance(self, iid):
        row = await self.fetch_one("SELECT * FROM ai_instances WHERE instance_id=?", (iid,))
        if not row:
            return None
        return row

    async def get_all_ai_instances(self, enabled_only=True):
        sql = "SELECT * FROM ai_instances"
        if enabled_only:
            sql += " WHERE enabled=1"
        rows = await self.fetch_all(sql)
        return rows if rows else []

    async def save_token_stats(self, stats: Dict):
        await self.execute(
            "INSERT INTO token_stats(task_id, role, model, prompt_tokens, completion_tokens, total_tokens, cost) VALUES(?,?,?,?,?,?,?)",
            (
                stats.get("task_id"),
                stats.get("role", "unknown"),
                stats.get("model", "unknown"),
                stats.get("prompt_tokens", 0),
                stats.get("completion_tokens", 0),
                stats.get("total_tokens", 0),
                stats.get("cost", 0.0),
            )
        )

    async def save_tool(self, tool_entry: Dict):
        await self.execute(
            "INSERT OR REPLACE INTO tool_parts(part_id, name, description, language, code, input_schema, output_schema, tags, model_path, created_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                tool_entry.get("tool_id", ""),
                tool_entry.get("name", tool_entry.get("tool_type", "model")),
                tool_entry.get("description", tool_entry.get("capabilities", str([]))),
                tool_entry.get("language", "python"),
                tool_entry.get("code", ""),
                tool_entry.get("input_schema", "{}"),
                tool_entry.get("output_schema", "{}"),
                json.dumps(tool_entry.get("tags", [])),
                tool_entry.get("model_path", tool_entry.get("model_id", "")),
                tool_entry.get("created_by", "model-factory"),
            )
        )


db = Database()