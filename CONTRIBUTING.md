# Contributing to Standalone AI Agents

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/standalone-agents.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit: `git commit -m "Add feature: description"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Copy config example
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings to all functions and classes
- Keep functions focused and small
- Write descriptive variable names

### Formatting

```bash
# Format code
black .

# Check linting
flake8

# Type checking
mypy .
```

## Testing

All new features should include tests.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=shared

# Run specific test file
pytest tests/education/test_personalized_learning.py
```

## Adding New Agents

### Structure

```python
"""
Agent Name - Brief description

Unique Features:
- Feature 1
- Feature 2
- Feature 3
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class YourAgent:
    """
    Agent description

    Features:
    - Feature details
    """

    def __init__(self, rag_engine, config: Optional[Dict[str, Any]] = None):
        self.rag_engine = rag_engine
        self.config = config or {}

    async def main_method(self, params) -> ReturnType:
        """Method description"""
        pass
```

### Checklist

- [ ] Agent follows project structure
- [ ] Includes comprehensive docstrings
- [ ] Uses RAG engine appropriately
- [ ] Includes type hints
- [ ] Has example usage in docstring or README
- [ ] Includes tests
- [ ] Updates domain README
- [ ] Updates main README if needed

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Commit Message Guidelines

Format: `<type>: <subject>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
- `feat: add property valuation agent`
- `fix: resolve embedding cache issue`
- `docs: update education agents README`

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

Open an issue or reach out to maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
