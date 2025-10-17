"""
AI Response Caching System
Reduces API calls and costs by caching common AI responses
"""

import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class AICache:
    """In-memory cache for AI responses with TTL"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = 3600  # 1 hour default
    
    def _generate_key(self, prompt: str, model: str, context: Optional[Dict] = None) -> str:
        """Generate cache key from prompt and context"""
        # Create deterministic hash
        content = f"{model}:{prompt}"
        if context:
            # Sort context keys for consistency
            sorted_context = json.dumps(context, sort_keys=True)
            content += f":{sorted_context}"
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        key = self._generate_key(prompt, model, context)
        
        if key not in self._cache:
            return None
        
        cached = self._cache[key]
        
        # Check if expired
        if datetime.now() > cached['expires_at']:
            del self._cache[key]
            logger.info("Cache expired", key=key[:8])
            return None
        
        logger.info("Cache hit", key=key[:8], age_seconds=(datetime.now() - cached['created_at']).seconds)
        return cached['response']
    
    def set(
        self, 
        prompt: str, 
        model: str, 
        response: Dict[str, Any], 
        context: Optional[Dict] = None,
        ttl_seconds: Optional[int] = None
    ):
        """Cache an AI response"""
        key = self._generate_key(prompt, model, context)
        ttl = ttl_seconds or self._ttl_seconds
        
        self._cache[key] = {
            'response': response,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl),
            'prompt': prompt[:100],  # Store snippet for debugging
            'model': model
        }
        
        logger.info("Cached AI response", key=key[:8], ttl_seconds=ttl)
    
    def clear_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self._cache.items()
            if now > value['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info("Cleared expired cache entries", count=len(expired_keys))
    
    def clear_all(self):
        """Clear entire cache"""
        count = len(self._cache)
        self._cache.clear()
        logger.info("Cleared all cache", count=count)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active = sum(1 for v in self._cache.values() if now <= v['expires_at'])
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active,
            'expired_entries': len(self._cache) - active,
            'models': list(set(v['model'] for v in self._cache.values()))
        }


# Global cache instance
ai_cache = AICache()
