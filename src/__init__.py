"""
Standalone Domain Agents - نظام الوكلاء المتخصصين
A revolutionary multi-domain agent system with RAG and continuous learning
"""

__version__ = "1.0.0"
__author__ = "Standalone Agents Team"
__license__ = "MIT"

from src.core.base_agent import BaseAgent
from src.core.orchestrator import AgentOrchestrator
from src.core.rag_system import RAGSystem
from src.core.learning_system import ContinuousLearningSystem

__all__ = [
    "BaseAgent",
    "AgentOrchestrator",
    "RAGSystem",
    "ContinuousLearningSystem",
]
