import json
import base64
import hashlib
from typing import Any, Dict, List, Optional


OPERATIONS = {
    "upper": lambda s, **kw: s.upper(),
    "lower": lambda s, **kw: s.lower(),
    "reverse": lambda s, **kw: s[::-1],
    "length": lambda s, **kw: str(len(s)),
    "trim": lambda s, **kw: s.strip(),
    "count": lambda s, target=None, **kw: str(s.count(target)) if target else str(len(s)),
    "base64_encode": lambda s, **kw: base64.b64encode(s.encode()).decode(),
    "base64_decode": lambda s, **kw: base64.b64decode(s).decode(errors="replace"),
    "md5": lambda s, **kw: hashlib.md5(s.encode()).hexdigest(),
    "sha256": lambda s, **kw: hashlib.sha256(s.encode()).hexdigest(),
    "json_parse": lambda s, **kw: json.dumps(json.loads(s), indent=2, ensure_ascii=False),
    "split": lambda s, sep=None, **kw: json.dumps(s.split(sep), ensure_ascii=False) if sep else json.dumps(list(s), ensure_ascii=False),
    "replace": lambda s, old=None, new="", **kw: s.replace(old, new) if old else s,
    "contains": lambda s, substr=None, **kw: str(substr in s) if substr else "False",
}


def string_toolbox(operation: str, *args, **kwargs) -> str:
    if operation not in OPERATIONS:
        return f"Unknown operation: {operation}. Available: {', '.join(sorted(OPERATIONS.keys()))}"
    text = args[0] if args else kwargs.get("text", "")
    result = OPERATIONS[operation](text, **kwargs)
    return str(result)