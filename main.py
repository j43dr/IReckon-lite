#!/usr/bin/env python3
import asyncio, io, signal, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
try:
    from app.core.logger import setup_logging, logger
    from app.core.database import db
    from app.core.config import config_manager
    from app.core.updater import updater
    from app.core.bootstrap import bootstrap_run
    from app.llm.pool import capability_pool
    from app.engine.tasks import task_manager
    from app.engine.learner import idle_loop
    from app.vision.vision_system import vision_system
    from app.web.ws import log_consumer
    from app.tools.registry import register_builtin_tools
except ImportError:
    setup_logging = None
    logger = None
    db = None
    config_manager = None  # type: ignore
    updater = None
    bootstrap_run = None  # type: ignore
    capability_pool = None
    task_manager = None
    idle_loop = None
    vision_system = None
    log_consumer = None  # type: ignore
    register_builtin_tools = None  # type: ignore
    import logging
    logger = logging.getLogger("ireckon-lite")
    logging.basicConfig(level=logging.INFO)

_IS_LITE = config_manager is None

class IReckonApp:
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._tasks = []

    async def initialize(self):
        if _IS_LITE:
            logger.info("IReckon Lite 模式启动 (仅前端)")
            return
        setup_logging()
        logger.info(f"启动 {config_manager.get('system.name')} v{config_manager.get('system.version')}")
        await self._check_update()
        await db.connect()
        await capability_pool.refresh()
        await register_builtin_tools()
        try:
            br = await bootstrap_run(dry_run=True)
            if br is not None:
                logger.info(f"Bootstrap dry-run result: {br}")
        except Exception as e:
            logger.debug(f"Bootstrap dry-run failed: {e}")
        self._tasks.append(asyncio.create_task(idle_loop.run()))
        self._tasks.append(asyncio.create_task(vision_system.start()))
        self._tasks.append(asyncio.create_task(log_consumer()))
        logger.info("系统初始化完成")

    async def _check_update(self):
        if updater is None or not updater.should_check():
            return
        updater.mark_checked()
        version = await updater.check()
        if version:
            logger.info(f"发现新版本 v{version}，请运行 python scripts/update.py 进行更新")

    async def shutdown(self):
        logger.info("正在关闭系统...")
        self._shutdown_event.set()
        for task in self._tasks:
            task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        if db is not None:
            await db.close()
        logger.info("系统已关闭")

async def start_backend():
    import uvicorn
    if _IS_LITE:
        logger.info("Lite 模式: 不启动后端 API (由 run_streamlit.py 独立运行)")
        return
    host = config_manager.get("server.host", "0.0.0.0")
    port = config_manager.get("server.port", 8000)
    log_level = config_manager.get("server.log_level", "info")
    config = uvicorn.Config("app.web.api:app", host=host, port=port, log_level=log_level, loop="asyncio")
    logger.info(f"后台 API 服务已启动 -> http://{host}:{port}/docs")
    await uvicorn.Server(config).serve()

async def main():
    app = IReckonApp()
    await app.initialize()
    loop = asyncio.get_running_loop()
    def _signal_handler():
        asyncio.create_task(app.shutdown())
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            try:
                loop = asyncio.get_event_loop()
                if hasattr(loop, "add_signal_handler"):
                    loop.add_signal_handler(sig, _signal_handler)
            except (NotImplementedError, RuntimeError):
                pass
    backend_task = asyncio.create_task(start_backend())
    try: await app._shutdown_event.wait()
    finally:
        backend_task.cancel()
        try: await backend_task
        except asyncio.CancelledError: pass
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
