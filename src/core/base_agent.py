"""
Base Agent Class - الوكيل الأساسي
Revolutionary agent architecture with built-in RAG and continuous learning
"""

from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from dataclasses import dataclass, field
import json

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.core.rag_system import RAGSystem
from src.core.learning_system import ContinuousLearningSystem


@dataclass
class AgentContext:
    """Context information for agent execution"""
    user_id: str
    session_id: str
    language: str = "en"
    domain: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Structured agent response"""
    content: str
    confidence: float
    sources: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    follow_up_questions: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Revolutionary Base Agent with:
    - Multi-language support (Arabic & English)
    - Built-in RAG system
    - Continuous learning capabilities
    - Self-healing mechanisms
    - Context-aware processing
    """

    def __init__(
        self,
        agent_name: str,
        domain: str,
        llm_provider: str = "openai",
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        enable_rag: bool = True,
        enable_learning: bool = True,
        **kwargs
    ):
        """Initialize the base agent"""
        self.agent_name = agent_name
        self.domain = domain
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

        # Initialize LLM
        self.llm = self._initialize_llm(llm_provider, model_name, temperature)

        # Initialize memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )

        # Initialize RAG system
        self.rag_system = None
        if enable_rag:
            self.rag_system = RAGSystem(
                domain=domain,
                collection_name=f"{domain}_knowledge"
            )

        # Initialize learning system
        self.learning_system = None
        if enable_learning:
            self.learning_system = ContinuousLearningSystem(
                agent_name=agent_name,
                domain=domain
            )

        # Agent capabilities
        self.capabilities = self._define_capabilities()

        # Performance metrics
        self.metrics = {
            "queries_processed": 0,
            "average_response_time": 0.0,
            "success_rate": 0.0,
            "user_satisfaction": 0.0
        }

        self.logger.info(f"Agent {agent_name} initialized for domain: {domain}")

    def _initialize_llm(
        self,
        provider: str,
        model_name: str,
        temperature: float
    ):
        """Initialize the language model"""
        if provider == "openai":
            return ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                streaming=True
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                streaming=True
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @abstractmethod
    def _define_capabilities(self) -> List[str]:
        """Define agent-specific capabilities"""
        pass

    @abstractmethod
    def _get_system_prompt(self, language: str = "en") -> str:
        """Get domain-specific system prompt"""
        pass

    @abstractmethod
    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        """Extract domain-specific pain points from query"""
        pass

    def query(
        self,
        user_query: str,
        context: Optional[AgentContext] = None,
        use_rag: bool = True,
        **kwargs
    ) -> AgentResponse:
        """
        Process a user query with full agent capabilities

        Args:
            user_query: The user's question or request
            context: Agent execution context
            use_rag: Whether to use RAG for knowledge retrieval

        Returns:
            AgentResponse with structured output
        """
        start_time = datetime.now()

        # Set default context
        if context is None:
            context = AgentContext(
                user_id="default",
                session_id="default",
                language="en",
                domain=self.domain
            )

        try:
            # Detect language if not specified
            if context.language == "auto":
                context.language = self._detect_language(user_query)

            # Extract pain points
            pain_points = self._extract_pain_points(user_query, context)

            # Retrieve relevant knowledge via RAG
            relevant_context = ""
            sources = []
            if use_rag and self.rag_system:
                rag_results = self.rag_system.retrieve(
                    query=user_query,
                    k=5,
                    filter_metadata={"language": context.language}
                )
                relevant_context = "\n".join([r["content"] for r in rag_results])
                sources = [r.get("source", "Unknown") for r in rag_results]

            # Build messages
            messages = self._build_messages(
                user_query=user_query,
                context=context,
                relevant_context=relevant_context,
                pain_points=pain_points
            )

            # Get LLM response
            response = self.llm.invoke(messages)
            response_content = response.content

            # Calculate confidence
            confidence = self._calculate_confidence(
                query=user_query,
                response=response_content,
                sources=sources
            )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(
                query=user_query,
                response=response_content,
                context=context
            )

            # Create structured response
            agent_response = AgentResponse(
                content=response_content,
                confidence=confidence,
                sources=sources,
                suggestions=self._generate_suggestions(user_query, context),
                follow_up_questions=follow_ups,
                metadata={
                    "agent": self.agent_name,
                    "domain": self.domain,
                    "language": context.language,
                    "pain_points": pain_points,
                    "response_time": (datetime.now() - start_time).total_seconds()
                }
            )

            # Learn from interaction
            if self.learning_system:
                self.learning_system.record_interaction(
                    query=user_query,
                    response=response_content,
                    context=context,
                    metadata={"confidence": confidence}
                )

            # Update metrics
            self._update_metrics(
                response_time=(datetime.now() - start_time).total_seconds(),
                success=True
            )

            return agent_response

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)

            # Self-healing: try fallback strategy
            fallback_response = self._handle_error_fallback(user_query, context, e)

            return fallback_response

    def _build_messages(
        self,
        user_query: str,
        context: AgentContext,
        relevant_context: str,
        pain_points: List[str]
    ) -> List[BaseMessage]:
        """Build conversation messages for LLM"""
        messages = []

        # System message with context
        system_prompt = self._get_system_prompt(context.language)

        if relevant_context:
            system_prompt += f"\n\n## Relevant Knowledge:\n{relevant_context}"

        if pain_points:
            system_prompt += f"\n\n## Pain Points Detected:\n" + "\n".join(f"- {p}" for p in pain_points)

        messages.append(SystemMessage(content=system_prompt))

        # Add conversation history
        history = self.memory.load_memory_variables({})
        if "chat_history" in history:
            messages.extend(history["chat_history"])

        # User query
        messages.append(HumanMessage(content=user_query))

        return messages

    def _detect_language(self, text: str) -> str:
        """Detect text language (Arabic or English)"""
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars > len(text) * 0.3:
            return "ar"
        return "en"

    def _calculate_confidence(
        self,
        query: str,
        response: str,
        sources: List[str]
    ) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence

        # Boost confidence if we have sources
        if sources:
            confidence += min(len(sources) * 0.1, 0.3)

        # Boost confidence based on response length and structure
        if len(response) > 100:
            confidence += 0.1

        # Ensure confidence is between 0 and 1
        return min(max(confidence, 0.0), 1.0)

    def _generate_follow_ups(
        self,
        query: str,
        response: str,
        context: AgentContext
    ) -> List[str]:
        """Generate relevant follow-up questions"""
        # This would ideally use LLM to generate contextual follow-ups
        # For now, return domain-specific defaults
        return []

    def _generate_suggestions(
        self,
        query: str,
        context: AgentContext
    ) -> List[str]:
        """Generate suggestions for the user"""
        return []

    def _update_metrics(self, response_time: float, success: bool):
        """Update agent performance metrics"""
        self.metrics["queries_processed"] += 1

        # Update average response time
        current_avg = self.metrics["average_response_time"]
        total_queries = self.metrics["queries_processed"]
        self.metrics["average_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )

        # Update success rate
        if success:
            current_rate = self.metrics["success_rate"]
            self.metrics["success_rate"] = (
                (current_rate * (total_queries - 1) + 1.0) / total_queries
            )

    def _handle_error_fallback(
        self,
        query: str,
        context: AgentContext,
        error: Exception
    ) -> AgentResponse:
        """Self-healing fallback strategy"""
        self.logger.warning(f"Using fallback strategy due to error: {str(error)}")

        fallback_content = self._get_fallback_response(context.language)

        return AgentResponse(
            content=fallback_content,
            confidence=0.3,
            sources=[],
            suggestions=["Try rephrasing your question", "Provide more details"],
            metadata={
                "fallback": True,
                "error": str(error)
            }
        )

    def _get_fallback_response(self, language: str) -> str:
        """Get language-specific fallback response"""
        if language == "ar":
            return "عذراً، واجهت صعوبة في معالجة استفسارك. هل يمكنك إعادة صياغة السؤال؟"
        return "I apologize, but I encountered difficulty processing your query. Could you please rephrase?"

    def add_knowledge(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "manual"
    ):
        """Add new knowledge to the agent's knowledge base"""
        if self.rag_system:
            self.rag_system.add_documents(
                documents=[content],
                metadatas=[metadata or {}],
                source=source
            )
            self.logger.info(f"Added new knowledge from source: {source}")

    def learn_from_feedback(
        self,
        query: str,
        response: str,
        feedback: Dict[str, Any]
    ):
        """Learn from user feedback"""
        if self.learning_system:
            self.learning_system.process_feedback(
                query=query,
                response=response,
                feedback=feedback
            )
            self.logger.info("Processed user feedback for learning")

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return self.metrics.copy()

    def reset_memory(self):
        """Reset conversation memory"""
        self.memory.clear()
        self.logger.info("Conversation memory reset")

    def export_knowledge(self, output_path: str):
        """Export agent's knowledge base"""
        if self.rag_system:
            self.rag_system.export_knowledge(output_path)
            self.logger.info(f"Knowledge exported to: {output_path}")
