"""
RAGCache: Fast in-memory cache with TTL
"""

import time
from typing import Any, Optional

class RAGCache:
    def __init__(self, ttl_seconds=300):  # 5 minutes default
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                # Expired - remove
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache a value with current timestamp"""
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
    
    def size(self):
        """Get cache size"""
        return len(self.cache)
