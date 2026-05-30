"""Docker-based test execution tool."""

import logging
import time
from pathlib import Path
from typing import Optional

import docker
from docker.errors import DockerException

from models import TestResult

logger = logging.getLogger(__name__)


class DockerTool:
    """Tool for running tests in Docker containers."""
    
    def __init__(self):
        """Initialize Docker tool."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker tool initialized")
        except DockerException as e:
            logger.error(f"Docker not available: {e}")
            raise
    
    def run_tests(
        self,
        repo_path: Path,
        test_command: Optional[str] = None,
        timeout: int = 300,
    ) -> TestResult:
        """
        Run tests in a Docker container.
        
        Args:
            repo_path: Path to repository
            test_command: Test command to run (auto-detect if None)
            timeout: Timeout in seconds
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        
        try:
            if test_command is None:
                test_command = self._detect_test_command(repo_path)
            
            if not test_command:
                logger.warning("No test command detected, skipping tests")
                return TestResult(
                    success=True,
                    output="No tests detected in repository",
                    exit_code=0,
                    duration=0.0,
                )
            
            logger.info(f"Running tests with command: {test_command}")
            
            dockerfile_content = self._generate_dockerfile(repo_path)
            
            dockerfile_path = repo_path / "Dockerfile.test"
            dockerfile_path.write_text(dockerfile_content)
            
            try:
                image, build_logs = self.client.images.build(
                    path=str(repo_path),
                    dockerfile="Dockerfile.test",
                    tag="reporepair-test:latest",
                    rm=True,
                )
                
                logger.info("Docker image built successfully")
                
                container = self.client.containers.run(
                    image=image.id,
                    command=test_command,
                    detach=True,
                    remove=True,
                )
                
                result = container.wait(timeout=timeout)
                output = container.logs().decode("utf-8")
                exit_code = result["StatusCode"]
                
                duration = time.time() - start_time
                
                success = exit_code == 0
                
                logger.info(f"Tests {'passed' if success else 'failed'} in {duration:.2f}s")
                
                return TestResult(
                    success=success,
                    output=output,
                    exit_code=exit_code,
                    duration=duration,
                )
                
            finally:
                if dockerfile_path.exists():
                    dockerfile_path.unlink()
                
                try:
                    self.client.images.remove("reporepair-test:latest", force=True)
                except:
                    pass
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Test execution failed: {e}")
            
            return TestResult(
                success=False,
                output=f"Error: {str(e)}",
                exit_code=1,
                duration=duration,
            )
    
    def _detect_test_command(self, repo_path: Path) -> Optional[str]:
        """
        Auto-detect test command based on project files.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Test command or None
        """
        if (repo_path / "pytest.ini").exists() or (repo_path / "setup.py").exists():
            return "pytest"
        
        if (repo_path / "package.json").exists():
            import json
            try:
                package_json = json.loads((repo_path / "package.json").read_text())
                if "test" in package_json.get("scripts", {}):
                    return "npm test"
            except:
                pass
        
        if (repo_path / "Makefile").exists():
            makefile_content = (repo_path / "Makefile").read_text()
            if "test:" in makefile_content:
                return "make test"
        
        if (repo_path / "pom.xml").exists():
            return "mvn test"
        
        if (repo_path / "go.mod").exists():
            return "go test ./..."
        
        if (repo_path / "Cargo.toml").exists():
            return "cargo test"
        
        return None
    
    def _generate_dockerfile(self, repo_path: Path) -> str:
        """
        Generate appropriate Dockerfile based on project type.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dockerfile content
        """
        if (repo_path / "requirements.txt").exists():
            return """FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["pytest"]
"""
        
        if (repo_path / "package.json").exists():
            return """FROM node:18-slim

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

CMD ["npm", "test"]
"""
        
        if (repo_path / "go.mod").exists():
            return """FROM golang:1.21-alpine

WORKDIR /app
COPY go.* ./
RUN go mod download

COPY . .

CMD ["go", "test", "./..."]
"""
        
        if (repo_path / "Cargo.toml").exists():
            return """FROM rust:1.75-slim

WORKDIR /app
COPY . /app

RUN cargo build --release

CMD ["cargo", "test"]
"""
        
        return """FROM alpine:latest

WORKDIR /app
COPY . /app

CMD ["echo", "No tests found"]
"""
    
    def is_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            self.client.ping()
            return True
        except:
            return False
