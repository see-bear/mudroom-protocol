"""
Mud Room Protocol v2.0 - Enhanced Core Classifier
Intelligent conversation classification using semantic similarity and context awareness
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import numpy as np

from semantic_scorer import SemanticScorer
from conversation_parser import ConversationParser
from metadata_enricher import MetadataEnricher
from context_analyzer import ContextAnalyzer
from vector_store import save_vector_store


def convert_numpy(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    return obj


@dataclass
class ClassificationResult:
    """Result of classifying a conversation block"""
    text: str  # The original text that was classified
    level: str  # L1, L2, L3
    confidence: float  # 0.0 to 1.0
    keywords: List[str] = field(default_factory=list)  # Keywords that contributed to classification
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context information
    speaker: Optional[str] = None  # User or AI
    timestamp: Optional[str] = None


@dataclass
class ConversationBlock:
    """A chunk of conversation to be classified"""
    text: str
    speaker: Optional[str] = None
    timestamp: Optional[str] = None
    line_numbers: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MudRoomClassifierV2:
    """
    Enhanced classifier that uses semantic similarity, context awareness,
    and intelligent conversation parsing
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.semantic_scorer = SemanticScorer()
        self.conversation_parser = ConversationParser()
        self.metadata_enricher = MetadataEnricher()
        self.context_analyzer = ContextAnalyzer()
        
        # Load keyword files with semantic clusters
        self.keywords = self._load_enhanced_keywords()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "confidence_threshold": 0.6,
            "min_block_size": 50,  # Minimum characters for a block
            "max_block_size": 2000,  # Maximum characters for a block
            "speaker_weight": 0.2,  # Weight for speaker role in scoring
            "proximity_weight": 0.3,  # Weight for keyword proximity
            "semantic_weight": 0.5,  # Weight for semantic similarity
            "output_formats": ["markdown", "json", "yaml"],
            "enable_cross_references": True,
            "enable_metadata_enrichment": True
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def _load_enhanced_keywords(self) -> Dict[str, Dict[str, Any]]:
        """Load keywords with semantic clusters and weights"""
        keywords_dir = Path("keywords")
        
        enhanced_keywords = {}
        for level in ["L1", "L2", "L3"]:
            level_file = keywords_dir / f"level{level[1]}.txt"
            if level_file.exists():
                with open(level_file, 'r', encoding='utf-8') as f:
                    raw_keywords = [line.strip().lower() for line in f if line.strip()]
                
                # Group keywords into semantic clusters
                clusters = self._create_semantic_clusters(raw_keywords, level)
                
                enhanced_keywords[level] = {
                    "keywords": raw_keywords,
                    "clusters": clusters,
                    "weights": self._calculate_keyword_weights(raw_keywords, level)
                }
        
        return enhanced_keywords
    
    def _create_semantic_clusters(self, keywords: List[str], level: str) -> Dict[str, List[str]]:
        """Group keywords into semantic clusters based on meaning"""
        # This is a simplified clustering - in practice, we'd use embeddings
        clusters = {
            "technical": [],
            "process": [],
            "decision": [],
            "outcome": []
        }
        
        # Simple rule-based clustering based on level
        if level == "L1":
            clusters["technical"].extend([kw for kw in keywords if kw in ["debug", "error", "fix", "trace", "test"]])
            clusters["process"].extend([kw for kw in keywords if kw in ["try", "attempt", "retry", "check"]])
        elif level == "L2":
            clusters["outcome"].extend([kw for kw in keywords if kw in ["worked", "verified", "confirmed", "complete"]])
            clusters["process"].extend([kw for kw in keywords if kw in ["lesson", "realized", "pattern", "hindsight"]])
        elif level == "L3":
            clusters["decision"].extend([kw for kw in keywords if kw in ["decision", "strategy", "vision", "direction"]])
            clusters["process"].extend([kw for kw in keywords if kw in ["committed", "finalized", "goal", "plan"]])
        
        return {k: v for k, v in clusters.items() if v}
    
    def _calculate_keyword_weights(self, keywords: List[str], level: str) -> Dict[str, float]:
        """Calculate importance weights for keywords based on level"""
        weights = {}
        base_weight = 1.0
        
        for keyword in keywords:
            # Adjust weights based on level and keyword importance
            if level == "L3" and keyword in ["strategy", "vision", "decision"]:
                weights[keyword] = base_weight * 1.5
            elif level == "L2" and keyword in ["worked", "verified", "lesson"]:
                weights[keyword] = base_weight * 1.3
            elif level == "L1" and keyword in ["error", "debug", "fix"]:
                weights[keyword] = base_weight * 1.2
            else:
                weights[keyword] = base_weight
                
        return weights
    
    def classify_conversation(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Main classification method that processes a conversation file
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting classification of: {input_path}")
        
        # Parse conversation into blocks
        logger.info("Parsing conversation into blocks...")
        blocks = self.conversation_parser.parse_conversation(input_path)
        logger.info(f"Parsed {len(blocks)} conversation blocks")
        
        # Analyze conversation context and flow
        logger.info("Analyzing conversation context and flow...")
        block_texts = [block.text for block in blocks]
        block_speakers = [block.speaker for block in blocks]
        
        context_analysis = self.context_analyzer.analyze_conversation_flow(
            block_texts, block_speakers
        )
        
        logger.info(f"Detected {context_analysis['num_sessions']} sessions with {len(context_analysis['topic_shifts'])} topic shifts")
        
        # Classify each block with context awareness
        logger.info("Classifying blocks with context awareness...")
        classifications = []
        for i, block in enumerate(blocks):
            result = self._classify_block_with_context(block, context_analysis, i)
            if result:
                classifications.append(result)
                if i % 10 == 0:  # Log every 10th block
                    logger.info(f"Processed {i+1}/{len(blocks)} blocks, found {len(classifications)} classifications")
        
        logger.info(f"Total classifications found: {len(classifications)}")
        
        # Group by level
        results = self._group_by_level(classifications)
        logger.info(f"Grouped results - L1: {len(results['L1'])}, L2: {len(results['L2'])}, L3: {len(results['L3'])}")
        
        # Enrich with metadata
        if self.config["enable_metadata_enrichment"]:
            logger.info("Enriching with metadata...")
            results = self.metadata_enricher.enrich_results(results, input_path)
        
        # Save results
        logger.info("Saving results...")
        self._save_results(results, output_dir, input_path)
        
        # Save structured metadata
        logger.info("Saving structured metadata...")
        metadata_path = os.path.join(output_dir, datetime.now().strftime("%Y-%m-%d"), f"{os.path.splitext(os.path.basename(input_path))[0]}-classification_metadata.json")
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        self.metadata_enricher.save_json(metadata_path)
        
        # Save vector store for persistent embedding storage
        logger.info("Saving vector store...")
        file_id_stem = Path(input_path).stem.replace(" ", "_")
        try:
            # Get metadata and ensure it's JSON-safe
            metadata_list = self.metadata_enricher.get_metadata()
            # Ensure metadata is JSON-serializable by creating a safe copy
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
            
            vector_store_result = save_vector_store(
                file_id=file_id_stem,
                embeddings_dict=self.semantic_scorer.get_block_embeddings(),
                metadata_list=safe_metadata,
                filename=os.path.basename(input_path),
                project="MudRoom"
            )
            logger.info(f"Vector store saved: {vector_store_result['embeddings_count']} embeddings, {vector_store_result['metadata_count']} metadata entries")
        except Exception as e:
            logger.warning(f"Failed to save vector store: {e}")
        
        logger.info(f"Classification complete for: {input_path}")
        return results

    def _classify_block_with_context(self, block: ConversationBlock, context_analysis: dict, block_index: int) -> Optional[ClassificationResult]:
        """
        Classify a single conversation block with context awareness
        """
        if len(block.text.strip()) < self.config["min_block_size"]:
            return None
            
        # Get semantic similarity scores
        semantic_scores = self.semantic_scorer.score_text(block.text, self.keywords)
        
        # Get keyword-based scores with proximity
        keyword_scores = self._calculate_keyword_scores(block.text)
        
        # Get speaker-based adjustments
        speaker_adjustment = self._calculate_speaker_adjustment(block.speaker)
        
        # Apply context-based adjustments
        context_adjustment = self._calculate_context_adjustment(block, context_analysis, block_index)
        
        # Combine scores using weighted approach
        final_scores = {}
        for level in ["L1", "L2", "L3"]:
            semantic_score = semantic_scores.get(level, 0.0)
            keyword_score = keyword_scores.get(level, 0.0)
            speaker_score = speaker_adjustment.get(level, 0.0)
            context_score = context_adjustment.get(level, 0.0)
            
            final_score = (
                semantic_score * self.config["semantic_weight"] +
                keyword_score * self.config["proximity_weight"] +
                speaker_score * self.config["speaker_weight"] +
                context_score * 0.2  # Context weight
            )
            
            final_scores[level] = final_score
        
        # Find best classification
        if not final_scores:
            return None
            
        best_level = max(final_scores, key=final_scores.get)
        confidence = final_scores[best_level]
        
        # Only return if confidence meets threshold
        if confidence < self.config["confidence_threshold"]:
            return None
        
        # Extract contributing keywords
        contributing_keywords = self._extract_contributing_keywords(
            block.text, best_level, final_scores[best_level]
        )
        
        # Get context information for metadata enrichment
        session_id = context_analysis["session_ids"][block_index] if block_index < len(context_analysis["session_ids"]) else 0
        topic_shift = context_analysis["topic_shifts"][block_index] if block_index < len(context_analysis["topic_shifts"]) else False
        
        # Determine speaker transition
        speaker_transition = None
        if "speaker_analysis" in context_analysis and context_analysis["speaker_analysis"]:
            speaker_transitions = context_analysis["speaker_analysis"].get("speaker_transitions", [])
            for transition in speaker_transitions:
                if transition["position"] == block_index:
                    speaker_transition = f"{transition['from']}→{transition['to']}"
                    break
        
        # Enrich metadata
        self.metadata_enricher.enrich(
            block_id=block_index,
            classification=best_level,
            session_id=session_id,
            topic_shift=topic_shift,
            speaker_transition=speaker_transition,
            confidence=confidence
        )
        
        return ClassificationResult(
            text=block.text,
            level=best_level,
            confidence=confidence,
            keywords=contributing_keywords,
            context={
                "semantic_score": semantic_scores.get(best_level, 0.0),
                "keyword_score": keyword_scores.get(best_level, 0.0),
                "speaker_adjustment": speaker_adjustment.get(best_level, 0.0),
                "context_adjustment": context_adjustment.get(best_level, 0.0),
                "block_size": len(block.text),
                "session_id": session_id,
                "topic_shift": topic_shift,
                "line_numbers": block.line_numbers,
                "speaker": block.speaker,
                "timestamp": block.timestamp
            },
            speaker=block.speaker,
            timestamp=block.timestamp
        )

    def _classify_block(self, block: ConversationBlock) -> Optional[ClassificationResult]:
        """
        Fallback classification method without context awareness
        """
        if len(block.text.strip()) < self.config["min_block_size"]:
            return None
            
        # Get semantic similarity scores
        semantic_scores = self.semantic_scorer.score_text(block.text, self.keywords)
        
        # Get keyword-based scores with proximity
        keyword_scores = self._calculate_keyword_scores(block.text)
        
        # Get speaker-based adjustments
        speaker_adjustment = self._calculate_speaker_adjustment(block.speaker)
        
        # Combine scores using weighted approach
        final_scores = {}
        for level in ["L1", "L2", "L3"]:
            semantic_score = semantic_scores.get(level, 0.0)
            keyword_score = keyword_scores.get(level, 0.0)
            speaker_score = speaker_adjustment.get(level, 0.0)
            
            final_score = (
                semantic_score * self.config["semantic_weight"] +
                keyword_score * self.config["proximity_weight"] +
                speaker_score * self.config["speaker_weight"]
            )
            
            final_scores[level] = final_score
        
        # Find best classification
        if not final_scores:
            return None
            
        best_level = max(final_scores, key=final_scores.get)
        confidence = final_scores[best_level]
        
        # Only return if confidence meets threshold
        if confidence < self.config["confidence_threshold"]:
            return None
        
        # Extract contributing keywords
        contributing_keywords = self._extract_contributing_keywords(
            block.text, best_level, final_scores[best_level]
        )
        
        return ClassificationResult(
            text=block.text,
            level=best_level,
            confidence=confidence,
            keywords=contributing_keywords,
            context={
                "semantic_score": semantic_scores.get(best_level, 0.0),
                "keyword_score": keyword_scores.get(best_level, 0.0),
                "speaker_adjustment": speaker_adjustment.get(best_level, 0.0),
                "block_size": len(block.text),
                "line_numbers": block.line_numbers
            },
            speaker=block.speaker,
            timestamp=block.timestamp
        )

    def _calculate_context_adjustment(self, block: ConversationBlock, context_analysis: dict, block_index: int) -> Dict[str, float]:
        """
        Calculate context-based adjustments for classification scores
        """
        adjustments = {"L1": 0.0, "L2": 0.0, "L3": 0.0}
        
        if block_index >= len(context_analysis["session_ids"]):
            return adjustments
        
        session_id = context_analysis["session_ids"][block_index]
        topic_shift = context_analysis["topic_shifts"][block_index]
        
        # Topic shifts often indicate strategic discussions (L3)
        if topic_shift:
            adjustments["L3"] += 0.3
            adjustments["L2"] += 0.1
        
        # Session boundaries often contain strategic content
        if block_index in context_analysis["session_boundaries"]:
            adjustments["L3"] += 0.2
            adjustments["L2"] += 0.1
        
        # Speaker transitions can indicate different types of content
        if "speaker_analysis" in context_analysis and context_analysis["speaker_analysis"]:
            speaker_transitions = context_analysis["speaker_analysis"].get("speaker_transitions", [])
            for transition in speaker_transitions:
                if transition["position"] == block_index:
                    # User-to-AI transitions often indicate strategic questions
                    if transition["from"] == "User" and transition["to"] == "AI":
                        adjustments["L3"] += 0.1
                    # AI-to-User transitions often indicate tactical responses
                    elif transition["from"] == "AI" and transition["to"] == "User":
                        adjustments["L2"] += 0.1
        
        return adjustments
    
    def _calculate_keyword_scores(self, text: str) -> Dict[str, float]:
        """Calculate keyword-based scores with proximity weighting"""
        text_lower = text.lower()
        scores = {"L1": 0.0, "L2": 0.0, "L3": 0.0}
        
        for level, level_data in self.keywords.items():
            level_score = 0.0
            keywords_found = []
            
            for keyword, weight in level_data["weights"].items():
                if keyword in text_lower:
                    # Calculate proximity bonus
                    proximity_bonus = self._calculate_proximity_bonus(text_lower, keyword)
                    keyword_score = weight * (1.0 + proximity_bonus)
                    level_score += keyword_score
                    keywords_found.append(keyword)
            
            # Apply cluster bonus if multiple keywords from same cluster found
            cluster_bonus = self._calculate_cluster_bonus(keywords_found, level_data["clusters"])
            scores[level] = level_score * (1.0 + cluster_bonus)
        
        return scores
    
    def _calculate_proximity_bonus(self, text: str, keyword: str) -> float:
        """Calculate bonus for keywords that appear close together"""
        # Simple proximity calculation - could be enhanced with NLP
        words = text.split()
        keyword_positions = [i for i, word in enumerate(words) if keyword in word]
        
        if len(keyword_positions) < 2:
            return 0.0
        
        # Calculate average distance between keyword occurrences
        distances = []
        for i in range(len(keyword_positions) - 1):
            distance = keyword_positions[i + 1] - keyword_positions[i]
            distances.append(distance)
        
        avg_distance = sum(distances) / len(distances)
        
        # Closer keywords get higher bonus (max 0.5 bonus)
        if avg_distance <= 3:
            return 0.5
        elif avg_distance <= 5:
            return 0.3
        elif avg_distance <= 10:
            return 0.1
        else:
            return 0.0
    
    def _calculate_cluster_bonus(self, keywords_found: List[str], clusters: Dict[str, List[str]]) -> float:
        """Calculate bonus for finding multiple keywords from the same semantic cluster"""
        max_cluster_bonus = 0.0
        
        for cluster_name, cluster_keywords in clusters.items():
            cluster_matches = [kw for kw in keywords_found if kw in cluster_keywords]
            if len(cluster_matches) >= 2:
                # Bonus increases with more matches in same cluster
                cluster_bonus = min(0.3, len(cluster_matches) * 0.1)
                max_cluster_bonus = max(max_cluster_bonus, cluster_bonus)
        
        return max_cluster_bonus
    
    def _calculate_speaker_adjustment(self, speaker: Optional[str]) -> Dict[str, float]:
        """Calculate scoring adjustments based on speaker role"""
        if not speaker:
            return {"L1": 0.0, "L2": 0.0, "L3": 0.0}
        
        # User statements might be more strategic (L3), AI responses more technical (L1/L2)
        if speaker.lower() in ["user", "you"]:
            return {"L1": 0.0, "L2": 0.1, "L3": 0.2}
        elif speaker.lower() in ["ai", "assistant", "chatgpt"]:
            return {"L1": 0.1, "L2": 0.2, "L3": 0.0}
        else:
            return {"L1": 0.0, "L2": 0.0, "L3": 0.0}
    
    def _extract_contributing_keywords(self, text: str, level: str, score: float) -> List[str]:
        """Extract keywords that contributed to the classification"""
        text_lower = text.lower()
        level_keywords = self.keywords[level]["keywords"]
        
        contributing = []
        for keyword in level_keywords:
            if keyword in text_lower:
                contributing.append(keyword)
        
        return contributing[:5]  # Limit to top 5 contributing keywords
    
    def _create_safe_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a safe copy of context to prevent circular references
        
        Args:
            context: Context dictionary
            
        Returns:
            Safe copy of context
        """
        if not context:
            return {}
        
        try:
            safe_context = {}
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    safe_context[key] = value
                elif isinstance(value, list):
                    safe_context[key] = [str(item) for item in value]
                elif isinstance(value, dict):
                    safe_context[key] = {k: str(v) for k, v in value.items()}
                else:
                    safe_context[key] = str(value)
            return safe_context
        except Exception as e:
            logger.warning(f"Failed to create safe context: {e}")
            return {"error": "Failed to serialize context"}
    
    def _group_by_level(self, classifications: List[ClassificationResult]) -> Dict[str, List[ClassificationResult]]:
        """Group classification results by level"""
        grouped = {"L1": [], "L2": [], "L3": []}
        
        for result in classifications:
            grouped[result.level].append(result)
        
        return grouped
    
    def _save_results(self, results: Dict[str, List[ClassificationResult]], 
                     output_dir: str, input_path: str):
        """Save classification results to files"""
        date_tag = datetime.now().strftime("%Y-%m-%d")
        output_folder = os.path.join(output_dir, date_tag)
        os.makedirs(output_folder, exist_ok=True)
        
        basename = os.path.splitext(os.path.basename(input_path))[0]
        
        # Save markdown files
        for level, classifications in results.items():
            if classifications:
                md_path = os.path.join(output_folder, f"{basename}-{level}.md")
                self._save_markdown(md_path, level, classifications)
        
        # Save metadata JSON
        metadata_path = os.path.join(output_folder, f"{basename}-metadata.json")
        self._save_metadata(metadata_path, results, input_path)
    
    def _save_markdown(self, path: str, level: str, classifications: List[ClassificationResult]):
        """Save classifications as markdown"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {level} Classifications\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            for i, result in enumerate(classifications, 1):
                f.write(f"## Entry {i}\n\n")
                f.write(f"**Confidence:** {result.confidence:.2f}\n\n")
                f.write(f"**Keywords:** {', '.join(result.keywords)}\n\n")
                if result.speaker:
                    f.write(f"**Speaker:** {result.speaker}\n\n")
                if result.timestamp:
                    f.write(f"**Timestamp:** {result.timestamp}\n\n")
                f.write(f"**Context:**\n")
                for key, value in result.context.items():
                    f.write(f"- {key}: {value}\n")
                f.write(f"\n**Text:**\n```\n{result.text}\n```\n\n---\n\n")
    
    def _save_metadata(self, path: str, results: Dict[str, List[ClassificationResult]], 
                      input_path: str):
        """Save detailed metadata as JSON"""
        try:
            metadata = {
                "input_file": input_path,
                "generated_at": datetime.now().isoformat(),
                "config": self.config,
                "statistics": {
                    level: {
                        "count": len(classifications),
                        "avg_confidence": sum(r.confidence for r in classifications) / len(classifications) if classifications else 0.0
                    }
                    for level, classifications in results.items()
                },
                "classifications": {
                    level: [
                        {
                            "confidence": r.confidence,
                            "keywords": r.keywords,
                            "speaker": r.speaker,
                            "timestamp": r.timestamp,
                            "context": self._create_safe_context(r.context)
                        }
                        for r in classifications
                    ]
                    for level, classifications in results.items()
                }
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=convert_numpy)
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            # Create a minimal safe version
            safe_metadata = {
                "input_file": input_path,
                "generated_at": datetime.now().isoformat(),
                "error": f"Failed to save full metadata: {str(e)}",
                "statistics": {
                    level: {"count": len(classifications)}
                    for level, classifications in results.items()
                }
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(safe_metadata, f, indent=2, default=convert_numpy)


if __name__ == "__main__":
    # Example usage
    classifier = MudRoomClassifierV2()
    results = classifier.classify_conversation(
        input_path="sample_chat.txt",
        output_dir="mudroom_logs"
    )
    print(f"Classification complete. Found {sum(len(v) for v in results.values())} classified blocks.")
