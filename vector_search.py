#!/usr/bin/env python3
"""
Vector Search Engine for Mud Room Protocol v2.0
Semantic search across stored conversation embeddings with metadata filtering
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import argparse
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

class VectorSearchEngine:
    """
    Semantic search engine for vector store
    """
    
    def __init__(self, vector_store_dir: str = "vector_store", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the search engine
        
        Args:
            vector_store_dir: Directory containing vector store files
            model_name: Sentence transformer model to use for embeddings
        """
        self.vector_store_dir = Path(vector_store_dir)
        self.model = SentenceTransformer(model_name)
        self.console = Console()
        
        # Load all available vector stores
        self.vector_stores = self._load_all_vector_stores()
        
    def _load_all_vector_stores(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all vector stores from disk
        
        Returns:
            Dictionary mapping file_id to vector store data
        """
        stores = {}
        
        if not self.vector_store_dir.exists():
            logger.warning(f"Vector store directory {self.vector_store_dir} does not exist")
            return stores
        
        # Find all vector store files
        for npy_file in self.vector_store_dir.glob("*_vectors.npy"):
            file_id = npy_file.stem.replace("_vectors", "")
            json_file = self.vector_store_dir / f"{file_id}_metadata.json"
            
            if json_file.exists():
                try:
                    # Load embeddings
                    embeddings = np.load(npy_file)
                    
                    # Load metadata
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    stores[file_id] = {
                        "embeddings": embeddings,
                        "metadata": metadata,
                        "npy_path": str(npy_file),
                        "json_path": str(json_file)
                    }
                    
                    logger.info(f"Loaded vector store: {file_id} ({len(embeddings)} embeddings)")
                    
                except Exception as e:
                    logger.error(f"Failed to load vector store {file_id}: {e}")
        
        logger.info(f"Loaded {len(stores)} vector stores")
        return stores
    
    def search(self, query: str, 
               top_k: int = 10, 
               classification_filter: Optional[str] = None,
               project_filter: Optional[str] = None,
               filename_filter: Optional[str] = None,
               date_filter: Optional[str] = None,
               confidence_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Perform semantic search across all vector stores
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            classification_filter: Filter by classification level (L1, L2, L3)
            project_filter: Filter by project name
            filename_filter: Filter by filename (partial match)
            date_filter: Filter by date (YYYY-MM-DD format)
            confidence_threshold: Minimum confidence score
            
        Returns:
            List of search results with metadata
        """
        # Encode query
        query_embedding = self.model.encode([query])[0]
        
        all_results = []
        
        # Search across all vector stores
        for file_id, store_data in self.vector_stores.items():
            embeddings = store_data["embeddings"]
            metadata = store_data["metadata"]
            
            # Calculate similarities
            similarities = self._calculate_similarities(query_embedding, embeddings)
            
            # Create results with metadata
            for i, (similarity, meta) in enumerate(zip(similarities, metadata)):
                # Apply filters
                if not self._passes_filters(meta, classification_filter, project_filter, 
                                          filename_filter, date_filter, confidence_threshold):
                    continue
                
                result = {
                    "file_id": file_id,
                    "block_id": meta.get("block_id", i),
                    "similarity": float(similarity),
                    "classification": meta.get("classification", "Unknown"),
                    "confidence_score": meta.get("confidence_score", 0.0),
                    "session_id": meta.get("session_id", 0),
                    "topic_shift": meta.get("topic_shift", False),
                    "speaker_transition": meta.get("speaker_transition", ""),
                    "filename": meta.get("filename", f"{file_id}.txt"),
                    "project": meta.get("project", "Unknown"),
                    "ingest_date": meta.get("ingest_date", ""),
                    "metadata": meta
                }
                
                all_results.append(result)
        
        # Sort by similarity and return top_k
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        return all_results[:top_k]
    
    def _calculate_similarities(self, query_embedding: np.ndarray, 
                              embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarities between query and embeddings
        
        Args:
            query_embedding: Query embedding vector
            embeddings: Matrix of stored embeddings
            
        Returns:
            Array of similarity scores
        """
        # Normalize embeddings for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Calculate cosine similarities
        similarities = np.dot(embeddings_norm, query_norm)
        return similarities
    
    def _passes_filters(self, metadata: Dict[str, Any], 
                       classification_filter: Optional[str],
                       project_filter: Optional[str],
                       filename_filter: Optional[str],
                       date_filter: Optional[str],
                       confidence_threshold: float) -> bool:
        """
        Check if metadata passes all filters
        
        Args:
            metadata: Metadata dictionary
            classification_filter: Classification level filter
            project_filter: Project name filter
            filename_filter: Filename filter
            date_filter: Date filter
            confidence_threshold: Minimum confidence score
            
        Returns:
            True if metadata passes all filters
        """
        # Classification filter
        if classification_filter and metadata.get("classification") != classification_filter:
            return False
        
        # Project filter
        if project_filter and metadata.get("project", "").lower() != project_filter.lower():
            return False
        
        # Filename filter (partial match)
        if filename_filter and filename_filter.lower() not in metadata.get("filename", "").lower():
            return False
        
        # Date filter
        if date_filter:
            ingest_date = metadata.get("ingest_date", "")
            if ingest_date and not ingest_date.startswith(date_filter):
                return False
        
        # Confidence threshold
        if metadata.get("confidence_score", 0.0) < confidence_threshold:
            return False
        
        return True
    
    def list_projects(self) -> List[str]:
        """List all available projects"""
        projects = set()
        for store_data in self.vector_stores.values():
            for meta in store_data["metadata"]:
                project = meta.get("project", "Unknown")
                projects.add(project)
        return sorted(list(projects))
    
    def list_files(self) -> List[str]:
        """List all available files"""
        files = set()
        for store_data in self.vector_stores.values():
            for meta in store_data["metadata"]:
                filename = meta.get("filename", "Unknown")
                files.add(filename)
        return sorted(list(files))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        total_embeddings = 0
        classifications = {"L1": 0, "L2": 0, "L3": 0}
        projects = {}
        
        for store_data in self.vector_stores.values():
            total_embeddings += len(store_data["embeddings"])
            
            for meta in store_data["metadata"]:
                # Count classifications
                classification = meta.get("classification", "Unknown")
                if classification in classifications:
                    classifications[classification] += 1
                
                # Count projects
                project = meta.get("project", "Unknown")
                projects[project] = projects.get(project, 0) + 1
        
        return {
            "total_vector_stores": len(self.vector_stores),
            "total_embeddings": total_embeddings,
            "classifications": classifications,
            "projects": projects
        }


def display_search_results(results: List[Dict[str, Any]], query: str):
    """Display search results in a rich table"""
    if not results:
        console.print(Panel("No results found", style="red"))
        return
    
    # Create table
    table = Table(title=f"Search Results for: '{query}'")
    table.add_column("Rank", style="cyan", no_wrap=True)
    table.add_column("Similarity", style="green", no_wrap=True)
    table.add_column("Level", style="yellow", no_wrap=True)
    table.add_column("File", style="blue", no_wrap=True)
    table.add_column("Project", style="magenta", no_wrap=True)
    table.add_column("Session", style="cyan", no_wrap=True)
    table.add_column("Speaker", style="white", no_wrap=True)
    table.add_column("Confidence", style="green", no_wrap=True)
    
    for i, result in enumerate(results, 1):
        table.add_row(
            str(i),
            f"{result['similarity']:.3f}",
            result['classification'],
            result['filename'][:20] + "..." if len(result['filename']) > 20 else result['filename'],
            result['project'][:15] + "..." if len(result['project']) > 15 else result['project'],
            str(result['session_id']),
            result['speaker_transition'][:10] + "..." if len(result['speaker_transition']) > 10 else result['speaker_transition'],
            f"{result['confidence_score']:.2f}"
        )
    
    console.print(table)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Vector Search Engine for Mud Room Protocol")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to return")
    parser.add_argument("--level", choices=["L1", "L2", "L3"], help="Filter by classification level")
    parser.add_argument("--project", help="Filter by project name")
    parser.add_argument("--file", help="Filter by filename (partial match)")
    parser.add_argument("--date", help="Filter by date (YYYY-MM-DD)")
    parser.add_argument("--confidence", type=float, default=0.0, help="Minimum confidence score")
    parser.add_argument("--list-projects", action="store_true", help="List all available projects")
    parser.add_argument("--list-files", action="store_true", help="List all available files")
    parser.add_argument("--stats", action="store_true", help="Show vector store statistics")
    
    args = parser.parse_args()
    
    # Initialize search engine
    search_engine = VectorSearchEngine()
    
    # Handle different commands
    if args.list_projects:
        projects = search_engine.list_projects()
        console.print(Panel(f"Available Projects:\n" + "\n".join(projects), title="Projects"))
        return
    
    if args.list_files:
        files = search_engine.list_files()
        console.print(Panel(f"Available Files:\n" + "\n".join(files), title="Files"))
        return
    
    if args.stats:
        stats = search_engine.get_statistics()
        console.print(Panel(
            f"Vector Store Statistics:\n"
            f"Total Stores: {stats['total_vector_stores']}\n"
            f"Total Embeddings: {stats['total_embeddings']}\n"
            f"Classifications: {stats['classifications']}\n"
            f"Projects: {stats['projects']}",
            title="Statistics"
        ))
        return
    
    if not args.query:
        console.print(Panel(
            "Vector Search Engine\n\n"
            "Usage examples:\n"
            "  python vector_search.py 'strategic decisions'\n"
            "  python vector_search.py 'performance optimization' --level L3\n"
            "  python vector_search.py 'debug issues' --level L1 --project MudRoom\n"
            "  python vector_search.py --list-projects\n"
            "  python vector_search.py --stats",
            title="Help"
        ))
        return
    
    # Perform search
    console.print(f"🔍 Searching for: '{args.query}'")
    
    results = search_engine.search(
        query=args.query,
        top_k=args.top_k,
        classification_filter=args.level,
        project_filter=args.project,
        filename_filter=args.file,
        date_filter=args.date,
        confidence_threshold=args.confidence
    )
    
    # Display results
    display_search_results(results, args.query)
    
    # Show summary
    console.print(f"\n📊 Found {len(results)} results")


if __name__ == "__main__":
    main()
