"""
Simple in-memory caching for API responses
Improves performance for repeated requests
"""
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """
    Simple in-memory cache with TTL support
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.cache = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        
    def _generate_key(self, data: Any) -> str:
        """
        Generate cache key from data
        
        Args:
            data: Data to generate key from
            
        Returns:
            str: Cache key (MD5 hash)
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.now() > entry['expires']:
            del self.cache[key]
            self.misses += 1
            logger.debug(f"Cache expired for key: {key[:8]}...")
            return None
        
        self.hits += 1
        logger.debug(f"Cache hit for key: {key[:8]}...")
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        ttl = ttl or self.default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            'value': value,
            'expires': expires,
            'created': datetime.now()
        }
        
        logger.debug(f"Cached value for key: {key[:8]}... (TTL: {ttl}s)")
    
    def delete(self, key: str):
        """
        Delete value from cache
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Deleted cache key: {key[:8]}...")
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry['expires']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'entries': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }
    
    def get_size_estimate(self) -> int:
        """
        Estimate cache size in bytes
        
        Returns:
            int: Estimated size in bytes
        """
        import sys
        total_size = sys.getsizeof(self.cache)
        
        for entry in self.cache.values():
            total_size += sys.getsizeof(entry)
            total_size += sys.getsizeof(entry['value'])
        
        return total_size


# Global cache instance
_global_cache = SimpleCache(default_ttl=300)


def get_cache() -> SimpleCache:
    """Get global cache instance"""
    return _global_cache


def cache_model_metadata(model_name: str, metadata: dict, ttl: int = 3600):
    """
    Cache model metadata
    
    Args:
        model_name: Model identifier
        metadata: Model metadata
        ttl: Time-to-live in seconds
    """
    cache = get_cache()
    key = f"model_meta_{model_name}"
    cache.set(key, metadata, ttl)


def get_cached_model_metadata(model_name: str) -> Optional[dict]:
    """
    Get cached model metadata
    
    Args:
        model_name: Model identifier
        
    Returns:
        Cached metadata or None
    """
    cache = get_cache()
    key = f"model_meta_{model_name}"
    return cache.get(key)
