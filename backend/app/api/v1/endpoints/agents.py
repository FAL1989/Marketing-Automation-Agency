from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from app.agents import (
    RequirementsAnalyzer,
    CodeAnalyzer,
    ArchitectureDesigner,
    SecurityAnalyzer,
    coordinator
)
from datetime import datetime, UTC
from app.core.redis import get_redis
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

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

class MessageRequest(BaseModel):
    recipient: str
    message: str

class MessageResponse(BaseModel):
    success: bool
    message: str

class BroadcastRequest(BaseModel):
    message: str

class BroadcastResponse(BaseModel):
    success: bool
    message: str

class ContextRequest(BaseModel):
    task: str
    data: Dict

class ContextShareRequest(BaseModel):
    recipient: str

class ContextResponse(BaseModel):
    success: bool
    message: str
    context: Optional[Dict] = None

class TaskRequest(BaseModel):
    id: str
    type: str
    subtasks: List[Dict[str, str]]

class TaskResponse(BaseModel):
    status: str
    results: Optional[List[Dict]] = None
    message: str

class FeedbackRequest(BaseModel):
    recipient: str
    feedback: str

class FeedbackStatusResponse(BaseModel):
    processed: bool
    message: str
    feedback: Optional[Dict] = None

class ConflictRequest(BaseModel):
    type: str
    agents: List[str]
    resource: str

class ConflictResolutionRequest(BaseModel):
    resolution: str

class ConflictResponse(BaseModel):
    resolved: bool
    message: str
    resolution: Optional[str] = None

class LearningFeedbackRequest(BaseModel):
    recipient: str
    feedback: Dict

class LearningStatusResponse(BaseModel):
    feedback_applied: bool
    message: str
    feedback: Optional[Dict] = None

class CoordinationRequest(BaseModel):
    task_id: str
    participants: List[str]
    task_details: Dict

class CoordinationResponse(BaseModel):
    task_id: str
    status: str
    assignments: Dict[str, Dict]
    message: str

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

@router.post("/{agent_id}/send", response_model=MessageResponse)
async def send_message(
    agent_id: str,
    message_request: MessageRequest
):
    """Send a message from one agent to another"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Creating message from {agent_id} to {message_request.recipient}")
        message = {
            "sender": agent_id,
            "message": message_request.message,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        logger.info("Storing message in Redis")
        redis_client.lpush(
            f"agent:{message_request.recipient}:messages",
            json.dumps(message)
        )
        
        logger.info("Message sent successfully")
        return MessageResponse(
            success=True,
            message=f"Message sent from {agent_id} to {message_request.recipient}"
        )
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/{agent_id}/messages", response_model=List[Dict])
async def get_messages(agent_id: str):
    """Get messages for a specific agent"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting messages for agent {agent_id}")
        messages = redis_client.lrange(f"agent:{agent_id}:messages", 0, -1)
        return [json.loads(msg) for msg in messages]
    except Exception as e:
        logger.error(f"Failed to get messages: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}"
        )

@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_message(request: BroadcastRequest):
    """Broadcast a message to all agents"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info("Creating message")
        message = {
            "sender": "broadcast",
            "message": request.message,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Lista de agentes (em um sistema real, isso viria de um registro de agentes)
        agent_ids = ["agent1", "agent2", "agent3"]
        
        logger.info("Broadcasting message to agents")
        # Envia a mensagem para cada agente
        for agent_id in agent_ids:
            logger.info(f"Sending message to agent {agent_id}")
            redis_client.lpush(f"agent:{agent_id}:messages", json.dumps(message))
        
        logger.info("Broadcast completed successfully")
        return BroadcastResponse(
            success=True,
            message="Message broadcasted successfully"
        )
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to broadcast message: {str(e)}"
        )

@router.post("/{agent_id}/context", response_model=ContextResponse)
async def set_context(
    agent_id: str,
    context: ContextRequest
):
    """Set context for an agent"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Setting context for agent {agent_id}")
        context_data = {
            "task": context.task,
            "data": context.data,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        redis_client.set(
            f"agent:{agent_id}:context",
            json.dumps(context_data)
        )
        
        logger.info("Context set successfully")
        return ContextResponse(
            success=True,
            message=f"Context set for agent {agent_id}",
            context=context_data
        )
    except Exception as e:
        logger.error(f"Failed to set context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set context: {str(e)}"
        )

@router.post("/{agent_id}/share-context", response_model=ContextResponse)
async def share_context(
    agent_id: str,
    request: ContextShareRequest
):
    """Share context from one agent to another"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        # Get source agent context
        logger.info(f"Getting context from agent {agent_id}")
        source_context = redis_client.get(f"agent:{agent_id}:context")
        if not source_context:
            raise HTTPException(
                status_code=404,
                detail=f"No context found for agent {agent_id}"
            )
        
        # Share context with recipient
        logger.info(f"Sharing context with agent {request.recipient}")
        redis_client.set(
            f"agent:{request.recipient}:context",
            source_context
        )
        
        context_data = json.loads(source_context)
        logger.info("Context shared successfully")
        return ContextResponse(
            success=True,
            message=f"Context shared from {agent_id} to {request.recipient}",
            context=context_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to share context: {str(e)}"
        )

@router.get("/{agent_id}/context", response_model=ContextResponse)
async def get_context(agent_id: str):
    """Get context for an agent"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting context for agent {agent_id}")
        context = redis_client.get(f"agent:{agent_id}:context")
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"No context found for agent {agent_id}"
            )
        
        context_data = json.loads(context)
        logger.info("Context retrieved successfully")
        return ContextResponse(
            success=True,
            message=f"Context retrieved for agent {agent_id}",
            context=context_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context: {str(e)}"
        )

@router.post("/tasks", response_model=TaskResponse)
async def coordinate_task(request: TaskRequest):
    """Coordinate a task between multiple agents"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Creating task {request.id}")
        task_data = {
            "id": request.id,
            "type": request.type,
            "subtasks": request.subtasks,
            "status": "pending",
            "results": [],
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Store task data
        redis_client.set(
            f"task:{request.id}",
            json.dumps(task_data)
        )
        
        # Assign subtasks to agents
        for subtask in request.subtasks:
            agent_id = subtask["agent"]
            subtask_data = {
                "task_id": request.id,
                "subtask": subtask,
                "status": "pending",
                "timestamp": datetime.now(UTC).isoformat()
            }
            redis_client.lpush(
                f"agent:{agent_id}:tasks",
                json.dumps(subtask_data)
            )
        
        # Update task status
        task_data["status"] = "in_progress"
        redis_client.set(
            f"task:{request.id}",
            json.dumps(task_data)
        )
        
        logger.info("Task coordination started successfully")
        return TaskResponse(
            status="in_progress",
            results=[],
            message=f"Task {request.id} started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to coordinate task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to coordinate task: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Get the status of a task"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting task {task_id}")
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        task = json.loads(task_data)
        logger.info("Task status retrieved successfully")
        return TaskResponse(
            status=task["status"],
            results=task.get("results", []),
            message=f"Task {task_id} status retrieved"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str):
    """Mark a task as completed"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting task {task_id}")
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        task = json.loads(task_data)
        task["status"] = "completed"
        task["timestamp"] = datetime.now(UTC).isoformat()
        
        redis_client.set(
            f"task:{task_id}",
            json.dumps(task)
        )
        
        logger.info("Task marked as completed successfully")
        return TaskResponse(
            status="completed",
            results=task.get("results", []),
            message=f"Task {task_id} completed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete task: {str(e)}"
        )

@router.post("/{agent_id}/feedback", response_model=FeedbackStatusResponse)
async def send_feedback(
    agent_id: str,
    request: FeedbackRequest
):
    """Send feedback from one agent to another"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Creating feedback from {agent_id} to {request.recipient}")
        feedback_data = {
            "sender": agent_id,
            "feedback": request.feedback,
            "processed": False,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        logger.info("Storing feedback in Redis")
        redis_client.lpush(
            f"agent:{request.recipient}:feedback",
            json.dumps(feedback_data)
        )
        
        logger.info("Feedback sent successfully")
        return FeedbackStatusResponse(
            processed=False,
            message=f"Feedback sent from {agent_id} to {request.recipient}",
            feedback=feedback_data
        )
    except Exception as e:
        logger.error(f"Failed to send feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send feedback: {str(e)}"
        )

@router.get("/{agent_id}/feedback/status", response_model=FeedbackStatusResponse)
async def get_feedback_status(agent_id: str):
    """Get feedback status for an agent"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting feedback for agent {agent_id}")
        feedback_list = redis_client.lrange(f"agent:{agent_id}:feedback", 0, 0)
        if not feedback_list:
            raise HTTPException(
                status_code=404,
                detail=f"No feedback found for agent {agent_id}"
            )
        
        feedback_data = json.loads(feedback_list[0])
        
        # Simulate feedback processing
        feedback_data["processed"] = True
        redis_client.lset(
            f"agent:{agent_id}:feedback",
            0,
            json.dumps(feedback_data)
        )
        
        logger.info("Feedback status retrieved successfully")
        return FeedbackStatusResponse(
            processed=True,
            message=f"Feedback processed for agent {agent_id}",
            feedback=feedback_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get feedback status: {str(e)}"
        )

@router.post("/conflicts", response_model=ConflictResponse)
async def create_conflict(request: ConflictRequest):
    """Create a conflict between agents"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Creating conflict for resource {request.resource}")
        conflict_data = {
            "type": request.type,
            "agents": request.agents,
            "resource": request.resource,
            "resolved": False,
            "resolution": None,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Store conflict data
        conflict_key = f"conflict:{request.type}:{request.resource}"
        redis_client.set(
            conflict_key,
            json.dumps(conflict_data)
        )
        
        logger.info("Conflict created successfully")
        return ConflictResponse(
            resolved=False,
            message=f"Conflict created for resource {request.resource}",
            resolution=None
        )
    except Exception as e:
        logger.error(f"Failed to create conflict: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conflict: {str(e)}"
        )

@router.post("/conflicts/{conflict_type}/resolve", response_model=ConflictResponse)
async def resolve_conflict(
    conflict_type: str,
    request: ConflictResolutionRequest
):
    """Resolve a conflict between agents"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        # Get all conflicts of this type
        pattern = f"conflict:{conflict_type}:*"
        conflict_keys = redis_client.keys(pattern)
        
        if not conflict_keys:
            raise HTTPException(
                status_code=404,
                detail=f"No conflicts found of type {conflict_type}"
            )
        
        # Resolve all conflicts of this type
        for key in conflict_keys:
            conflict_data = json.loads(redis_client.get(key))
            conflict_data["resolved"] = True
            conflict_data["resolution"] = request.resolution
            conflict_data["resolved_at"] = datetime.now(UTC).isoformat()
            
            redis_client.set(key, json.dumps(conflict_data))
        
        logger.info("Conflict resolved successfully")
        return ConflictResponse(
            resolved=True,
            message=f"Conflicts of type {conflict_type} resolved",
            resolution=request.resolution
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve conflict: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve conflict: {str(e)}"
        )

@router.post("/{agent_id}/learning-feedback", response_model=LearningStatusResponse)
async def send_learning_feedback(
    agent_id: str,
    request: LearningFeedbackRequest
):
    """Send learning feedback from one agent to another"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Creating learning feedback from {agent_id} to {request.recipient}")
        feedback_data = {
            "sender": agent_id,
            "feedback": request.feedback,
            "applied": False,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        logger.info("Storing learning feedback in Redis")
        redis_client.lpush(
            f"agent:{request.recipient}:learning_feedback",
            json.dumps(feedback_data)
        )
        
        logger.info("Learning feedback sent successfully")
        return LearningStatusResponse(
            feedback_applied=False,
            message=f"Learning feedback sent from {agent_id} to {request.recipient}",
            feedback=feedback_data
        )
    except Exception as e:
        logger.error(f"Failed to send learning feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send learning feedback: {str(e)}"
        )

@router.get("/{agent_id}/learning-status", response_model=LearningStatusResponse)
async def get_learning_status(agent_id: str):
    """Get learning status for an agent"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting learning feedback for agent {agent_id}")
        feedback_list = redis_client.lrange(f"agent:{agent_id}:learning_feedback", 0, 0)
        if not feedback_list:
            raise HTTPException(
                status_code=404,
                detail=f"No learning feedback found for agent {agent_id}"
            )
        
        feedback_data = json.loads(feedback_list[0])
        
        # Simulate feedback application
        feedback_data["applied"] = True
        redis_client.lset(
            f"agent:{agent_id}:learning_feedback",
            0,
            json.dumps(feedback_data)
        )
        
        logger.info("Learning status retrieved successfully")
        return LearningStatusResponse(
            feedback_applied=True,
            message=f"Learning feedback applied for agent {agent_id}",
            feedback=feedback_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get learning status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning status: {str(e)}"
        )

@router.post("/coordinate", response_model=CoordinationResponse)
async def coordinate_task(request: CoordinationRequest):
    """Coordinate a task between multiple agents"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Creating task coordination for task {request.task_id}")
        coordination_data = {
            "task_id": request.task_id,
            "status": "assigned",
            "assignments": {},
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Simulate task assignment
        for agent in request.participants:
            coordination_data["assignments"][agent] = {
                "role": "participant",
                "status": "assigned",
                "subtasks": ["analyze", "implement", "test"]
            }
        
        logger.info("Storing coordination data in Redis")
        redis_client.set(
            f"task:{request.task_id}:coordination",
            json.dumps(coordination_data)
        )
        
        logger.info("Task coordination created successfully")
        return CoordinationResponse(
            task_id=request.task_id,
            status="assigned",
            assignments=coordination_data["assignments"],
            message="Task coordination created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to coordinate task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to coordinate task: {str(e)}"
        )

@router.get("/tasks/{task_id}/status", response_model=CoordinationResponse)
async def get_task_status(task_id: str):
    """Get status of a coordinated task"""
    try:
        logger.info("Getting Redis client")
        redis_client = await get_redis()
        
        logger.info(f"Getting coordination data for task {task_id}")
        coordination_data = redis_client.get(f"task:{task_id}:coordination")
        if not coordination_data:
            raise HTTPException(
                status_code=404,
                detail=f"No coordination data found for task {task_id}"
            )
        
        coordination_data = json.loads(coordination_data)
        
        # Simulate task progress
        coordination_data["status"] = "in_progress"
        for agent in coordination_data["assignments"]:
            coordination_data["assignments"][agent]["status"] = "in_progress"
        
        redis_client.set(
            f"task:{task_id}:coordination",
            json.dumps(coordination_data)
        )
        
        logger.info("Task status retrieved successfully")
        return CoordinationResponse(
            task_id=task_id,
            status=coordination_data["status"],
            assignments=coordination_data["assignments"],
            message="Task status retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        ) 