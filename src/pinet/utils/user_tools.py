import importlib.util
import os
from typing import Dict, Any


def load_user_tools(base_path: str = None) -> Dict[str, Any]:
    """
    Loads `__tools__` from `__pinet__.py` in the given path.
    If no path is provided, defaults to current working directory.
    """
    base_path = base_path or os.getcwd()
    user_module_path = os.path.join(base_path, "__pinet__.py")

    if not os.path.exists(user_module_path):
        return {}

    spec = importlib.util.spec_from_file_location("__pinet__", user_module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore

    return getattr(module, "__tools__", {})
