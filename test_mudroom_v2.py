"""
Test script for Mud Room Protocol v2.0 - Phase 1
Tests the enhanced classifier, semantic scorer, conversation parser, and metadata enricher
"""

import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import our modules
from mudroom_classifier_v2 import MudRoomClassifierV2
from semantic_scorer import SemanticScorer
from conversation_parser import ConversationParser
from metadata_enricher import MetadataEnricher

console = Console()


def create_test_conversation():
    """Create a test conversation file for testing"""
    test_conversation = """You said: I need help with a complex debugging issue in my React application.
ChatGPT said: I'd be happy to help! Can you describe the error you're encountering?
You said: The app is crashing when I try to load the user dashboard. I'm getting a 500 error from the API endpoint.
ChatGPT said: Let's debug this step by step. First, can you check the browser console for any JavaScript errors?
You said: I see "TypeError: Cannot read property 'data' of undefined" in the console.
ChatGPT said: That's a common issue. It looks like the API response isn't in the expected format. Let's check the API endpoint.
You said: I found the issue! The API is returning null when the user doesn't have any data, but my code expects an empty array.
ChatGPT said: Perfect! That's exactly the problem. You need to handle the null case. Here's how to fix it:
```javascript
const userData = response.data || [];
```
You said: That worked! The dashboard loads properly now. Thanks for the help.
ChatGPT said: Great! Always remember to handle null/undefined cases in your API responses. This is a common pattern you'll encounter.

You said: By the way, I've been thinking about the overall architecture of this app. We should probably implement proper error boundaries.
ChatGPT said: That's an excellent strategic decision! Error boundaries will make your app much more robust. Here's what I recommend:
1. Create a global error boundary component
2. Add specific error boundaries for critical sections
3. Implement proper error logging and monitoring

You said: I agree. Let's commit to this approach going forward. We'll implement error boundaries in the next sprint.
ChatGPT said: Excellent! That's a solid architectural decision. Error boundaries will significantly improve the user experience and make debugging easier.

You said: Speaking of architecture, I've been reading about microservices vs monoliths. What's your take on this for our project?
ChatGPT said: That's a great strategic question! For your current scale, I'd recommend starting with a well-structured monolith. Here's why:
- Easier to develop and deploy initially
- Simpler debugging and testing
- Can always extract microservices later when you have clear service boundaries

You said: That makes sense. We'll stick with the monolith for now but design it with clear separation of concerns.
ChatGPT said: Perfect strategy! That's exactly the right approach - build a clean monolith that can evolve into microservices when needed."""
    
    with open("test_conversation_v2.txt", "w", encoding="utf-8") as f:
        f.write(test_conversation)
    
    return "test_conversation_v2.txt"


def test_semantic_scorer():
    """Test the semantic scorer"""
    console.print("\n[bold blue]Testing Semantic Scorer...[/bold blue]")
    
    scorer = SemanticScorer()
    
    test_text = "We need to debug this error and fix the server endpoint"
    
    # Mock keywords structure
    test_keywords = {
        "L1": {
            "keywords": ["debug", "error", "fix", "server", "endpoint"],
            "clusters": {
                "technical": ["debug", "error", "fix"],
                "infrastructure": ["server", "endpoint"]
            }
        },
        "L2": {
            "keywords": ["worked", "verified", "confirmed"],
            "clusters": {
                "outcome": ["worked", "verified", "confirmed"]
            }
        },
        "L3": {
            "keywords": ["strategy", "vision", "decision"],
            "clusters": {
                "decision": ["strategy", "vision", "decision"]
            }
        }
    }
    
    scores = scorer.score_text(test_text, test_keywords)
    
    table = Table(title="Semantic Scoring Results")
    table.add_column("Level", style="cyan")
    table.add_column("Score", style="green")
    
    for level, score in scores.items():
        table.add_row(level, f"{score:.3f}")
    
    console.print(table)
    return scores


def test_conversation_parser():
    """Test the conversation parser"""
    console.print("\n[bold blue]Testing Conversation Parser...[/bold blue]")
    
    parser = ConversationParser()
    test_file = create_test_conversation()
    
    blocks = parser.parse_conversation(test_file)
    
    table = Table(title="Conversation Blocks")
    table.add_column("Block", style="cyan")
    table.add_column("Speaker", style="yellow")
    table.add_column("Type", style="green")
    table.add_column("Lines", style="magenta")
    table.add_column("Text Preview", style="white")
    
    for i, block in enumerate(blocks, 1):
        preview = block.text[:50] + "..." if len(block.text) > 50 else block.text
        table.add_row(
            str(i),
            block.speaker or "Unknown",
            block.block_type,
            str(block.line_numbers),
            preview
        )
    
    console.print(table)
    return blocks


def test_metadata_enricher():
    """Test the metadata enricher"""
    console.print("\n[bold blue]Testing Metadata Enricher...[/bold blue]")
    
    enricher = MetadataEnricher()
    
    # Mock classification result
    class MockResult:
        def __init__(self):
            self.text = "We need to debug this error and fix the server endpoint. The database connection is failing."
            self.timestamp = "2025-01-15 14:30:00"
            self.speaker = "User"
            self.confidence = 0.85
            self.level = "L1"
    
    mock_result = MockResult()
    results = {"L1": [mock_result]}
    
    enriched_results = enricher.enrich_results(results, "test_file.txt")
    
    for level, classifications in enriched_results.items():
        for result in classifications:
            console.print(f"\n[bold]Level:[/bold] {level}")
            console.print(f"[bold]Session ID:[/bold] {result.session_metadata['session_id']}")
            console.print(f"[bold]Content Hash:[/bold] {result.content_hash}")
            console.print(f"[bold]Complexity Score:[/bold] {result.semantic_metadata['complexity_score']:.3f}")
            console.print(f"[bold]Speaker Type:[/bold] {result.speaker_analysis['speaker_type']}")
    
    return enriched_results


def test_full_classifier():
    """Test the full enhanced classifier"""
    console.print("\n[bold blue]Testing Full Enhanced Classifier...[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing conversation...", total=None)
        
        classifier = MudRoomClassifierV2()
        test_file = create_test_conversation()
        
        results = classifier.classify_conversation(
            input_path=test_file,
            output_dir="test_output"
        )
        
        progress.update(task, description="Classification complete!")
    
    # Display results summary
    table = Table(title="Classification Results Summary")
    table.add_column("Level", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Avg Confidence", style="yellow")
    
    for level, classifications in results.items():
        if classifications:
            avg_confidence = sum(r.confidence for r in classifications) / len(classifications)
            table.add_row(level, str(len(classifications)), f"{avg_confidence:.3f}")
        else:
            table.add_row(level, "0", "N/A")
    
    console.print(table)
    
    # Show some example classifications
    console.print("\n[bold]Example Classifications:[/bold]")
    for level, classifications in results.items():
        if classifications:
            console.print(f"\n[bold cyan]{level}:[/bold cyan]")
            for i, result in enumerate(classifications[:2], 1):  # Show first 2
                console.print(f"  {i}. Confidence: {result.confidence:.3f}")
                console.print(f"     Keywords: {', '.join(result.keywords)}")
                console.print(f"     Preview: {result.text[:100]}...")
    
    return results


def main():
    """Run all tests"""
    console.print("[bold green]Mud Room Protocol v2.0 - Phase 1 Testing[/bold green]")
    console.print("=" * 60)
    
    try:
        # Test individual components
        test_semantic_scorer()
        test_conversation_parser()
        test_metadata_enricher()
        
        # Test full classifier
        test_full_classifier()
        
        console.print("\n[bold green]✅ All tests completed successfully![/bold green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Install dependencies: pip install -r requirements.txt")
        console.print("2. Run the enhanced classifier on your actual conversation files")
        console.print("3. Review the output in the test_output directory")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]")
        console.print("\n[bold]Troubleshooting:[/bold]")
        console.print("1. Make sure all dependencies are installed")
        console.print("2. Check that the keywords directory exists with level1.txt, level2.txt, level3.txt")
        console.print("3. Verify that sentence-transformers can be loaded")


if __name__ == "__main__":
    main()
