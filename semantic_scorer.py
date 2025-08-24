"""
Semantic Scorer for Mud Room Protocol v2.0
Uses sentence transformers to calculate semantic similarity between text and keyword clusters
"""

import numpy as np
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticScorer:
    """
    Calculates semantic similarity between text and keyword clusters using sentence embeddings
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic scorer with a sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load sentence transformer model: {e}")
            logger.info("Falling back to simple keyword matching")
            self.model = None
        
        # Cache for block embeddings to avoid recomputation
        self.block_embeddings = {}
    
    def score_text(self, text: str, keywords: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Score text against each level's keyword clusters using semantic similarity
        
        Args:
            text: The text to score
            keywords: Dictionary of level -> keyword data with clusters
            
        Returns:
            Dictionary of level -> similarity score (0.0 to 1.0)
        """
        if not self.model:
            return self._fallback_scoring(text, keywords)
        
        scores = {}
        
        for level, level_data in keywords.items():
            level_score = self._score_against_level(text, level_data)
            scores[level] = level_score
        
        return scores

    def score_text_batch(self, texts: List[str], keywords: Dict[str, Dict[str, Any]]) -> List[Dict[str, float]]:
        """
        Score multiple texts against each level's keyword clusters using batch embedding
        
        Args:
            texts: List of texts to score
            keywords: Dictionary of level -> keyword data with clusters
            
        Returns:
            List of dictionaries with level -> similarity score (0.0 to 1.0)
        """
        if not self.model:
            return [self._fallback_scoring(text, keywords) for text in texts]
        
        # Batch embed all texts at once for speedup
        try:
            embeddings = self.model.encode(texts, batch_size=16, convert_to_tensor=True)
            # Convert to numpy for compatibility
            embeddings = embeddings.cpu().numpy()
        except Exception as e:
            logger.warning(f"Batch embedding failed, falling back to individual: {e}")
            return [self.score_text(text, keywords) for text in texts]
        
        # Store embeddings in cache for reuse
        for i, embedding in enumerate(embeddings):
            self.block_embeddings[i] = embedding
        
        # Score each text using precomputed embeddings
        results = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            scores = {}
            for level, level_data in keywords.items():
                level_score = self._score_against_level_with_embedding(embedding, level_data)
                scores[level] = level_score
            results.append(scores)
        
        return results

    def _score_against_level(self, text: str, level_data: Dict[str, Any]) -> float:
        """
        Score text against a specific level's keyword clusters
        
        Args:
            text: The text to score
            level_data: Keyword data for the level including clusters
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not level_data.get("clusters"):
            return 0.0
        
        # Check if we have a cached embedding for this text
        # For now, we'll compute the embedding, but in the future we could hash the text
        # and use that as a cache key for individual text scoring
        
        # Get embeddings for the text
        text_embedding = self.model.encode([text])[0]
        
        # Score against each cluster
        cluster_scores = []
        
        for cluster_name, cluster_keywords in level_data["clusters"].items():
            if not cluster_keywords:
                continue
            
            # Create cluster representation (average of keyword embeddings)
            cluster_embeddings = self.model.encode(cluster_keywords)
            cluster_embedding = np.mean(cluster_embeddings, axis=0)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(text_embedding, cluster_embedding)
            cluster_scores.append(similarity)
        
        # Return the maximum cluster score for this level
        return max(cluster_scores) if cluster_scores else 0.0

    def get_cached_embedding(self, block_index: int) -> Optional[np.ndarray]:
        """
        Get a cached embedding for a block index
        
        Args:
            block_index: Index of the block
            
        Returns:
            Cached embedding or None if not found
        """
        return self.block_embeddings.get(block_index)

    def clear_cache(self):
        """Clear the block embeddings cache"""
        self.block_embeddings.clear()
        logger.info("Block embeddings cache cleared")

    def get_cache_size(self) -> int:
        """Get the number of cached embeddings"""
        return len(self.block_embeddings)

    def get_block_embeddings(self) -> Dict[int, np.ndarray]:
        """
        Get all cached block embeddings
        
        Returns:
            Dictionary mapping block index to embedding array
        """
        return self.block_embeddings.copy()

    def has_cached_embedding(self, block_index: int) -> bool:
        """
        Check if a block embedding is cached
        
        Args:
            block_index: Index of the block
            
        Returns:
            True if embedding is cached
        """
        return block_index in self.block_embeddings

    def get_cached_embeddings_count(self) -> int:
        """Get the total number of cached embeddings"""
        return len(self.block_embeddings)

    def _score_against_level_with_embedding(self, text_embedding: np.ndarray, level_data: Dict[str, Any]) -> float:
        """
        Score precomputed text embedding against a specific level's keyword clusters
        
        Args:
            text_embedding: Precomputed text embedding
            level_data: Keyword data for the level including clusters
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not level_data.get("clusters"):
            return 0.0
        
        # Score against each cluster
        cluster_scores = []
        
        for cluster_name, cluster_keywords in level_data["clusters"].items():
            if not cluster_keywords:
                continue
            
            # Create cluster representation (average of keyword embeddings)
            cluster_embeddings = self.model.encode(cluster_keywords)
            cluster_embedding = np.mean(cluster_embeddings, axis=0)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(text_embedding, cluster_embedding)
            cluster_scores.append(similarity)
        
        # Return the maximum cluster score for this level
        return max(cluster_scores) if cluster_scores else 0.0
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _fallback_scoring(self, text: str, keywords: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Fallback scoring method when sentence transformers are not available
        
        Args:
            text: The text to score
            keywords: Dictionary of level -> keyword data
            
        Returns:
            Dictionary of level -> similarity score (0.0 to 1.0)
        """
        text_lower = text.lower()
        scores = {}
        
        for level, level_data in keywords.items():
            level_keywords = level_data.get("keywords", [])
            if not level_keywords:
                scores[level] = 0.0
                continue
            
            # Count keyword matches
            matches = sum(1 for keyword in level_keywords if keyword in text_lower)
            
            # Calculate simple score based on match ratio
            if matches > 0:
                # Normalize by text length and keyword count
                text_words = len(text_lower.split())
                keyword_count = len(level_keywords)
                score = min(1.0, (matches / max(text_words, 1)) * (keyword_count / max(keyword_count, 1)))
                scores[level] = score
            else:
                scores[level] = 0.0
        
        return scores
    
    def get_semantic_keywords(self, text: str, keywords: Dict[str, Dict[str, Any]], 
                            top_k: int = 5) -> Dict[str, List[str]]:
        """
        Find the most semantically similar keywords for each level
        
        Args:
            text: The text to analyze
            keywords: Dictionary of level -> keyword data
            top_k: Number of top keywords to return per level
            
        Returns:
            Dictionary of level -> list of most similar keywords
        """
        if not self.model:
            return self._fallback_semantic_keywords(text, keywords, top_k)
        
        text_embedding = self.model.encode([text])[0]
        semantic_keywords = {}
        
        for level, level_data in keywords.items():
            level_keywords = level_data.get("keywords", [])
            if not level_keywords:
                semantic_keywords[level] = []
                continue
            
            # Calculate similarity with each keyword
            keyword_embeddings = self.model.encode(level_keywords)
            similarities = []
            
            for i, keyword in enumerate(level_keywords):
                similarity = self._cosine_similarity(text_embedding, keyword_embeddings[i])
                similarities.append((keyword, similarity))
            
            # Sort by similarity and take top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            semantic_keywords[level] = [kw for kw, _ in similarities[:top_k]]
        
        return semantic_keywords
    
    def _fallback_semantic_keywords(self, text: str, keywords: Dict[str, Dict[str, Any]], 
                                  top_k: int) -> Dict[str, List[str]]:
        """
        Fallback method for finding semantic keywords
        
        Args:
            text: The text to analyze
            keywords: Dictionary of level -> keyword data
            top_k: Number of top keywords to return per level
            
        Returns:
            Dictionary of level -> list of most similar keywords
        """
        text_lower = text.lower()
        semantic_keywords = {}
        
        for level, level_data in keywords.items():
            level_keywords = level_data.get("keywords", [])
            if not level_keywords:
                semantic_keywords[level] = []
                continue
            
            # Find keywords that appear in the text
            found_keywords = [kw for kw in level_keywords if kw in text_lower]
            
            # Sort by frequency (simple heuristic)
            keyword_freq = {}
            for kw in found_keywords:
                keyword_freq[kw] = text_lower.count(kw)
            
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
            semantic_keywords[level] = [kw for kw, _ in sorted_keywords[:top_k]]
        
        return semantic_keywords
    
    def calculate_context_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two text blocks for context analysis
        
        Args:
            text1: First text block
            text2: Second text block
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not self.model:
            # Fallback to simple word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union)
        
        # Use sentence embeddings
        embeddings = self.model.encode([text1, text2])
        return self._cosine_similarity(embeddings[0], embeddings[1])
    
    def get_text_summary_embedding(self, text: str) -> np.ndarray:
        """
        Get a summary embedding for a text block (useful for clustering)
        
        Args:
            text: The text to summarize
            
        Returns:
            Summary embedding vector
        """
        if not self.model:
            # Fallback: return a simple hash-based vector
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            return np.array([int(hash_obj.hexdigest()[:8], 16) % 1000] * 384) / 1000.0
        
        return self.model.encode([text])[0]


if __name__ == "__main__":
    # Test the semantic scorer
    scorer = SemanticScorer()
    
    # Test text
    test_text = "We need to debug this error and fix the issue with the server endpoint"
    
    # Mock keywords structure
    test_keywords = {
        "L1": {
            "keywords": ["debug", "error", "fix", "server", "endpoint"],
            "clusters": {
                "technical": ["debug", "error", "fix"],
                "infrastructure": ["server", "endpoint"]
            }
        },
        "L2": {
            "keywords": ["worked", "verified", "confirmed"],
            "clusters": {
                "outcome": ["worked", "verified", "confirmed"]
            }
        },
        "L3": {
            "keywords": ["strategy", "vision", "decision"],
            "clusters": {
                "decision": ["strategy", "vision", "decision"]
            }
        }
    }
    
    # Test scoring
    scores = scorer.score_text(test_text, test_keywords)
    print(f"Semantic scores: {scores}")
    
    # Test semantic keywords
    semantic_keywords = scorer.get_semantic_keywords(test_text, test_keywords)
    print(f"Semantic keywords: {semantic_keywords}")
