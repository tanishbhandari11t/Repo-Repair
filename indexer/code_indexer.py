"""Code indexing with ChromaDB for semantic search."""

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class CodeIndexer:
    """Index and search code using vector embeddings."""
    
    EXCLUDED_DIRS = {
        ".git", "node_modules", "__pycache__", "venv", "env", 
        ".venv", "dist", "build", ".egg-info", "coverage",
    }
    
    INDEXED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
        ".rs", ".cpp", ".c", ".h", ".cs", ".rb", ".php",
        ".swift", ".kt", ".scala", ".sh", ".bash",
    }
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize code indexer.
        
        Args:
            workspace_dir: Directory for ChromaDB storage
        """
        self.workspace_dir = Path(workspace_dir)
        chroma_dir = self.workspace_dir / "chroma_db"
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        logger.info("Code indexer initialized")
    
    def index_repository(self, repo_path: Path, collection_name: str = "codebase") -> int:
        """
        Index all code files in a repository.
        
        Args:
            repo_path: Path to repository
            collection_name: Name for the collection
            
        Returns:
            Number of files indexed
        """
        # Count target files first to prevent hanging on massive repositories
        target_files = list(self._walk_repository(repo_path))
        if len(target_files) > 300:
            logger.info(f"Repository has {len(target_files)} files. Skipping semantic indexing for speed.")
            raise ValueError(f"Repository too large for free-tier semantic index ({len(target_files)} files > 300 limit)")
            
        try:
            self.client.delete_collection(collection_name)
        except:
            pass
        
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        
        files_indexed = 0
        documents = []
        metadatas = []
        ids = []
        
        for file_path in target_files:
            try:
                rel_path = file_path.relative_to(repo_path)
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                if len(content.strip()) == 0:
                    continue
                
                chunks = self._chunk_file(content, max_chunk_size=1000)
                
                for i, chunk in enumerate(chunks):
                    doc_id = f"{rel_path}:chunk_{i}"
                    documents.append(chunk)
                    metadatas.append({
                        "file_path": str(rel_path),
                        "chunk_index": i,
                        "extension": file_path.suffix,
                    })
                    ids.append(doc_id)
                
                files_indexed += 1
                
                if len(documents) >= 100:
                    collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids,
                    )
                    documents, metadatas, ids = [], [], []
                
            except Exception as e:
                logger.warning(f"Failed to index {file_path}: {e}")
        
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
        
        logger.info(f"Indexed {files_indexed} files from {repo_path}")
        return files_indexed
    
    def search(
        self,
        query: str,
        collection_name: str = "codebase",
        n_results: int = 10,
    ) -> list[dict]:
        """
        Search for code semantically.
        
        Args:
            query: Search query
            collection_name: Collection to search
            n_results: Number of results to return
            
        Returns:
            List of search results with file paths and content
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            
            search_results = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0
                
                search_results.append({
                    "file_path": metadata["file_path"],
                    "content": doc,
                    "relevance_score": 1 - distance,
                    "chunk_index": metadata["chunk_index"],
                })
            
            logger.info(f"Found {len(search_results)} results for query: {query}")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _walk_repository(self, repo_path: Path):
        """Walk repository and yield code files."""
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            if any(excluded in file_path.parts for excluded in self.EXCLUDED_DIRS):
                continue
            
            if file_path.suffix in self.INDEXED_EXTENSIONS:
                yield file_path
    
    def _chunk_file(self, content: str, max_chunk_size: int = 1000) -> list[str]:
        """Split file content into chunks."""
        lines = content.split("\n")
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1
            
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
