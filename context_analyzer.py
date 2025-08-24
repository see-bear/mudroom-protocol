# context_analyzer.py

from typing import List, Tuple
import numpy as np
from semantic_scorer import SemanticScorer
import logging

logger = logging.getLogger(__name__)

class ContextAnalyzer:
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2"):
        self.scorer = SemanticScorer(embedding_model_name)

    def compute_topic_shifts(self, blocks: List[str], threshold: float = 0.35) -> List[bool]:
        """
        Returns a list of booleans indicating whether a topic shift occurred before each block.
        """
        shifts = [False]  # No shift before the first block
        for i in range(1, len(blocks)):
            sim = self.scorer.calculate_context_similarity(blocks[i - 1], blocks[i])
            shifts.append(sim < threshold)
        return shifts

    def label_sessions(self, blocks: List[str], threshold: float = 0.35) -> List[int]:
        """
        Assigns session IDs to blocks based on topic shift detection.
        """
        shifts = self.compute_topic_shifts(blocks, threshold)
        session_ids = []
        current = 0
        for shift in shifts:
            if shift:
                current += 1
            session_ids.append(current)
        return session_ids

    def get_block_embeddings(self, blocks: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for a list of text blocks using batch processing for speedup.
        """
        if not blocks:
            return []
        
        # Use batch embedding for speedup
        try:
            embeddings = self.scorer.model.encode(blocks, batch_size=16, convert_to_tensor=True)
            # Convert to numpy and store in cache
            embeddings = embeddings.cpu().numpy()
            
            # Store in cache for reuse
            for i, embedding in enumerate(embeddings):
                self.scorer.block_embeddings[i] = embedding
                
            return embeddings.tolist()
        except Exception as e:
            # Fallback to individual embedding if batch fails
            logger.warning(f"Batch embedding failed, falling back to individual: {e}")
            embeddings = []
            for block in blocks:
                embedding = self.scorer.get_text_summary_embedding(block)
                embeddings.append(embedding)
            return embeddings

    def analyze_conversation_flow(self, blocks: List[str], speakers: List[str] = None) -> dict:
        """
        Analyze the flow of conversation including topic shifts, speaker patterns, and session boundaries.
        
        Args:
            blocks: List of conversation blocks
            speakers: Optional list of speaker identifiers for each block
            
        Returns:
            Dictionary with analysis results
        """
        # Get topic shifts
        topic_shifts = self.compute_topic_shifts(blocks)
        
        # Get session labels
        session_ids = self.label_sessions(blocks)
        
        # Analyze speaker patterns if provided
        speaker_analysis = {}
        if speakers:
            speaker_analysis = self._analyze_speaker_patterns(blocks, speakers, session_ids)
        
        # Get embeddings for potential clustering
        embeddings = self.get_block_embeddings(blocks)
        
        return {
            "topic_shifts": topic_shifts,
            "session_ids": session_ids,
            "num_sessions": max(session_ids) + 1 if session_ids else 0,
            "speaker_analysis": speaker_analysis,
            "embeddings": embeddings,
            "session_boundaries": self._find_session_boundaries(session_ids)
        }

    def _analyze_speaker_patterns(self, blocks: List[str], speakers: List[str], session_ids: List[int]) -> dict:
        """
        Analyze patterns in speaker roles across sessions.
        """
        if len(speakers) != len(blocks):
            return {}
        
        analysis = {
            "session_speakers": {},
            "speaker_transitions": [],
            "dominant_speakers": {}
        }
        
        # Group by session
        for i, session_id in enumerate(session_ids):
            if session_id not in analysis["session_speakers"]:
                analysis["session_speakers"][session_id] = []
            analysis["session_speakers"][session_id].append(speakers[i])
        
        # Find speaker transitions
        for i in range(1, len(speakers)):
            if speakers[i] != speakers[i-1]:
                analysis["speaker_transitions"].append({
                    "position": i,
                    "from": speakers[i-1],
                    "to": speakers[i],
                    "session": session_ids[i]
                })
        
        # Find dominant speakers per session
        for session_id, session_speakers in analysis["session_speakers"].items():
            from collections import Counter
            speaker_counts = Counter(session_speakers)
            dominant = speaker_counts.most_common(1)[0] if speaker_counts else None
            analysis["dominant_speakers"][session_id] = dominant
        
        return analysis

    def _find_session_boundaries(self, session_ids: List[int]) -> List[int]:
        """
        Find the positions where sessions change.
        """
        boundaries = []
        for i in range(1, len(session_ids)):
            if session_ids[i] != session_ids[i-1]:
                boundaries.append(i)
        return boundaries
