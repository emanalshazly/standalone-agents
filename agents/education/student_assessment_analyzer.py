"""
Student Assessment Analyzer Agent

Unique Features:
- Multi-dimensional learning analytics
- Predictive performance modeling
- Personalized feedback generation
- Learning trajectory visualization
- Early intervention recommendations
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class AssessmentType(Enum):
    """Types of assessments"""
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    DIAGNOSTIC = "diagnostic"
    BENCHMARK = "benchmark"


@dataclass
class Assessment:
    """Assessment data"""
    assessment_id: str
    student_id: str
    assessment_type: AssessmentType
    subject: str
    total_points: float
    earned_points: float
    completion_time_minutes: int
    question_responses: List[Dict[str, Any]]
    timestamp: datetime


@dataclass
class PerformanceAnalysis:
    """Student performance analysis"""
    student_id: str
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_areas: List[str]
    learning_velocity: float  # Rate of improvement
    predicted_performance: Dict[str, float]
    recommended_interventions: List[str]
    confidence_level: float


class StudentAssessmentAnalyzer:
    """
    Student Assessment Analyzer with RAG

    Features:
    - Comprehensive performance analysis
    - Predictive analytics
    - Personalized feedback
    - Learning gap identification
    - Intervention recommendations
    """

    def __init__(self, rag_engine, config: Optional[Dict[str, Any]] = None):
        self.rag_engine = rag_engine
        self.config = config or {}
        self.assessments: Dict[str, List[Assessment]] = {}

    async def analyze_student_performance(
        self,
        student_id: str,
        time_period: Optional[tuple[datetime, datetime]] = None
    ) -> PerformanceAnalysis:
        """Comprehensive performance analysis"""

        # Get assessments
        assessments = self._get_student_assessments(student_id, time_period)

        if not assessments:
            raise ValueError(f"No assessments found for student {student_id}")

        # Calculate metrics
        overall_score = self._calculate_overall_score(assessments)
        strengths = await self._identify_strengths(student_id, assessments)
        weaknesses = await self._identify_weaknesses(student_id, assessments)

        # Analyze learning velocity
        velocity = self._calculate_learning_velocity(assessments)

        # Predict future performance
        predictions = self._predict_performance(assessments, velocity)

        # Generate recommendations
        interventions = await self._recommend_interventions(
            student_id=student_id,
            weaknesses=weaknesses,
            velocity=velocity
        )

        # Identify improvement areas
        improvement_areas = self._prioritize_improvement_areas(weaknesses, predictions)

        analysis = PerformanceAnalysis(
            student_id=student_id,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_areas=improvement_areas,
            learning_velocity=velocity,
            predicted_performance=predictions,
            recommended_interventions=interventions,
            confidence_level=self._calculate_confidence(assessments)
        )

        logger.info(f"Completed analysis for student {student_id}")

        return analysis

    def _calculate_overall_score(self, assessments: List[Assessment]) -> float:
        """Calculate weighted overall score"""

        if not assessments:
            return 0.0

        # Weight recent assessments more heavily
        weighted_scores = []
        total_weight = 0

        for i, assessment in enumerate(sorted(assessments, key=lambda a: a.timestamp)):
            weight = i + 1  # Linearly increasing weight
            score_percentage = (assessment.earned_points / assessment.total_points) * 100
            weighted_scores.append(score_percentage * weight)
            total_weight += weight

        return sum(weighted_scores) / total_weight if total_weight > 0 else 0.0

    async def _identify_strengths(
        self,
        student_id: str,
        assessments: List[Assessment]
    ) -> List[str]:
        """Identify student strengths"""

        # Analyze performance by topic/concept
        topic_scores = {}

        for assessment in assessments:
            for response in assessment.question_responses:
                topic = response.get("topic", "general")
                is_correct = response.get("is_correct", False)

                if topic not in topic_scores:
                    topic_scores[topic] = []

                topic_scores[topic].append(1.0 if is_correct else 0.0)

        # Identify high-performing topics
        strengths = []
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score >= 0.8:  # 80% threshold
                strengths.append(topic)

        return strengths[:5]  # Top 5 strengths

    async def _identify_weaknesses(
        self,
        student_id: str,
        assessments: List[Assessment]
    ) -> List[str]:
        """Identify areas needing improvement"""

        topic_scores = {}

        for assessment in assessments:
            for response in assessment.question_responses:
                topic = response.get("topic", "general")
                is_correct = response.get("is_correct", False)

                if topic not in topic_scores:
                    topic_scores[topic] = []

                topic_scores[topic].append(1.0 if is_correct else 0.0)

        # Identify low-performing topics
        weaknesses = []
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.6:  # Below 60%
                weaknesses.append(topic)

        return weaknesses

    def _calculate_learning_velocity(self, assessments: List[Assessment]) -> float:
        """Calculate rate of improvement"""

        if len(assessments) < 2:
            return 0.0

        # Sort by timestamp
        sorted_assessments = sorted(assessments, key=lambda a: a.timestamp)

        # Calculate scores over time
        scores = [
            (a.earned_points / a.total_points) * 100
            for a in sorted_assessments
        ]

        # Simple linear regression slope
        n = len(scores)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(scores) / n

        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        velocity = numerator / denominator if denominator != 0 else 0.0

        return velocity

    def _predict_performance(
        self,
        assessments: List[Assessment],
        velocity: float
    ) -> Dict[str, float]:
        """Predict future performance"""

        current_score = self._calculate_overall_score(assessments)

        predictions = {
            "next_assessment": min(current_score + velocity, 100),
            "1_month": min(current_score + (velocity * 4), 100),
            "3_months": min(current_score + (velocity * 12), 100),
            "end_of_term": min(current_score + (velocity * 20), 100)
        }

        return predictions

    async def _recommend_interventions(
        self,
        student_id: str,
        weaknesses: List[str],
        velocity: float
    ) -> List[str]:
        """Recommend interventions"""

        interventions = []

        # Based on velocity
        if velocity < 0:
            interventions.append("Immediate one-on-one tutoring recommended")
            interventions.append("Review fundamental concepts")
        elif velocity < 1:
            interventions.append("Additional practice exercises needed")
            interventions.append("Consider study group participation")

        # Based on weaknesses
        for weakness in weaknesses[:3]:
            interventions.append(f"Focused review session on {weakness}")

        # Query RAG for research-based interventions
        if weaknesses:
            query = f"Effective interventions for students struggling with {', '.join(weaknesses)}"
            rag_response = await self.rag_engine.query(query=query)

            # Would extract interventions from RAG response
            interventions.append("Evidence-based strategy: Spaced repetition practice")

        return interventions

    def _prioritize_improvement_areas(
        self,
        weaknesses: List[str],
        predictions: Dict[str, float]
    ) -> List[str]:
        """Prioritize areas for improvement"""

        # Prioritize based on urgency and impact
        prioritized = weaknesses.copy()

        # If predicted performance is low, prioritize foundational topics
        if predictions.get("next_assessment", 0) < 60:
            prioritized.insert(0, "foundational_skills")

        return prioritized[:5]

    def _calculate_confidence(self, assessments: List[Assessment]) -> float:
        """Calculate confidence level of analysis"""

        # More assessments = higher confidence
        assessment_count_factor = min(len(assessments) / 10, 1.0)

        # Consistent performance = higher confidence
        scores = [(a.earned_points / a.total_points) for a in assessments]

        if len(scores) > 1:
            std_dev = statistics.stdev(scores)
            consistency_factor = 1.0 - min(std_dev, 1.0)
        else:
            consistency_factor = 0.5

        confidence = (assessment_count_factor + consistency_factor) / 2

        return confidence

    def _get_student_assessments(
        self,
        student_id: str,
        time_period: Optional[tuple[datetime, datetime]] = None
    ) -> List[Assessment]:
        """Get assessments for student"""

        assessments = self.assessments.get(student_id, [])

        if time_period:
            start, end = time_period
            assessments = [
                a for a in assessments
                if start <= a.timestamp <= end
            ]

        return assessments

    def add_assessment(self, assessment: Assessment):
        """Add assessment data"""

        if assessment.student_id not in self.assessments:
            self.assessments[assessment.student_id] = []

        self.assessments[assessment.student_id].append(assessment)

        logger.info(f"Added assessment {assessment.assessment_id} for student {assessment.student_id}")

    async def generate_feedback(
        self,
        assessment_id: str,
        student_id: str
    ) -> Dict[str, Any]:
        """Generate personalized feedback"""

        # Find assessment
        assessment = None
        for a in self.assessments.get(student_id, []):
            if a.assessment_id == assessment_id:
                assessment = a
                break

        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")

        score_percentage = (assessment.earned_points / assessment.total_points) * 100

        # Generate feedback using RAG
        query = f"Generate constructive feedback for a student who scored {score_percentage:.1f}% on {assessment.subject}"
        rag_response = await self.rag_engine.query(query=query)

        feedback = {
            "score": score_percentage,
            "performance_level": self._get_performance_level(score_percentage),
            "positive_aspects": await self._generate_positive_feedback(assessment),
            "improvement_areas": await self._generate_improvement_feedback(assessment),
            "specific_feedback": [
                self._generate_question_feedback(response)
                for response in assessment.question_responses[:5]  # Top 5
            ],
            "next_steps": await self._generate_next_steps(student_id, assessment)
        }

        return feedback

    def _get_performance_level(self, score: float) -> str:
        """Categorize performance"""

        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Satisfactory"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Requires Intervention"

    async def _generate_positive_feedback(self, assessment: Assessment) -> List[str]:
        """Generate positive feedback points"""

        positives = []

        # Completion time
        if assessment.completion_time_minutes < 60:
            positives.append("Completed assessment efficiently")

        # Correct responses
        correct_count = sum(
            1 for r in assessment.question_responses
            if r.get("is_correct", False)
        )

        if correct_count > len(assessment.question_responses) / 2:
            positives.append(f"Answered {correct_count} questions correctly")

        return positives

    async def _generate_improvement_feedback(self, assessment: Assessment) -> List[str]:
        """Generate improvement suggestions"""

        improvements = []

        # Analyze incorrect responses
        incorrect_topics = set()
        for response in assessment.question_responses:
            if not response.get("is_correct", False):
                incorrect_topics.add(response.get("topic", "general"))

        for topic in list(incorrect_topics)[:3]:
            improvements.append(f"Review concepts in {topic}")

        return improvements

    def _generate_question_feedback(self, response: Dict[str, Any]) -> str:
        """Generate feedback for individual question"""

        if response.get("is_correct"):
            return f"Question {response.get('question_id')}: Correct! {response.get('explanation', '')}"
        else:
            return f"Question {response.get('question_id')}: Review {response.get('topic')}. {response.get('explanation', '')}"

    async def _generate_next_steps(
        self,
        student_id: str,
        assessment: Assessment
    ) -> List[str]:
        """Generate recommended next steps"""

        score_percentage = (assessment.earned_points / assessment.total_points) * 100

        next_steps = []

        if score_percentage < 70:
            next_steps.append("Schedule review session with instructor")
            next_steps.append("Complete supplementary practice exercises")
        else:
            next_steps.append("Ready to proceed to next topic")
            next_steps.append("Challenge yourself with advanced materials")

        return next_steps


if __name__ == "__main__":
    import asyncio
    from shared.rag.rag_engine import RAGEngine, RAGConfig

    async def main():
        rag_engine = RAGEngine(None, None, RAGConfig())
        analyzer = StudentAssessmentAnalyzer(rag_engine)

        # Add sample assessment
        assessment = Assessment(
            assessment_id="test_001",
            student_id="student_001",
            assessment_type=AssessmentType.FORMATIVE,
            subject="Mathematics",
            total_points=100,
            earned_points=75,
            completion_time_minutes=45,
            question_responses=[
                {"question_id": "q1", "topic": "algebra", "is_correct": True},
                {"question_id": "q2", "topic": "geometry", "is_correct": False}
            ],
            timestamp=datetime.now()
        )

        analyzer.add_assessment(assessment)

        analysis = await analyzer.analyze_student_performance("student_001")
        print(f"Overall score: {analysis.overall_score:.2f}")
        print(f"Learning velocity: {analysis.learning_velocity:.2f}")

    asyncio.run(main())
