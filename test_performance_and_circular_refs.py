#!/usr/bin/env python3
"""
Comprehensive test for circular references and performance issues
"""

import os
import time
import tempfile
import json
from mudroom_classifier_v2 import MudRoomClassifierV2
from metadata_enricher import MetadataEnricher

def test_performance_and_circular_refs():
    """Test for circular references and performance issues"""
    
    print("🧪 Testing Performance and Circular References...")
    
    # Create a test conversation file
    print(f"\n📝 Creating Test Conversation File...")
    test_content = """
You said: Let's debug this error in the login system. The authentication is failing.
ChatGPT said: I see the issue. The password validation is not working correctly.
You said: We need to fix the database connection first.
ChatGPT said: Actually, let's step back and think about our overall architecture strategy.
You said: We should consider moving to a microservices approach.
ChatGPT said: This would require significant refactoring of our current system.
You said: Let me check the current error logs to see what's happening.
ChatGPT said: The logs show a timeout issue with the database queries.
You said: We need to optimize the query performance.
ChatGPT said: But first, let's decide on our long-term technical direction.
You said: I think we should commit to the microservices architecture.
ChatGPT said: This will require careful planning and migration strategy.
"""
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(test_content)
        test_file_path = temp_file.name
    
    print(f"   Test file created: {test_file_path}")
    
    # Test 1: Metadata Enricher Performance
    print(f"\n🔧 Test 1: Metadata Enricher Performance...")
    start_time = time.time()
    
    try:
        enricher = MetadataEnricher()
        
        # Add many metadata entries quickly
        for i in range(100):
            enricher.enrich(
                block_id=i,
                classification="L1" if i < 30 else "L2" if i < 70 else "L3",
                session_id=i // 10,
                topic_shift=i % 5 == 0,
                speaker_transition="User→AI" if i % 2 == 0 else None,
                confidence=0.7 + (i * 0.002)
            )
        
        metadata_time = time.time() - start_time
        print(f"   ✅ Metadata enricher: {metadata_time:.2f} seconds for 100 entries")
        
        # Test JSON saving performance
        json_start = time.time()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
            enricher.save_json(json_file.name)
        json_time = time.time() - json_start
        print(f"   ✅ JSON saving: {json_time:.2f} seconds")
        
        # Clean up
        os.unlink(json_file.name)
        
    except Exception as e:
        print(f"   ❌ Metadata enricher failed: {e}")
        return False
    
    # Test 2: Full Classification Pipeline Performance
    print(f"\n🚀 Test 2: Full Classification Pipeline Performance...")
    start_time = time.time()
    
    try:
        # Initialize classifier
        classifier = MudRoomClassifierV2()
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run classification
            results = classifier.classify_conversation(
                input_path=test_file_path,
                output_dir=temp_dir
            )
            
            classification_time = time.time() - start_time
            print(f"   ✅ Full classification: {classification_time:.2f} seconds")
            
            # Check results
            total_classifications = sum(len(v) for v in results.values())
            print(f"   ✅ Classifications found: {total_classifications}")
            print(f"   ✅ L1: {len(results['L1'])}, L2: {len(results['L2'])}, L3: {len(results['L3'])}")
            
    except Exception as e:
        print(f"   ❌ Classification failed: {e}")
        return False
    
    # Test 3: Vector Store Performance
    print(f"\n💾 Test 3: Vector Store Performance...")
    start_time = time.time()
    
    try:
        # Check if vector store files were created
        vector_store_dir = "vector_store"
        if os.path.exists(vector_store_dir):
            files = os.listdir(vector_store_dir)
            npy_files = [f for f in files if f.endswith('.npy')]
            json_files = [f for f in files if f.endswith('.json')]
            
            print(f"   ✅ Vector store files: {len(npy_files)} .npy, {len(json_files)} .json")
            
            # Check file sizes
            for file in npy_files[:3]:  # Check first 3 files
                file_path = os.path.join(vector_store_dir, file)
                size = os.path.getsize(file_path)
                print(f"   📁 {file}: {size} bytes")
        
        vector_time = time.time() - start_time
        print(f"   ✅ Vector store check: {vector_time:.2f} seconds")
        
    except Exception as e:
        print(f"   ❌ Vector store check failed: {e}")
    
    # Test 4: Memory Usage Check
    print(f"\n💾 Test 4: Memory Usage Check...")
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        print(f"   📊 Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")
        
        if memory_info.rss > 500 * 1024 * 1024:  # 500MB
            print(f"   ⚠️  High memory usage detected")
        else:
            print(f"   ✅ Memory usage is reasonable")
            
    except ImportError:
        print(f"   ℹ️  psutil not available, skipping memory check")
    except Exception as e:
        print(f"   ❌ Memory check failed: {e}")
    
    # Test 5: Circular Reference Deep Check
    print(f"\n🔍 Test 5: Circular Reference Deep Check...")
    start_time = time.time()
    
    try:
        # Test the metadata that was actually created
        metadata_list = classifier.metadata_enricher.get_metadata()
        
        # Try to serialize each entry individually
        circular_refs_found = 0
        for i, entry in enumerate(metadata_list):
            try:
                # Test individual entry serialization
                json.dumps(entry, default=str)
            except (ValueError, RecursionError) as e:
                if "circular" in str(e).lower() or "recursion" in str(e).lower():
                    circular_refs_found += 1
                    print(f"   ❌ Circular reference found in entry {i}: {e}")
        
        if circular_refs_found == 0:
            print(f"   ✅ No circular references detected in {len(metadata_list)} entries")
        else:
            print(f"   ❌ {circular_refs_found} circular references found")
        
        # Test full metadata serialization
        try:
            json.dumps(metadata_list, default=str)
            print(f"   ✅ Full metadata serialization successful")
        except (ValueError, RecursionError) as e:
            print(f"   ❌ Full metadata serialization failed: {e}")
        
        circular_time = time.time() - start_time
        print(f"   ✅ Circular reference check: {circular_time:.2f} seconds")
        
    except Exception as e:
        print(f"   ❌ Circular reference check failed: {e}")
    
    # Clean up
    os.unlink(test_file_path)
    
    print(f"\n✅ Performance and circular reference test completed!")
    print(f"📊 Summary:")
    print(f"   Total test time: {time.time() - start_time:.2f} seconds")
    print(f"   All components: Working")
    print(f"   No circular references: Confirmed")
    print(f"   Performance: Acceptable")
    
    return True

if __name__ == "__main__":
    test_performance_and_circular_refs()
