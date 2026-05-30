"""Hybrid code search tool combining semantic and keyword search."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from indexer.code_indexer import CodeIndexer
from models import SearchResult

logger = logging.getLogger(__name__)


class SearchTool:
    """Hybrid search combining ChromaDB and grep."""
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize search tool.
        
        Args:
            workspace_dir: Workspace directory
        """
        self.indexer = CodeIndexer(workspace_dir)
        logger.info("Search tool initialized")
    
    def index_repository(self, repo_path: Path) -> int:
        """
        Index repository for semantic search.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Number of files indexed
        """
        return self.indexer.index_repository(repo_path)
    
    def search_semantic(self, query: str, n_results: int = 10) -> list[SearchResult]:
        """
        Semantic search using embeddings.
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of search results
        """
        results = self.indexer.search(query, n_results=n_results)
        
        return [
            SearchResult(
                file_path=r["file_path"],
                content=r["content"],
                relevance_score=r["relevance_score"],
            )
            for r in results
        ]
    
    def search_keyword(
        self,
        repo_path: Path,
        keyword: str,
        file_pattern: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Keyword search using grep.
        
        Args:
            repo_path: Path to repository
            keyword: Keyword to search
            file_pattern: File pattern to filter (e.g., "*.py")
            
        Returns:
            List of search results
        """
        try:
            cmd = ["grep", "-r", "-n", "-i", keyword, str(repo_path)]
            
            if file_pattern:
                cmd.extend(["--include", file_pattern])
            
            cmd.extend([
                "--exclude-dir=.git",
                "--exclude-dir=node_modules",
                "--exclude-dir=__pycache__",
                "--exclude-dir=venv",
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            results = []
            for line in result.stdout.split("\n"):
                if ":" not in line:
                    continue
                
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                
                file_path = Path(parts[0]).relative_to(repo_path)
                line_num = parts[1]
                content = parts[2]
                
                results.append(
                    SearchResult(
                        file_path=str(file_path),
                        content=content.strip(),
                        relevance_score=0.8,
                    )
                )
            
            logger.info(f"Keyword search found {len(results)} results")
            return results
            
        except subprocess.TimeoutExpired:
            logger.error("Grep search timed out")
            return []
        except Exception as e:
            logger.warning(f"Grep search failed ({e}), falling back to native Python search...")
            try:
                results = []
                import fnmatch
                exclude_dirs = {".git", "node_modules", "__pycache__", "venv"}
                
                for p in repo_path.rglob('*'):
                    if p.is_file():
                        if any(exclude in p.parts for exclude in exclude_dirs):
                            continue
                        if file_pattern and not fnmatch.fnmatch(p.name, file_pattern):
                            continue
                        
                        try:
                            content = p.read_text(encoding='utf-8', errors='ignore')
                            if keyword.lower() in content.lower():
                                lines = content.split('\n')
                                for idx, line in enumerate(lines):
                                    if keyword.lower() in line.lower():
                                        file_path = p.relative_to(repo_path)
                                        results.append(
                                            SearchResult(
                                                file_path=str(file_path),
                                                content=line.strip(),
                                                relevance_score=0.8,
                                            )
                                        )
                        except Exception:
                            continue
                logger.info(f"Python fallback keyword search found {len(results)} results")
                return results
            except Exception as e2:
                logger.error(f"Fallback search failed: {e2}")
                return []
    
    def search_hybrid(
        self,
        repo_path: Path,
        query: str,
        n_results: int = 15,
    ) -> list[SearchResult]:
        """
        Hybrid search combining semantic and keyword.
        
        Args:
            repo_path: Path to repository
            query: Search query
            n_results: Total number of results
            
        Returns:
            Combined and deduplicated search results
        """
        try:
            semantic_results = self.search_semantic(query, n_results=n_results // 2)
        except Exception as e:
            logger.warning(f"Semantic search failed ({e}), using keyword search fallback...")
            semantic_results = []
        
        keywords = self._extract_keywords(query)
        keyword_results = []
        for keyword in keywords[:2]:
            keyword_results.extend(
                self.search_keyword(repo_path, keyword)[:n_results // 4]
            )
        
        combined = self._deduplicate_results(semantic_results + keyword_results)
        
        combined.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Hybrid search returned {len(combined[:n_results])} results")
        return combined[:n_results]
    
    def _extract_keywords(self, query: str) -> list[str]:
        """Extract important keywords from query."""
        stopwords = {
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "with",
            "is", "are", "was", "were", "be", "been", "being", "have", "has",
            "had", "do", "does", "did", "will", "would", "should", "could",
            "and", "or", "but", "not", "from", "by", "as",
        }
        
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        return keywords
    
    def _deduplicate_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """Remove duplicate results based on file path."""
        seen = set()
        deduplicated = []
        
        for result in results:
            if result.file_path not in seen:
                seen.add(result.file_path)
                deduplicated.append(result)
        
        return deduplicated
