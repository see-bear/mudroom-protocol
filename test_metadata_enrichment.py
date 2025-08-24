#!/usr/bin/env python3
"""
Test script for vector metadata enrichment
Verifies that filename, project, and ingest_date are properly added to vector store entries
"""

import os
import json
import tempfile
import numpy as np
from datetime import datetime
from vector_store import save_vector_store, load_vector_store

def test_metadata_enrichment():
    """Test that metadata enrichment works correctly"""
    print("🧪 Testing Vector Metadata Enrichment...")
    
    # Create test data
    test_embeddings = {
        0: np.random.rand(384),  # all-MiniLM-L6-v2 dimension
        1: np.random.rand(384),
        2: np.random.rand(384)
    }
    
    test_metadata = [
        {"classification": "L2", "session_id": 1, "topic_shift": False, "confidence_score": 0.85},
        {"classification": "L3", "session_id": 1, "topic_shift": True, "confidence_score": 0.92},
        {"classification": "L1", "session_id": 2, "topic_shift": False, "confidence_score": 0.78}
    ]
    
    # Test parameters
    test_filename = "test_conversation.txt"
    test_project = "TestProject"
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Save vector store with metadata enrichment
        result = save_vector_store(
            file_id="test_file",
            embeddings_dict=test_embeddings,
            metadata_list=test_metadata,
            filename=test_filename,
            project=test_project,
            output_dir=temp_dir
        )
        
        print(f"✅ Vector store saved: {result['embeddings_count']} embeddings, {result['metadata_count']} metadata entries")
        
        # Load and verify the enriched metadata
        loaded_data = load_vector_store("test_file", output_dir=temp_dir)
        enriched_metadata = loaded_data["metadata"]
        
        print(f"📋 Loaded {len(enriched_metadata)} metadata entries")
        
        # Verify each entry has the required fields
        required_fields = ["block_id", "filename", "project", "ingest_date"]
        all_fields_present = True
        
        for i, entry in enumerate(enriched_metadata):
            print(f"\n📄 Entry {i}:")
            print(f"  Original: {entry['classification']} (confidence: {entry['confidence_score']})")
            
            # Check required fields
            for field in required_fields:
                if field not in entry:
                    print(f"  ❌ Missing field: {field}")
                    all_fields_present = False
                else:
                    print(f"  ✅ {field}: {entry[field]}")
            
            # Verify specific values
            if entry.get("filename") != test_filename:
                print(f"  ❌ Filename mismatch: expected {test_filename}, got {entry.get('filename')}")
                all_fields_present = False
            
            if entry.get("project") != test_project:
                print(f"  ❌ Project mismatch: expected {test_project}, got {entry.get('project')}")
                all_fields_present = False
            
            # Verify ingest_date is valid ISO format
            try:
                datetime.fromisoformat(entry.get("ingest_date", "").replace("Z", "+00:00"))
                print(f"  ✅ ingest_date format: Valid ISO timestamp")
            except ValueError:
                print(f"  ❌ ingest_date format: Invalid ISO timestamp")
                all_fields_present = False
        
        # Test backward compatibility (no metadata parameters)
        print(f"\n🔄 Testing backward compatibility...")
        compat_result = save_vector_store(
            file_id="test_compat",
            embeddings_dict={0: np.random.rand(384)},
            metadata_list=[{"classification": "L1", "confidence_score": 0.8}],
            output_dir=temp_dir
        )
        
        compat_data = load_vector_store("test_compat", output_dir=temp_dir)
        compat_entry = compat_data["metadata"][0]
        
        print(f"  ✅ Backward compatibility: {compat_entry.get('filename', 'Missing')}")
        print(f"  ✅ Default project: {compat_entry.get('project', 'Missing')}")
        
        # Final results
        if all_fields_present:
            print(f"\n🎉 All tests passed! Metadata enrichment is working correctly.")
            return True
        else:
            print(f"\n❌ Some tests failed. Check the output above.")
            return False

if __name__ == "__main__":
    success = test_metadata_enrichment()
    exit(0 if success else 1)
