"""
Metadata Enricher for Mud Room Protocol v2.0
Adds rich metadata to classification results including cross-references and session analysis
"""

import os
import re
import json
import copy
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_numpy(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    return obj


class MetadataEnricher:
    """
    Enriches classification results with metadata, cross-references, and session analysis
    """
    
    def __init__(self):
        """Initialize the metadata enricher"""
        self.session_cache = {}  # Cache for session metadata
        self.cross_references = {}  # Cross-reference database
        self.metadata = []  # Structured classification metadata

    def enrich(self, block_id: int, classification: str, session_id: int, topic_shift: bool,
               speaker_transition: str = None, confidence: float = None):
        """
        Add structured metadata for a classification result
        
        Args:
            block_id: Index of the conversation block
            classification: L1, L2, or L3 classification
            session_id: Session identifier from context analysis
            topic_shift: Whether a topic shift occurred
            speaker_transition: Speaker transition type (if any)
            confidence: Classification confidence score
        """
        # Create a safe, flattened metadata entry with explicit type conversion
        # No deep copy needed since we're only using primitive types
        safe_metadata = {
            "block_id": int(block_id),
            "classification": str(classification),
            "session_id": int(session_id),
            "topic_shift": bool(topic_shift),
            "speaker_transition": str(speaker_transition) if speaker_transition else None,
            "confidence_score": float(confidence) if confidence is not None else None
        }
        
        self.metadata.append(safe_metadata)

    def save_json(self, path: str):
        """
        Save structured metadata to JSON file
        
        Args:
            path: Output file path
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, default=convert_numpy)
        except ValueError as e:
            if "Circular reference" in str(e):
                # Fallback: create a safe copy of metadata without circular references
                logger.warning("Circular reference detected, creating safe copy for serialization")
                safe_metadata = []
                for entry in self.metadata:
                    # Create a minimal safe version with explicit type conversion
                    safe_metadata.append({
                        "block_id": int(entry.get("block_id", 0)),
                        "classification": str(entry.get("classification", "unknown")),
                        "session_id": int(entry.get("session_id", 0)),
                        "topic_shift": bool(entry.get("topic_shift", False)),
                        "speaker_transition": str(entry.get("speaker_transition", "")) if entry.get("speaker_transition") else None,
                        "confidence_score": float(entry.get("confidence_score", 0.0)) if entry.get("confidence_score") is not None else None
                    })
                
                # Try saving the safe copy
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(safe_metadata, f, indent=2, default=convert_numpy)
                logger.info(f"Successfully saved metadata with {len(safe_metadata)} entries after circular reference fix")
            else:
                raise e

    def get_metadata(self):
        """Get the current metadata list"""
        return self.metadata
    
    def _create_safe_copy(self, obj):
        """
        Create a safe copy of an object to prevent circular references
        
        Args:
            obj: Object to copy
            
        Returns:
            Safe copy of the object
        """
        if obj is None:
            return None
        
        try:
            # For dictionaries, create a new dict with safe values
            if isinstance(obj, dict):
                safe_dict = {}
                for key, value in obj.items():
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        safe_dict[key] = value
                    elif isinstance(value, list):
                        safe_dict[key] = [self._create_safe_copy(item) for item in value]
                    elif isinstance(value, dict):
                        safe_dict[key] = self._create_safe_copy(value)
                    else:
                        # Convert other types to string
                        safe_dict[key] = str(value)
                return safe_dict
            
            # For lists, create a new list with safe values
            elif isinstance(obj, list):
                return [self._create_safe_copy(item) for item in obj]
            
            # For primitive types, return as is
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            
            # For other types, convert to string
            else:
                return str(obj)
                
        except Exception as e:
            logger.warning(f"Failed to create safe copy: {e}")
            return str(obj) if obj is not None else None
    
    def enrich_results(self, results: Dict[str, List[Any]], input_path: str) -> Dict[str, List[Any]]:
        """
        Enrich classification results with metadata
        
        Args:
            results: Dictionary of level -> classification results
            input_path: Path to the input conversation file
            
        Returns:
            Enriched results with additional metadata
        """
        try:
            # Extract session metadata
            session_metadata = self._extract_session_metadata(input_path)
            
            # Add metadata to each classification result
            for level, classifications in results.items():
                for result in classifications:
                    try:
                        # Add session metadata (safe copy)
                        result.session_metadata = self._create_safe_copy(session_metadata)
                        
                        # Add content hash for deduplication
                        result.content_hash = self._calculate_content_hash(result.text)
                        
                        # Add cross-references (safe copy)
                        cross_refs = self._find_cross_references(result)
                        result.cross_references = self._create_safe_copy(cross_refs)
                        
                        # Add temporal metadata (safe copy)
                        temporal_metadata = self._extract_temporal_metadata(result)
                        result.temporal_metadata = self._create_safe_copy(temporal_metadata)
                        
                        # Add semantic metadata (safe copy)
                        semantic_metadata = self._extract_semantic_metadata(result)
                        result.semantic_metadata = self._create_safe_copy(semantic_metadata)
                        
                        # Add speaker analysis (safe copy)
                        speaker_analysis = self._analyze_speaker_patterns(result)
                        result.speaker_analysis = self._create_safe_copy(speaker_analysis)
                        
                    except Exception as e:
                        logger.warning(f"Failed to enrich result: {e}")
                        # Continue with other results
                        continue
            
            # Update cross-reference database
            self._update_cross_references(results, input_path)
            
        except Exception as e:
            logger.error(f"Failed to enrich results: {e}")
            # Return original results if enrichment fails
            pass
        
        return results
    
    def _extract_session_metadata(self, input_path: str) -> Dict[str, Any]:
        """
        Extract metadata about the conversation session
        
        Args:
            input_path: Path to the conversation file
            
        Returns:
            Session metadata dictionary
        """
        if input_path in self.session_cache:
            return self.session_cache[input_path]
        
        metadata = {
            "file_path": input_path,
            "file_name": os.path.basename(input_path),
            "file_size": os.path.getsize(input_path) if os.path.exists(input_path) else 0,
            "extraction_time": datetime.now().isoformat(),
            "session_id": self._generate_session_id(input_path)
        }
        
        # Extract content statistics
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            metadata.update({
                "total_lines": len(content.split('\n')),
                "total_words": len(content.split()),
                "total_characters": len(content),
                "estimated_duration": self._estimate_session_duration(content)
            })
        except Exception as e:
            logger.warning(f"Could not extract content statistics: {e}")
        
        # Cache the metadata
        self.session_cache[input_path] = metadata
        return metadata
    
    def _generate_session_id(self, input_path: str) -> str:
        """
        Generate a unique session ID based on file path and content
        
        Args:
            input_path: Path to the conversation file
            
        Returns:
            Unique session ID
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create hash from file path and first 1000 characters
            hash_input = f"{input_path}:{content[:1000]}"
            return hashlib.md5(hash_input.encode()).hexdigest()[:12]
        except Exception:
            # Fallback to path-based hash
            return hashlib.md5(input_path.encode()).hexdigest()[:12]
    
    def _estimate_session_duration(self, content: str) -> Optional[int]:
        """
        Estimate the duration of the conversation session in minutes
        
        Args:
            content: Conversation content
            
        Returns:
            Estimated duration in minutes, or None if cannot estimate
        """
        # Count message exchanges (simple heuristic)
        user_messages = len(re.findall(r'You said:|User:|Human:', content, re.IGNORECASE))
        ai_messages = len(re.findall(r'ChatGPT said:|Assistant:|AI:|Bot:', content, re.IGNORECASE))
        
        total_exchanges = max(user_messages, ai_messages)
        
        # Estimate 2-3 minutes per exchange
        if total_exchanges > 0:
            return total_exchanges * 2.5
        
        return None
    
    def _calculate_content_hash(self, text: str) -> str:
        """
        Calculate a hash of the text content for deduplication
        
        Args:
            text: Text content
            
        Returns:
            Content hash
        """
        # Normalize text (remove extra whitespace, lowercase)
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _find_cross_references(self, result: Any) -> List[Dict[str, Any]]:
        """
        Find cross-references to similar content in other sessions
        
        Args:
            result: Classification result
            
        Returns:
            List of cross-reference dictionaries
        """
        cross_refs = []
        content_hash = result.content_hash
        
        # Check if we have this content hash in our database
        if content_hash in self.cross_references:
            for ref in self.cross_references[content_hash]:
                if ref['session_id'] != result.session_metadata['session_id']:
                    cross_refs.append(ref)
        
        return cross_refs
    
    def _extract_temporal_metadata(self, result: Any) -> Dict[str, Any]:
        """
        Extract temporal metadata from the classification result
        
        Args:
            result: Classification result
            
        Returns:
            Temporal metadata dictionary
        """
        temporal_metadata = {
            "has_timestamp": bool(result.timestamp),
            "timestamp_parsed": None,
            "time_of_day": None,
            "day_of_week": None
        }
        
        if result.timestamp:
            try:
                # Try to parse the timestamp
                if len(result.timestamp) == 19:  # Full datetime
                    dt = datetime.strptime(result.timestamp, "%Y-%m-%d %H:%M:%S")
                elif len(result.timestamp) == 8:  # Time only
                    dt = datetime.strptime(result.timestamp, "%H:%M:%S")
                else:
                    dt = None
                
                if dt:
                    temporal_metadata.update({
                        "timestamp_parsed": dt.isoformat(),
                        "time_of_day": dt.strftime("%H:%M"),
                        "day_of_week": dt.strftime("%A"),
                        "hour": dt.hour,
                        "minute": dt.minute
                    })
            except ValueError:
                pass
        
        return temporal_metadata
    
    def _extract_semantic_metadata(self, result: Any) -> Dict[str, Any]:
        """
        Extract semantic metadata from the classification result
        
        Args:
            result: Classification result
            
        Returns:
            Semantic metadata dictionary
        """
        text = result.text.lower()
        
        # Extract entities and patterns
        entities = {
            "urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', result.text),
            "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', result.text),
            "code_blocks": len(re.findall(r'```[\s\S]*?```', result.text)),
            "inline_code": len(re.findall(r'`[^`]+`', result.text)),
            "numbers": re.findall(r'\b\d+(?:\.\d+)?\b', result.text),
            "mentions": re.findall(r'@\w+', result.text)
        }
        
        # Calculate text statistics
        text_stats = {
            "word_count": len(text.split()),
            "sentence_count": len(re.split(r'[.!?]+', text)),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "avg_words_per_sentence": len(text.split()) / max(len(re.split(r'[.!?]+', text)), 1),
            "has_question": '?' in result.text,
            "has_exclamation": '!' in result.text,
            "has_code": entities["code_blocks"] > 0 or entities["inline_code"] > 0
        }
        
        # Detect language patterns
        language_patterns = {
            "technical_terms": len(re.findall(r'\b(api|endpoint|server|database|error|debug|fix|test|deploy)\b', text)),
            "decision_terms": len(re.findall(r'\b(decide|choose|select|pick|go with|settle on)\b', text)),
            "problem_terms": len(re.findall(r'\b(issue|problem|bug|error|fail|broken|wrong)\b', text)),
            "solution_terms": len(re.findall(r'\b(fix|solve|resolve|work|success|complete|done)\b', text))
        }
        
        return {
            "entities": entities,
            "text_statistics": text_stats,
            "language_patterns": language_patterns,
            "complexity_score": self._calculate_complexity_score(text)
        }
    
    def _calculate_complexity_score(self, text: str) -> float:
        """
        Calculate a complexity score for the text
        
        Args:
            text: Text to analyze
            
        Returns:
            Complexity score (0.0 to 1.0)
        """
        words = text.split()
        if not words:
            return 0.0
        
        # Factors that increase complexity
        long_words = len([w for w in words if len(w) > 8])
        technical_terms = len(re.findall(r'\b(api|endpoint|server|database|algorithm|implementation|architecture)\b', text.lower()))
        code_blocks = len(re.findall(r'```[\s\S]*?```', text))
        
        # Calculate complexity score
        complexity = (
            (long_words / len(words)) * 0.3 +
            (technical_terms / max(len(words), 1)) * 0.4 +
            (code_blocks / max(len(words) / 50, 1)) * 0.3
        )
        
        return min(1.0, complexity)
    
    def _analyze_speaker_patterns(self, result: Any) -> Dict[str, Any]:
        """
        Analyze speaker patterns in the classification result
        
        Args:
            result: Classification result
            
        Returns:
            Speaker analysis dictionary
        """
        speaker_analysis = {
            "speaker_identified": bool(result.speaker),
            "speaker_type": None,
            "speaker_confidence": 0.0,
            "interaction_pattern": None
        }
        
        if result.speaker:
            speaker_lower = result.speaker.lower()
            
            # Classify speaker type
            if any(term in speaker_lower for term in ['user', 'you', 'human']):
                speaker_analysis["speaker_type"] = "user"
                speaker_analysis["speaker_confidence"] = 0.9
            elif any(term in speaker_lower for term in ['ai', 'assistant', 'chatgpt', 'bot']):
                speaker_analysis["speaker_type"] = "ai"
                speaker_analysis["speaker_confidence"] = 0.9
            else:
                speaker_analysis["speaker_type"] = "unknown"
                speaker_analysis["speaker_confidence"] = 0.3
            
            # Analyze interaction pattern
            text_lower = result.text.lower()
            if '?' in result.text:
                speaker_analysis["interaction_pattern"] = "question"
            elif any(term in text_lower for term in ['thanks', 'thank you', 'appreciate']):
                speaker_analysis["interaction_pattern"] = "gratitude"
            elif any(term in text_lower for term in ['sorry', 'apologize', 'my bad']):
                speaker_analysis["interaction_pattern"] = "apology"
            elif any(term in text_lower for term in ['let\'s', 'we should', 'we will']):
                speaker_analysis["interaction_pattern"] = "collaboration"
            else:
                speaker_analysis["interaction_pattern"] = "statement"
        
        return speaker_analysis
    
    def _update_cross_references(self, results: Dict[str, List[Any]], input_path: str):
        """
        Update the cross-reference database with new results
        
        Args:
            results: Classification results
            input_path: Path to the input file
        """
        session_id = self._generate_session_id(input_path)
        
        for level, classifications in results.items():
            for result in classifications:
                content_hash = result.content_hash
                
                if content_hash not in self.cross_references:
                    self.cross_references[content_hash] = []
                
                # Add this reference
                ref = {
                    "session_id": session_id,
                    "file_path": input_path,
                    "level": level,
                    "confidence": result.confidence,
                    "timestamp": result.timestamp,
                    "speaker": result.speaker,
                    "extraction_time": datetime.now().isoformat()
                }
                
                # Avoid duplicates
                if not any(r["session_id"] == session_id and r["level"] == level 
                          for r in self.cross_references[content_hash]):
                    self.cross_references[content_hash].append(ref)
    
    def save_cross_references(self, output_path: str):
        """
        Save the cross-reference database to a file
        
        Args:
            output_path: Path to save the cross-references
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.cross_references, f, indent=2, default=convert_numpy)
            logger.info(f"Cross-references saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save cross-references: {e}")
    
    def load_cross_references(self, input_path: str):
        """
        Load the cross-reference database from a file
        
        Args:
            input_path: Path to load the cross-references from
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.cross_references = json.load(f, object_hook=lambda d: {k: convert_numpy(v) for k, v in d.items()})
            logger.info(f"Cross-references loaded from {input_path}")
        except Exception as e:
            logger.error(f"Failed to load cross-references: {e}")
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a specific session
        
        Args:
            session_id: Session ID to summarize
            
        Returns:
            Session summary dictionary or None if not found
        """
        session_data = []
        
        for content_hash, refs in self.cross_references.items():
            for ref in refs:
                if ref["session_id"] == session_id:
                    session_data.append(ref)
        
        if not session_data:
            return None
        
        # Calculate summary statistics
        levels = [ref["level"] for ref in session_data]
        confidences = [ref["confidence"] for ref in session_data]
        
        summary = {
            "session_id": session_id,
            "total_classifications": len(session_data),
            "level_distribution": {
                "L1": levels.count("L1"),
                "L2": levels.count("L2"),
                "L3": levels.count("L3")
            },
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "file_paths": list(set(ref["file_path"] for ref in session_data)),
            "time_range": {
                "start": min(ref["extraction_time"] for ref in session_data),
                "end": max(ref["extraction_time"] for ref in session_data)
            }
        }
        
        return summary


if __name__ == "__main__":
    # Test the metadata enricher
    enricher = MetadataEnricher()
    
    # Mock classification result
    class MockResult:
        def __init__(self):
            self.text = "We need to debug this error and fix the server endpoint. The database connection is failing."
            self.timestamp = "2025-01-15 14:30:00"
            self.speaker = "User"
            self.confidence = 0.85
            self.level = "L1"
    
    mock_result = MockResult()
    
    # Test enrichment
    results = {"L1": [mock_result]}
    enriched_results = enricher.enrich_results(results, "test_file.txt")
    
    print("Enriched result metadata:")
    for level, classifications in enriched_results.items():
        for result in classifications:
            print(f"\nLevel: {level}")
            print(f"Session ID: {result.session_metadata['session_id']}")
            print(f"Content Hash: {result.content_hash}")
            print(f"Temporal: {result.temporal_metadata}")
            print(f"Semantic: {result.semantic_metadata}")
            print(f"Speaker: {result.speaker_analysis}")
