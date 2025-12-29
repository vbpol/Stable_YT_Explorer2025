import json
import os
import json
import os
from typing import List, Dict, Any, Optional
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from src.logger import setup_logger
    logger = setup_logger()
except ImportError:
    import logging
    logger = logging.getLogger("ConfigManager")

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    pass

CONFIG_FILE = "config.json"
ENV_FILE = ".env"

class ConfigManager:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from config.json, with priority over individual env lookups."""
        try:
            data = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as file:
                    data = json.load(file) or {}
            
            # Priority: 1. config.json 2. first key in .env
            api_key = data.get("api_key", "").strip()
            if not api_key:
                keys = ConfigManager.get_available_api_keys()
                api_key = keys[0] if keys else ""

            return {
                "api_key": api_key,
                "default_folder": data.get("default_folder", ""),
                "ui": data.get("ui", {})
            }
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"api_key": "", "default_folder": "", "ui": {}}

    @staticmethod
    def save_config(api_key: str, default_folder: str) -> None:
        """Save configuration values to the config file."""
        if not isinstance(api_key, str): api_key = ""
        if not isinstance(default_folder, str): default_folder = ""
        try:
            data = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as file:
                        data = json.load(file) or {}
                except Exception: pass
            data["api_key"] = api_key.strip()
            data["default_folder"] = default_folder.strip()
            with open(CONFIG_FILE, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    @staticmethod
    def get_available_api_keys() -> List[str]:
        """Retrieve all unique API keys from .env and settings.py."""
        keys: List[str] = []
        try:
            if load_dotenv is not None:
                load_dotenv(ENV_FILE)
            env_multi = os.getenv("YOUTUBE_API_KEYS", "")
            env_single = os.getenv("YOUTUBE_API_KEY", "")
            if env_multi:
                keys.extend([k.strip() for k in env_multi.split(",") if k.strip()])
            if env_single:
                keys.append(env_single.strip())
        except Exception as e:
            logger.error(f"Error loading env keys: {e}")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("settings", os.path.join(os.getcwd(), "settings.py"))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                val = getattr(mod, "API_KEY", "")
                if val:
                    keys.append(str(val).strip())
        except Exception as e:
            logger.error(f"Error loading settings.py keys: {e}")

        seen = set()
        unique = []
        for k in keys:
            if k and k not in seen:
                unique.append(k)
                seen.add(k)
        return unique

    @staticmethod
    def save_env_api_keys(api_keys: List[str]):
        content = "YOUTUBE_API_KEYS=" + ",".join(api_keys)
        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    @staticmethod
    def get_data_dir() -> str:
        try:
            base = os.getcwd()
            data_dir = os.path.join(base, "data")
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except Exception:
            return os.getcwd()

    @staticmethod
    def get_last_search_path(kind: str) -> str:
        name = "last_" + (kind or "playlists") + "_search.json"
        return os.path.join(ConfigManager.get_data_dir(), name)

    @staticmethod
    def save_json(path: str, data: Any) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def load_json(path: str) -> Any:
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
    def save_last_mode(mode: str) -> None:
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
    def set_cookie_source(source: str) -> None:
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
    def set_use_channel_title_fallback(value: bool) -> None:
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
            val = ui.get("ui", {}).get("use_channel_title_fallback")
            # If manually called it might be nested, handle safely
            if val is None:
                 val = ui.get("use_channel_title_fallback")
            if val is None:
                return True
            return bool(val)
        except Exception:
            return True

    @staticmethod
    def validate_api_key(api_key: str) -> str:
        """
        Validates an API key by making a small request.
        Returns: "VALID", "QUOTA", "INVALID", "ERROR"
        """
        if not api_key:
            return "INVALID"
        try:
            # We need to do a lightweight call. Searching for 1 item is usually fine.
            # If we don't have the lib, we can't strictly validate, but assume VALID/ERROR?
            # We imported build above.
            youtube = build("youtube", "v3", developerKey=api_key)
            # Try a very cheap call, e.g. a search for "test" with 1 result
            youtube.search().list(part="id", q="test", maxResults=1).execute()
            return "VALID"
        except HttpError as e:
            try:
                # parse error reason
                content = e.content.decode() if isinstance(e.content, bytes) else str(e.content)
                data = json.loads(content)
                reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                if reason in ("quotaExceeded", "dailyLimitExceeded"):
                    return "QUOTA"
                if reason in ("keyInvalid", "badRequest", "api_key_invalid"):
                    return "INVALID"
            except Exception:
                pass
            return "INVALID"
        except Exception as e:
            logger.error(f"Validation network error: {e}")
            return "ERROR"

    @staticmethod
    def add_to_env_keys(new_key: str):
        """Adds a new key to the .env list if not already present."""
        if not new_key:
            return
        current_keys = ConfigManager.get_available_api_keys()
        if new_key in current_keys:
            return
        current_keys.append(new_key)
        ConfigManager.save_env_api_keys(current_keys)
