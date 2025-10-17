"""
AI Router - Smart model selection and request management
Chooses between GPT-4o and GPT-4o-mini based on complexity
"""

from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.services.ai_cache import ai_cache
from app.services.ai_queue import ai_queue

logger = structlog.get_logger()


class AIRouter:
    """Smart AI request router with caching and model selection"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Model selection criteria
        self.simple_keywords = [
            'simple', 'basic', 'quick', 'explain', 'what is', 'how to',
            'define', 'list', 'show me', 'tell me'
        ]
        
        self.complex_keywords = [
            'analyze', 'optimize', 'backtest', 'strategy', 'advanced',
            'complex', 'detailed', 'comprehensive', 'calculate', 'predict'
        ]
    
    def _select_model(self, prompt: str, force_model: Optional[str] = None) -> str:
        """
        Select appropriate model based on prompt complexity
        
        GPT-4o-mini: Simple queries, explanations, basic tasks (80% cheaper)
        GPT-4o: Complex analysis, strategy building, advanced tasks
        """
        if force_model:
            return force_model
        
        prompt_lower = prompt.lower()
        
        # Check for simple keywords
        simple_score = sum(1 for kw in self.simple_keywords if kw in prompt_lower)
        complex_score = sum(1 for kw in self.complex_keywords if kw in prompt_lower)
        
        # Short prompts are usually simple
        if len(prompt) < 50:
            simple_score += 1
        
        # Use mini for simple tasks
        if simple_score > complex_score:
            logger.info("Selected GPT-4o-mini for simple task")
            return "gpt-4o-mini"
        
        logger.info("Selected GPT-4o for complex task")
        return "gpt-4o"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        request_type: str = "general",
        temperature: float = 0.7,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        force_model: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl: int = 3600,
        priority: int = 0
    ) -> Any:
        """
        Make a chat completion request with caching and queueing
        
        Args:
            messages: Chat messages
            user_id: User making the request
            request_type: Type of request (coach, copilot, block_helper)
            temperature: Model temperature
            tools: Function calling tools
            tool_choice: Tool choice strategy
            force_model: Force specific model (gpt-4o or gpt-4o-mini)
            use_cache: Whether to use caching
            cache_ttl: Cache time-to-live in seconds
            priority: Request priority (higher = processed first)
        
        Returns:
            OpenAI chat completion response
        """
        
        # Get user's last message for model selection
        user_message = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), '')
        
        # Select model
        model = self._select_model(user_message, force_model)
        
        # Check cache (only for non-tool requests)
        if use_cache and not tools:
            cache_key_context = {
                'temperature': temperature,
                'request_type': request_type
            }
            cached_response = ai_cache.get(user_message, model, cache_key_context)
            if cached_response:
                logger.info("Returning cached AI response", user_id=user_id, model=model)
                return cached_response
        
        # Define request handler
        async def handler():
            logger.info(
                "Making AI request",
                user_id=user_id,
                model=model,
                request_type=request_type,
                has_tools=bool(tools)
            )
            
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = tool_choice
            
            response = await self.client.chat.completions.create(**request_params)
            
            # Cache response (only for non-tool requests)
            if use_cache and not tools:
                cache_key_context = {
                    'temperature': temperature,
                    'request_type': request_type
                }
                ai_cache.set(user_message, model, response, cache_key_context, cache_ttl)
            
            return response
        
        # Queue the request
        try:
            response = await ai_queue.enqueue(
                user_id=user_id,
                request_type=request_type,
                handler=handler,  # Pass the async function
                priority=priority
            )
            
            # Ensure we got a valid response
            if response is None:
                logger.error("AI router received None response", user_id=user_id)
                raise Exception("AI request returned no response")
            
            return response
        except Exception as e:
            logger.error("AI request failed", error=str(e), user_id=user_id)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI system statistics"""
        return {
            'cache': ai_cache.get_stats(),
            'queue': ai_queue.get_queue_status()
        }


# Global router instance
ai_router = AIRouter()
