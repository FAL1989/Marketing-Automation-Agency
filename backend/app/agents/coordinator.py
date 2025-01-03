from typing import List, Dict, Any, Optional, Type
from .base import BaseAgent, Message
from .requirements import RequirementsAnalyzer
from .code import CodeAnalyzer
from .architecture import ArchitectureDesigner
from .security import SecurityAnalyzer

class AgentCoordinator:
    """Coordinates collaboration between multiple agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.shared_context: List[Message] = []
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the coordinator"""
        self.agents[agent.name] = agent
        
    def register_default_agents(self):
        """Register the default set of agents"""
        self.register_agent(RequirementsAnalyzer())
        self.register_agent(CodeAnalyzer())
        self.register_agent(ArchitectureDesigner())
        self.register_agent(SecurityAnalyzer())
        
    def add_to_shared_context(self, role: str, content: str):
        """Add a message to the shared context"""
        message = Message(role=role, content=content)
        self.shared_context.append(message)
        
        # Update all agents with the new context
        for agent in self.agents.values():
            agent.add_to_context(role, content)
            
    async def analyze_project(self, requirement: str) -> Dict[str, str]:
        """Perform a complete project analysis using all agents"""
        results = {}
        
        # 1. Requirements Analysis
        if "RequirementsAnalyzer" in self.agents:
            req_analysis = await self.agents["RequirementsAnalyzer"].process(requirement)
            self.add_to_shared_context("assistant", req_analysis)
            results["requirements"] = req_analysis
            
        # 2. Architecture Design
        if "ArchitectureDesigner" in self.agents:
            arch_design = await self.agents["ArchitectureDesigner"].process(
                requirement,
                context="\n".join(msg.content for msg in self.shared_context)
            )
            self.add_to_shared_context("assistant", arch_design)
            results["architecture"] = arch_design
            
        # 3. Security Analysis
        if "SecurityAnalyzer" in self.agents:
            security_analysis = await self.agents["SecurityAnalyzer"].process(
                requirement,
                context="\n".join(msg.content for msg in self.shared_context)
            )
            self.add_to_shared_context("assistant", security_analysis)
            results["security"] = security_analysis
            
        return results
        
    async def review_code(self, code: str, original_code: Optional[str] = None) -> Dict[str, str]:
        """Perform a complete code review using all agents"""
        results = {}
        
        # 1. Code Analysis
        if "CodeAnalyzer" in self.agents:
            code_analysis = await self.agents["CodeAnalyzer"].process(
                code,
                mode="review" if original_code else "analyze",
                original_code=original_code
            )
            self.add_to_shared_context("assistant", code_analysis)
            results["code"] = code_analysis
            
        # 2. Security Review
        if "SecurityAnalyzer" in self.agents:
            security_analysis = await self.agents["SecurityAnalyzer"].process(
                code,
                context="\n".join(msg.content for msg in self.shared_context)
            )
            self.add_to_shared_context("assistant", security_analysis)
            results["security"] = security_analysis
            
        # 3. Architecture Impact
        if "ArchitectureDesigner" in self.agents and original_code:
            arch_evaluation = await self.agents["ArchitectureDesigner"].process(
                code,
                mode="evaluate",
                context=f"Original Code:\n{original_code}\n\nAnalysis Context:\n" + 
                       "\n".join(msg.content for msg in self.shared_context)
            )
            self.add_to_shared_context("assistant", arch_evaluation)
            results["architecture"] = arch_evaluation
            
        return results
        
    async def get_agent_opinion(self, agent_name: str, content: str, **kwargs) -> str:
        """Get a specific agent's opinion on a topic"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
            
        result = await self.agents[agent_name].process(content, **kwargs)
        self.add_to_shared_context("assistant", result)
        return result
        
    def clear_context(self):
        """Clear the shared context and all agents' contexts"""
        self.shared_context = []
        for agent in self.agents.values():
            agent.clear_context()
            
    async def initialize_all(self):
        """Initialize all registered agents"""
        for agent in self.agents.values():
            await agent.initialize() 