# Education Domain Agents

Collection of 5 specialized AI agents for educational applications.

## Agents

### 1. Personalized Learning Assistant
**File**: `personalized_learning_assistant.py`

**Unique Features**:
- Adaptive learning path generation based on student's learning style
- Multi-modal content recommendations (visual, auditory, kinesthetic)
- Spaced repetition scheduling
- Real-time difficulty adjustment

**Key Capabilities**:
- Create personalized learning paths
- Recommend content based on learning style
- Track progress and adjust difficulty
- Generate spaced repetition schedules

### 2. Academic Research Helper
**File**: `academic_research_helper.py`

**Unique Features**:
- Citation network analysis and visualization
- Research gap identification
- Methodology recommendation engine
- Collaboration network suggestions

**Key Capabilities**:
- Conduct automated literature reviews
- Identify research gaps
- Recommend research methodologies
- Analyze citation networks

### 3. Course Content Generator
**File**: `course_content_generator.py`

**Unique Features**:
- Multi-format content creation (slides, quizzes, video scripts)
- Bloom's Taxonomy alignment
- Accessibility compliance (WCAG)
- Gamification elements integration

**Key Capabilities**:
- Generate course modules
- Create assessments aligned with learning objectives
- Produce multimedia content
- Ensure accessibility standards

### 4. Student Assessment Analyzer
**File**: `student_assessment_analyzer.py`

**Unique Features**:
- Multi-dimensional learning analytics
- Predictive performance modeling
- Personalized feedback generation
- Early intervention recommendations

**Key Capabilities**:
- Analyze student performance
- Predict future performance
- Generate personalized feedback
- Recommend interventions

### 5. Study Schedule Optimizer
**File**: `study_schedule_optimizer.py`

**Unique Features**:
- Circadian rhythm-aware scheduling
- Spaced repetition integration
- Energy level optimization
- Adaptive scheduling based on performance

**Key Capabilities**:
- Generate optimal study schedules
- Apply spaced repetition algorithms
- Optimize for peak performance times
- Balance difficulty across study sessions

## Usage Example

```python
from agents.education import PersonalizedLearningAssistant
from shared.rag import RAGEngine, RAGConfig

# Initialize
rag_engine = RAGEngine(vector_store, llm, RAGConfig())
assistant = PersonalizedLearningAssistant(rag_engine)

# Create student profile
profile = assistant.create_student_profile(
    student_id="student_001",
    name="Alice",
    learning_style=LearningStyle.VISUAL,
    current_level=DifficultyLevel.INTERMEDIATE
)

# Generate learning path
path = await assistant.create_learning_path(
    student_id="student_001",
    subject="Data Science",
    learning_goals=["Python basics", "Statistics"],
    time_available=10
)
```
