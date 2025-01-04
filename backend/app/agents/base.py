from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from abc import ABC, abstractmethod

class Message(BaseModel):
    role: str
    content: str
    
class AgentContext(BaseModel):
    messages: List[Message] = []
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    """Base class for all LLM agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.context = AgentContext()
        
    @abstractmethod
    async def process(self, message: str) -> str:
        """Process a message and return a response"""
        pass
        
    def add_to_context(self, role: str, content: str):
        """Add a message to the agent's context"""
        self.context.messages.append(
            Message(role=role, content=content)
        )
        
    def clear_context(self):
        """Clear the agent's context"""
        self.context = AgentContext()
        
    @abstractmethod
    async def initialize(self):
        """Initialize the agent with any required setup"""
        pass 