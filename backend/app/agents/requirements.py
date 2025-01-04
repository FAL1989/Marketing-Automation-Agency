from typing import List, Dict, Any
from .base import BaseAgent
from .providers import provider_manager, ProviderType

class RequirementsAnalyzer(BaseAgent):
    """Agent specialized in analyzing and breaking down requirements"""
    
    def __init__(self):
        super().__init__("RequirementsAnalyzer")
        self.analysis_template = """
        Please analyze the following requirement and provide:
        
        1. Core Functionality:
           - Main features and capabilities
           - Critical user interactions
           - Expected outcomes
        
        2. Technical Considerations:
           - Architecture implications
           - Performance requirements
           - Security considerations
           - Scalability needs
        
        3. Dependencies:
           - External systems
           - Required APIs
           - Data requirements
        
        4. Implementation Risks:
           - Technical challenges
           - Potential bottlenecks
           - Security concerns
        
        5. Acceptance Criteria:
           - Functional requirements
           - Non-functional requirements
           - Performance metrics
        
        Requirement: {requirement}
        """
        
    async def initialize(self):
        """No special initialization needed"""
        pass
        
    async def process(self, requirement: str) -> str:
        """Analyze a requirement and provide structured insights"""
        
        # Add requirement to context
        self.add_to_context("user", requirement)
        
        # Generate analysis
        prompt = self.analysis_template.format(requirement=requirement)
        try:
            analysis = await provider_manager.get_completion(
                prompt,
                provider_type=ProviderType.OPENAI  # Prefer OpenAI for complex analysis
            )
            
            # Add analysis to context
            self.add_to_context("assistant", analysis)
            
            return analysis
            
        except Exception as e:
            error_msg = f"Failed to analyze requirement: {str(e)}"
            self.add_to_context("system", error_msg)
            raise Exception(error_msg) 