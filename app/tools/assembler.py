from loguru import logger
from typing import Dict, Any


class Assembler:
    def __init__(self):
        self.assemblies = {}

    def assemble(self, components: Dict[str, Any]) -> str:
        assembled = "\n\n".join(components.values())
        return assembled

    def validate(self, code: str) -> bool:
        try:
            compile(code, "<string>", "exec")
            return True
        except:
            return False


assembler = Assembler()