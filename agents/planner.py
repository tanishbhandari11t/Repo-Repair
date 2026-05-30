"""Planner agent for analyzing issues and creating strategies."""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from models import Issue, AgentState

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent that analyzes issues and creates fix strategies."""
    
    SYSTEM_PROMPT = """You are a senior software engineer analyzing a GitHub issue to create a fix strategy.

Your task:
1. Analyze the issue description carefully
2. Identify the type of bug/feature (e.g., logic error, missing feature, performance issue)
3. Determine what parts of the codebase are likely involved
4. Generate specific search queries to find relevant code files
5. Create a high-level strategy for fixing the issue

Be specific and actionable. Focus on finding the RIGHT files, not just related files.

Output format:
STRATEGY: <one paragraph describing the fix approach>
SEARCH_QUERIES: <comma-separated list of 3-5 specific search queries>
"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        """
        Initialize planner agent.
        
        Args:
            api_key: Gemini, OpenAI, Anthropic, or Groq API key
            model_name: Model to use
        """
        import os
        
        # 1. Groq Support (Key starts with gsk_)
        if api_key and api_key.startswith("gsk_"):
            from langchain_groq import ChatGroq
            actual_model = "llama-3.3-70b-specdec" if any(x in model_name.lower() for x in ["gemini", "gpt", "claude"]) else model_name
            self.llm = ChatGroq(
                model=actual_model,
                groq_api_key=api_key,
                temperature=0.3,
            )
            
        # 2. Anthropic (Claude) Support (Key starts with sk-ant-)
        elif api_key and api_key.startswith("sk-ant-"):
            from langchain_anthropic import ChatAnthropic
            actual_model = "claude-3-5-sonnet-latest" if any(x in model_name.lower() for x in ["gemini", "gpt", "llama"]) else model_name
            self.llm = ChatAnthropic(
                model=actual_model,
                api_key=api_key,
                temperature=0.3,
            )
            
        # 3. OpenRouter Support (Key starts with sk-or-)
        elif api_key and api_key.startswith("sk-or-"):
            from langchain_openai import ChatOpenAI
            base_url = "https://openrouter.ai/api/v1"
            actual_model = model_name
            if "gemini-2.5-flash" in model_name:
                actual_model = "google/gemini-2.5-flash"
            elif "gemini-1.5-flash" in model_name:
                actual_model = "google/gemini-1.5-flash"
            elif "gemini-2.5-pro" in model_name:
                actual_model = "google/gemini-2.5-pro"
            elif "gemini-1.5-pro" in model_name:
                actual_model = "google/gemini-1.5-pro"
            elif "/" not in model_name:
                actual_model = "google/gemini-2.5-flash"
            
            self.llm = ChatOpenAI(
                model=actual_model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.3,
                max_tokens=4096,
            )

        # 3.5. OpenAI / Custom Endpoint Support (Key starts with sk-)
        elif api_key and api_key.startswith("sk-"):
            from langchain_openai import ChatOpenAI
            base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or None
            actual_model = "gpt-4o-mini" if any(x in model_name.lower() for x in ["gemini", "llama", "claude"]) else model_name
            self.llm = ChatOpenAI(
                model=actual_model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.3,
            )
            
        # 4. Standard Gemini Fallback
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.3,
            )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("user", """Repository: {repo_name}
Issue #{issue_number}: {issue_title}

Description:
{issue_body}

Create a fix strategy and search queries."""),
        ])
        
        self.chain = self.prompt | self.llm
        
        logger.info(f"Planner agent initialized with model: {model_name}")
    
    def plan(self, state: AgentState) -> AgentState:
        """
        Analyze issue and create fix strategy.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with strategy and search queries
        """
        logger.info(f"Planning fix for issue #{state.issue_number}")
        
        try:
            response = self.chain.invoke({
                "repo_name": f"{state.owner}/{state.repo}",
                "issue_number": state.issue_number,
                "issue_title": state.issue.title,
                "issue_body": state.issue.body,
            })
            
            content = response.content
            
            strategy = self._extract_section(content, "STRATEGY:")
            search_queries_str = self._extract_section(content, "SEARCH_QUERIES:")
            
            search_queries = [q.strip() for q in search_queries_str.split(",") if q.strip()]
            
            if not search_queries:
                fallback_query = state.issue.title
                search_queries = [fallback_query]
                logger.info(f"No search queries found in LLM output, falling back to issue title: {fallback_query}")
                
            if not strategy:
                strategy = "Fixing issue: " + state.issue.title
                
            state.strategy = strategy
            state.search_queries = search_queries
            
            # Store reasoning for UI
            state.reasoning["planner"] = {
                "strategy": strategy,
                "search_queries": search_queries,
                "raw_response": content
            }
            
            logger.info(f"Strategy created with {len(search_queries)} search queries")
            logger.debug(f"Strategy: {strategy}")
            
            return state
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            state.error = f"Planning failed: {str(e)}"
            return state
    
    def _extract_section(self, content: str, marker: str) -> str:
        """Extract section from LLM response."""
        lines = content.split("\n")
        result = []
        capturing = False
        
        for line in lines:
            if marker in line:
                capturing = True
                result.append(line.replace(marker, "").strip())
            elif capturing:
                if line.strip().startswith("STRATEGY:") or line.strip().startswith("SEARCH_QUERIES:"):
                    break
                result.append(line)
        
        return "\n".join(result).strip()
