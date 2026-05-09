#!/usr/bin/env python3
"""
安全代码执行实现 - 支持沙箱模式/本地模式切换
"""
import asyncio
import io
import os
import sys
import json
import textwrap
import tempfile
import subprocess
import importlib.util
from typing import Dict, Any, List, Optional
from loguru import logger
from app.core.config import config_manager


_BUILTIN_WHITELIST = frozenset({
    "print", "len", "range", "int", "float", "str", "bool", "list", "dict",
    "tuple", "set", "type", "True", "False", "None", "Exception",
    "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError",
    "StopIteration", "hasattr", "getattr", "setattr", "isinstance",
    "issubclass", "callable", "sorted", "reversed", "enumerate", "zip",
    "map", "filter", "any", "all", "min", "max", "sum", "abs", "round",
    "ord", "chr", "hex", "oct", "bin", "format", "id", "repr", "iter",
    "next", "slice", "super", "property", "staticmethod", "classmethod",
    "object", "MemoryError", "RuntimeError", "SystemError",
    "NotImplementedError", "StopAsyncIteration", "TimeoutError",
    "bytes", "bytearray", "memoryview", "input", "open",
})


def _is_sandbox_mode() -> bool:
    return config_manager.get("execution.sandbox_mode", False)


def _get_allowed_modules() -> List[str]:
    return config_manager.get("execution.local.allowed_modules", [
        "json", "re", "asyncio", "math", "random", "datetime",
        "collections", "itertools", "typing", "textwrap", "string",
        "fractions", "decimal", "statistics",
    ])


def _get_max_code_length() -> int:
    return config_manager.get("execution.local.max_code_length", 100000)


def _build_safe_globals() -> dict:
    safe_builtins = {}
    for name in _BUILTIN_WHITELIST:
        if hasattr(__builtins__, name):
            safe_builtins[name] = getattr(__builtins__, name)
        elif isinstance(__builtins__, dict) and name in __builtins__:
            safe_builtins[name] = __builtins__[name]
    safe_globals = {
        "__name__": "__main__",
        "__builtins__": safe_builtins,
    }
    for mod_name in _get_allowed_modules():
        try:
            mod = importlib.import_module(mod_name)
            safe_globals[mod_name] = mod
        except ImportError:
            pass
    return safe_globals


def _validate_code(code: str) -> Optional[str]:
    if not code or not code.strip():
        return "代码为空"
    if len(code) > _get_max_code_length():
        return f"代码过长（最大{_get_max_code_length()}字符）"
    dangerous_keywords = [
        "__import__", "__subclasses__", "__mro__", "__bases__",
        "__globals__", "__code__", "__func__", "__self__",
    ]
    for kw in dangerous_keywords:
        if kw in code:
            return f"代码包含危险关键字: {kw}"
    return None


async def _execute_local(code: str, timeout: int) -> Dict[str, Any]:
    validation = _validate_code(code)
    if validation:
        return {"success": False, "output": "", "error": validation}

    safe_globals = _build_safe_globals()
    local_vars = {}

    def _run():
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        try:
            compiled = compile(code, "<exec>", "exec", flags=0, dont_inherit=True)
            exec(compiled, safe_globals, local_vars)
            return {
                "success": True,
                "output": stdout_capture.getvalue(),
                "error": stderr_capture.getvalue(),
                "locals": {k: str(type(v)) for k, v in local_vars.items()
                           if not k.startswith("_")},
            }
        except Exception as e:
            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "error": str(e),
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    try:
        return await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _run),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return {"success": False, "output": "", "error": f"执行超时（{timeout}秒）"}


async def _execute_in_sandbox(code: str, timeout: int) -> Dict[str, Any]:
    sandbox_script = textwrap.dedent("""\
    import sys, io, json, traceback
    allowed_modules = {allowed_modules!r}
    safe_builtins = {safe_builtins!r}
    sys.modules.clear()
    for mn in list(sys.modules.keys()):
        if mn not in ("sys", "io", "json", "traceback"):
            del sys.modules[mn]
    safe_globals = {{"__name__": "__main__", "__builtins__": safe_builtins}}
    for mod_name in allowed_modules:
        try:
            safe_globals[mod_name] = __import__(mod_name)
        except Exception:
            pass
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    local_vars = {{}}
    try:
        exec({code!r}, safe_globals, local_vars)
        result = {{"success": True, "output": stdout_capture.getvalue(), "error": stderr_capture.getvalue()}}
    except Exception:
        result = {{"success": False, "output": stdout_capture.getvalue(), "error": traceback.format_exc()}}
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print(json.dumps(result), flush=True)
    """).format(
        code=code,
        allowed_modules=list(_get_allowed_modules()),
        safe_builtins=list(_BUILTIN_WHITELIST),
    )

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
    try:
        tmp.write(sandbox_script)
        tmp.close()
        sandbox_timeout = config_manager.get("execution.sandbox.timeout", timeout)
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-I", "-u", tmp.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={},
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=sandbox_timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"success": False, "output": "", "error": f"执行超时（{sandbox_timeout}秒）"}
        stdout_str = stdout_bytes.decode("utf-8", errors="replace")
        stderr_str = stderr_bytes.decode("utf-8", errors="replace")
        try:
            result = json.loads(stdout_str.strip().split("\n")[-1])
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, IndexError):
            pass
        return {"success": proc.returncode == 0, "output": stdout_str, "error": stderr_str}
    finally:
        os.unlink(tmp.name)


async def execute_safe(
    code: str,
    timeout: int = 30,
    allowed_modules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if _is_sandbox_mode():
        return await _execute_in_sandbox(code, timeout)
    return await _execute_local(code, timeout)
