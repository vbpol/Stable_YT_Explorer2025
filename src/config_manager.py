import json
import os
from typing import List
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

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
                data = {"api_key": "", "default_folder": ""}

            keys = ConfigManager.get_available_api_keys()
            api_key = keys[0] if keys else data.get("api_key", "")
            return {
                "api_key": api_key,
                "default_folder": data.get("default_folder", "")
            }
        except Exception:
            return {"api_key": "", "default_folder": ""}

    @staticmethod
    def save_config(api_key, default_folder):
        with open(CONFIG_FILE, "w") as file:
            json.dump({
                "api_key": "",
                "default_folder": default_folder
            }, file, indent=4)

    @staticmethod
    def get_available_api_keys() -> List[str]:
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
        except Exception:
            pass

        try:
            import importlib
            spec = importlib.util.spec_from_file_location("settings", os.path.join(os.getcwd(), "settings.py"))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                val = getattr(mod, "API_KEY", "")
                if val:
                    keys.append(str(val).strip())
        except Exception:
            pass

        seen = set()
        unique = []
        for k in keys:
            if k not in seen:
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
    def get_preferred_quality() -> str:
        try:
            data = {}
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            return data.get("preferred_quality", "best")
        except Exception:
            return "best"

    @staticmethod
    def set_preferred_quality(quality: str):
        try:
            data = {}
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            data["preferred_quality"] = quality or "best"
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass