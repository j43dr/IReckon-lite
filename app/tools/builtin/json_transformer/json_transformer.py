"""
JSON Transformer
"""
import json
from collections.abc import MutableMapping


def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten(d, sep='_'):
    result = {}
    for k, v in d.items():
        parts = k.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = v
    return result


def json_transformer(operation: str, *args, **kwargs):
    ops = {
        "flatten": lambda d: flatten(d),
        "unflatten": lambda d: unflatten(d),
        "diff": lambda d1, d2: json.dumps({k: d1.get(k) != d2.get(k) for k in set(d1) | set(d2)}),
    }
    if operation not in ops:
        return f"不支持的操作: {operation}"
    try:
        return ops[operation](*args, **kwargs)
    except Exception as e:
        return f"计算出错: {e}"