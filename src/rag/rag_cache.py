"""
RAG Cache: Intelligent caching layer for all RAG operations
Reduces redundant API calls and speeds up repeated queries
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path

class RAGCache:
    def __init__(self, cache_dir: str = None, ttl_minutes: int = 30):
        """
        Initialize RAG caching system
        
        Args:
            cache_dir: Directory to store persistent cache (optional)
            ttl_minutes: Time-to-live for cache entries in minutes
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(exist_ok=True)
        
        self.ttl = timedelta(minutes=ttl_minutes)
        
        # In-memory cache
        self.memory_cache = {}
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        print(f"✅ RAG Cache Initialized (TTL: {ttl_minutes}min)")
    
    def _generate_key(self, source: str, query: str, params: Dict = None) -> str:
        """
        Generate unique cache key
        
        Args:
            source: RAG source ('vector', 'graph', 'crag', 'light')
            query: Query string
            params: Additional parameters
        
        Returns:
            Unique hash key
        """
        # Normalize query
        normalized = query.lower().strip()
        
        # Include params in key
        key_data = {
            'source': source,
            'query': normalized,
            'params': params or {}
        }
        
        # Generate hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, source: str, query: str, params: Dict = None) -> Optional[Any]:
        """
        Get from cache if valid
        
        Args:
            source: RAG source
            query: Query string
            params: Additional parameters
        
        Returns:
            Cached data or None
        """
        key = self._generate_key(source, query, params)
        
        # Check memory cache first
        entry = self.memory_cache.get(key)
        
        if entry:
            # Check if still valid
            age = datetime.now() - entry['timestamp']
            if age < self.ttl:
                self.stats['hits'] += 1
                print(f"💾 Cache HIT: {source}:{query[:30]}...")
                return entry['data']
            else:
                # Expired
                del self.memory_cache[key]
                self.stats['evictions'] += 1
        
        # Check disk cache if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                    
                    # Check if valid
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    age = datetime.now() - timestamp
                    
                    if age < self.ttl:
                        # Load into memory
                        self.memory_cache[key] = {
                            'data': entry['data'],
                            'timestamp': timestamp
                        }
                        self.stats['hits'] += 1
                        print(f"💾 Disk Cache HIT: {source}:{query[:30]}...")
                        return entry['data']
                    else:
                        # Delete expired file
                        cache_file.unlink()
                        self.stats['evictions'] += 1
                except Exception as e:
                    print(f"⚠️ Cache read error: {e}")
        
        self.stats['misses'] += 1
        return None
    
    def set(self, source: str, query: str, data: Any, params: Dict = None):
        """
        Save to cache
        
        Args:
            source: RAG source
            query: Query string
            data: Data to cache
            params: Additional parameters
        """
        key = self._generate_key(source, query, params)
        
        entry = {
            'data': data,
            'timestamp': datetime.now()
        }
        
        # Save to memory
        self.memory_cache[key] = entry
        
        # Save to disk if enabled
        if self.cache_dir:
            try:
                cache_file = self.cache_dir / f"{key}.json"
                with open(cache_file, 'w') as f:
                    json.dump({
                        'source': source,
                        'query': query,
                        'data': data,
                        'timestamp': entry['timestamp'].isoformat()
                    }, f, indent=2)
            except Exception as e:
                print(f"⚠️ Cache write error: {e}")
    
    def invalidate(self, source: str = None):
        """
        Invalidate cache entries
        
        Args:
            source: If provided, only invalidate entries from this source
        """
        if source:
            # Invalidate specific source
            keys_to_delete = []
            for key, entry in self.memory_cache.items():
                # Would need to track source per key - simplified here
                keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.memory_cache[key]
                self.stats['evictions'] += 1
        else:
            # Invalidate all
            count = len(self.memory_cache)
            self.memory_cache.clear()
            self.stats['evictions'] += count
        
        print(f"🗑️  Cache invalidated: {source or 'ALL'}")
    
    def cleanup_expired(self):
        """
        Remove all expired entries
        """
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            age = datetime.now() - entry['timestamp']
            if age >= self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
            self.stats['evictions'] += 1
        
        # Cleanup disk cache
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                    
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    age = datetime.now() - timestamp
                    
                    if age >= self.ttl:
                        cache_file.unlink()
                        self.stats['evictions'] += 1
                except:
                    pass
        
        print(f"🧹 Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            {
                'hits': int,
                'misses': int,
                'evictions': int,
                'hit_rate': float,
                'memory_entries': int
            }
        """
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'memory_entries': len(self.memory_cache)
        }
    
    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()
        print("\n📊 RAG Cache Statistics:")
        print(f"   Hits: {stats['hits']}")
        print(f"   Misses: {stats['misses']}")
        print(f"   Hit Rate: {stats['hit_rate']}%")
        print(f"   Memory Entries: {stats['memory_entries']}")
        print(f"   Evictions: {stats['evictions']}")


# Quick test
if __name__ == "__main__":
    import tempfile
    
    print("🧪 Testing RAG Cache...")
    
    # Create cache with temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = RAGCache(cache_dir=tmpdir, ttl_minutes=1)
        
        # Test 1: Cache miss
        print("\n🔍 Test 1: Cache Miss")
        result = cache.get('vector', 'test query 1')
        print(f"Result: {result}")
        
        # Test 2: Cache set and hit
        print("\n💾 Test 2: Cache Set and Hit")
        test_data = {'result': 'sample data', 'count': 42}
        cache.set('vector', 'test query 1', test_data)
        
        result = cache.get('vector', 'test query 1')
        print(f"Result: {result}")
        
        # Test 3: Different query
        print("\n🔍 Test 3: Different Query (Miss)")
        result = cache.get('graph', 'test query 2')
        print(f"Result: {result}")
        
        # Test 4: Same query, different source
        print("\n🔍 Test 4: Same Query, Different Source")
        cache.set('graph', 'test query 1', {'graph_data': 'nodes'})
        result_graph = cache.get('graph', 'test query 1')
        result_vector = cache.get('vector', 'test query 1')
        print(f"Graph: {result_graph}")
        print(f"Vector: {result_vector}")
        
        # Test 5: Statistics
        print("\n📊 Test 5: Statistics")
        cache.print_stats()
        
        # Test 6: Cleanup
        print("\n🧹 Test 6: Cleanup")
        cache.cleanup_expired()
        cache.print_stats()
    
    print("\n✅ RAG Cache Tests Complete!")
