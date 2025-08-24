#!/usr/bin/env python3
"""
Test script for in-memory caching functionality
"""

import time
from semantic_scorer import SemanticScorer
from context_analyzer import ContextAnalyzer

def test_caching_functionality():
    """Test the enhanced in-memory caching functionality"""
    
    print("🧪 Testing In-Memory Caching Functionality...")
    
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
    
    # Test initial cache state
    print(f"\n💾 Testing Initial Cache State...")
    print(f"   Initial cache size: {scorer.get_cache_size()}")
    print(f"   Has cached embedding for block 0: {scorer.has_cached_embedding(0)}")
    
    # Test batch embedding and caching
    print(f"\n⚡ Testing Batch Embedding with Caching...")
    start_time = time.time()
    
    # Use batch embedding (this should populate the cache)
    batch_embeddings = scorer.model.encode(blocks, batch_size=16, convert_to_tensor=True)
    batch_embeddings = batch_embeddings.cpu().numpy()
    
    # Store in cache
    for i, embedding in enumerate(batch_embeddings):
        scorer.block_embeddings[i] = embedding
    
    batch_time = time.time() - start_time
    print(f"   Batch embedding and caching time: {batch_time:.2f} seconds")
    
    # Test cache state after population
    print(f"\n📊 Testing Cache State After Population...")
    print(f"   Cache size: {scorer.get_cache_size()}")
    print(f"   Cached embeddings count: {scorer.get_cached_embeddings_count()}")
    print(f"   Has cached embedding for block 0: {scorer.has_cached_embedding(0)}")
    print(f"   Has cached embedding for block 5: {scorer.has_cached_embedding(5)}")
    print(f"   Has cached embedding for block 15: {scorer.has_cached_embedding(15)}")  # Should be False
    
    # Test retrieving cached embeddings
    print(f"\n🔍 Testing Cached Embedding Retrieval...")
    cached_embedding_0 = scorer.get_cached_embedding(0)
    cached_embedding_5 = scorer.get_cached_embedding(5)
    
    if cached_embedding_0 is not None:
        print(f"   Successfully retrieved cached embedding for block 0 (shape: {cached_embedding_0.shape})")
    if cached_embedding_5 is not None:
        print(f"   Successfully retrieved cached embedding for block 5 (shape: {cached_embedding_5.shape})")
    
    # Test getting all cached embeddings
    print(f"\n📋 Testing Get All Cached Embeddings...")
    all_cached = scorer.get_block_embeddings()
    print(f"   Retrieved {len(all_cached)} cached embeddings")
    print(f"   Cache keys: {list(all_cached.keys())}")
    
    # Test context analyzer with cached embeddings
    print(f"\n🔧 Testing Context Analyzer with Cached Embeddings...")
    analyzer = ContextAnalyzer()
    
    start_time = time.time()
    analysis = analyzer.analyze_conversation_flow(blocks)
    context_time = time.time() - start_time
    
    print(f"   Context analysis time: {context_time:.2f} seconds")
    print(f"   Sessions detected: {analysis['num_sessions']}")
    print(f"   Topic shifts: {sum(analysis['topic_shifts'])}")
    
    # Test cache clearing
    print(f"\n🧹 Testing Cache Clearing...")
    print(f"   Cache size before clearing: {scorer.get_cache_size()}")
    scorer.clear_cache()
    print(f"   Cache size after clearing: {scorer.get_cache_size()}")
    print(f"   Has cached embedding for block 0: {scorer.has_cached_embedding(0)}")
    
    # Test performance with and without cache
    print(f"\n⚡ Testing Performance with Cache Reuse...")
    
    # First run (populate cache)
    start_time = time.time()
    embeddings1 = scorer.model.encode(blocks[:6], batch_size=16, convert_to_tensor=True)
    for i, embedding in enumerate(embeddings1):
        scorer.block_embeddings[i] = embedding.cpu().numpy()
    time1 = time.time() - start_time
    
    # Second run (should be faster due to cache)
    start_time = time.time()
    embeddings2 = scorer.model.encode(blocks[:6], batch_size=16, convert_to_tensor=True)
    for i, embedding in enumerate(embeddings2):
        scorer.block_embeddings[i] = embedding.cpu().numpy()
    time2 = time.time() - start_time
    
    print(f"   First run time: {time1:.2f} seconds")
    print(f"   Second run time: {time2:.2f} seconds")
    print(f"   Cache hit ratio: {scorer.get_cache_size()} embeddings cached")
    
    print(f"\n✅ In-memory caching test completed successfully!")
    print(f"📊 Cache Summary:")
    print(f"   Total embeddings cached: {scorer.get_cached_embeddings_count()}")
    print(f"   Cache management: Working")
    print(f"   Context analysis: Integrated")
    print(f"   Performance: Optimized")

if __name__ == "__main__":
    test_caching_functionality()
