"""
FastAPI Application - تطبيق الAPI
RESTful API for standalone agents
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from src.core.orchestrator import AgentOrchestrator, CollaborationStrategy
from src.core.base_agent import AgentContext
from src.agents.medical.medical_agent import MedicalAgent
from src.agents.legal.legal_agent import LegalAgent
from src.agents.finance.finance_agent import FinanceAgent
from src.agents.education.education_agent import EducationAgent
from src.agents.ecommerce.ecommerce_agent import EcommerceAgent
from src.agents.customer_service.customer_service_agent import CustomerServiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Standalone Domain Agents API",
    description="Revolutionary multi-domain agent system with RAG and continuous learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator and agents
orchestrator = AgentOrchestrator(max_workers=5)


# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    language: str = Field(default="auto", description="Language: en, ar, or auto")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    use_rag: bool = Field(default=True, description="Use RAG for knowledge retrieval")


class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: float = Field(..., ge=0.0, le=5.0)
    corrections: Optional[str] = None
    feedback_text: Optional[str] = None


class CollaborativeQueryRequest(BaseModel):
    query: str
    language: str = "auto"
    user_id: str = "anonymous"
    required_agents: List[str]
    strategy: str = "consensus"


class AgentResponse(BaseModel):
    content: str
    confidence: float
    sources: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    logger.info("Initializing agents...")

    # Register all agents
    agents_config = [
        ("medical", MedicalAgent(), ["medical", "health", "healthcare"]),
        ("legal", LegalAgent(), ["legal", "law", "rights"]),
        ("finance", FinanceAgent(), ["finance", "money", "investment"]),
        ("education", EducationAgent(), ["education", "learning", "training"]),
        ("ecommerce", EcommerceAgent(), ["shopping", "products", "ecommerce"]),
        ("customer_service", CustomerServiceAgent(), ["support", "service", "help"]),
    ]

    for name, agent, domains in agents_config:
        orchestrator.register_agent(
            agent_name=name,
            agent=agent,
            domains=domains
        )
        logger.info(f"Registered {name} agent")

    logger.info("All agents initialized successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Standalone Domain Agents API",
        "version": "1.0.0",
        "status": "running",
        "agents": list(orchestrator.agents.keys())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_count": len(orchestrator.agents)
    }


@app.post("/query/{agent_name}", response_model=AgentResponse)
async def query_agent(agent_name: str, request: QueryRequest):
    """
    Query a specific agent

    - **agent_name**: medical, legal, finance, education, ecommerce, customer_service
    - **query**: User's question
    - **language**: en, ar, or auto (auto-detect)
    """
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    try:
        context = AgentContext(
            user_id=request.user_id,
            session_id=request.session_id or f"session_{datetime.now().timestamp()}",
            language=request.language,
            domain=agent_name
        )

        response = orchestrator.query(
            user_query=request.query,
            context=context,
            preferred_agent=agent_name
        )

        return AgentResponse(
            content=response.content,
            confidence=response.confidence,
            sources=response.sources,
            suggestions=response.suggestions,
            metadata=response.metadata,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborative-query")
async def collaborative_query(request: CollaborativeQueryRequest):
    """
    Query multiple agents collaboratively

    Strategies: parallel, sequential, hierarchical, consensus
    """
    try:
        # Validate agents
        for agent_name in request.required_agents:
            if agent_name not in orchestrator.agents:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent '{agent_name}' not found"
                )

        # Parse strategy
        strategy_map = {
            "parallel": CollaborationStrategy.PARALLEL,
            "sequential": CollaborationStrategy.SEQUENTIAL,
            "hierarchical": CollaborationStrategy.HIERARCHICAL,
            "consensus": CollaborationStrategy.CONSENSUS,
        }

        strategy = strategy_map.get(
            request.strategy.lower(),
            CollaborationStrategy.CONSENSUS
        )

        context = AgentContext(
            user_id=request.user_id,
            session_id=f"collab_{datetime.now().timestamp()}",
            language=request.language
        )

        response = orchestrator.collaborative_query(
            user_query=request.query,
            context=context,
            required_agents=request.required_agents,
            strategy=strategy
        )

        return {
            "content": response.primary_response,
            "confidence": response.confidence,
            "contributing_agents": response.contributing_agents,
            "strategy": response.collaboration_strategy,
            "metadata": response.metadata,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in collaborative query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback/{agent_name}")
async def submit_feedback(agent_name: str, request: FeedbackRequest):
    """Submit feedback for an agent response"""
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    try:
        agent = orchestrator.agents[agent_name]

        feedback = {
            "rating": request.rating,
            "corrections": request.corrections,
            "text": request.feedback_text
        }

        agent.learn_from_feedback(
            query=request.query,
            response=request.response,
            feedback=feedback
        )

        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "agent": agent_name
        }

    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {
        "agents": orchestrator.list_agents(),
        "total": len(orchestrator.agents)
    }


@app.get("/agent/{agent_name}/metrics")
async def get_agent_metrics(agent_name: str):
    """Get performance metrics for an agent"""
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    agent = orchestrator.agents[agent_name]
    return {
        "agent": agent_name,
        "metrics": agent.get_metrics(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/agent/{agent_name}/learning-insights")
async def get_learning_insights(agent_name: str):
    """Get learning insights for an agent"""
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    agent = orchestrator.agents[agent_name]

    if not agent.learning_system:
        return {"message": "Learning system not enabled for this agent"}

    insights = agent.learning_system.get_learning_insights()

    return {
        "agent": agent_name,
        "insights": insights,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_orchestrator_stats():
    """Get orchestrator statistics"""
    return {
        "stats": orchestrator.get_stats(),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
