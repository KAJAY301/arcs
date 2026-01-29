import json
import os
from pathlib import Path
import shutil
import tempfile
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def load_resource_path(name: str) -> str:
    """
    :param name: Should includ file type (.jpg, .png)
    :type name: str
    :return: return the path of the resource
    """
    resource_path = BASE_DIR / "resources" / f"{name}"
    if not resource_path.exists():
        print(f"[config] can't find {resource_path}")
        return ""
    try:
        return str(resource_path)
    except Exception as e:
        print(f"[config] failed to load {resource_path}: {e}")
        return ""

def load_model_path(model_name: str = "best") -> str:
    """
    return: `model_path`
    Deflut: best
    """
    model_path = BASE_DIR / "models" / f"{model_name}.pt"
    if not model_path.exists():
        print(f"[config] can't find {model_path}")
        return ""
    try:
        return str(model_path)
    except Exception as e:
        print(f"[config] failed to load {model_path}: {e}")
        return ""

def load_stylesheet(theme_name: str = "dark") -> str:
    """
    Load `theme_name.qss`
    Deflut: dark
    """
    qss_path = BASE_DIR / "configs" / f"{theme_name}.qss"
    if not qss_path.exists():
        print(f"[config] can't find {qss_path}")
        return ""
    
    try:
        return qss_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[config] failed to load {qss_path}: {e}")
        return ""

def load_env_config() -> dict:
    """
    Load `.env`, return as dict 
    """
    env_path = BASE_DIR / ".env"
    load_dotenv(env_path)
    return{
        "plc_ip": os.getenv("PLC_IP"),
        "plc_port": int(os.getenv("PLC_PORT")),
        "motor_mm_per_pulse_x": float(os.getenv("MOTOR_MM_PER_PULSE_X")),
        "motor_mm_per_pulse_y": float(os.getenv("MOTOR_MM_PER_PULSE_Y")),
    }

def load_json_config(defaults: dict = None) -> dict:
    """
    Load `config.json`, return as dict
    """
    json_path = BASE_DIR / "configs" / "config.json"
    defaults = defaults or {}
    try:
        text = json_path.read_text(encoding="utf-8")
        data = json.loads(text)
        merged = defaults.copy()
        deep_merge(data, merged)
        return merged
    except Exception as e:
        print(f"[config] failed to load {json_path}: {e}")

def deep_merge(source, destination):
    """

    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination

def save_json_config_atomic(cfg: dict, backup: bool = True) -> bool:
    """

    """
    json_path = BASE_DIR / "configs" / "config.json"
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(json_path.parent)) as tf:
            json.dump(cfg, tf, indent=2, ensure_ascii=False)
            tmp_name = tf.name
        if backup and json_path.exists():
            shutil.copy2(str(json_path), str(json_path) + ".bak")
        shutil.move(tmp_name, str(json_path))
        return True
    except Exception as e:
        print(f"[config] failed to save {json_path}: {e}")
        return False




