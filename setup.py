"""Setup script for RepoRepair."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="reporepair",
    version="0.1.0",
    author="RepoRepair Team",
    description="AI GitHub Issue to Pull Request Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/RepoRepair",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Bug Tracking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "typer[all]>=0.12.3",
        "langgraph>=0.2.20",
        "langchain>=0.2.16",
        "langchain-google-genai>=1.0.10",
        "PyGithub>=2.3.0",
        "GitPython>=3.1.43",
        "chromadb>=0.5.3",
        "sentence-transformers>=3.0.1",
        "python-dotenv>=1.0.1",
        "requests>=2.31.0",
        "rich>=13.7.1",
        "pydantic>=2.7.4",
        "pydantic-settings>=2.3.4",
        "docker>=7.1.0",
    ],
    entry_points={
        "console_scripts": [
            "reporepair=cli.main:app",
        ],
    },
)
