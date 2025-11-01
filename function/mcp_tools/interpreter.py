"""Safe Python code execution tool for data analysis and reasoning."""

from __future__ import annotations

import ast
import io
from contextlib import redirect_stdout
from typing import Callable


def create_interpreter_tool() -> dict[str, Callable]:
    """Create safe Python code interpreter tool.

    Returns:
        Dictionary mapping tool name to callable function.
    """

    def python_interpreter(code: str) -> str:
        """Execute Python code safely for data analysis.

        Args:
            code: Python code to execute.

        Returns:
            Execution result or error message.

        Security:
            Only allows importing: math, statistics, datetime, json, re
            No file I/O, network access, or system calls permitted.
        """
        allowed_modules = {"math", "statistics", "datetime", "json", "re"}

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in allowed_modules:
                            return f"Security Error: Module '{alias.name}' not allowed. Permitted modules: {', '.join(allowed_modules)}"

                elif isinstance(node, ast.ImportFrom):
                    if node.module not in allowed_modules:
                        return f"Security Error: Module '{node.module}' not allowed. Permitted modules: {', '.join(allowed_modules)}"

            safe_builtins = {
                "abs": abs,
                "all": all,
                "any": any,
                "ascii": ascii,
                "bin": bin,
                "bool": bool,
                "chr": chr,
                "dict": dict,
                "divmod": divmod,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "format": format,
                "hex": hex,
                "int": int,
                "isinstance": isinstance,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "oct": oct,
                "ord": ord,
                "pow": pow,
                "print": print,
                "range": range,
                "reversed": reversed,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
            }

            buffer = io.StringIO()

            with redirect_stdout(buffer):
                exec(code, {"__builtins__": safe_builtins})

            output = buffer.getvalue()

            if not output.strip():
                return "Code executed successfully (no output)"

            return output

        except SyntaxError as e:
            return f"Syntax Error: {e!s}"

        except Exception as e:
            return f"Execution Error: {e!s}"

    return {
        "python_interpreter": python_interpreter,
    }
