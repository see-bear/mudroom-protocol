#!/usr/bin/env python3
"""
Test script for the enhanced metadata functionality
"""

from mudroom_classifier_v2 import MudRoomClassifierV2
from context_analyzer import ContextAnalyzer
import os

def test_enhanced_metadata():
    """Test the enhanced metadata functionality with context analysis"""
    
    print("🧪 Testing Enhanced Metadata with Context Analysis...")
    
    # Initialize the classifier
    classifier = MudRoomClassifierV2()
    
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
    
    # Sample speakers
    speakers = ["User", "AI", "User", "User", "AI", "AI", "User", "AI", "User", "User", "AI", "User"]
    
    print(f"📝 Testing with {len(blocks)} conversation blocks")
    
    # Test context analysis
    context_analysis = classifier.context_analyzer.analyze_conversation_flow(blocks, speakers)
    
    print(f"\n📊 Context Analysis Results:")
    print(f"   Sessions detected: {context_analysis['num_sessions']}")
    print(f"   Topic shifts: {sum(context_analysis['topic_shifts'])}")
    
    # Test metadata enrichment
    print(f"\n🔧 Testing Metadata Enrichment...")
    
    # Simulate classification and metadata enrichment
    for i, (block_text, speaker) in enumerate(zip(blocks, speakers)):
        # Mock classification (L1, L2, or L3)
        import random
        classification = random.choice(["L1", "L2", "L3"])
        confidence = random.uniform(0.6, 0.95)
        
        # Get context information
        session_id = context_analysis["session_ids"][i] if i < len(context_analysis["session_ids"]) else 0
        topic_shift = context_analysis["topic_shifts"][i] if i < len(context_analysis["topic_shifts"]) else False
        
        # Determine speaker transition
        speaker_transition = None
        if "speaker_analysis" in context_analysis and context_analysis["speaker_analysis"]:
            speaker_transitions = context_analysis["speaker_analysis"].get("speaker_transitions", [])
            for transition in speaker_transitions:
                if transition["position"] == i:
                    speaker_transition = f"{transition['from']}→{transition['to']}"
                    break
        
        # Enrich metadata
        classifier.metadata_enricher.enrich(
            block_id=i,
            classification=classification,
            session_id=session_id,
            topic_shift=topic_shift,
            speaker_transition=speaker_transition,
            confidence=confidence
        )
        
        print(f"   Block {i}: {classification} (Session {session_id}, Topic Shift: {topic_shift}, Speaker: {speaker_transition or speaker})")
    
    # Test metadata saving
    print(f"\n💾 Testing Metadata Saving...")
    test_output_dir = "test_outputs"
    os.makedirs(test_output_dir, exist_ok=True)
    
    metadata_path = os.path.join(test_output_dir, "test_classification_metadata.json")
    classifier.metadata_enricher.save_json(metadata_path)
    
    print(f"   Metadata saved to: {metadata_path}")
    
    # Display metadata
    metadata = classifier.metadata_enricher.get_metadata()
    print(f"\n📋 Metadata Summary:")
    print(f"   Total entries: {len(metadata)}")
    
    # Count by classification
    classifications = {}
    for entry in metadata:
        level = entry["classification"]
        classifications[level] = classifications.get(level, 0) + 1
    
    for level, count in classifications.items():
        print(f"   {level}: {count} entries")
    
    # Count topic shifts
    topic_shifts = sum(1 for entry in metadata if entry["topic_shift"])
    print(f"   Topic shifts: {topic_shifts}")
    
    # Count speaker transitions
    speaker_transitions = sum(1 for entry in metadata if entry["speaker_transition"])
    print(f"   Speaker transitions: {speaker_transitions}")
    
    print(f"\n✅ Enhanced metadata test completed successfully!")
    print(f"📁 Check {metadata_path} for the full metadata output")

if __name__ == "__main__":
    test_enhanced_metadata()
