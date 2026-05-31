"""Validator agent for testing and validating changes."""

import logging
from pathlib import Path

from tools.docker_tool import DockerTool
from models import AgentState, ReasoningStep
import time

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """Agent that validates code changes by running tests."""
    
    def __init__(self, docker_tool: DockerTool):
        """
        Initialize validator agent.
        
        Args:
            docker_tool: Docker tool instance
        """
        self.docker_tool = docker_tool
        logger.info("Validator agent initialized")
    
    def validate(self, state: AgentState, skip_tests: bool = False) -> AgentState:
        """
        Validate changes by running tests.
        
        Args:
            state: Current agent state
            skip_tests: Skip test execution
            
        Returns:
            Updated state with validation results
        """
        logger.info("Validating changes")
        
        if skip_tests:
            logger.warning("Skipping tests as requested")
            state.validation_passed = True
            return state
        
        if state.changes is not None and len(state.changes) == 0:
            logger.info("No changes to validate (empty changes list)")
            state.validation_passed = True
            return state
            
        if not state.changes:
            logger.error("No changes available to validate")
            state.error = "No changes available for validation"
            return state
        
        try:
            if not self.docker_tool.is_docker_available():
                logger.warning("Docker not available, skipping tests")
                state.validation_passed = True
                return state
            
            result = self.docker_tool.run_tests(Path(state.repo_path))
            
            state.test_result = result
            state.validation_passed = result.success
            
            if result.success:
                state.reasoning_trace.append(ReasoningStep(
                    agent="Validator",
                    message=f"All tests passed in {result.duration:.2f}s.",
                    timestamp=time.time()
                ))
                logger.info(f"Tests passed in {result.duration:.2f}s")
            else:
                state.reasoning_trace.append(ReasoningStep(
                    agent="Validator",
                    message=f"Tests failed: {result.output[:200]}...",
                    timestamp=time.time()
                ))
                logger.error(f"Tests failed: {result.output[:200]}")
                
                if state.retry_count < state.max_retries:
                    state.retry_count += 1
                    logger.info(f"Will retry (attempt {state.retry_count}/{state.max_retries})")
                else:
                    state.error = "Tests failed after maximum retries"
            
            return state
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            state.error = f"Validation failed: {str(e)}"
            return state
    
    def should_retry(self, state: AgentState) -> bool:
        """Check if we should retry code generation."""
        return (
            not state.validation_passed
            and state.retry_count < state.max_retries
            and state.test_result is not None
        )
