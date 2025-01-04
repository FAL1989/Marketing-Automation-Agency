from typing import List, Dict, Any, Optional
from .base import BaseAgent
from .providers import provider_manager, ProviderType

class SecurityAnalyzer(BaseAgent):
    """Agent specialized in security analysis and vulnerability assessment"""
    
    def __init__(self):
        super().__init__("SecurityAnalyzer")
        self.analysis_template = """
        Please perform a security analysis of the following system:
        
        1. Vulnerability Assessment:
           - OWASP Top 10 analysis
           - Common vulnerabilities
           - Security misconfigurations
           - Exposure points
        
        2. Authentication & Authorization:
           - Access control review
           - Authentication mechanisms
           - Session management
           - Permission models
        
        3. Data Security:
           - Data protection measures
           - Encryption practices
           - Sensitive data handling
           - Data privacy compliance
        
        4. Infrastructure Security:
           - Network security
           - Cloud security
           - Container security
           - Service security
        
        5. Security Controls:
           - Input validation
           - Output encoding
           - Error handling
           - Logging practices
        
        System Description:
        {system_description}
        
        Additional Context:
        {context}
        """
        
        self.remediation_template = """
        Please provide security remediation recommendations for the following vulnerabilities:
        
        1. Risk Assessment:
           - Vulnerability severity
           - Exploit likelihood
           - Business impact
           - Risk rating
        
        2. Remediation Steps:
           - Technical fixes
           - Configuration changes
           - Code updates
           - Process improvements
        
        3. Implementation Plan:
           - Priority order
           - Resource requirements
           - Timeline estimation
           - Testing approach
        
        4. Prevention Measures:
           - Security controls
           - Monitoring setup
           - Training needs
           - Policy updates
        
        Vulnerabilities:
        {vulnerabilities}
        
        System Context:
        {context}
        """
        
    async def initialize(self):
        """No special initialization needed"""
        pass
        
    async def process(self,
                     content: str,
                     mode: str = "analyze",
                     context: Optional[str] = None) -> str:
        """Analyze security or provide remediation recommendations"""
        
        if mode == "analyze":
            # Add system description to context
            self.add_to_context(
                "user",
                f"Analyze security for:\n{content}\nContext:\n{context or 'No specific context provided.'}"
            )
            
            # Generate analysis
            prompt = self.analysis_template.format(
                system_description=content,
                context=context or "No specific context provided."
            )
            
        elif mode == "remediate":
            # Add vulnerabilities to context
            self.add_to_context(
                "user",
                f"Provide remediation for:\n{content}\nContext:\n{context or 'No specific context provided.'}"
            )
            
            # Generate remediation
            prompt = self.remediation_template.format(
                vulnerabilities=content,
                context=context or "No specific context provided."
            )
            
        else:
            raise ValueError("Invalid mode")
            
        try:
            result = await provider_manager.get_completion(
                prompt,
                provider_type=ProviderType.OPENAI  # Prefer OpenAI for security analysis
            )
            
            # Add result to context
            self.add_to_context("assistant", result)
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to process security request: {str(e)}"
            self.add_to_context("system", error_msg)
            raise Exception(error_msg) 