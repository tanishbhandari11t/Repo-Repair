"""Searcher agent for finding relevant code files."""

import logging
from pathlib import Path

from tools.search_tool import SearchTool
from models import AgentState, SearchResult

logger = logging.getLogger(__name__)


class SearcherAgent:
    """Agent that finds relevant code files using hybrid search."""
    
    def __init__(self, search_tool: SearchTool):
        """
        Initialize searcher agent.
        
        Args:
            search_tool: Search tool instance
        """
        self.search_tool = search_tool
        logger.info("Searcher agent initialized")
    
    def search(self, state: AgentState) -> AgentState:
        """
        Search for relevant code files.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with relevant files
        """
        logger.info("Searching for relevant files")
        
        if not state.search_queries:
            logger.error("No search queries available")
            state.error = "No search queries from planner"
            return state
        
        try:
            try:
                logger.info(f"Indexing repository: {state.repo_path}")
                self.search_tool.index_repository(Path(state.repo_path))
            except Exception as e:
                logger.warning(f"Semantic indexing failed ({e}). Proceeding with pure keyword search.")
            
            all_results = []
            
            for query in state.search_queries:
                logger.info(f"Searching: {query}")
                results = self.search_tool.search_hybrid(
                    Path(state.repo_path),
                    query,
                    n_results=5,
                )
                all_results.extend(results)
            
            deduplicated = self._deduplicate_by_file(all_results)
            
            sorted_results = sorted(
                deduplicated,
                key=lambda x: x.relevance_score,
                reverse=True,
            )[:10]
            
            if not sorted_results:
                logger.info("No hybrid search results found. Finding any files present in the repository as fallback...")
                try:
                    repo_dir = Path(state.repo_path)
                    fallback_files = []
                    for path in repo_dir.rglob("*"):
                        if path.is_file():
                            rel_path = path.relative_to(repo_dir)
                            parts_lower = [p.lower() for p in rel_path.parts]
                            if not any(p.startswith('.') or p in ('venv', 'node_modules', '__pycache__', 'dist', 'build') for p in parts_lower):
                                fallback_files.append(rel_path.as_posix())
                                if len(fallback_files) >= 5:
                                    break
                    
                    if fallback_files:
                        sorted_results = [
                            SearchResult(
                                file_path=f,
                                content="Fallback file representation",
                                relevance_score=0.1
                            )
                            for f in fallback_files
                        ]
                        logger.info(f"Fallback added {len(sorted_results)} files from repository: {fallback_files}")
                except Exception as ex:
                    logger.warning(f"Failed to find fallback files: {ex}")
            
            state.relevant_files = sorted_results
            
            logger.info(f"Found {len(sorted_results)} relevant files")
            for result in sorted_results[:3]:
                logger.debug(f"  - {result.file_path} (score: {result.relevance_score:.3f})")
            
            return state
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            state.error = f"Search failed: {str(e)}"
            return state
    
    def _deduplicate_by_file(self, results: list[SearchResult]) -> list[SearchResult]:
        """Deduplicate results, keeping highest score for each file."""
        file_map = {}
        
        for result in results:
            if result.file_path not in file_map:
                file_map[result.file_path] = result
            else:
                if result.relevance_score > file_map[result.file_path].relevance_score:
                    file_map[result.file_path] = result
        
        return list(file_map.values())
