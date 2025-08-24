#!/usr/bin/env python3
"""
Test script for Vector Search Engine
Tests semantic search functionality with various queries and filters
"""

import os
import tempfile
import numpy as np
from datetime import datetime
from vector_search import VectorSearchEngine
from vector_store import save_vector_store

def test_vector_search():
    """Test the vector search engine functionality"""
    print("🧪 Testing Vector Search Engine...")
    
    # Create test data with enriched metadata
    test_embeddings = {
        0: np.random.rand(384),  # all-MiniLM-L6-v2 dimension
        1: np.random.rand(384),
        2: np.random.rand(384),
        3: np.random.rand(384),
        4: np.random.rand(384)
    }
    
    test_metadata = [
        {
            "block_id": 0,
            "classification": "L3",
            "session_id": 1,
            "topic_shift": True,
            "speaker_transition": "User→AI",
            "confidence_score": 0.95,
            "filename": "strategic_planning.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T10:00:00Z"
        },
        {
            "block_id": 1,
            "classification": "L2",
            "session_id": 1,
            "topic_shift": False,
            "speaker_transition": "AI→User",
            "confidence_score": 0.87,
            "filename": "strategic_planning.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T10:05:00Z"
        },
        {
            "block_id": 2,
            "classification": "L1",
            "session_id": 2,
            "topic_shift": True,
            "speaker_transition": "User→AI",
            "confidence_score": 0.72,
            "filename": "debug_session.txt",
            "project": "DoorHub",
            "ingest_date": "2025-08-17T14:00:00Z"
        },
        {
            "block_id": 3,
            "classification": "L3",
            "session_id": 3,
            "topic_shift": False,
            "speaker_transition": "AI→User",
            "confidence_score": 0.91,
            "filename": "performance_optimization.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T16:00:00Z"
        },
        {
            "block_id": 4,
            "classification": "L2",
            "session_id": 3,
            "topic_shift": False,
            "speaker_transition": "User→AI",
            "confidence_score": 0.83,
            "filename": "performance_optimization.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T16:05:00Z"
        }
    ]
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Save test vector store
        result = save_vector_store(
            file_id="test_search",
            embeddings_dict=test_embeddings,
            metadata_list=test_metadata,
            filename="test_data.txt",
            project="TestProject",
            output_dir=temp_dir
        )
        
        print(f"✅ Test vector store saved: {result['embeddings_count']} embeddings")
        
        # Initialize search engine
        search_engine = VectorSearchEngine(vector_store_dir=temp_dir)
        
        # Test 1: Basic search
        print(f"\n🔍 Test 1: Basic search for 'strategic'")
        results = search_engine.search("strategic", top_k=5)
        print(f"Found {len(results)} results")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['classification']} - {result['filename']} (sim: {result['similarity']:.3f})")
        
        # Test 2: Filter by classification level
        print(f"\n🔍 Test 2: Search for 'performance' with L3 filter")
        results = search_engine.search("performance", classification_filter="L3", top_k=5)
        print(f"Found {len(results)} L3 results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['classification']} - {result['filename']} (sim: {result['similarity']:.3f})")
        
        # Test 3: Filter by project
        print(f"\n🔍 Test 3: Search for 'debug' with MudRoom project filter")
        results = search_engine.search("debug", project_filter="MudRoom", top_k=5)
        print(f"Found {len(results)} MudRoom results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['classification']} - {result['filename']} (sim: {result['similarity']:.3f})")
        
        # Test 4: Filter by filename
        print(f"\n🔍 Test 4: Search for 'planning' with filename filter")
        results = search_engine.search("planning", filename_filter="strategic", top_k=5)
        print(f"Found {len(results)} results from strategic files")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['classification']} - {result['filename']} (sim: {result['similarity']:.3f})")
        
        # Test 5: Filter by confidence threshold
        print(f"\n🔍 Test 5: Search for 'optimization' with confidence > 0.85")
        results = search_engine.search("optimization", confidence_threshold=0.85, top_k=5)
        print(f"Found {len(results)} high-confidence results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['classification']} - {result['filename']} (conf: {result['confidence_score']:.2f})")
        
        # Test 6: List projects
        print(f"\n📋 Test 6: List available projects")
        projects = search_engine.list_projects()
        print(f"Available projects: {projects}")
        
        # Test 7: List files
        print(f"\n📋 Test 7: List available files")
        files = search_engine.list_files()
        print(f"Available files: {files}")
        
        # Test 8: Get statistics
        print(f"\n📊 Test 8: Get vector store statistics")
        stats = search_engine.get_statistics()
        print(f"Statistics: {stats}")
        
        # Test 9: Combined filters
        print(f"\n🔍 Test 9: Combined filters - L2/L3 from MudRoom project")
        results = search_engine.search("important", classification_filter="L2", project_filter="MudRoom", top_k=5)
        print(f"Found {len(results)} L2 MudRoom results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['classification']} - {result['filename']} (sim: {result['similarity']:.3f})")
        
        print(f"\n🎉 Vector search engine tests completed successfully!")
        return True

if __name__ == "__main__":
    success = test_vector_search()
    exit(0 if success else 1)
