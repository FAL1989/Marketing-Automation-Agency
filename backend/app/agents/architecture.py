from typing import List, Dict, Any, Optional
from .base import BaseAgent
from .providers import provider_manager, ProviderType

class ArchitectureDesigner(BaseAgent):
    """Agent specialized in designing and evaluating software architectures"""
    
    def __init__(self):
        super().__init__("ArchitectureDesigner")
        self.design_template = """
        Please design an architecture for the following requirements:
        
        1. System Overview:
           - High-level components
           - Component interactions
           - Data flow
           - System boundaries
        
        2. Technical Stack:
           - Technologies selection
           - Framework choices
           - Database decisions
           - Infrastructure requirements
        
        3. Architecture Patterns:
           - Design patterns
           - Architecture styles
           - Integration patterns
           - Communication protocols
        
        4. Non-Functional Requirements:
           - Scalability approach
           - Performance considerations
           - Security measures
           - Reliability strategies
        
        5. Implementation Guidelines:
           - Development practices
           - Testing strategy
           - Deployment approach
           - Monitoring setup
        
        Requirements:
        {requirements}
        """
        
        self.evaluation_template = """
        Please evaluate the following architecture design:
        
        1. Architecture Review:
           - Design principles adherence
           - Pattern appropriateness
           - Component cohesion
           - System coupling
        
        2. Quality Attributes:
           - Performance characteristics
           - Scalability potential
           - Maintainability aspects
           - Security considerations
        
        3. Risk Assessment:
           - Technical risks
           - Integration challenges
           - Scalability concerns
           - Security vulnerabilities
        
        4. Improvement Areas:
           - Design enhancements
           - Alternative approaches
           - Modern practices adoption
           - Technology updates
        
        Architecture Design:
        {design}
        
        Context and Constraints:
        {context}
        """
        
    async def initialize(self):
        """No special initialization needed"""
        pass
        
    async def process(self, 
                     content: str, 
                     mode: str = "design", 
                     context: Optional[str] = None) -> str:
        """Design new architecture or evaluate existing one"""
        
        if mode == "design":
            # Add requirements to context
            self.add_to_context("user", f"Design architecture for:\n{content}")
            
            # Generate design
            prompt = self.design_template.format(requirements=content)
            
        elif mode == "evaluate":
            # Add design to context
            self.add_to_context(
                "user", 
                f"Evaluate architecture:\nDesign:\n{content}\nContext:\n{context or 'No specific context provided.'}"
            )
            
            # Generate evaluation
            prompt = self.evaluation_template.format(
                design=content,
                context=context or "No specific context provided."
            )
            
        else:
            raise ValueError("Invalid mode")
            
        try:
            result = await provider_manager.get_completion(
                prompt,
                provider_type=ProviderType.ANTHROPIC  # Prefer Anthropic for complex reasoning
            )
            
            # Add result to context
            self.add_to_context("assistant", result)
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to process architecture request: {str(e)}"
            self.add_to_context("system", error_msg)
            raise Exception(error_msg) 