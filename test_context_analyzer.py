#!/usr/bin/env python3
"""
Test script for the ContextAnalyzer
"""

from context_analyzer import ContextAnalyzer

def test_context_analyzer():
    """Test the context analyzer with sample conversation blocks"""
    
    # Sample conversation blocks that should show topic shifts
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
    
    # Sample speakers (User/AI alternating)
    speakers = ["User", "AI", "User", "User", "AI", "AI", "User", "AI", "User", "User", "AI", "User"]
    
    print("🧪 Testing ContextAnalyzer...")
    print(f"📝 Testing with {len(blocks)} conversation blocks")
    
    # Initialize the context analyzer
    analyzer = ContextAnalyzer()
    
    # Analyze conversation flow
    analysis = analyzer.analyze_conversation_flow(blocks, speakers)
    
    print(f"\n📊 Analysis Results:")
    print(f"   Sessions detected: {analysis['num_sessions']}")
    print(f"   Topic shifts: {sum(analysis['topic_shifts'])}")
    print(f"   Session boundaries: {analysis['session_boundaries']}")
    
    print(f"\n🔄 Topic Shifts:")
    for i, shift in enumerate(analysis['topic_shifts']):
        if shift:
            print(f"   Block {i}: {blocks[i][:50]}...")
    
    print(f"\n🏷️  Session IDs:")
    for i, session_id in enumerate(analysis['session_ids']):
        print(f"   Block {i} (Session {session_id}): {blocks[i][:50]}...")
    
    if analysis['speaker_analysis']:
        print(f"\n👥 Speaker Analysis:")
        print(f"   Speaker transitions: {len(analysis['speaker_analysis']['speaker_transitions'])}")
        for transition in analysis['speaker_analysis']['speaker_transitions']:
            print(f"   Block {transition['position']}: {transition['from']} → {transition['to']}")
    
    print(f"\n✅ ContextAnalyzer test completed successfully!")

if __name__ == "__main__":
    test_context_analyzer()
