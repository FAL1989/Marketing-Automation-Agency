from typing import List, Dict, Any, Optional
from .base import BaseAgent
from .providers import provider_manager, ProviderType

class CodeAnalyzer(BaseAgent):
    """Agent specialized in analyzing code quality and suggesting improvements"""
    
    def __init__(self):
        super().__init__("CodeAnalyzer")
        self.analysis_template = """
        Please analyze the following code and provide:
        
        1. Code Quality Assessment:
           - Clean Code principles adherence
           - SOLID principles compliance
           - Design patterns identification
           - Code complexity analysis
        
        2. Performance Analysis:
           - Algorithmic efficiency
           - Resource usage
           - Potential bottlenecks
           - Optimization opportunities
        
        3. Security Review:
           - Security vulnerabilities
           - Input validation
           - Data protection
           - Authentication/Authorization concerns
        
        4. Maintainability:
           - Code organization
           - Documentation quality
           - Test coverage
           - Technical debt indicators
        
        5. Improvement Suggestions:
           - Refactoring opportunities
           - Architecture improvements
           - Best practices adoption
           - Modern patterns integration
        
        Code to analyze:
        ```
        {code}
        ```
        """
        
        self.review_template = """
        Please review the following code changes and provide:
        
        1. Impact Analysis:
           - Affected components
           - Breaking changes
           - Dependencies affected
           - Migration requirements
        
        2. Quality Check:
           - Code style consistency
           - Best practices compliance
           - Error handling
           - Edge cases coverage
        
        3. Testing Requirements:
           - Unit test scenarios
           - Integration test needs
           - Performance test cases
           - Security test considerations
        
        Original code:
        ```
        {original_code}
        ```
        
        Changed code:
        ```
        {changed_code}
        ```
        """
        
    async def initialize(self):
        """No special initialization needed"""
        pass
        
    async def process(self, code: str, mode: str = "analyze", original_code: Optional[str] = None) -> str:
        """Analyze code or review changes"""
        
        if mode == "analyze":
            # Add code to context
            self.add_to_context("user", f"Analyze code:\n{code}")
            
            # Generate analysis
            prompt = self.analysis_template.format(code=code)
            
        elif mode == "review" and original_code:
            # Add code to context
            self.add_to_context("user", f"Review changes:\nOriginal:\n{original_code}\nChanged:\n{code}")
            
            # Generate review
            prompt = self.review_template.format(
                original_code=original_code,
                changed_code=code
            )
            
        else:
            raise ValueError("Invalid mode or missing original code for review")
            
        try:
            result = await provider_manager.get_completion(
                prompt,
                provider_type=ProviderType.OPENAI  # Prefer OpenAI for code analysis
            )
            
            # Add result to context
            self.add_to_context("assistant", result)
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to analyze code: {str(e)}"
            self.add_to_context("system", error_msg)
            raise Exception(error_msg) 