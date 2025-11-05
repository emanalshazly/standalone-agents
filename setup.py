"""
Setup configuration for Standalone Domain Agents
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="standalone-agents",
    version="1.0.0",
    author="Standalone Agents Team",
    author_email="info@standalone-agents.dev",
    description="Revolutionary multi-domain agent system with RAG and continuous learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emanalshazly/standalone-agents",
    project_urls={
        "Bug Tracker": "https://github.com/emanalshazly/standalone-agents/issues",
        "Documentation": "https://docs.standalone-agents.dev",
        "Source Code": "https://github.com/emanalshazly/standalone-agents",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.20",
        "langchain-openai>=0.0.5",
        "openai>=1.12.0",
        "anthropic>=0.18.0",
        "chromadb>=0.4.22",
        "sentence-transformers>=2.3.1",
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.6.0",
        "pyyaml>=6.0.1",
        "loguru>=0.7.2",
        "tenacity>=8.2.3",
        "numpy>=1.26.3",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.4",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
        ],
        "arabic": [
            "camel-tools>=1.5.2",
            "pyarabic>=0.6.15",
        ],
        "full": [
            "redis>=5.0.1",
            "prometheus-client>=0.19.0",
            "sentry-sdk>=1.40.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "standalone-agents=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
