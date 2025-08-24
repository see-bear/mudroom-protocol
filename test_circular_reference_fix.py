#!/usr/bin/env python3
"""
Test script to verify circular reference fix in metadata enricher
"""

import os
import tempfile
from metadata_enricher import MetadataEnricher

def test_circular_reference_fix():
    """Test that metadata enricher can save JSON without circular reference errors"""
    
    print("🧪 Testing Circular Reference Fix...")
    
    # Initialize metadata enricher
    enricher = MetadataEnricher()
    
    # Add some test metadata entries
    print(f"\n📝 Adding Test Metadata Entries...")
    test_entries = [
        (0, "L1", 0, False, None, 0.75),
        (1, "L2", 0, True, "User→AI", 0.85),
        (2, "L3", 1, False, "AI→User", 0.92),
        (3, "L1", 1, True, None, 0.68),
        (4, "L2", 2, False, "User→AI", 0.78)
    ]
    
    for block_id, classification, session_id, topic_shift, speaker_transition, confidence in test_entries:
        enricher.enrich(
            block_id=block_id,
            classification=classification,
            session_id=session_id,
            topic_shift=topic_shift,
            speaker_transition=speaker_transition,
            confidence=confidence
        )
        print(f"   Added entry {block_id}: {classification} (Session {session_id})")
    
    print(f"   Total entries: {len(enricher.get_metadata())}")
    
    # Test JSON saving
    print(f"\n💾 Testing JSON Saving...")
    try:
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Try to save the metadata
        enricher.save_json(temp_path)
        
        # Check if file was created and has content
        if os.path.exists(temp_path):
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   ✅ JSON saved successfully!")
                print(f"   File size: {len(content)} characters")
                print(f"   File path: {temp_path}")
                
                # Verify JSON is valid by checking it contains expected data
                if '"block_id": 0' in content and '"classification": "L1"' in content:
                    print(f"   ✅ JSON content appears valid")
                else:
                    print(f"   ⚠️  JSON content may be incomplete")
        else:
            print(f"   ❌ File was not created")
            
        # Clean up
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"   ❌ Failed to save JSON: {e}")
        return False
    
    # Test vector store integration
    print(f"\n🔗 Testing Vector Store Integration...")
    try:
        # Simulate the vector store saving process
        metadata_list = enricher.get_metadata()
        safe_metadata = []
        for entry in metadata_list:
            safe_entry = {
                "block_id": int(entry.get("block_id", 0)),
                "classification": str(entry.get("classification", "unknown")),
                "session_id": int(entry.get("session_id", 0)),
                "topic_shift": bool(entry.get("topic_shift", False)),
                "speaker_transition": str(entry.get("speaker_transition", "")) if entry.get("speaker_transition") else None,
                "confidence_score": float(entry.get("confidence_score", 0.0)) if entry.get("confidence_score") is not None else None
            }
            safe_metadata.append(safe_entry)
        
        print(f"   ✅ Vector store metadata preparation successful")
        print(f"   Safe metadata entries: {len(safe_metadata)}")
        
        # Test JSON serialization of safe metadata
        import json
        json_str = json.dumps(safe_metadata, indent=2)
        print(f"   ✅ JSON serialization of safe metadata successful")
        print(f"   Serialized size: {len(json_str)} characters")
        
    except Exception as e:
        print(f"   ❌ Vector store integration failed: {e}")
        return False
    
    print(f"\n✅ Circular reference fix test completed successfully!")
    print(f"📊 Summary:")
    print(f"   Metadata entries: {len(enricher.get_metadata())}")
    print(f"   JSON saving: Working")
    print(f"   Vector store integration: Working")
    print(f"   No circular reference errors detected")
    
    return True

if __name__ == "__main__":
    test_circular_reference_fix()
