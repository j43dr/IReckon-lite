from loguru import logger
from typing import Dict, Any, Optional
import asyncio
import io
import sys
import os
import textwrap
import tempfile
import subprocess
from app.core.config import config_manager


_BUILTIN_ALLOWLIST = frozenset({
    "print", "len", "range", "int", "float", "str", "bool", "list", "dict",
    "tuple", "set", "type", "True", "False", "None", "Exception",
    "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError",
    "StopIteration", "hasattr", "getattr", "setattr", "isinstance",
    "issubclass", "callable", "sorted", "reversed", "enumerate", "zip",
    "map", "filter", "any", "all", "min", "max", "sum", "abs", "round",
    "ord", "chr", "hex", "oct", "bin", "format", "id", "repr", "iter",
    "next", "slice", "super", "property", "staticmethod", "classmethod",
    "object", "MemoryError", "RuntimeError", "SystemError",
    "NotImplementedError",
})


def _safe_builtins() -> dict:
    result = {}
    for name in _BUILTIN_ALLOWLIST:
        if hasattr(__builtins__, name):
            result[name] = getattr(__builtins__, name)
        elif isinstance(__builtins__, dict) and name in __builtins__:
            result[name] = __builtins__[name]
    return result


class SandboxEnvironment:
    def __init__(self):
        self.allowed_modules = config_manager.get(
            "execution.local.allowed_modules",
            ["json", "re", "math", "random", "datetime", "collections", "itertools"],
        )
        self.blocked_keywords = [
            "__import__", "__subclasses__", "subprocess", "socket",
            "ctypes", "os.system", "shutil.rmtree",
        ]

    def _validate_code(self, code: str) -> Optional[str]:
        if not code or not code.strip():
            return "代码为空"
        for kw in self.blocked_keywords:
            if kw in code:
                return f"代码包含禁用内容: {kw}"
        return None

    async def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        is_sandbox = config_manager.get("execution.sandbox_mode", False)
        if is_sandbox:
            return await self._execute_subprocess(code, timeout)
        return await self._execute_local(code, timeout)

    async def _execute_local(self, code: str, timeout: int) -> Dict[str, Any]:
        validation = self._validate_code(code)
        if validation:
            return {"success": False, "error": validation}
        safe_globals = {"__name__": "__main__", "__builtins__": _safe_builtins()}
        for mod in self.allowed_modules:
            try:
                safe_globals[mod] = __import__(mod)
            except ImportError:
                pass
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        try:
            compiled = compile(code, "<sandbox>", "exec", flags=0, dont_inherit=True)
            exec(compiled, safe_globals)
            return {"success": True, "output": stdout_capture.getvalue(), "error": stderr_capture.getvalue()}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    async def _execute_subprocess(self, code: str, timeout: int) -> Dict[str, Any]:
        runner = textwrap.dedent("""\
        import sys, io, json, traceback
        safe_builtins = {builtins}
        allowed = {modules}
        sys.modules.clear()
        safe_globals = {{"__name__": "__main__", "__builtins__": safe_builtins}}
        for m in allowed:
            try:
                safe_globals[m] = __import__(m)
            except:
                pass
        out = io.StringIO(); err = io.StringIO()
        sys.stdout = out; sys.stderr = err
        try:
            exec({code_repr}, safe_globals)
            res = {{"success": True, "output": out.getvalue(), "error": err.getvalue()}}
        except:
            res = {{"success": False, "output": out.getvalue(), "error": traceback.format_exc()}}
        sys.stdout = sys.__stdout__; sys.stderr = sys.__stderr__
        print(json.dumps(res), flush=True)
        """).format(
            builtins=list(_BUILTIN_ALLOWLIST),
            modules=self.allowed_modules,
            code_repr=repr(code),
        )
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
        try:
            tmp.write(runner)
            tmp.close()
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-I", "-u", tmp.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={},
            )
            try:
                stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {"success": False, "error": f"超时（{timeout}秒）"}
            stdout_s = stdout_b.decode("utf-8", errors="replace")
            stderr_s = stderr_b.decode("utf-8", errors="replace")
            try:
                result = json.loads(stdout_s.strip().split("\n")[-1])
                if isinstance(result, dict):
                    return result
            except (json.JSONDecodeError, IndexError):
                pass
            return {"success": proc.returncode == 0, "output": stdout_s, "error": stderr_s}
        finally:
            os.unlink(tmp.name)


sandbox = SandboxEnvironment()
