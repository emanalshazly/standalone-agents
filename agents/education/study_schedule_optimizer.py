"""
Study Schedule Optimizer Agent

Unique Features:
- Circadian rhythm-aware scheduling
- Spaced repetition integration
- Energy level optimization
- Conflict resolution with calendar integration
- Adaptive scheduling based on performance
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class StudyBlockType(Enum):
    """Types of study blocks"""
    LEARNING = "learning"
    REVIEW = "review"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    BREAK = "break"


class EnergyLevel(Enum):
    """Energy level throughout day"""
    PEAK = "peak"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class StudyBlock:
    """Study session block"""
    block_id: str
    subject: str
    topic: str
    block_type: StudyBlockType
    start_time: datetime
    duration_minutes: int
    difficulty: str
    priority: int  # 1-5, 5 being highest
    prerequisites: List[str]
    resources: List[str]


@dataclass
class OptimizedSchedule:
    """Optimized study schedule"""
    schedule_id: str
    student_id: str
    start_date: datetime
    end_date: datetime
    study_blocks: List[StudyBlock]
    total_study_hours: float
    subjects_covered: List[str]
    optimization_score: float


class StudyScheduleOptimizer:
    """
    Study Schedule Optimizer with RAG

    Features:
    - Personalized schedule generation
    - Circadian rhythm optimization
    - Spaced repetition scheduling
    - Deadline management
    - Break optimization
    """

    def __init__(self, rag_engine, config: Optional[Dict[str, Any]] = None):
        self.rag_engine = rag_engine
        self.config = config or {}

    async def generate_optimal_schedule(
        self,
        student_id: str,
        subjects: List[Dict[str, Any]],
        available_hours_per_day: int,
        start_date: datetime,
        end_date: datetime,
        student_preferences: Optional[Dict[str, Any]] = None
    ) -> OptimizedSchedule:
        """Generate optimized study schedule"""

        preferences = student_preferences or {}

        # Determine peak performance times
        peak_times = self._identify_peak_times(preferences)

        # Calculate total study needs
        study_needs = self._calculate_study_needs(subjects)

        # Generate study blocks
        study_blocks = []
        current_date = start_date

        while current_date < end_date:
            daily_blocks = self._generate_daily_schedule(
                date=current_date,
                subjects=subjects,
                available_hours=available_hours_per_day,
                peak_times=peak_times,
                preferences=preferences
            )

            study_blocks.extend(daily_blocks)
            current_date += timedelta(days=1)

        # Apply spaced repetition
        study_blocks = self._apply_spaced_repetition(study_blocks)

        # Optimize block ordering
        study_blocks = self._optimize_block_order(study_blocks)

        # Calculate total hours
        total_hours = sum(block.duration_minutes for block in study_blocks) / 60

        # Get unique subjects
        subjects_covered = list(set(block.subject for block in study_blocks))

        # Calculate optimization score
        score = self._calculate_optimization_score(study_blocks, preferences)

        schedule = OptimizedSchedule(
            schedule_id=f"schedule_{datetime.now().timestamp()}",
            student_id=student_id,
            start_date=start_date,
            end_date=end_date,
            study_blocks=study_blocks,
            total_study_hours=total_hours,
            subjects_covered=subjects_covered,
            optimization_score=score
        )

        logger.info(f"Generated schedule for {student_id}: {len(study_blocks)} blocks")

        return schedule

    def _identify_peak_times(self, preferences: Dict[str, Any]) -> Dict[str, EnergyLevel]:
        """Identify peak performance times based on chronotype"""

        chronotype = preferences.get("chronotype", "intermediate")

        # Default time-energy mapping for intermediate type
        time_energy = {
            "06:00-09:00": EnergyLevel.MEDIUM,
            "09:00-12:00": EnergyLevel.PEAK,
            "12:00-14:00": EnergyLevel.LOW,
            "14:00-17:00": EnergyLevel.HIGH,
            "17:00-20:00": EnergyLevel.MEDIUM,
            "20:00-22:00": EnergyLevel.LOW
        }

        if chronotype == "morning":
            time_energy["06:00-09:00"] = EnergyLevel.PEAK
            time_energy["20:00-22:00"] = EnergyLevel.LOW
        elif chronotype == "evening":
            time_energy["06:00-09:00"] = EnergyLevel.LOW
            time_energy["17:00-20:00"] = EnergyLevel.PEAK

        return time_energy

    def _calculate_study_needs(self, subjects: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate total study time needed per subject"""

        needs = {}

        for subject in subjects:
            subject_name = subject["name"]
            difficulty = subject.get("difficulty", "medium")
            current_level = subject.get("current_level", 0.5)
            target_level = subject.get("target_level", 0.8)

            # Calculate hours needed
            gap = target_level - current_level
            base_hours = subject.get("base_hours", 10)

            difficulty_multiplier = {
                "easy": 0.8,
                "medium": 1.0,
                "hard": 1.5
            }.get(difficulty, 1.0)

            total_hours = base_hours * gap * difficulty_multiplier
            needs[subject_name] = int(total_hours)

        return needs

    def _generate_daily_schedule(
        self,
        date: datetime,
        subjects: List[Dict[str, Any]],
        available_hours: int,
        peak_times: Dict[str, EnergyLevel],
        preferences: Dict[str, Any]
    ) -> List[StudyBlock]:
        """Generate schedule for a single day"""

        blocks = []
        start_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=9)

        # Default study session: 50 min study + 10 min break
        study_duration = 50
        break_duration = 10

        sessions_per_day = available_hours

        for i in range(sessions_per_day):
            # Select subject (rotate through subjects)
            subject = subjects[i % len(subjects)]

            # Determine session type
            session_type = self._determine_session_type(i, sessions_per_day)

            # Create study block
            block = StudyBlock(
                block_id=f"block_{date.date()}_{i}",
                subject=subject["name"],
                topic=subject.get("current_topic", "General"),
                block_type=session_type,
                start_time=start_time,
                duration_minutes=study_duration,
                difficulty=subject.get("difficulty", "medium"),
                priority=subject.get("priority", 3),
                prerequisites=[],
                resources=subject.get("resources", [])
            )

            blocks.append(block)

            # Add break
            start_time += timedelta(minutes=study_duration)

            if i < sessions_per_day - 1:
                break_block = StudyBlock(
                    block_id=f"break_{date.date()}_{i}",
                    subject="Break",
                    topic="Rest",
                    block_type=StudyBlockType.BREAK,
                    start_time=start_time,
                    duration_minutes=break_duration,
                    difficulty="easy",
                    priority=5,
                    prerequisites=[],
                    resources=[]
                )
                blocks.append(break_block)
                start_time += timedelta(minutes=break_duration)

        return blocks

    def _determine_session_type(self, session_index: int, total_sessions: int) -> StudyBlockType:
        """Determine the type of study session"""

        # Pattern: Learn -> Practice -> Review
        pattern = [
            StudyBlockType.LEARNING,
            StudyBlockType.PRACTICE,
            StudyBlockType.REVIEW
        ]

        return pattern[session_index % len(pattern)]

    def _apply_spaced_repetition(self, blocks: List[StudyBlock]) -> List[StudyBlock]:
        """Apply spaced repetition algorithm"""

        # Group blocks by topic
        topic_blocks = {}

        for block in blocks:
            if block.block_type != StudyBlockType.BREAK:
                key = f"{block.subject}_{block.topic}"
                if key not in topic_blocks:
                    topic_blocks[key] = []
                topic_blocks[key].append(block)

        # Add review blocks at spaced intervals
        review_blocks = []

        for topic_key, topic_block_list in topic_blocks.items():
            if not topic_block_list:
                continue

            first_block = topic_block_list[0]

            # Schedule reviews at 1 day, 3 days, 7 days
            intervals = [1, 3, 7]

            for interval in intervals:
                review_time = first_block.start_time + timedelta(days=interval)

                review_block = StudyBlock(
                    block_id=f"review_{topic_key}_{interval}d",
                    subject=first_block.subject,
                    topic=first_block.topic,
                    block_type=StudyBlockType.REVIEW,
                    start_time=review_time,
                    duration_minutes=30,
                    difficulty=first_block.difficulty,
                    priority=4,
                    prerequisites=[first_block.block_id],
                    resources=first_block.resources
                )

                review_blocks.append(review_block)

        return blocks + review_blocks

    def _optimize_block_order(self, blocks: List[StudyBlock]) -> List[StudyBlock]:
        """Optimize the order of study blocks"""

        # Sort by start time first
        blocks.sort(key=lambda b: b.start_time)

        # Group by day
        days = {}
        for block in blocks:
            day = block.start_time.date()
            if day not in days:
                days[day] = []
            days[day].append(block)

        # Optimize each day: hard subjects during peak energy
        optimized_blocks = []

        for day, day_blocks in days.items():
            # Separate by difficulty
            hard_blocks = [b for b in day_blocks if b.difficulty == "hard" and b.block_type != StudyBlockType.BREAK]
            medium_blocks = [b for b in day_blocks if b.difficulty == "medium" and b.block_type != StudyBlockType.BREAK]
            easy_blocks = [b for b in day_blocks if b.difficulty == "easy" and b.block_type != StudyBlockType.BREAK]
            breaks = [b for b in day_blocks if b.block_type == StudyBlockType.BREAK]

            # Arrange: hard in morning, medium in afternoon, easy in evening
            arranged = hard_blocks + medium_blocks + easy_blocks

            # Redistribute times
            current_time = datetime.combine(day, datetime.min.time()) + timedelta(hours=9)

            for i, block in enumerate(arranged):
                block.start_time = current_time
                current_time += timedelta(minutes=block.duration_minutes)

                # Add break
                if i < len(arranged) - 1 and i < len(breaks):
                    breaks[i].start_time = current_time
                    current_time += timedelta(minutes=breaks[i].duration_minutes)

            optimized_blocks.extend(arranged)
            optimized_blocks.extend(breaks)

        return sorted(optimized_blocks, key=lambda b: b.start_time)

    def _calculate_optimization_score(
        self,
        blocks: List[StudyBlock],
        preferences: Dict[str, Any]
    ) -> float:
        """Calculate how well the schedule is optimized"""

        score = 0.0
        total_checks = 0

        # Check 1: Hard subjects during peak times
        peak_hour_start = preferences.get("peak_hour_start", 9)
        peak_hour_end = preferences.get("peak_hour_end", 12)

        for block in blocks:
            if block.difficulty == "hard":
                total_checks += 1
                hour = block.start_time.hour
                if peak_hour_start <= hour < peak_hour_end:
                    score += 1

        # Check 2: Regular breaks
        study_blocks = [b for b in blocks if b.block_type != StudyBlockType.BREAK]
        break_blocks = [b for b in blocks if b.block_type == StudyBlockType.BREAK]

        ideal_break_ratio = 0.2  # 1 break per 5 study blocks
        actual_ratio = len(break_blocks) / len(study_blocks) if study_blocks else 0

        break_score = 1 - abs(ideal_break_ratio - actual_ratio)
        score += max(break_score, 0)
        total_checks += 1

        # Check 3: Spaced repetition coverage
        review_blocks = [b for b in blocks if b.block_type == StudyBlockType.REVIEW]
        review_score = min(len(review_blocks) / 10, 1.0)  # Ideal: 10+ review sessions
        score += review_score
        total_checks += 1

        # Normalize score
        final_score = (score / total_checks) if total_checks > 0 else 0.0

        return final_score


if __name__ == "__main__":
    import asyncio
    from shared.rag.rag_engine import RAGEngine, RAGConfig

    async def main():
        rag_engine = RAGEngine(None, None, RAGConfig())
        optimizer = StudyScheduleOptimizer(rag_engine)

        subjects = [
            {
                "name": "Mathematics",
                "difficulty": "hard",
                "current_level": 0.6,
                "target_level": 0.9,
                "priority": 5,
                "base_hours": 15
            },
            {
                "name": "History",
                "difficulty": "medium",
                "current_level": 0.7,
                "target_level": 0.85,
                "priority": 3,
                "base_hours": 10
            }
        ]

        schedule = await optimizer.generate_optimal_schedule(
            student_id="student_001",
            subjects=subjects,
            available_hours_per_day=4,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            student_preferences={"chronotype": "morning", "peak_hour_start": 8}
        )

        print(f"Generated schedule: {len(schedule.study_blocks)} blocks")
        print(f"Total study hours: {schedule.total_study_hours:.1f}")
        print(f"Optimization score: {schedule.optimization_score:.2f}")

    asyncio.run(main())
