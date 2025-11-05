"""
Multi-Agent Orchestrator - منسق الوكلاء المتعددين
Revolutionary orchestration system for multi-agent collaboration
"""

from typing import Dict, List, Any, Optional, Set
import logging
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from src.core.base_agent import BaseAgent, AgentContext, AgentResponse


class CollaborationStrategy(Enum):
    """Collaboration strategies for multi-agent tasks"""
    PARALLEL = "parallel"  # All agents work simultaneously
    SEQUENTIAL = "sequential"  # Agents work one after another
    HIERARCHICAL = "hierarchical"  # Lead agent delegates to others
    CONSENSUS = "consensus"  # Agents vote on best response
    SPECIALIZED = "specialized"  # Each agent handles specific part


@dataclass
class AgentTask:
    """Task for an agent"""
    task_id: str
    query: str
    agent_name: str
    priority: int = 1
    dependencies: List[str] = field(default_factory=list)
    context: Optional[AgentContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborativeResponse:
    """Response from multiple agents"""
    primary_response: str
    confidence: float
    contributing_agents: List[str]
    agent_responses: Dict[str, AgentResponse]
    collaboration_strategy: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """
    Revolutionary Multi-Agent Orchestrator with:
    - Dynamic agent selection
    - Multi-agent collaboration
    - Task decomposition and delegation
    - Cross-domain knowledge synthesis
    - Intelligent routing
    - Performance optimization
    """

    def __init__(
        self,
        max_workers: int = 5,
        enable_parallel: bool = True
    ):
        """Initialize the orchestrator"""
        self.logger = logging.getLogger(__name__)

        # Registry of available agents
        self.agents: Dict[str, BaseAgent] = {}

        # Agent capabilities mapping
        self.capabilities_map: Dict[str, Set[str]] = {}

        # Domain expertise mapping
        self.domain_experts: Dict[str, List[str]] = {}

        # Execution pool
        self.max_workers = max_workers
        self.enable_parallel = enable_parallel
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Orchestration statistics
        self.stats = {
            "total_queries": 0,
            "collaborative_queries": 0,
            "single_agent_queries": 0,
            "average_agents_per_query": 0.0,
            "collaboration_strategies": {},
        }

        self.logger.info("Agent Orchestrator initialized")

    def register_agent(
        self,
        agent_name: str,
        agent: BaseAgent,
        capabilities: Optional[List[str]] = None,
        domains: Optional[List[str]] = None
    ):
        """
        Register an agent with the orchestrator

        Args:
            agent_name: Unique agent identifier
            agent: Agent instance
            capabilities: List of agent capabilities
            domains: List of domains the agent can handle
        """
        self.agents[agent_name] = agent

        # Register capabilities
        if capabilities:
            self.capabilities_map[agent_name] = set(capabilities)
        else:
            self.capabilities_map[agent_name] = set(agent.capabilities)

        # Register domains
        if domains:
            for domain in domains:
                if domain not in self.domain_experts:
                    self.domain_experts[domain] = []
                self.domain_experts[domain].append(agent_name)

        self.logger.info(
            f"Registered agent '{agent_name}' with {len(self.capabilities_map[agent_name])} capabilities"
        )

    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            if agent_name in self.capabilities_map:
                del self.capabilities_map[agent_name]

            # Remove from domain experts
            for domain, experts in self.domain_experts.items():
                if agent_name in experts:
                    experts.remove(agent_name)

            self.logger.info(f"Unregistered agent '{agent_name}'")

    def query(
        self,
        user_query: str,
        context: Optional[AgentContext] = None,
        preferred_agent: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None
    ) -> AgentResponse:
        """
        Route query to appropriate agent

        Args:
            user_query: User's question
            context: Execution context
            preferred_agent: Specific agent to use
            required_capabilities: Required agent capabilities

        Returns:
            AgentResponse from selected agent
        """
        self.stats["total_queries"] += 1

        # Select agent
        if preferred_agent and preferred_agent in self.agents:
            agent = self.agents[preferred_agent]
        else:
            agent = self._select_best_agent(
                query=user_query,
                context=context,
                required_capabilities=required_capabilities
            )

        if not agent:
            raise ValueError("No suitable agent found for query")

        # Execute query
        response = agent.query(user_query, context)

        self.stats["single_agent_queries"] += 1

        return response

    def collaborative_query(
        self,
        user_query: str,
        context: Optional[AgentContext] = None,
        required_agents: Optional[List[str]] = None,
        strategy: CollaborationStrategy = CollaborationStrategy.CONSENSUS,
        min_confidence: float = 0.7
    ) -> CollaborativeResponse:
        """
        Handle query requiring multiple agents

        Args:
            user_query: User's question
            context: Execution context
            required_agents: Specific agents to involve
            strategy: Collaboration strategy
            min_confidence: Minimum confidence threshold

        Returns:
            CollaborativeResponse combining multiple agents
        """
        self.stats["total_queries"] += 1
        self.stats["collaborative_queries"] += 1

        # Track strategy usage
        strategy_name = strategy.value
        if strategy_name not in self.stats["collaboration_strategies"]:
            self.stats["collaboration_strategies"][strategy_name] = 0
        self.stats["collaboration_strategies"][strategy_name] += 1

        # Select agents
        if required_agents:
            agents = [
                self.agents[name]
                for name in required_agents
                if name in self.agents
            ]
        else:
            agents = self._select_collaborating_agents(
                query=user_query,
                context=context,
                strategy=strategy
            )

        if not agents:
            raise ValueError("No suitable agents found for collaborative query")

        # Execute based on strategy
        if strategy == CollaborationStrategy.PARALLEL:
            collaborative_response = self._parallel_execution(
                user_query, context, agents
            )
        elif strategy == CollaborationStrategy.SEQUENTIAL:
            collaborative_response = self._sequential_execution(
                user_query, context, agents
            )
        elif strategy == CollaborationStrategy.CONSENSUS:
            collaborative_response = self._consensus_execution(
                user_query, context, agents, min_confidence
            )
        elif strategy == CollaborationStrategy.HIERARCHICAL:
            collaborative_response = self._hierarchical_execution(
                user_query, context, agents
            )
        else:
            collaborative_response = self._specialized_execution(
                user_query, context, agents
            )

        # Update stats
        total_queries = self.stats["total_queries"]
        current_avg = self.stats["average_agents_per_query"]
        self.stats["average_agents_per_query"] = (
            (current_avg * (total_queries - 1) + len(agents)) / total_queries
        )

        return collaborative_response

    def _select_best_agent(
        self,
        query: str,
        context: Optional[AgentContext],
        required_capabilities: Optional[List[str]]
    ) -> Optional[BaseAgent]:
        """Select the best agent for a query"""
        if not self.agents:
            return None

        # If domain is specified in context
        if context and context.domain:
            if context.domain in self.domain_experts:
                agent_name = self.domain_experts[context.domain][0]
                return self.agents[agent_name]

        # Filter by capabilities
        if required_capabilities:
            candidate_agents = []
            for agent_name, capabilities in self.capabilities_map.items():
                if all(cap in capabilities for cap in required_capabilities):
                    candidate_agents.append(agent_name)

            if candidate_agents:
                return self.agents[candidate_agents[0]]

        # Default: return first agent
        return list(self.agents.values())[0]

    def _select_collaborating_agents(
        self,
        query: str,
        context: Optional[AgentContext],
        strategy: CollaborationStrategy,
        max_agents: int = 3
    ) -> List[BaseAgent]:
        """Select agents for collaboration"""
        # Simple selection: use domain experts
        selected_agents = []

        if context and context.domain:
            if context.domain in self.domain_experts:
                agent_names = self.domain_experts[context.domain][:max_agents]
                selected_agents = [
                    self.agents[name] for name in agent_names
                ]

        # Fallback: use all agents (limited)
        if not selected_agents:
            selected_agents = list(self.agents.values())[:max_agents]

        return selected_agents

    def _parallel_execution(
        self,
        query: str,
        context: Optional[AgentContext],
        agents: List[BaseAgent]
    ) -> CollaborativeResponse:
        """Execute query on multiple agents in parallel"""
        agent_responses = {}

        # Execute in parallel
        if self.enable_parallel:
            futures = {
                agent.agent_name: self.executor.submit(
                    agent.query, query, context
                )
                for agent in agents
            }

            for agent_name, future in futures.items():
                try:
                    agent_responses[agent_name] = future.result(timeout=30)
                except Exception as e:
                    self.logger.error(
                        f"Error in parallel execution for {agent_name}: {str(e)}"
                    )
        else:
            # Sequential fallback
            for agent in agents:
                try:
                    agent_responses[agent.agent_name] = agent.query(query, context)
                except Exception as e:
                    self.logger.error(
                        f"Error executing {agent.agent_name}: {str(e)}"
                    )

        # Combine responses
        return self._combine_responses(
            agent_responses,
            strategy="parallel"
        )

    def _sequential_execution(
        self,
        query: str,
        context: Optional[AgentContext],
        agents: List[BaseAgent]
    ) -> CollaborativeResponse:
        """Execute query on agents sequentially, each building on previous"""
        agent_responses = {}
        accumulated_context = query

        for agent in agents:
            try:
                response = agent.query(accumulated_context, context)
                agent_responses[agent.agent_name] = response

                # Add response to context for next agent
                accumulated_context += f"\n\nPrevious analysis by {agent.agent_name}:\n{response.content}"

            except Exception as e:
                self.logger.error(
                    f"Error in sequential execution for {agent.agent_name}: {str(e)}"
                )

        return self._combine_responses(
            agent_responses,
            strategy="sequential"
        )

    def _consensus_execution(
        self,
        query: str,
        context: Optional[AgentContext],
        agents: List[BaseAgent],
        min_confidence: float
    ) -> CollaborativeResponse:
        """Execute query and select response with highest consensus"""
        agent_responses = {}

        # Get all responses
        for agent in agents:
            try:
                agent_responses[agent.agent_name] = agent.query(query, context)
            except Exception as e:
                self.logger.error(
                    f"Error in consensus execution for {agent.agent_name}: {str(e)}"
                )

        # Find response with highest confidence
        best_response = None
        best_confidence = 0.0

        for agent_name, response in agent_responses.items():
            if response.confidence > best_confidence:
                best_confidence = response.confidence
                best_response = response

        # If no response meets minimum confidence, combine all
        if best_confidence < min_confidence:
            return self._combine_responses(
                agent_responses,
                strategy="consensus"
            )

        # Return best response
        return CollaborativeResponse(
            primary_response=best_response.content,
            confidence=best_response.confidence,
            contributing_agents=list(agent_responses.keys()),
            agent_responses=agent_responses,
            collaboration_strategy="consensus",
            metadata={
                "best_agent": [
                    name for name, resp in agent_responses.items()
                    if resp.confidence == best_confidence
                ][0]
            }
        )

    def _hierarchical_execution(
        self,
        query: str,
        context: Optional[AgentContext],
        agents: List[BaseAgent]
    ) -> CollaborativeResponse:
        """Lead agent coordinates others"""
        if not agents:
            raise ValueError("No agents provided")

        # First agent is lead
        lead_agent = agents[0]
        supporting_agents = agents[1:]

        agent_responses = {}

        # Get supporting agents' responses
        for agent in supporting_agents:
            try:
                agent_responses[agent.agent_name] = agent.query(query, context)
            except Exception as e:
                self.logger.error(f"Error with supporting agent {agent.agent_name}: {str(e)}")

        # Lead agent synthesizes
        synthesis_context = query
        if agent_responses:
            synthesis_context += "\n\n## Supporting Analysis:\n"
            for agent_name, response in agent_responses.items():
                synthesis_context += f"\n### {agent_name}:\n{response.content}\n"

        lead_response = lead_agent.query(synthesis_context, context)
        agent_responses[lead_agent.agent_name] = lead_response

        return CollaborativeResponse(
            primary_response=lead_response.content,
            confidence=lead_response.confidence,
            contributing_agents=list(agent_responses.keys()),
            agent_responses=agent_responses,
            collaboration_strategy="hierarchical",
            metadata={"lead_agent": lead_agent.agent_name}
        )

    def _specialized_execution(
        self,
        query: str,
        context: Optional[AgentContext],
        agents: List[BaseAgent]
    ) -> CollaborativeResponse:
        """Each agent handles specific aspect"""
        # This would ideally decompose the query
        # For now, similar to parallel
        return self._parallel_execution(query, context, agents)

    def _combine_responses(
        self,
        agent_responses: Dict[str, AgentResponse],
        strategy: str
    ) -> CollaborativeResponse:
        """Combine multiple agent responses"""
        if not agent_responses:
            raise ValueError("No agent responses to combine")

        # Calculate average confidence
        avg_confidence = sum(
            r.confidence for r in agent_responses.values()
        ) / len(agent_responses)

        # Combine content
        combined_content = ""
        for agent_name, response in agent_responses.items():
            combined_content += f"\n## {agent_name}:\n{response.content}\n"

        # Collect all sources
        all_sources = []
        for response in agent_responses.values():
            all_sources.extend(response.sources)

        return CollaborativeResponse(
            primary_response=combined_content.strip(),
            confidence=avg_confidence,
            contributing_agents=list(agent_responses.keys()),
            agent_responses=agent_responses,
            collaboration_strategy=strategy,
            metadata={
                "total_sources": len(set(all_sources)),
                "timestamp": datetime.now().isoformat()
            }
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        return self.stats.copy()

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [
            {
                "name": agent_name,
                "domain": agent.domain,
                "capabilities": list(self.capabilities_map.get(agent_name, [])),
                "metrics": agent.get_metrics()
            }
            for agent_name, agent in self.agents.items()
        ]

    def shutdown(self):
        """Shutdown the orchestrator"""
        self.executor.shutdown(wait=True)
        self.logger.info("Orchestrator shut down")
