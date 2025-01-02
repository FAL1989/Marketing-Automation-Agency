import anthropic
from typing import Optional, Dict, Any, List
from ..base import AIProvider, AIRequest, AIResponse
from app.core.config import settings
from ...monitoring.metrics import monitor_ai_request

class AnthropicProvider(AIProvider):
    def __init__(self):
        super().__init__()
        # TODO: Implementar integração com Anthropic quando necessário
        pass

    @monitor_ai_request(service="anthropic", model="claude")
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Implementação temporária"""
        return AIResponse(
            content="Anthropic provider not implemented yet",
            model_used="claude",
            usage={"total_tokens": 0},
            raw_response={}
        )

    @monitor_ai_request(service="anthropic", model="sentiment")
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Implementação temporária"""
        return {"sentiment": 0.0}

    @monitor_ai_request(service="anthropic", model="classification")
    async def classify_text(self, text: str, categories: List[str]) -> Dict[str, float]:
        """Implementação temporária"""
        return {category: 0.0 for category in categories} 