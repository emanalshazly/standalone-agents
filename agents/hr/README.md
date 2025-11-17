# HR Domain Agents

Collection of 5 specialized AI agents for human resources applications.

## Agents

### 1. Resume Screening & Matching Agent
**File**: `resume_screening.py`

**Unique Features**:
- Semantic skill matching using embeddings
- Bias detection in screening process
- Skills gap analysis per candidate
- Diversity metrics tracking

**Key Capabilities**:
- Match candidates to job postings
- Semantic skill matching
- Detect and flag potential biases
- Rank candidates objectively

### 2. Employee Onboarding Assistant
**File**: `employee_onboarding.py`

**Unique Features**:
- Personalized onboarding journeys
- Cultural integration support
- Buddy matching algorithm
- Progress tracking dashboards

**Key Capabilities**:
- Create customized onboarding plans
- Assign mentors/buddies
- Track onboarding progress
- Generate role-specific training paths

### 3. Performance Review Analyzer
**File**: `performance_review.py`

**Unique Features**:
- 360-degree feedback synthesis
- Growth pattern recognition
- Objective assessment calibration
- Development planning automation

**Key Capabilities**:
- Aggregate multi-source feedback
- Identify performance patterns
- Generate development recommendations
- Suggest performance goals

### 4. Skills Gap Analyzer
**File**: `skills_gap_analyzer.py`

**Unique Features**:
- Future-skills forecasting
- Team-level skills analysis
- Learning path recommendations
- Succession planning support

**Key Capabilities**:
- Analyze team skill composition
- Predict future skill requirements
- Identify critical skills gaps
- Recommend training programs

### 5. Talent Development Advisor
**File**: `talent_development.py`

**Unique Features**:
- Career trajectory modeling
- Personalized coaching recommendations
- Opportunity matching
- Retention risk analysis

**Key Capabilities**:
- Create career development paths
- Match employees to opportunities
- Generate development activities
- Track career progression

## Usage Example

```python
from agents.hr import ResumeScreeningAgent

agent = ResumeScreeningAgent(rag_engine)

# Match candidates to job
matches = await agent.match_candidates(
    job=job_posting,
    candidates=candidate_list
)

# Get top matches with bias detection
for match in matches[:5]:
    print(f"{match['name']}: {match['fit_score']:.2f}")
    print(f"Bias flags: {match['bias_flags']}")
```
