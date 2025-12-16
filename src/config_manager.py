import json
import os
from typing import List
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
import re

CONFIG_FILE = "config.json"
ENV_FILE = ".env"

class ConfigManager:
    @staticmethod
    def load_config():
        try:
            data = {}
            try:
                with open(CONFIG_FILE, "r") as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {"api_key": "", "default_folder": "", "ui": {}}

            keys = ConfigManager.get_available_api_keys()
            api_key = keys[0] if keys else data.get("api_key", "")
            return {
                "api_key": api_key,
                "default_folder": data.get("default_folder", ""),
                "ui": data.get("ui", {})
            }
        except Exception:
            return {"api_key": "", "default_folder": "", "ui": {}}

    @staticmethod
    def save_config(api_key, default_folder):
        try:
            data = {}
            try:
                with open(CONFIG_FILE, "r") as file:
                    data = json.load(file) or {}
            except Exception:
                data = {}
            data["api_key"] = ""
            data["default_folder"] = default_folder
            with open(CONFIG_FILE, "w") as file:
                json.dump(data, file, indent=4)
        except Exception:
            pass

    @staticmethod
    def get_available_api_keys() -> List[str]:
        keys: List[str] = []
        try:
            if load_dotenv is not None:
                base = os.getcwd()
                candidates = [
                    os.path.join(base, ENV_FILE),
                    os.path.join(base, "dist", ENV_FILE),
                ]
                for p in candidates:
                    try:
                        if os.path.exists(p):
                            load_dotenv(p, override=True)
                    except Exception:
                        pass
            env_multi = os.getenv("YOUTUBE_API_KEYS", "")
            env_single = os.getenv("YOUTUBE_API_KEY", "")
            if env_multi:
                keys.extend([k.strip() for k in env_multi.split(",") if k.strip()])
            if env_single:
                keys.append(env_single.strip())
        except Exception:
            pass
        # Manual parse fallback if environment not set correctly
        try:
            base = os.getcwd()
            for p in (os.path.join(base, ENV_FILE), os.path.join(base, "dist", ENV_FILE)):
                try:
                    if not os.path.exists(p):
                        continue
                    with open(p, "r", encoding="utf-8") as f:
                        content = f.read()
                    for line in content.splitlines():
                        ln = line.strip()
                        if not ln or ln.startswith("#"):
                            continue
                        if ln.upper().startswith("YOUTUBE_API_KEYS="):
                            vals = ln.split("=", 1)[1]
                            keys.extend([k.strip() for k in vals.split(",") if k.strip()])
                        elif ln.upper().startswith("YOUTUBE_API_KEY="):
                            val = ln.split("=", 1)[1].strip()
                            if val:
                                keys.append(val)
                except Exception:
                    pass
        except Exception:
            pass
        # Normalize and filter to likely API keys
        def _normalize(s: str) -> str:
            try:
                s = s.strip().strip("[]").strip("\"").strip("'")
                return s.strip()
            except Exception:
                return s
        def _is_likely_api_key(s: str) -> bool:
            try:
                if not s:
                    return False
                if "googleusercontent.com" in s.lower():
                    return False
                if len(s) < 30 or len(s) > 120:
                    return False
                if not re.match(r"^[A-Za-z0-9_-]+$", s):
                    return False
                return True
            except Exception:
                return False
        cleaned: List[str] = []
        for k in keys:
            nk = _normalize(k)
            if _is_likely_api_key(nk):
                cleaned.append(nk)

        try:
            import importlib
            spec = importlib.util.spec_from_file_location("settings", os.path.join(os.getcwd(), "settings.py"))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                val = getattr(mod, "API_KEY", "")
                if val:
                    cleaned.append(str(val).strip())
        except Exception:
            pass

        seen = set()
        unique = []
        for k in cleaned:
            if k not in seen:
                unique.append(k)
                seen.add(k)
        return unique

    @staticmethod
    def save_env_api_keys(api_keys: List[str]):
        try:
            existing = ConfigManager.get_available_api_keys() or []
        except Exception:
            existing = []
        merged = []
        seen = set()
        for k in list(existing) + list(api_keys or []):
            try:
                s = str(k or "").strip()
            except Exception:
                s = k
            if s and s not in seen:
                merged.append(s)
                seen.add(s)
        content = "YOUTUBE_API_KEYS=" + ",".join(merged)
        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    @staticmethod
    def get_data_dir():
        try:
            base = os.getcwd()
            data_dir = os.path.join(base, "data")
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except Exception:
            return os.getcwd()

    @staticmethod
    def get_last_search_path(kind: str):
        name = "last_" + (kind or "playlists") + "_search.json"
        return os.path.join(ConfigManager.get_data_dir(), name)

    @staticmethod
    def save_json(path: str, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def load_json(path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def get_last_mode_path() -> str:
        try:
            base = ConfigManager.get_data_dir()
            return os.path.join(base, "last_mode.json")
        except Exception:
            return "last_mode.json"

    @staticmethod
    def save_last_mode(mode: str):
        try:
            path = ConfigManager.get_last_mode_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"mode": (mode or "").strip().lower()}, f)
        except Exception:
            pass

    @staticmethod
    def load_last_mode() -> str:
        try:
            path = ConfigManager.get_last_mode_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                    m = str(data.get("mode", "")).strip().lower()
                    if m in ("videos", "playlists"):
                        return m
        except Exception:
            pass
        return ""

    @staticmethod
    def get_persistence_mode() -> str:
        try:
            val = os.getenv("PERSISTENCE_MODE", "json").strip().lower()
            if val in ("json", "sqlite", "django"):
                return val
        except Exception:
            pass
        return "json"

    @staticmethod
    def get_ui_pagination_min_rows() -> int:
        try:
            env_val = os.getenv("PAGINATION_MIN_ROWS")
            if env_val:
                v = int(env_val)
                if v > 0:
                    return v
        except Exception:
            pass
        try:
            cfg = ConfigManager.load_config() or {}
            ui = cfg.get("ui", {}) or {}
            v = int(ui.get("pagination_min_rows", 10))
            return max(1, v)
        except Exception:
            return 10

    @staticmethod
    def set_cookie_source(source: str):
        try:
            src = (source or "").strip().lower()
            data = {}
            try:
                with open(CONFIG_FILE, "r") as file:
                    data = json.load(file) or {}
            except Exception:
                data = {}
            ui = dict(data.get("ui", {}) or {})
            ui["cookie_source"] = src
            data["ui"] = ui
            with open(CONFIG_FILE, "w") as file:
                json.dump(data, file, indent=4)
        except Exception:
            pass

    @staticmethod
    def get_cookie_source() -> str:
        try:
            cfg = ConfigManager.load_config() or {}
            ui = cfg.get("ui", {}) or {}
            src = str(ui.get("cookie_source", "firefox")).strip().lower()
            if src in ("none","edge","chrome","firefox","cookiefile"):
                return src
        except Exception:
            pass
        return "firefox"

    @staticmethod
    def set_use_channel_title_fallback(value: bool):
        try:
            data = {}
            try:
                with open(CONFIG_FILE, "r") as file:
                    data = json.load(file) or {}
            except Exception:
                data = {}
            ui = dict(data.get("ui", {}) or {})
            ui["use_channel_title_fallback"] = bool(value)
            data["ui"] = ui
            with open(CONFIG_FILE, "w") as file:
                json.dump(data, file, indent=4)
        except Exception:
            pass

    @staticmethod
    def get_use_channel_title_fallback() -> bool:
        try:
            cfg = ConfigManager.load_config() or {}
            ui = cfg.get("ui", {}) or {}
            val = ui.get("use_channel_title_fallback")
            if val is None:
                return True
            return bool(val)
        except Exception:
            return True
