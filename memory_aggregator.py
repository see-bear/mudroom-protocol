#!/usr/bin/env python3
"""
Memory Aggregation and Deduplication Tool

Phase 3 of the Mudroom Protocol V2 Pipeline:
✅ Load vector metadata from multiple files
✅ Cluster semantically similar entries
✅ Deduplicate or merge related content
✅ Output an aggregated, lightweight strategic memory view
"""

import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from collections import defaultdict
from datetime import datetime
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Configure console
console = Console()

# Default configuration
DEFAULT_CONFIG = {
    "vector_store_dir": "vector_store",
    "output_dir": "mudroom_logs/aggregated_memory",
    "model_name": "all-MiniLM-L6-v2",
    "similarity_threshold": 0.82,
    "min_confidence": 0.7,
    "focus_levels": ["L2", "L3"],  # Focus on strategic content
    "max_cluster_size": 10,  # Maximum entries per cluster
    "output_formats": ["markdown", "json"]
}

class MemoryAggregator:
    """
    Enhanced memory aggregation and deduplication tool
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory aggregator
        
        Args:
            config: Configuration dictionary
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.vector_store_dir = Path(self.config["vector_store_dir"])
        self.output_dir = Path(self.config["output_dir"])
        self.model = SentenceTransformer(self.config["model_name"])
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_vectors_and_metadata(self) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Load all vectors and metadata from vector store
        
        Returns:
            Tuple of (vectors_array, metadata_list)
        """
        all_vectors = []
        all_metadata = []
        
        if not self.vector_store_dir.exists():
            console.print(f"[red]Vector store directory {self.vector_store_dir} does not exist[/red]")
            return np.array([]), []
        
        # Find all vector store files
        npy_files = list(self.vector_store_dir.glob("*_vectors.npy"))
        
        if not npy_files:
            console.print(f"[yellow]No vector store files found in {self.vector_store_dir}[/yellow]")
            return np.array([]), []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Loading vector stores...", total=len(npy_files))
            
            for npy_file in npy_files:
                try:
                    file_id = npy_file.stem.replace("_vectors", "")
                    json_file = self.vector_store_dir / f"{file_id}_metadata.json"
                    
                    if not json_file.exists():
                        console.print(f"[yellow]Warning: No metadata file for {file_id}[/yellow]")
                        progress.advance(task)
                        continue
                    
                    # Load vectors
                    vectors = np.load(npy_file)
                    
                    # Load metadata
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Validate data integrity
                    if len(vectors) != len(metadata):
                        console.print(f"[yellow]Warning: Vector/metadata count mismatch for {file_id}[/yellow]")
                        progress.advance(task)
                        continue
                    
                    # Filter by classification level and confidence
                    filtered_vectors = []
                    filtered_metadata = []
                    
                    for i, meta in enumerate(metadata):
                        classification = meta.get("classification", "")
                        confidence = meta.get("confidence_score", 0.0)
                        
                        if (classification in self.config["focus_levels"] and 
                            confidence >= self.config["min_confidence"]):
                            filtered_vectors.append(vectors[i])
                            filtered_metadata.append(meta)
                    
                    all_vectors.extend(filtered_vectors)
                    all_metadata.extend(filtered_metadata)
                    
                    progress.advance(task)
                    
                except Exception as e:
                    console.print(f"[red]Error loading {npy_file.name}: {e}[/red]")
                    progress.advance(task)
                    continue
        
        console.print(f"[green]Loaded {len(all_vectors)} vectors from {len(npy_files)} files[/green]")
        return np.array(all_vectors), all_metadata
    
    def cluster_and_deduplicate(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster similar entries and deduplicate
        
        Args:
            vectors: Array of embedding vectors
            metadata: List of metadata dictionaries
            
        Returns:
            List of deduplicated metadata entries
        """
        if len(vectors) == 0:
            return []
        
        console.print(f"[bold blue]Clustering {len(vectors)} entries with threshold {self.config['similarity_threshold']}...[/bold blue]")
        
        used = set()
        clusters = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Clustering entries...", total=len(vectors))
            
            for i in range(len(vectors)):
                if i in used:
                    progress.advance(task)
                    continue
                
                cluster = [i]
                cluster_size = 1
                
                for j in range(i + 1, len(vectors)):
                    if j in used or cluster_size >= self.config["max_cluster_size"]:
                        continue
                    
                    try:
                        sim = util.cos_sim(vectors[i], vectors[j]).item()
                        if sim >= self.config["similarity_threshold"]:
                            cluster.append(j)
                            used.add(j)
                            cluster_size += 1
                    except Exception as e:
                        console.print(f"[yellow]Warning: Error calculating similarity: {e}[/yellow]")
                        continue
                
                used.add(i)
                clusters.append(cluster)
                progress.advance(task)
        
        # Merge clusters
        merged = []
        for cluster in clusters:
            entries = [metadata[idx] for idx in cluster]
            
            # Select best entry based on multiple criteria
            best_entry = self._select_best_entry(entries)
            merged.append(best_entry)
        
        console.print(f"[green]Created {len(clusters)} clusters, reduced to {len(merged)} unique entries[/green]")
        return merged
    
    def _select_best_entry(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select the best entry from a cluster based on multiple criteria
        
        Args:
            entries: List of metadata entries in the cluster
            
        Returns:
            Best entry with cluster information added
        """
        if len(entries) == 1:
            return entries[0]
        
        # Score each entry based on multiple criteria
        scored_entries = []
        for entry in entries:
            score = 0.0
            
            # Higher confidence gets higher score
            confidence = entry.get("confidence_score", 0.0)
            score += confidence * 0.4
            
            # More recent entries get higher score
            ingest_date = entry.get("ingest_date", "")
            if ingest_date:
                try:
                    date_obj = datetime.fromisoformat(ingest_date.replace("Z", "+00:00"))
                    # Normalize date score (0-1 scale)
                    days_ago = (datetime.now() - date_obj).days
                    date_score = max(0, 1 - (days_ago / 365))  # Decay over a year
                    score += date_score * 0.3
                except:
                    pass
            
            # L3 entries get higher score than L2
            classification = entry.get("classification", "")
            if classification == "L3":
                score += 0.2
            elif classification == "L2":
                score += 0.1
            
            # Topic shifts get higher score
            if entry.get("topic_shift", False):
                score += 0.1
            
            scored_entries.append((score, entry))
        
        # Select entry with highest score
        best_score, best_entry = max(scored_entries, key=lambda x: x[0])
        
        # Add cluster information
        best_entry["cluster_size"] = len(entries)
        best_entry["cluster_score"] = best_score
        best_entry["cluster_sources"] = [e.get("filename", "Unknown") for e in entries]
        
        return best_entry
    
    def save_aggregated_output(self, merged: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Save aggregated output in multiple formats
        
        Args:
            merged: List of deduplicated metadata entries
            
        Returns:
            Dictionary of output file paths
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        output_files = {}
        
        # Save markdown
        if "markdown" in self.config["output_formats"]:
            md_path = self.output_dir / f"aggregated_memory_{timestamp}.md"
            self._save_markdown(md_path, merged, timestamp)
            output_files["markdown"] = str(md_path)
        
        # Save JSON
        if "json" in self.config["output_formats"]:
            json_path = self.output_dir / f"aggregated_memory_{timestamp}.json"
            self._save_json(json_path, merged, timestamp)
            output_files["json"] = str(json_path)
        
        # Save statistics
        stats_path = self.output_dir / f"aggregation_stats_{timestamp}.json"
        self._save_statistics(stats_path, merged, timestamp)
        output_files["statistics"] = str(stats_path)
        
        return output_files
    
    def _save_markdown(self, path: Path, merged: List[Dict[str, Any]], timestamp: str):
        """Save aggregated memory as markdown"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# Aggregated Strategic Memory — {timestamp}\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Entries: {len(merged)}\n")
            f.write(f"Similarity Threshold: {self.config['similarity_threshold']}\n\n")
            
            # Group by classification
            by_level = defaultdict(list)
            for entry in merged:
                level = entry.get("classification", "Unknown")
                by_level[level].append(entry)
            
            for level in ["L3", "L2"]:
                if level in by_level:
                    f.write(f"## {level} Strategic Content\n\n")
                    
                    for i, entry in enumerate(by_level[level], 1):
                        f.write(f"### Entry {i}\n\n")
                        f.write(f"**Source:** {entry.get('filename', 'Unknown')}\n")
                        f.write(f"**Project:** {entry.get('project', 'Unknown')}\n")
                        f.write(f"**Confidence:** {entry.get('confidence_score', 0.0):.2f}\n")
                        f.write(f"**Cluster Size:** {entry.get('cluster_size', 1)} similar entries\n")
                        f.write(f"**Date:** {entry.get('ingest_date', 'Unknown')}\n")
                        f.write(f"**Speaker:** {entry.get('speaker_transition', 'Unknown')}\n")
                        
                        if entry.get("topic_shift", False):
                            f.write(f"**Topic Shift:** Yes\n")
                        
                        f.write(f"\n**Sources:** {', '.join(entry.get('cluster_sources', []))}\n\n")
                        f.write("---\n\n")
    
    def _save_json(self, path: Path, merged: List[Dict[str, Any]], timestamp: str):
        """Save aggregated memory as JSON"""
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "timestamp": timestamp,
                "total_entries": len(merged),
                "similarity_threshold": self.config["similarity_threshold"],
                "focus_levels": self.config["focus_levels"],
                "min_confidence": self.config["min_confidence"]
            },
            "entries": merged
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def _save_statistics(self, path: Path, merged: List[Dict[str, Any]], timestamp: str):
        """Save aggregation statistics"""
        stats = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "timestamp": timestamp
            },
            "summary": {
                "total_entries": len(merged),
                "l3_count": len([e for e in merged if e.get("classification") == "L3"]),
                "l2_count": len([e for e in merged if e.get("classification") == "L2"]),
                "avg_confidence": sum(e.get("confidence_score", 0.0) for e in merged) / len(merged) if merged else 0.0,
                "avg_cluster_size": sum(e.get("cluster_size", 1) for e in merged) / len(merged) if merged else 0.0
            },
            "projects": defaultdict(int),
            "files": defaultdict(int)
        }
        
        for entry in merged:
            stats["projects"][entry.get("project", "Unknown")] += 1
            stats["files"][entry.get("filename", "Unknown")] += 1
        
        stats["projects"] = dict(stats["projects"])
        stats["files"] = dict(stats["files"])
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def run(self) -> Dict[str, str]:
        """
        Run the complete aggregation pipeline
        
        Returns:
            Dictionary of output file paths
        """
        console.print(Panel("🧠 Memory Aggregator", style="bold blue"))
        
        # Load data
        vectors, metadata = self.load_vectors_and_metadata()
        
        if len(vectors) == 0:
            console.print("[red]No data to process[/red]")
            return {}
        
        # Cluster and deduplicate
        merged = self.cluster_and_deduplicate(vectors, metadata)
        
        if len(merged) == 0:
            console.print("[yellow]No entries met the filtering criteria[/yellow]")
            return {}
        
        # Save output
        output_files = self.save_aggregated_output(merged)
        
        # Display summary
        self._display_summary(merged, output_files)
        
        return output_files
    
    def _display_summary(self, merged: List[Dict[str, Any]], output_files: Dict[str, str]):
        """Display aggregation summary"""
        table = Table(title="Aggregation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Entries", str(len(merged)))
        table.add_row("L3 Entries", str(len([e for e in merged if e.get("classification") == "L3"])))
        table.add_row("L2 Entries", str(len([e for e in merged if e.get("classification") == "L2"])))
        table.add_row("Avg Confidence", f"{sum(e.get('confidence_score', 0.0) for e in merged) / len(merged):.2f}")
        table.add_row("Avg Cluster Size", f"{sum(e.get('cluster_size', 1) for e in merged) / len(merged):.1f}")
        
        console.print(table)
        
        console.print(f"\n[green]Output files:[/green]")
        for format_type, path in output_files.items():
            console.print(f"  {format_type}: {path}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Memory Aggregator for Mud Room Protocol")
    parser.add_argument("--threshold", type=float, default=0.82, help="Similarity threshold (0.0-1.0)")
    parser.add_argument("--min-confidence", type=float, default=0.7, help="Minimum confidence score")
    parser.add_argument("--levels", nargs="+", default=["L2", "L3"], help="Classification levels to focus on")
    parser.add_argument("--output-dir", default="mudroom_logs/aggregated_memory", help="Output directory")
    parser.add_argument("--formats", nargs="+", default=["markdown", "json"], help="Output formats")
    
    args = parser.parse_args()
    
    # Create configuration
    config = {
        "similarity_threshold": args.threshold,
        "min_confidence": args.min_confidence,
        "focus_levels": args.levels,
        "output_dir": args.output_dir,
        "output_formats": args.formats
    }
    
    # Run aggregator
    aggregator = MemoryAggregator(config)
    output_files = aggregator.run()
    
    if output_files:
        console.print(f"\n[bold green]✅ Memory aggregation completed successfully![/bold green]")
    else:
        console.print(f"\n[red]❌ Memory aggregation failed or no data found[/red]")


if __name__ == "__main__":
    main()
