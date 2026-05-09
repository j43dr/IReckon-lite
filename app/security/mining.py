import re
from loguru import logger


class MiningDetector:
    def __init__(self):
        self.mining_patterns = [
            r"pool\.minexmr\.com",
            r"stratum\+tcp://",
            r"stratum\+ssl://",
            r"xmrig",
            r"minergate",
            r"cryptonight",
            r"ethminer",
            r"cpuminer",
            r"cgminer",
            r"bfgminer",
            r"ccminer",
            r"sgminer",
            r"claymore",
            r"phoenixminer",
            r"t-rex",
            r"nbminer",
            r"lolminer",
            r"teamredminer",
            r"gminer",
            r"-u\s+\w+\.\w+",
            r"--algo\s+(rx/0|cn/gpu|ethash|kawpow)",
            r"donate-level\s*=\s*0",
            r"nicehash",
            r"prohashing",
            r"nanopool",
            r"ethermine",
            r"f2pool",
            r"hiveon",
            r"flexpool",
        ]
        self.compiled = [re.compile(p, re.IGNORECASE) for p in self.mining_patterns]

    def scan_code(self, code: str) -> bool:
        for pattern in self.compiled:
            if pattern.search(code):
                logger.warning(f"检测到挖矿代码: {pattern.pattern[:40]}...")
                return True
        return False

    def scan_command_line(self, cmdline: str) -> bool:
        for pattern in self.compiled:
            if pattern.search(cmdline):
                logger.warning(f"检测到挖矿命令: {cmdline[:80]}...")
                return True
        return False

    async def scan_processes(self, process_list: list) -> bool:
        for proc_info in process_list:
            cmdline = proc_info.get('cmdline', '') if isinstance(proc_info, dict) else str(proc_info)
            if self.scan_command_line(cmdline):
                return True
        return False
