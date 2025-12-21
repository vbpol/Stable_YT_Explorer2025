import unittest
import os
import shutil
import time
import json
from src.services.cache_manager import CacheManager

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_cache.db"
        # Ensure clean state
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except OSError:
                pass
        self.cache = CacheManager(db_path=self.test_db)
        
    def tearDown(self):
        # Retry cleanup for Windows file locking issues
        max_retries = 5
        for i in range(max_retries):
            if os.path.exists(self.test_db):
                try:
                    os.remove(self.test_db)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                break
            
    def test_set_and_get(self):
        service = "test_service"
        method = "test_method"
        params = {"q": "hello"}
        data = {"items": [1, 2, 3]}
        
        # Set
        self.cache.set(service, method, params, data)
        
        # Get
        cached = self.cache.get(service, method, params)
        self.assertEqual(cached, data)
        
    def test_cache_miss(self):
        cached = self.cache.get("unknown", "method", {})
        self.assertIsNone(cached)
        
    def test_expiration(self):
        service = "temp_service"
        method = "temp_method"
        params = {}
        data = "temp_data"
        
        # Set with 1 second TTL
        self.cache.set(service, method, params, data, ttl=1)
        
        # Should exist immediately
        self.assertIsNotNone(self.cache.get(service, method, params))
        
        # Sleep to expire
        time.sleep(1.1)
        
        # Should be gone
        self.assertIsNone(self.cache.get(service, method, params))

    def test_complex_params(self):
        service = "s"
        method = "m"
        params = {"list": [1, 2], "dict": {"a": 1}}
        data = "complex"
        
        self.cache.set(service, method, params, data)
        self.assertEqual(self.cache.get(service, method, params), data)
        
        # Different params order should produce same key if sorted?
        # CacheManager uses json.dumps(sort_keys=True)
        params2 = {"dict": {"a": 1}, "list": [1, 2]}
        self.assertEqual(self.cache.get(service, method, params2), data)

if __name__ == '__main__':
    unittest.main()
