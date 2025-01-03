from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from app.agents import (
    RequirementsAnalyzer,
    CodeAnalyzer,
    ArchitectureDesigner,
    SecurityAnalyzer,
    coordinator
)

router = APIRouter(prefix="/agents", tags=["agents"])

# Request/Response models
class RequirementAnalysisRequest(BaseModel):
    requirement: str
    
class RequirementAnalysisResponse(BaseModel):
    analysis: str
    
class CodeAnalysisRequest(BaseModel):
    code: str
    mode: str = "analyze"  # "analyze" or "review"
    original_code: Optional[str] = None
    
class CodeAnalysisResponse(BaseModel):
    analysis: str
    
class ArchitectureRequest(BaseModel):
    content: str
    mode: str = "design"  # "design" or "evaluate"
    context: Optional[str] = None
    
class ArchitectureResponse(BaseModel):
    result: str
    
class SecurityRequest(BaseModel):
    content: str
    mode: str = "analyze"  # "analyze" or "remediate"
    context: Optional[str] = None
    
class SecurityResponse(BaseModel):
    result: str
    
class ProjectAnalysisRequest(BaseModel):
    requirement: str
    
class ProjectAnalysisResponse(BaseModel):
    requirements: Optional[str] = None
    architecture: Optional[str] = None
    security: Optional[str] = None
    
class CodeReviewRequest(BaseModel):
    code: str
    original_code: Optional[str] = None
    
class CodeReviewResponse(BaseModel):
    code: Optional[str] = None
    security: Optional[str] = None
    architecture: Optional[str] = None
    
class AgentOpinionRequest(BaseModel):
    agent_name: str
    content: str
    mode: Optional[str] = None
    context: Optional[str] = None

# Individual Agent Endpoints
@router.post("/analyze-requirement", response_model=RequirementAnalysisResponse)
async def analyze_requirement(request: RequirementAnalysisRequest):
    """Analyze a requirement using the RequirementsAnalyzer agent"""
    try:
        analyzer = RequirementsAnalyzer()
        await analyzer.initialize()
        
        analysis = await analyzer.process(request.requirement)
        return RequirementAnalysisResponse(analysis=analysis)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze requirement: {str(e)}"
        )
        
@router.post("/analyze-code", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code using the CodeAnalyzer agent"""
    try:
        analyzer = CodeAnalyzer()
        await analyzer.initialize()
        
        analysis = await analyzer.process(
            request.code,
            mode=request.mode,
            original_code=request.original_code
        )
        return CodeAnalysisResponse(analysis=analysis)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze code: {str(e)}"
        )
        
@router.post("/design-architecture", response_model=ArchitectureResponse)
async def design_architecture(request: ArchitectureRequest):
    """Design or evaluate architecture using the ArchitectureDesigner agent"""
    try:
        designer = ArchitectureDesigner()
        await designer.initialize()
        
        result = await designer.process(
            request.content,
            mode=request.mode,
            context=request.context
        )
        return ArchitectureResponse(result=result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process architecture request: {str(e)}"
        )
        
@router.post("/analyze-security", response_model=SecurityResponse)
async def analyze_security(request: SecurityRequest):
    """Analyze security or provide remediation using the SecurityAnalyzer agent"""
    try:
        analyzer = SecurityAnalyzer()
        await analyzer.initialize()
        
        result = await analyzer.process(
            request.content,
            mode=request.mode,
            context=request.context
        )
        return SecurityResponse(result=result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process security request: {str(e)}"
        )

# Collaboration Endpoints
@router.post("/analyze-project", response_model=ProjectAnalysisResponse)
async def analyze_project(request: ProjectAnalysisRequest):
    """Perform a complete project analysis using all agents"""
    try:
        await coordinator.initialize_all()
        results = await coordinator.analyze_project(request.requirement)
        return ProjectAnalysisResponse(**results)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze project: {str(e)}"
        )
        
@router.post("/review-code", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    """Perform a complete code review using all agents"""
    try:
        await coordinator.initialize_all()
        results = await coordinator.review_code(
            request.code,
            original_code=request.original_code
        )
        return CodeReviewResponse(**results)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to review code: {str(e)}"
        )
        
@router.post("/agent-opinion", response_model=SecurityResponse)
async def get_agent_opinion(request: AgentOpinionRequest):
    """Get a specific agent's opinion on a topic"""
    try:
        await coordinator.initialize_all()
        result = await coordinator.get_agent_opinion(
            request.agent_name,
            request.content,
            mode=request.mode,
            context=request.context
        )
        return SecurityResponse(result=result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent opinion: {str(e)}"
        ) 