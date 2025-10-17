"""
AI Request Queue System
Manages concurrent AI requests with rate limiting and queueing
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
import structlog
import uuid

logger = structlog.get_logger()


class AIRequestQueue:
    """Queue system for AI requests with rate limiting"""
    
    def __init__(self, max_concurrent: int = 5, requests_per_minute: int = 50):
        self.max_concurrent = max_concurrent
        self.requests_per_minute = requests_per_minute
        self.queue: deque = deque()
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.request_history: deque = deque(maxlen=requests_per_minute)
        self._lock = asyncio.Lock()
    
    async def enqueue(
        self, 
        user_id: str, 
        request_type: str,
        handler: Callable,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Enqueue an AI request
        
        Args:
            user_id: User making the request
            request_type: Type of AI request (coach, copilot, block_helper)
            handler: Async function to execute
            priority: Higher priority = processed first (default 0)
        
        Returns:
            Response from the handler
        """
        request_id = str(uuid.uuid4())
        
        # Check rate limit
        if not await self._check_rate_limit():
            raise Exception("Rate limit exceeded. Please wait a moment and try again.")
        
        # Create request object
        request = {
            'id': request_id,
            'user_id': user_id,
            'type': request_type,
            'handler': handler,
            'priority': priority,
            'created_at': datetime.now(),
            'status': 'queued'
        }
        
        async with self._lock:
            # Add to queue (sorted by priority)
            self.queue.append(request)
            self.queue = deque(sorted(self.queue, key=lambda x: -x['priority']))
            
            queue_position = len(self.queue)
            logger.info(
                "Request queued",
                request_id=request_id[:8],
                user_id=user_id,
                type=request_type,
                queue_position=queue_position,
                active_requests=len(self.active_requests)
            )
        
        # Wait for processing
        return await self._process_queue(request_id)
    
    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Remove old requests from history
        while self.request_history and self.request_history[0] < one_minute_ago:
            self.request_history.popleft()
        
        # Check if under limit
        return len(self.request_history) < self.requests_per_minute
    
    async def _process_queue(self, request_id: str) -> Dict[str, Any]:
        """Process queued requests"""
        while True:
            async with self._lock:
                # Find our request
                request = next((r for r in self.queue if r['id'] == request_id), None)
                
                if not request:
                    # Request was processed - check if it's complete
                    if request_id in self.active_requests:
                        request = self.active_requests[request_id]
                        
                        # Wait for completion
                        if request['status'] == 'completed':
                            result = request.get('result')
                            del self.active_requests[request_id]
                            
                            if result is None:
                                raise Exception("Request completed but result is None")
                            return result
                        
                        elif request['status'] == 'failed':
                            error = request.get('error', 'Unknown error')
                            del self.active_requests[request_id]
                            raise Exception(error)
                        
                        # Still processing, wait more
                    else:
                        raise Exception("Request not found in queue or active requests")
                
                # Check if we can process
                if len(self.active_requests) < self.max_concurrent and request in self.queue:
                    # Remove from queue and mark as active
                    try:
                        self.queue.remove(request)
                    except ValueError:
                        # Already removed by another coroutine
                        continue
                    
                    request['status'] = 'processing'
                    self.active_requests[request_id] = request
                    
                    logger.info(
                        "Processing request",
                        request_id=request_id[:8],
                        type=request['type'],
                        wait_time=(datetime.now() - request['created_at']).seconds
                    )
                    
                    # Process in background
                    asyncio.create_task(self._execute_request(request_id))
                    
            # Wait a bit before checking again
            await asyncio.sleep(0.1)  # Check more frequently
    
    async def _execute_request(self, request_id: str):
        """Execute the actual AI request"""
        request = self.active_requests.get(request_id)
        if not request:
            return
        
        try:
            # Record request time for rate limiting
            self.request_history.append(datetime.now())
            
            # Execute handler
            logger.info("Executing handler", request_id=request_id[:8])
            result = await request['handler']()
            
            # Validate result
            if result is None:
                logger.error("Handler returned None", request_id=request_id[:8])
                raise Exception("Handler returned None result")
            
            # Store result
            request['result'] = result
            request['status'] = 'completed'
            
            logger.info(
                "Request completed",
                request_id=request_id[:8],
                type=request['type'],
                duration=(datetime.now() - request['created_at']).seconds,
                has_result=result is not None
            )
            
        except Exception as e:
            logger.error(
                "Request failed",
                request_id=request_id[:8],
                error=str(e)
            )
            request['error'] = str(e)
            request['status'] = 'failed'
    
    def get_queue_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current queue status"""
        if user_id:
            user_queued = sum(1 for r in self.queue if r['user_id'] == user_id)
            user_active = sum(1 for r in self.active_requests.values() if r['user_id'] == user_id)
            
            return {
                'user_queued': user_queued,
                'user_active': user_active,
                'total_queued': len(self.queue),
                'total_active': len(self.active_requests),
                'requests_last_minute': len(self.request_history)
            }
        
        return {
            'total_queued': len(self.queue),
            'total_active': len(self.active_requests),
            'max_concurrent': self.max_concurrent,
            'requests_last_minute': len(self.request_history),
            'rate_limit': self.requests_per_minute
        }


# Global queue instance
ai_queue = AIRequestQueue(max_concurrent=10, requests_per_minute=100)
