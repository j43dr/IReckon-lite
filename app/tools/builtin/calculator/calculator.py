import math
import operator
from typing import List, Union, Optional


OPERATIONS = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
    "power": operator.pow,
    "mod": operator.mod,
    "sqrt": lambda x: math.sqrt(x),
    "sin": lambda x: math.sin(x),
    "cos": lambda x: math.cos(x),
    "tan": lambda x: math.tan(x),
    "log": lambda x, base=math.e: math.log(x, base),
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
}


def multi_calculator(operation: str, *args: Union[int, float]) -> Optional[Union[int, float, str]]:
    if operation not in OPERATIONS:
        return f"Unknown operation: {operation}. Available: {', '.join(sorted(OPERATIONS.keys()))}"
    try:
        func = OPERATIONS[operation]
        result = func(*args)
        if isinstance(result, float):
            result = round(result, 10)
        return result
    except ZeroDivisionError:
        return "Error: division by zero"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    print("Calculator test:")
    print("add(1,2,3):", multi_calculator("add", 1, 2, 3))
    print("sqrt(16):", multi_calculator("sqrt", 16))
    print("sin(pi/2):", multi_calculator("sin", math.pi / 2))