#!/usr/bin/env python3
"""
Test script for Memory Aggregator
Tests clustering, deduplication, and output generation
"""

import os
import tempfile
import numpy as np
from datetime import datetime, timedelta
from memory_aggregator import MemoryAggregator
from vector_store import save_vector_store

def test_memory_aggregator():
    """Test the memory aggregator functionality"""
    print("🧪 Testing Memory Aggregator...")
    
    # Create test data with similar content for clustering
    test_embeddings_1 = {
        0: np.random.rand(384),  # all-MiniLM-L6-v2 dimension
        1: np.random.rand(384),
        2: np.random.rand(384)
    }
    
    test_embeddings_2 = {
        0: np.random.rand(384),
        1: np.random.rand(384),
        2: np.random.rand(384)
    }
    
    # Create similar embeddings for clustering test
    base_embedding = np.random.rand(384)
    similar_embedding = base_embedding + np.random.normal(0, 0.1, 384)  # Similar but not identical
    
    test_embeddings_1[1] = base_embedding
    test_embeddings_2[0] = similar_embedding
    
    test_metadata_1 = [
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
            "classification": "L3",
            "session_id": 1,
            "topic_shift": False,
            "speaker_transition": "AI→User",
            "confidence_score": 0.92,
            "filename": "strategic_planning.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T10:05:00Z"
        },
        {
            "block_id": 2,
            "classification": "L2",
            "session_id": 1,
            "topic_shift": False,
            "speaker_transition": "User→AI",
            "confidence_score": 0.87,
            "filename": "strategic_planning.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T10:10:00Z"
        }
    ]
    
    test_metadata_2 = [
        {
            "block_id": 0,
            "classification": "L3",
            "session_id": 2,
            "topic_shift": True,
            "speaker_transition": "User→AI",
            "confidence_score": 0.89,
            "filename": "performance_optimization.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T16:00:00Z"
        },
        {
            "block_id": 1,
            "classification": "L2",
            "session_id": 2,
            "topic_shift": False,
            "speaker_transition": "AI→User",
            "confidence_score": 0.83,
            "filename": "performance_optimization.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T16:05:00Z"
        },
        {
            "block_id": 2,
            "classification": "L1",
            "session_id": 2,
            "topic_shift": False,
            "speaker_transition": "User→AI",
            "confidence_score": 0.75,
            "filename": "performance_optimization.txt",
            "project": "MudRoom",
            "ingest_date": "2025-08-17T16:10:00Z"
        }
    ]
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Save test vector stores
        result1 = save_vector_store(
            file_id="test_aggregator_1",
            embeddings_dict=test_embeddings_1,
            metadata_list=test_metadata_1,
            filename="strategic_planning.txt",
            project="MudRoom",
            output_dir=temp_dir
        )
        
        result2 = save_vector_store(
            file_id="test_aggregator_2",
            embeddings_dict=test_embeddings_2,
            metadata_list=test_metadata_2,
            filename="performance_optimization.txt",
            project="MudRoom",
            output_dir=temp_dir
        )
        
        print(f"✅ Test vector stores saved: {result1['embeddings_count']} + {result2['embeddings_count']} embeddings")
        
        # Test 1: Basic aggregation with default settings
        print(f"\n🔍 Test 1: Basic aggregation with default settings")
        config1 = {
            "vector_store_dir": temp_dir,
            "output_dir": os.path.join(temp_dir, "output"),
            "similarity_threshold": 0.85,  # Lower threshold for testing
            "min_confidence": 0.7,
            "focus_levels": ["L2", "L3"]
        }
        
        aggregator1 = MemoryAggregator(config1)
        output_files1 = aggregator1.run()
        
        if output_files1:
            print(f"✅ Basic aggregation successful: {len(output_files1)} output files")
            for format_type, path in output_files1.items():
                print(f"  {format_type}: {path}")
        else:
            print(f"❌ Basic aggregation failed")
            return False
        
        # Test 2: Aggregation with higher threshold (should create more clusters)
        print(f"\n🔍 Test 2: Aggregation with higher threshold (0.95)")
        config2 = config1.copy()
        config2["similarity_threshold"] = 0.95
        
        aggregator2 = MemoryAggregator(config2)
        output_files2 = aggregator2.run()
        
        if output_files2:
            print(f"✅ High-threshold aggregation successful")
        else:
            print(f"❌ High-threshold aggregation failed")
            return False
        
        # Test 3: Aggregation with L3 focus only
        print(f"\n🔍 Test 3: Aggregation with L3 focus only")
        config3 = config1.copy()
        config3["focus_levels"] = ["L3"]
        
        aggregator3 = MemoryAggregator(config3)
        output_files3 = aggregator3.run()
        
        if output_files3:
            print(f"✅ L3-only aggregation successful")
        else:
            print(f"❌ L3-only aggregation failed")
            return False
        
        # Test 4: Aggregation with higher confidence threshold
        print(f"\n🔍 Test 4: Aggregation with higher confidence threshold (0.9)")
        config4 = config1.copy()
        config4["min_confidence"] = 0.9
        
        aggregator4 = MemoryAggregator(config4)
        output_files4 = aggregator4.run()
        
        if output_files4:
            print(f"✅ High-confidence aggregation successful")
        else:
            print(f"❌ High-confidence aggregation failed")
            return False
        
        # Test 5: Check output file contents
        print(f"\n📄 Test 5: Check output file contents")
        if "markdown" in output_files1:
            md_path = output_files1["markdown"]
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✅ Markdown file created: {len(content)} characters")
                    print(f"  Contains 'L3 Strategic Content': {'L3 Strategic Content' in content}")
                    print(f"  Contains 'L2 Strategic Content': {'L2 Strategic Content' in content}")
            else:
                print(f"❌ Markdown file not found: {md_path}")
                return False
        
        if "json" in output_files1:
            json_path = output_files1["json"]
            if os.path.exists(json_path):
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ JSON file created: {len(data.get('entries', []))} entries")
                    print(f"  Metadata: {data.get('metadata', {})}")
            else:
                print(f"❌ JSON file not found: {json_path}")
                return False
        
        print(f"\n🎉 Memory aggregator tests completed successfully!")
        return True

if __name__ == "__main__":
    success = test_memory_aggregator()
    exit(0 if success else 1)
