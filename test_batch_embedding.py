#!/usr/bin/env python3
"""
Test script for batch embedding functionality
"""

import time
from semantic_scorer import SemanticScorer
from context_analyzer import ContextAnalyzer

def test_batch_embedding():
    """Test batch embedding functionality and performance"""
    
    print("🧪 Testing Batch Embedding Performance...")
    
    # Sample conversation blocks
    blocks = [
        "Let's debug this error in the login system. The authentication is failing.",
        "I see the issue. The password validation is not working correctly.",
        "We need to fix the database connection first.",
        "Actually, let's step back and think about our overall architecture strategy.",
        "We should consider moving to a microservices approach.",
        "This would require significant refactoring of our current system.",
        "Let me check the current error logs to see what's happening.",
        "The logs show a timeout issue with the database queries.",
        "We need to optimize the query performance.",
        "But first, let's decide on our long-term technical direction.",
        "I think we should commit to the microservices architecture.",
        "This will require careful planning and migration strategy."
    ]
    
    # Initialize semantic scorer
    scorer = SemanticScorer()
    
    print(f"📝 Testing with {len(blocks)} conversation blocks")
    
    # Test individual embedding (old method)
    print(f"\n⏱️  Testing Individual Embedding...")
    start_time = time.time()
    
    individual_embeddings = []
    for block in blocks:
        embedding = scorer.get_text_summary_embedding(block)
        individual_embeddings.append(embedding)
    
    individual_time = time.time() - start_time
    print(f"   Individual embedding time: {individual_time:.2f} seconds")
    
    # Test batch embedding (new method)
    print(f"\n⚡ Testing Batch Embedding...")
    start_time = time.time()
    
    # Use the new batch method
    batch_embeddings = scorer.model.encode(blocks, batch_size=16, convert_to_tensor=True)
    batch_embeddings = batch_embeddings.cpu().numpy()
    
    batch_time = time.time() - start_time
    print(f"   Batch embedding time: {batch_time:.2f} seconds")
    
    # Calculate speedup
    speedup = individual_time / batch_time if batch_time > 0 else 0
    print(f"   Speedup: {speedup:.1f}x")
    
    # Test cache functionality
    print(f"\n💾 Testing Cache Functionality...")
    print(f"   Cache size before: {scorer.get_cache_size()}")
    
    # Store embeddings in cache
    for i, embedding in enumerate(batch_embeddings):
        scorer.block_embeddings[i] = embedding
    
    print(f"   Cache size after: {scorer.get_cache_size()}")
    
    # Test retrieving from cache
    cached_embedding = scorer.get_cached_embedding(0)
    if cached_embedding is not None:
        print(f"   Successfully retrieved cached embedding for block 0")
    
    # Test context analyzer with batch embedding
    print(f"\n🔧 Testing Context Analyzer with Batch Embedding...")
    analyzer = ContextAnalyzer()
    
    start_time = time.time()
    analysis = analyzer.analyze_conversation_flow(blocks)
    context_time = time.time() - start_time
    
    print(f"   Context analysis time: {context_time:.2f} seconds")
    print(f"   Sessions detected: {analysis['num_sessions']}")
    print(f"   Topic shifts: {sum(analysis['topic_shifts'])}")
    
    # Test cache clearing
    print(f"\n🧹 Testing Cache Management...")
    scorer.clear_cache()
    print(f"   Cache size after clearing: {scorer.get_cache_size()}")
    
    print(f"\n✅ Batch embedding test completed successfully!")
    print(f"📊 Performance Summary:")
    print(f"   Individual: {individual_time:.2f}s")
    print(f"   Batch: {batch_time:.2f}s")
    print(f"   Speedup: {speedup:.1f}x")
    print(f"   Context analysis: {context_time:.2f}s")

if __name__ == "__main__":
    test_batch_embedding()
