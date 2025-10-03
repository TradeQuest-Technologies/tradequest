"""
Custom middleware for logging, rate limiting, etc.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import structlog
from typing import Callable
from app.core.config import settings

logger = structlog.get_logger()

class LoggingMiddleware:
    """Middleware for structured request/response logging"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Process request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                logger.info(
                    "Request completed",
                    method=request.method,
                    url=str(request.url),
                    status_code=message["status"],
                    process_time=process_time
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class RateLimitMiddleware:
    """Simple rate limiting middleware"""
    
    def __init__(self, app):
        self.app = app
        self.requests = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(ts > current_time - settings.RATE_LIMIT_WINDOW for ts in timestamps)
        }
        
        # Check rate limit
        if client_ip in self.requests:
            recent_requests = [
                ts for ts in self.requests[client_ip]
                if ts > current_time - settings.RATE_LIMIT_WINDOW
            ]
            if len(recent_requests) >= settings.RATE_LIMIT_REQUESTS:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )
                await response(scope, receive, send)
                return
        else:
            self.requests[client_ip] = []
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        await self.app(scope, receive, send)