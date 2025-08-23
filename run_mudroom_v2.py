#!/usr/bin/env python3
"""
Mud Room Protocol v2.0 - Batch Processor
Enhanced conversation classification with semantic understanding
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

from mudroom_classifier_v2 import MudRoomClassifierV2

console = Console()


def setup_directories():
    """Ensure required directories exist"""
    directories = ["batch_txts", "mudroom_logs", "keywords"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Check if keyword files exist
    keyword_files = ["keywords/level1.txt", "keywords/level2.txt", "keywords/level3.txt"]
    missing_files = []
    
    for file_path in keyword_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        console.print(f"[yellow]Warning: Missing keyword files: {missing_files}[/yellow]")
        console.print("Please ensure all keyword files exist before running the classifier.")


def get_input_files(input_dir: str = "batch_txts") -> list:
    """Get list of .txt files to process"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        console.print(f"[red]Error: Input directory '{input_dir}' does not exist[/red]")
        return []
    
    txt_files = list(input_path.glob("*.txt"))
    
    if not txt_files:
        console.print(f"[yellow]No .txt files found in '{input_dir}'[/yellow]")
        console.print("Please add some conversation files to process.")
    
    return txt_files


def process_file(classifier: MudRoomClassifierV2, file_path: Path, output_dir: str) -> dict:
    """Process a single conversation file"""
    console.print(f"[blue]Starting to process: {file_path.name}[/blue]")
    
    try:
        # Check file size and basic info
        file_size = file_path.stat().st_size
        console.print(f"[blue]File size: {file_size:,} bytes[/blue]")
        
        # Read first few lines to check format
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = [f.readline().strip() for _ in range(5)]
        console.print(f"[blue]First few lines: {first_lines[:3]}[/blue]")
        
        results = classifier.classify_conversation(
            input_path=str(file_path),
            output_dir=output_dir
        )
        
        # Calculate statistics
        stats = {
            "file": file_path.name,
            "total_blocks": sum(len(classifications) for classifications in results.values()),
            "l1_count": len(results.get("L1", [])),
            "l2_count": len(results.get("L2", [])),
            "l3_count": len(results.get("L3", [])),
            "avg_confidence": 0.0,
            "success": True
        }
        
        console.print(f"[green]✓ Successfully processed {file_path.name}[/green]")
        console.print(f"[green]  - L1: {stats['l1_count']}, L2: {stats['l2_count']}, L3: {stats['l3_count']}[/green]")
        
        # Calculate average confidence
        all_classifications = []
        for classifications in results.values():
            all_classifications.extend(classifications)
        
        if all_classifications:
            stats["avg_confidence"] = sum(r.confidence for r in all_classifications) / len(all_classifications)
        
        return stats
        
    except Exception as e:
        console.print(f"[red]❌ Error processing {file_path.name}: {e}[/red]")
        console.print(f"[red]Error type: {type(e).__name__}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        return {
            "file": file_path.name,
            "total_blocks": 0,
            "l1_count": 0,
            "l2_count": 0,
            "l3_count": 0,
            "avg_confidence": 0.0,
            "success": False,
            "error": str(e)
        }


def display_results(results: list):
    """Display processing results in a nice table"""
    if not results:
        return
    
    # Filter successful results
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    if successful:
        table = Table(title="Processing Results")
        table.add_column("File", style="cyan")
        table.add_column("Total Blocks", style="green")
        table.add_column("L1", style="yellow")
        table.add_column("L2", style="blue")
        table.add_column("L3", style="magenta")
        table.add_column("Avg Confidence", style="white")
        
        for result in successful:
            table.add_row(
                result["file"],
                str(result["total_blocks"]),
                str(result["l1_count"]),
                str(result["l2_count"]),
                str(result["l3_count"]),
                f"{result['avg_confidence']:.3f}"
            )
        
        console.print(table)
    
    if failed:
        console.print(f"\n[red]Failed to process {len(failed)} files:[/red]")
        for result in failed:
            console.print(f"  - {result['file']}: {result.get('error', 'Unknown error')}")
    
    # Summary statistics
    if successful:
        total_files = len(successful)
        total_blocks = sum(r["total_blocks"] for r in successful)
        total_l1 = sum(r["l1_count"] for r in successful)
        total_l2 = sum(r["l2_count"] for r in successful)
        total_l3 = sum(r["l3_count"] for r in successful)
        avg_confidence = sum(r["avg_confidence"] for r in successful) / len(successful)
        
        summary = f"""
        [bold]Summary:[/bold]
        • Processed {total_files} files successfully
        • Found {total_blocks} classified blocks
        • Level distribution: L1={total_l1}, L2={total_l2}, L3={total_l3}
        • Average confidence: {avg_confidence:.3f}
        """
        
        console.print(Panel(summary, title="Processing Summary", border_style="green"))


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Mud Room Protocol v2.0 - Enhanced Conversation Classifier")
    parser.add_argument("--input-dir", default="batch_txts", help="Directory containing .txt files to process")
    parser.add_argument("--output-dir", default="mudroom_logs", help="Directory to save classification results")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--test", action="store_true", help="Run in test mode with sample data")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold blue]Mud Room Protocol v2.0[/bold blue]\n"
        "[italic]Enhanced Conversation Classification with Semantic Understanding[/italic]",
        border_style="blue"
    ))
    
    # Setup directories
    setup_directories()
    
    # Get input files
    input_files = get_input_files(args.input_dir)
    
    if not input_files:
        console.print("[red]No files to process. Exiting.[/red]")
        return
    
    console.print(f"[green]Found {len(input_files)} files to process[/green]")
    
    # Initialize classifier
    try:
        classifier = MudRoomClassifierV2(config_path=args.config)
        console.print("[green]✓ Classifier initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize classifier: {e}[/red]")
        return
    
    # Process files
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Processing files...", total=len(input_files))
        
        for file_path in input_files:
            progress.update(task, description=f"Processing {file_path.name}...")
            
            result = process_file(classifier, file_path, args.output_dir)
            results.append(result)
            
            progress.advance(task)
    
    # Display results
    display_results(results)
    
    console.print(f"\n[green]✓ Processing complete! Results saved to '{args.output_dir}'[/green]")


if __name__ == "__main__":
    main()
