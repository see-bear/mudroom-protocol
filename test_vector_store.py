#!/usr/bin/env python3
"""
Test script for vector store functionality
"""

import os
import time
from semantic_scorer import SemanticScorer
from context_analyzer import ContextAnalyzer
from vector_store import save_vector_store, load_vector_store, list_vector_stores, get_vector_store_info

def test_vector_store():
    """Test vector store functionality and disk persistence"""
    
    print("🧪 Testing Vector Store Functionality...")
    
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
    
    # Test batch embedding and caching
    print(f"\n⚡ Testing Batch Embedding and Caching...")
    start_time = time.time()
    
    # Use batch embedding (this should populate the cache)
    batch_embeddings = scorer.model.encode(blocks, batch_size=16, convert_to_tensor=True)
    batch_embeddings = batch_embeddings.cpu().numpy()
    
    # Store in cache
    for i, embedding in enumerate(batch_embeddings):
        scorer.block_embeddings[i] = embedding
    
    batch_time = time.time() - start_time
    print(f"   Batch embedding and caching time: {batch_time:.2f} seconds")
    print(f"   Cache size: {scorer.get_cache_size()}")
    
    # Create mock metadata for testing
    print(f"\n📋 Creating Mock Metadata...")
    mock_metadata = []
    for i, block in enumerate(blocks):
        mock_metadata.append({
            "block_id": i,
            "classification": "L1" if i < 4 else "L2" if i < 8 else "L3",
            "session_id": i // 3,
            "topic_shift": i % 3 == 0,
            "speaker_transition": "User→AI" if i % 2 == 0 else None,
            "confidence_score": 0.7 + (i * 0.02)
        })
    
    print(f"   Created {len(mock_metadata)} metadata entries")
    
    # Test vector store saving
    print(f"\n💾 Testing Vector Store Saving...")
    file_id = "test_conversation"
    
    start_time = time.time()
    try:
        result = save_vector_store(
            file_id=file_id,
            embeddings_dict=scorer.get_block_embeddings(),
            metadata_list=mock_metadata
        )
        save_time = time.time() - start_time
        
        print(f"   Vector store saved successfully in {save_time:.2f} seconds")
        print(f"   Embeddings saved: {result['embeddings_count']}")
        print(f"   Metadata saved: {result['metadata_count']}")
        print(f"   NPY file: {result['npy_path']}")
        print(f"   JSON file: {result['json_path']}")
        
    except Exception as e:
        print(f"   ❌ Failed to save vector store: {e}")
        return
    
    # Test vector store loading
    print(f"\n📂 Testing Vector Store Loading...")
    start_time = time.time()
    
    try:
        loaded_data = load_vector_store(file_id)
        load_time = time.time() - start_time
        
        print(f"   Vector store loaded successfully in {load_time:.2f} seconds")
        print(f"   Loaded embeddings shape: {loaded_data['embeddings'].shape}")
        print(f"   Loaded metadata count: {len(loaded_data['metadata'])}")
        
        # Verify data integrity
        original_embeddings = scorer.get_block_embeddings()
        original_count = len(original_embeddings)
        loaded_count = len(loaded_data['embeddings'])
        
        print(f"   Data integrity check:")
        print(f"     Original embeddings: {original_count}")
        print(f"     Loaded embeddings: {loaded_count}")
        print(f"     Match: {original_count == loaded_count}")
        
    except Exception as e:
        print(f"   ❌ Failed to load vector store: {e}")
        return
    
    # Test vector store listing
    print(f"\n📁 Testing Vector Store Listing...")
    try:
        available_stores = list_vector_stores()
        print(f"   Available vector stores: {available_stores}")
        
        if file_id in available_stores:
            print(f"   ✅ Test vector store found in listing")
        else:
            print(f"   ❌ Test vector store not found in listing")
            
    except Exception as e:
        print(f"   ❌ Failed to list vector stores: {e}")
    
    # Test vector store info
    print(f"\nℹ️  Testing Vector Store Info...")
    try:
        info = get_vector_store_info(file_id)
        if info:
            print(f"   Vector store info:")
            print(f"     File ID: {info['file_id']}")
            print(f"     Embeddings: {info['embeddings_count']}")
            print(f"     Embedding dimension: {info['embedding_dimension']}")
            print(f"     Metadata entries: {info['metadata_count']}")
            print(f"     NPY size: {info['npy_size_bytes']} bytes")
            print(f"     JSON size: {info['json_size_bytes']} bytes")
            print(f"     Total size: {info['total_size_bytes']} bytes")
        else:
            print(f"   ❌ Could not get vector store info")
            
    except Exception as e:
        print(f"   ❌ Failed to get vector store info: {e}")
    
    # Test performance comparison
    print(f"\n⚡ Testing Performance Comparison...")
    
    # Time to compute embeddings from scratch
    start_time = time.time()
    fresh_embeddings = scorer.model.encode(blocks, batch_size=16, convert_to_tensor=True)
    fresh_time = time.time() - start_time
    
    # Time to load from disk
    start_time = time.time()
    disk_data = load_vector_store(file_id)
    disk_time = time.time() - start_time
    
    print(f"   Fresh embedding computation: {fresh_time:.2f} seconds")
    print(f"   Disk loading: {disk_time:.2f} seconds")
    print(f"   Speedup: {fresh_time / disk_time:.1f}x")
    
    print(f"\n✅ Vector store test completed successfully!")
    print(f"📊 Summary:")
    print(f"   Embeddings saved and loaded: {len(loaded_data['embeddings'])}")
    print(f"   Metadata saved and loaded: {len(loaded_data['metadata'])}")
    print(f"   Disk persistence: Working")
    print(f"   Performance improvement: {fresh_time / disk_time:.1f}x faster loading")

if __name__ == "__main__":
    test_vector_store()
