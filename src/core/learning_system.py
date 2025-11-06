"""
Continuous Learning System - نظام التعلم المستمر
Revolutionary learning system with real-time adaptation and self-improvement
"""

from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
import statistics

from dataclasses import dataclass, field, asdict
import pickle


@dataclass
class Interaction:
    """Record of a single interaction"""
    query: str
    response: str
    timestamp: datetime
    user_id: str
    session_id: str
    language: str
    domain: str
    confidence: float = 0.0
    feedback_rating: Optional[float] = None
    feedback_text: Optional[str] = None
    corrections: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningPattern:
    """Identified learning pattern"""
    pattern_type: str
    description: str
    occurrences: int
    confidence: float
    examples: List[str] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)


class ContinuousLearningSystem:
    """
    Revolutionary Continuous Learning System with:
    - Real-time feedback integration
    - Adaptive behavior modification
    - Pattern recognition and learning
    - Experience-based optimization
    - Self-improvement mechanisms
    - Performance tracking
    """

    def __init__(
        self,
        agent_name: str,
        domain: str,
        persistence_path: Optional[str] = None,
        max_memory_size: int = 10000,
        feedback_threshold: float = 3.5
    ):
        """Initialize the continuous learning system"""
        self.agent_name = agent_name
        self.domain = domain
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

        # Set persistence path
        if persistence_path is None:
            persistence_path = f"./src/knowledge/learning/{domain}"

        self.persistence_path = Path(persistence_path)
        self.persistence_path.mkdir(parents=True, exist_ok=True)

        # Interaction memory
        self.max_memory_size = max_memory_size
        self.interactions: deque = deque(maxlen=max_memory_size)

        # Learning patterns
        self.patterns: Dict[str, LearningPattern] = {}

        # Performance metrics over time
        self.performance_history = {
            "daily": defaultdict(list),
            "weekly": defaultdict(list),
            "monthly": defaultdict(list)
        }

        # Learned improvements
        self.improvements = {
            "successful_patterns": [],
            "failed_patterns": [],
            "user_preferences": {},
            "common_corrections": {},
            "optimal_responses": {}
        }

        # Feedback analysis
        self.feedback_threshold = feedback_threshold
        self.feedback_stats = {
            "total_feedbacks": 0,
            "positive_feedbacks": 0,
            "negative_feedbacks": 0,
            "average_rating": 0.0,
            "improvement_trend": []
        }

        # Load existing learning data
        self._load_learning_data()

        self.logger.info(f"Continuous Learning System initialized for {agent_name}")

    def record_interaction(
        self,
        query: str,
        response: str,
        context: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record an interaction for learning

        Args:
            query: User query
            response: Agent response
            context: Agent context
            metadata: Additional metadata
        """
        interaction = Interaction(
            query=query,
            response=response,
            timestamp=datetime.now(),
            user_id=getattr(context, 'user_id', 'unknown'),
            session_id=getattr(context, 'session_id', 'unknown'),
            language=getattr(context, 'language', 'en'),
            domain=self.domain,
            confidence=metadata.get('confidence', 0.0) if metadata else 0.0,
            metadata=metadata or {}
        )

        self.interactions.append(interaction)

        # Analyze for patterns
        self._analyze_interaction(interaction)

        # Update performance metrics
        self._update_performance_metrics(interaction)

        # Periodic save
        if len(self.interactions) % 100 == 0:
            self._save_learning_data()

    def process_feedback(
        self,
        query: str,
        response: str,
        feedback: Dict[str, Any]
    ):
        """
        Process user feedback for learning

        Args:
            query: Original query
            response: Agent response
            feedback: User feedback (rating, corrections, etc.)
        """
        rating = feedback.get('rating', 0.0)
        corrections = feedback.get('corrections', '')
        feedback_text = feedback.get('text', '')

        # Find the corresponding interaction
        matching_interaction = None
        for interaction in reversed(self.interactions):
            if interaction.query == query and interaction.response == response:
                matching_interaction = interaction
                break

        if matching_interaction:
            matching_interaction.feedback_rating = rating
            matching_interaction.feedback_text = feedback_text
            matching_interaction.corrections = corrections

        # Update feedback statistics
        self.feedback_stats['total_feedbacks'] += 1

        if rating >= self.feedback_threshold:
            self.feedback_stats['positive_feedbacks'] += 1
        else:
            self.feedback_stats['negative_feedbacks'] += 1

        # Update average rating
        total = self.feedback_stats['total_feedbacks']
        current_avg = self.feedback_stats['average_rating']
        self.feedback_stats['average_rating'] = (
            (current_avg * (total - 1) + rating) / total
        )

        # Learn from corrections
        if corrections:
            self._learn_from_correction(query, response, corrections, rating)

        # Identify successful patterns from positive feedback
        if rating >= self.feedback_threshold:
            self._identify_successful_pattern(query, response)
        else:
            self._identify_failed_pattern(query, response)

        # Update improvement trend
        self.feedback_stats['improvement_trend'].append({
            'timestamp': datetime.now().isoformat(),
            'rating': rating,
            'average': self.feedback_stats['average_rating']
        })

        # Keep only last 1000 trend points
        if len(self.feedback_stats['improvement_trend']) > 1000:
            self.feedback_stats['improvement_trend'] = \
                self.feedback_stats['improvement_trend'][-1000:]

        self.logger.info(f"Processed feedback: rating={rating}, avg={self.feedback_stats['average_rating']:.2f}")

        self._save_learning_data()

    def _analyze_interaction(self, interaction: Interaction):
        """Analyze interaction for patterns"""
        # Detect query patterns
        query_lower = interaction.query.lower()

        # Common question patterns
        question_words_en = ['what', 'when', 'where', 'why', 'how', 'who', 'which']
        question_words_ar = ['ما', 'متى', 'أين', 'لماذا', 'كيف', 'من', 'أي', 'هل']

        question_words = question_words_ar if interaction.language == 'ar' else question_words_en

        for word in question_words:
            if word in query_lower:
                pattern_id = f"question_type_{word}"
                self._update_pattern(
                    pattern_id=pattern_id,
                    pattern_type="question_type",
                    description=f"Questions starting with '{word}'",
                    example=interaction.query
                )

        # Length-based patterns
        query_length = len(interaction.query.split())
        if query_length < 5:
            self._update_pattern(
                pattern_id="query_length_short",
                pattern_type="query_length",
                description="Short queries (< 5 words)",
                example=interaction.query
            )
        elif query_length > 20:
            self._update_pattern(
                pattern_id="query_length_long",
                pattern_type="query_length",
                description="Long queries (> 20 words)",
                example=interaction.query
            )

        # Language patterns
        self._update_pattern(
            pattern_id=f"language_{interaction.language}",
            pattern_type="language",
            description=f"Queries in {interaction.language}",
            example=interaction.query
        )

    def _update_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        example: str
    ):
        """Update or create a learning pattern"""
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.occurrences += 1
            pattern.last_seen = datetime.now()

            # Add example if not too many
            if len(pattern.examples) < 10:
                pattern.examples.append(example)

            # Update confidence based on occurrences
            pattern.confidence = min(pattern.occurrences / 100.0, 1.0)
        else:
            self.patterns[pattern_id] = LearningPattern(
                pattern_type=pattern_type,
                description=description,
                occurrences=1,
                confidence=0.01,
                examples=[example]
            )

    def _learn_from_correction(
        self,
        query: str,
        response: str,
        correction: str,
        rating: float
    ):
        """Learn from user corrections"""
        # Store common corrections
        correction_key = f"{query[:50]}..."  # Truncate for key

        if correction_key not in self.improvements['common_corrections']:
            self.improvements['common_corrections'][correction_key] = []

        self.improvements['common_corrections'][correction_key].append({
            'original_response': response,
            'correction': correction,
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        })

        # If highly rated correction, mark as optimal
        if rating >= 4.5:
            self.improvements['optimal_responses'][query] = correction

        self.logger.info(f"Learned from correction for query: {query[:50]}...")

    def _identify_successful_pattern(self, query: str, response: str):
        """Identify successful response patterns"""
        pattern = {
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }

        self.improvements['successful_patterns'].append(pattern)

        # Keep only last 500
        if len(self.improvements['successful_patterns']) > 500:
            self.improvements['successful_patterns'] = \
                self.improvements['successful_patterns'][-500:]

    def _identify_failed_pattern(self, query: str, response: str):
        """Identify failed response patterns to avoid"""
        pattern = {
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }

        self.improvements['failed_patterns'].append(pattern)

        # Keep only last 500
        if len(self.improvements['failed_patterns']) > 500:
            self.improvements['failed_patterns'] = \
                self.improvements['failed_patterns'][-500:]

    def _update_performance_metrics(self, interaction: Interaction):
        """Update performance metrics"""
        now = datetime.now()
        day_key = now.strftime('%Y-%m-%d')
        week_key = now.strftime('%Y-W%W')
        month_key = now.strftime('%Y-%m')

        metric = {
            'confidence': interaction.confidence,
            'timestamp': now.isoformat()
        }

        self.performance_history['daily'][day_key].append(metric)
        self.performance_history['weekly'][week_key].append(metric)
        self.performance_history['monthly'][month_key].append(metric)

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data"""
        # Calculate pattern insights
        top_patterns = sorted(
            self.patterns.items(),
            key=lambda x: x[1].occurrences,
            reverse=True
        )[:10]

        # Calculate improvement trend
        if len(self.feedback_stats['improvement_trend']) > 10:
            recent_ratings = [
                t['rating']
                for t in self.feedback_stats['improvement_trend'][-10:]
            ]
            old_ratings = [
                t['rating']
                for t in self.feedback_stats['improvement_trend'][:10]
            ]

            improvement = statistics.mean(recent_ratings) - statistics.mean(old_ratings)
        else:
            improvement = 0.0

        insights = {
            'total_interactions': len(self.interactions),
            'feedback_stats': self.feedback_stats.copy(),
            'improvement_rate': improvement,
            'top_patterns': [
                {
                    'id': pid,
                    'type': p.pattern_type,
                    'description': p.description,
                    'occurrences': p.occurrences,
                    'confidence': p.confidence
                }
                for pid, p in top_patterns
            ],
            'successful_patterns_count': len(self.improvements['successful_patterns']),
            'failed_patterns_count': len(self.improvements['failed_patterns']),
            'common_corrections_count': len(self.improvements['common_corrections']),
            'optimal_responses_count': len(self.improvements['optimal_responses'])
        }

        return insights

    def get_recommendations(self, query: str) -> Dict[str, Any]:
        """Get recommendations based on learned patterns"""
        recommendations = {
            'similar_successful_queries': [],
            'suggested_improvements': [],
            'optimal_response': None
        }

        # Check for optimal response
        if query in self.improvements['optimal_responses']:
            recommendations['optimal_response'] = \
                self.improvements['optimal_responses'][query]

        # Find similar successful patterns
        query_words = set(query.lower().split())
        for pattern in self.improvements['successful_patterns'][-100:]:
            pattern_words = set(pattern['query'].lower().split())
            similarity = len(query_words & pattern_words) / len(query_words | pattern_words)

            if similarity > 0.5:
                recommendations['similar_successful_queries'].append({
                    'query': pattern['query'],
                    'response': pattern['response'],
                    'similarity': similarity
                })

        # Sort by similarity
        recommendations['similar_successful_queries'].sort(
            key=lambda x: x['similarity'],
            reverse=True
        )

        return recommendations

    def _save_learning_data(self):
        """Save learning data to disk"""
        try:
            # Save interactions
            interactions_file = self.persistence_path / 'interactions.pkl'
            with open(interactions_file, 'wb') as f:
                pickle.dump(list(self.interactions), f)

            # Save patterns
            patterns_file = self.persistence_path / 'patterns.json'
            patterns_data = {
                pid: {
                    **asdict(pattern),
                    'first_seen': pattern.first_seen.isoformat(),
                    'last_seen': pattern.last_seen.isoformat()
                }
                for pid, pattern in self.patterns.items()
            }
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)

            # Save improvements
            improvements_file = self.persistence_path / 'improvements.json'
            with open(improvements_file, 'w', encoding='utf-8') as f:
                json.dump(self.improvements, f, ensure_ascii=False, indent=2)

            # Save feedback stats
            feedback_file = self.persistence_path / 'feedback_stats.json'
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_stats, f, ensure_ascii=False, indent=2)

            self.logger.debug("Learning data saved successfully")

        except Exception as e:
            self.logger.error(f"Error saving learning data: {str(e)}")

    def _load_learning_data(self):
        """Load learning data from disk"""
        try:
            # Load interactions
            interactions_file = self.persistence_path / 'interactions.pkl'
            if interactions_file.exists():
                with open(interactions_file, 'rb') as f:
                    loaded_interactions = pickle.load(f)
                    self.interactions = deque(loaded_interactions, maxlen=self.max_memory_size)
                self.logger.info(f"Loaded {len(self.interactions)} interactions")

            # Load patterns
            patterns_file = self.persistence_path / 'patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                    self.patterns = {
                        pid: LearningPattern(
                            pattern_type=p['pattern_type'],
                            description=p['description'],
                            occurrences=p['occurrences'],
                            confidence=p['confidence'],
                            examples=p['examples'],
                            first_seen=datetime.fromisoformat(p['first_seen']),
                            last_seen=datetime.fromisoformat(p['last_seen'])
                        )
                        for pid, p in patterns_data.items()
                    }
                self.logger.info(f"Loaded {len(self.patterns)} patterns")

            # Load improvements
            improvements_file = self.persistence_path / 'improvements.json'
            if improvements_file.exists():
                with open(improvements_file, 'r', encoding='utf-8') as f:
                    self.improvements = json.load(f)
                self.logger.info("Loaded improvements data")

            # Load feedback stats
            feedback_file = self.persistence_path / 'feedback_stats.json'
            if feedback_file.exists():
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_stats = json.load(f)
                self.logger.info("Loaded feedback statistics")

        except Exception as e:
            self.logger.error(f"Error loading learning data: {str(e)}")

    def export_learning_report(self, output_path: str):
        """Export comprehensive learning report"""
        report = {
            'agent_name': self.agent_name,
            'domain': self.domain,
            'generated_at': datetime.now().isoformat(),
            'insights': self.get_learning_insights(),
            'top_patterns': [
                {
                    'id': pid,
                    'type': p.pattern_type,
                    'description': p.description,
                    'occurrences': p.occurrences,
                    'confidence': p.confidence,
                    'examples': p.examples[:3]
                }
                for pid, p in sorted(
                    self.patterns.items(),
                    key=lambda x: x[1].occurrences,
                    reverse=True
                )[:20]
            ],
            'performance_summary': self.feedback_stats
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Learning report exported to: {output_path}")
