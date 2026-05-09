import asyncio
import tempfile
import os
import subprocess
import json
import re
from typing import List, Dict, Optional, Any
from loguru import logger
from app.core.config import config_manager


class CodeScanner:
    def __init__(self, tool: Optional[str] = None):
        self.tool = tool or config_manager.get("security.code_scanner", "bandit")
        self._available = self._check_tool()

    def _check_tool(self) -> bool:
        try:
            subprocess.run([self.tool, "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    async def scan(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
        issues = self._scan_static(code, language)
        if self._available:
            external = await self._run_external_scanner(code, language)
            issues.extend(external)
        return issues

    def _scan_static(self, code: str, language: str) -> List[Dict[str, Any]]:
        issues = []
        if language != "python":
            return issues
        patterns = {
            "hardcoded_password": (r'(password|passwd|pwd|secret|api[_-]?key)\s*[:=]\s*["\'][^"\']+["\']', "HIGH"),
            "eval_usage": (r'\beval\s*\(', "HIGH"),
            "exec_usage": (r'\bexec\s*\(', "HIGH"),
            "pickle_load": (r'\bpickle\.loads?\s*\(', "HIGH"),
            "insecure_request": (r'requests\.get\(["\']http:', "MEDIUM"),
            "sql_injection": (r'execute\(.*["\']%.*["\']\s*%', "HIGH"),
            "shell_injection": (r'subprocess\.\w+\(.*shell\s*=\s*True', "HIGH"),
            "tempfile_unsafe": (r'tempfile\.mktemp\s*\(', "MEDIUM"),
            "assert_usage": (r'\bassert\s+', "LOW"),
            "broad_except": (r'\bexcept\s*:', "LOW"),
        }
        for rule_name, (pattern, severity) in patterns.items():
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count("\n") + 1
                issues.append({
                    "rule": rule_name,
                    "severity": severity,
                    "line": line_num,
                    "code": match.group()[:80],
                })
        return issues

    async def _run_external_scanner(self, code: str, language: str) -> List[Dict[str, Any]]:
        filepath = None
        try:
            suffix = f".{language}" if language else ".py"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w") as f:
                f.write(code)
                f.flush()
                filepath = f.name
            return await self._run_scanner(filepath)
        except Exception as e:
            logger.error(f"外部扫描器失败: {e}")
            return []
        finally:
            if filepath and os.path.exists(filepath):
                try:
                    os.unlink(filepath)
                except Exception:
                    pass

    async def _run_scanner(self, filepath: str) -> List[Dict[str, Any]]:
        proc = None
        try:
            if self.tool == "bandit":
                proc = await asyncio.create_subprocess_exec(
                    "bandit", "-f", "json", filepath,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                if proc.returncode is not None:
                    report = json.loads(stdout.decode())
                    return report.get("results", [])
            elif self.tool == "semgrep":
                proc = await asyncio.create_subprocess_exec(
                    "semgrep", "--config", "auto", "--json", filepath,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                report = json.loads(stdout.decode())
                return report.get("results", [])
        except asyncio.TimeoutError:
            if proc:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
            logger.warning(f"扫描超时: {filepath}")
        except Exception as e:
            logger.error(f"扫描执行失败: {e}")
        return []


code_scanner = CodeScanner()
