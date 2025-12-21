import sqlite3
import json
import hashlib
import time
import os
from typing import Optional, Any, Dict

class CacheManager:
    """
    Manages SQLite-based caching for API responses to reduce quota usage.
    """
    DB_PATH = os.path.join("src", "data", "api_cache.sqlite3")

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self.DB_PATH
        self._init_db()

    def _init_db(self):
        try:
            dirname = os.path.dirname(self.db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_cache (
                        key TEXT PRIMARY KEY,
                        response TEXT,
                        timestamp REAL,
                        expires_at REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"CacheManager init error: {e}")

    def _generate_key(self, service: str, method: str, params: Dict[str, Any]) -> str:
        """Generates a unique key for the API request."""
        # Sort params to ensure consistent keys
        param_str = json.dumps(params, sort_keys=True)
        raw = f"{service}:{method}:{param_str}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, service: str, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """Retrieve cached response if valid."""
        key = self._generate_key(service, method, params)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT response, expires_at FROM api_cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    response_json, expires_at = row
                    # Check expiration (if expires_at is 0, it never expires)
                    if expires_at > 0 and time.time() > expires_at:
                        self.delete(key)
                        return None
                    return json.loads(response_json)
        except Exception:
            pass
        return None

    def set(self, service: str, method: str, params: Dict[str, Any], response: Any, ttl: int = 86400 * 7):
        """
        Cache a response.
        ttl: Time to live in seconds. Default 7 days. 0 for infinite.
        """
        key = self._generate_key(service, method, params)
        expires_at = time.time() + ttl if ttl > 0 else 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO api_cache (key, response, timestamp, expires_at) VALUES (?, ?, ?, ?)",
                    (key, json.dumps(response), time.time(), expires_at)
                )
                conn.commit()
        except Exception:
            pass

    def delete(self, key: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM api_cache WHERE key = ?", (key,))
                conn.commit()
        except Exception:
            pass
    
    def clear_expired(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM api_cache WHERE expires_at > 0 AND expires_at < ?", (time.time(),))
                conn.commit()
        except Exception:
            pass
