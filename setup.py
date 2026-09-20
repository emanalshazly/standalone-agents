"""
Setup configuration for the Egyptian Arabic Legal-Literacy Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="egypt-legal-agent",
    version="2.0.0",
    author="Standalone Agents Team",
    author_email="info@standalone-agents.dev",
    description="Citation-verified Arabic legal-literacy agent for Egyptian contracts and rights questions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emanalshazly/standalone-agents",
    project_urls={
        "Bug Tracker": "https://github.com/emanalshazly/standalone-agents/issues",
        "Source Code": "https://github.com/emanalshazly/standalone-agents",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "openai>=1.12.0",
        "anthropic>=0.18.0",
        "langgraph>=0.2.0",
        "langchain-core>=0.3.0",
        "llama-index-core>=0.11.0",
        "llama-index-vector-stores-chroma>=0.2.0",
        "llama-index-embeddings-huggingface>=0.3.0",
        "chromadb>=0.4.22",
        "sentence-transformers>=2.3.1",
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.6.0",
        "sqlalchemy>=2.0.25",
        "pyyaml>=6.0.1",
        "loguru>=0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.4",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "eval": [
            "ragas>=0.2.0",
            "datasets>=2.19.0",
        ],
        "observability": [
            "langfuse>=2.50.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
