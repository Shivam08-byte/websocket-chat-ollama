import os
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def load_config(app_name: str) -> Dict[str, Any]:
    """
    Load YAML config for a given sub-app from the `config/` directory.
    Falls back to empty dict if file missing or PyYAML not available.
    
    Looks for `config/{app_name}.yaml` and `config/{app_name}.yml`.
    """
    base_dir = Path(os.getenv("APP_ROOT", "."))
    config_dir = base_dir / "config"
    candidates = [config_dir / f"{app_name}.yaml", config_dir / f"{app_name}.yml"]

    for path in candidates:
        if path.exists() and path.is_file():
            if yaml is None:
                return {}
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    if isinstance(data, dict):
                        return data
                    return {}
            except Exception:
                return {}
    return {}
