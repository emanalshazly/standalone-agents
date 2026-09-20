# Contributing to Standalone Agents

<div dir="rtl">

نرحب بمساهماتكم! هذا المشروع مفتوح المصدر ونسعد بأي إضافات أو تحسينات.

</div>

Thank you for your interest in contributing to Standalone Agents! This document provides guidelines for contributing to the project.

## 🌟 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages or logs

### Suggesting Enhancements

We welcome enhancement suggestions! Please:
- Check existing issues first
- Provide clear use case
- Explain expected benefits
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/emanalshazly/standalone-agents.git
   cd standalone-agents
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests if applicable
   - Update documentation
   - Ensure all tests pass

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Code Style Guidelines

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Use type hints
def process_query(query: str, context: AgentContext) -> AgentResponse:
    pass

# Docstrings for all public methods
def public_method(self, param: str) -> bool:
    """
    Brief description

    Args:
        param: Parameter description

    Returns:
        Return value description
    """
    pass

# Clear variable names
user_query = request.query  # Good
q = request.query  # Avoid
```

### Documentation

- Add docstrings to all classes and public methods
- Update README.md if adding new features
- Include examples for new functionality
- Support both English and Arabic documentation

## 🧪 Testing

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_agent.py
```

### Writing Tests

```python
import pytest
from src.agents.medical.medical_agent import MedicalAgent

def test_medical_agent_initialization():
    agent = MedicalAgent()
    assert agent.agent_name == "MedicalAgent"
    assert agent.domain == "medical"

def test_symptom_analysis():
    agent = MedicalAgent()
    result = agent.analyze_symptoms("headache and fever")
    assert result is not None
    assert "analysis" in result
```

## 🎯 Extending the Legal Agent

This project deliberately scoped itself down to a single domain (Egyptian
labor/contract literacy) after a competitive/technical audit found that a
generic multi-domain `BaseAgent` pattern was reinventing weaker versions of
mature open-source frameworks — see
[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for the full reasoning. There is
no `BaseAgent` to subclass anymore, and no plan to add a seventh
generalist domain. Contributions in this domain are welcome; a proposal to
add another unrelated vertical back into this repo should probably be its
own project instead.

The two ways to extend this agent safely:

### 1. Add or correct knowledge-base content

Do **not** hand-edit `src/knowledge/legal_eg/labor_law_2025_seed.json` and
call it verified. The real path is:

1. `POST /feedback/submit` (or `CurationPipeline.submit_correction(...)`)
   with the query, the current (wrong/incomplete) answer, and your proposed
   correction, plus the primary source (Official Gazette article/date), not
   a secondary law-firm summary.
2. A named human reviewer approves it via `POST /feedback/{id}/approve` (or
   `CurationPipeline.approve(...)`), which embeds it into
   `EgyptianLegalIndex` tagged `verified_by_lawyer=True`.
3. Update `docs/eval/citation_audit.md`'s row for that topic.

### 2. Extend scope (new legal topics, e.g. rental/consumer contracts)

1. Add the topic to `scope.in_scope_topics` in `config/config.example.yaml`
   and `IN_SCOPE_TOPICS` in `src/graph/legal_graph.py` — otherwise
   `classify_intent` will hand off the query even with good source content.
2. Add seed entries following the same JSON structure as
   `labor_law_2025_seed.json`, with the same honesty requirements: real
   sources cited, `verified_by_lawyer: false` until a lawyer reviews it,
   and any conflicting information across sources flagged explicitly
   rather than resolved by guessing (see the `notice_period_indefinite`
   entry for the pattern).
3. Add corresponding rows to `tests/eval/golden_qa.jsonl` and
   `docs/eval/citation_audit.md`.
4. Run `pytest tests/` and `python tests/eval/run_eval.py --mode retrieval`
   before opening a PR.

## 🌐 Internationalization (i18n)

### Adding Language Support

We currently support English and Arabic. To add a new language:

1. **Update language detection**
   ```python
   def _detect_language(self, text: str) -> str:
       # Add language detection logic
       pass
   ```

2. **Add translations**
   - System prompts
   - Error messages
   - Documentation

3. **Update configuration**
   ```yaml
   languages:
     supported:
       - "en"
       - "ar"
       - "your_language_code"
   ```

## 📚 Knowledge Base Contributions

### Adding Domain Knowledge

```python
# Example: Adding medical knowledge
medical_knowledge = [
    {
        "pain_point": "Common symptom description",
        "solution": "Detailed guidance and recommendations",
        "metadata": {
            "priority": "high",
            "language": "en",
            "verified": True
        }
    }
]

agent.rag_system.add_pain_point_knowledge(
    pain_point=knowledge["pain_point"],
    solution=knowledge["solution"],
    metadata=knowledge["metadata"]
)
```

### Knowledge Quality Guidelines

- **Accuracy**: Ensure information is accurate and up-to-date
- **Sources**: Cite reliable sources
- **Language**: Support multiple languages
- **Structure**: Follow consistent format
- **Verification**: Mark verified vs unverified content

## 🔒 Security

### Reporting Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead:
- Email: security@standalone-agents.dev
- Include: Detailed description, impact, steps to reproduce
- We'll respond within 48 hours

### Security Best Practices

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Sanitize user inputs
- Follow principle of least privilege
- Keep dependencies updated

## 📋 Code Review Process

All submissions require review. We follow these principles:

1. **Quality**: Code is clean, well-documented, tested
2. **Functionality**: Changes work as intended
3. **Compatibility**: No breaking changes without discussion
4. **Performance**: No significant performance degradation
5. **Security**: No security vulnerabilities introduced

## 🎓 Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pytest Documentation](https://docs.pytest.org/)

## 💬 Community

- **Discord**: [Join our community](https://discord.gg/standalone-agents)
- **Discussions**: [GitHub Discussions](https://github.com/emanalshazly/standalone-agents/discussions)
- **Twitter**: [@StandaloneAgents](https://twitter.com/standaloneagents)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

<div dir="rtl" align="center">

### شكراً لمساهمتكم في تطوير هذا المشروع!

**معاً نبني مستقبل الوكلاء الذكيين**

</div>

Thank you for contributing to Standalone Agents! 🚀
