from loguru import logger
from typing import Dict, Any, List, Optional
import re


class SecurityFilter:
    def __init__(self):
        self.blocked_patterns: List[str] = config_manager.get(
            "security.blocked_patterns",
            [
                r"rm\s+-rf\s+/",
                r"format\s+\w:\s*/q",
                r"del\s+/[sf].*",
                r":\(\)\s*\{.*:\);",
                r"bash\s+-i\s+>&/dev/tcp/",
                r"powershell.*-EncodedCommand",
                r"certutil.*-urlcache.*-f",
                r"wget.*\|\s*(bash|sh)",
                r"curl.*\|\s*(bash|sh)",
                r"chmod\s+\+?777",
                r"usermod.*root",
                r"passwd.*root",
            ],
        )
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.blocked_patterns]
        self.command_filter = CommandFilter()

    async def check(self, content: str) -> Dict[str, Any]:
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return {"allowed": False, "reason": f"blocked_pattern: {pattern.pattern[:50]}"}
        return {"allowed": True}

    async def check_command(self, cmd: str) -> Dict[str, Any]:
        return self.command_filter.check(cmd)

    async def filter_content(self, content: str) -> str:
        result = await self.check(content)
        if result["allowed"]:
            return content
        return "[内容被安全过滤器拦截]"

    async def check_code(self, code: str) -> Dict[str, Any]:
        dangerous = [
            "os.system", "subprocess.", "shutil.rmtree", "os.remove",
            "__import__", "eval(", "exec(", "compile(",
            "pickle.load", "cPickle.load",
            "ctypes.", "socket.", "win32api",
            "base64.b64decode", "bytes.fromhex",
        ]
        for kw in dangerous:
            if kw in code:
                return {"allowed": False, "reason": f"危险代码模式: {kw}"}
        return {"allowed": True}


class CommandFilter:
    DANGEROUS_COMMANDS = [
        r"^\s*(rm|del|deltree|rd)\s+",
        r"^\s*format\s+",
        r"^\s*mkfs\s+",
        r"^\s*dd\s+if=",
        r"^\s*shutdown\s+",
        r"^\s*reboot\s+",
        r"^\s*init\s+0",
        r"^\s*poweroff\s+",
        r"^\s*halt\s+",
        r"^\s*chmod\s+777",
        r"^\s*chown\s+",
        r"^\s*usermod\s+",
        r"^\s*passwd\s+",
        r"^\s*mv\s+.*\s+/(?!dev|tmp)",
        r"^\s*cp\s+.*\s+/(?!dev|tmp)",
        r"^\s*>.*/dev/",
        r"^\s*wget.*\|.*(bash|sh|python)",
        r"^\s*curl.*\|.*(bash|sh|python)",
        r"^\s*echo.*>.*/etc/",
        r"^\s*iptables",
        r"^\s*route\s+",
        r"^\s*ifconfig\s+.*(down|0\.0\.0\.0)",
    ]

    def __init__(self):
        self.compiled = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_COMMANDS]

    def check(self, cmd: str) -> Dict[str, Any]:
        for pattern in self.compiled:
            if pattern.search(cmd):
                return {"allowed": False, "reason": f"危险命令: {cmd[:50]}"}
        return {"allowed": True}

    def sanitize(self, cmd: str) -> str:
        for pat in self.DANGEROUS_COMMANDS:
            cmd = re.sub(pat, "# BLOCKED: ", cmd, flags=re.IGNORECASE)
        return cmd


from app.core.config import config_manager
security_filter = SecurityFilter()
command_filter = CommandFilter()
