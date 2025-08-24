import os
import numpy as np
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def save_vector_store(file_id: str, embeddings_dict: Dict[int, np.ndarray], 
                     metadata_list: List[Dict[str, Any]], 
                     filename: str = None, 
                     project: str = None,
                     output_dir: str = "vector_store"):
    """
    Save block embeddings and metadata to disk for persistent storage
    
    Args:
        file_id: Unique identifier for the file (e.g., filename without extension)
        embeddings_dict: Dictionary mapping block index to embedding array
        metadata_list: List of metadata dictionaries for each block
        output_dir: Directory to save the vector store files
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert embeddings dict to array (sorted by block index)
        block_ids = sorted(embeddings_dict.keys())
        embeddings = np.array([embeddings_dict[bid] for bid in block_ids])
        
        # Save vectors to .npy file
        npy_path = os.path.join(output_dir, f"{file_id}_vectors.npy")
        np.save(npy_path, embeddings)
        
        # Inject metadata into each entry
        enriched_metadata = []
        for i, item in enumerate(metadata_list):
            enriched_item = dict(item)  # shallow copy
            enriched_item["block_id"] = block_ids[i]
            enriched_item["filename"] = filename or f"{file_id}.txt"
            enriched_item["project"] = project or "Unknown"
            enriched_item["ingest_date"] = datetime.utcnow().isoformat()
            enriched_metadata.append(enriched_item)
        
        # Save metadata to .json file
        json_path = os.path.join(output_dir, f"{file_id}_metadata.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(enriched_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Vector store saved: {len(embeddings)} embeddings to {npy_path}")
        logger.info(f"Metadata saved: {len(metadata_list)} entries to {json_path}")
        
        return {
            "npy_path": npy_path,
            "json_path": json_path,
            "embeddings_count": len(embeddings),
            "metadata_count": len(metadata_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to save vector store for {file_id}: {e}")
        raise

def load_vector_store(file_id: str, output_dir: str = "vector_store"):
    """
    Load block embeddings and metadata from disk
    
    Args:
        file_id: Unique identifier for the file
        output_dir: Directory containing the vector store files
        
    Returns:
        Dictionary containing embeddings array and metadata list
    """
    try:
        # Load vectors from .npy file
        npy_path = os.path.join(output_dir, f"{file_id}_vectors.npy")
        embeddings = np.load(npy_path)
        
        # Load metadata from .json file
        json_path = os.path.join(output_dir, f"{file_id}_metadata.json")
        with open(json_path, "r", encoding="utf-8") as f:
            metadata_list = json.load(f)
        
        logger.info(f"Vector store loaded: {len(embeddings)} embeddings from {npy_path}")
        logger.info(f"Metadata loaded: {len(metadata_list)} entries from {json_path}")
        
        return {
            "embeddings": embeddings,
            "metadata": metadata_list
        }
        
    except Exception as e:
        logger.error(f"Failed to load vector store for {file_id}: {e}")
        raise

def list_vector_stores(output_dir: str = "vector_store"):
    """
    List all available vector stores
    
    Args:
        output_dir: Directory containing vector store files
        
    Returns:
        List of available file IDs
    """
    try:
        if not os.path.exists(output_dir):
            return []
        
        file_ids = set()
        for filename in os.listdir(output_dir):
            if filename.endswith("_vectors.npy"):
                file_id = filename.replace("_vectors.npy", "")
                file_ids.add(file_id)
        
        return sorted(list(file_ids))
        
    except Exception as e:
        logger.error(f"Failed to list vector stores: {e}")
        return []

def get_vector_store_info(file_id: str, output_dir: str = "vector_store"):
    """
    Get information about a specific vector store
    
    Args:
        file_id: Unique identifier for the file
        output_dir: Directory containing vector store files
        
    Returns:
        Dictionary with vector store information
    """
    try:
        npy_path = os.path.join(output_dir, f"{file_id}_vectors.npy")
        json_path = os.path.join(output_dir, f"{file_id}_metadata.json")
        
        if not os.path.exists(npy_path) or not os.path.exists(json_path):
            return None
        
        # Get file sizes
        npy_size = os.path.getsize(npy_path)
        json_size = os.path.getsize(json_path)
        
        # Load metadata to get count
        with open(json_path, "r", encoding="utf-8") as f:
            metadata_list = json.load(f)
        
        # Load embeddings to get shape
        embeddings = np.load(npy_path)
        
        return {
            "file_id": file_id,
            "npy_path": npy_path,
            "json_path": json_path,
            "embeddings_count": len(embeddings),
            "embedding_dimension": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
            "metadata_count": len(metadata_list),
            "npy_size_bytes": npy_size,
            "json_size_bytes": json_size,
            "total_size_bytes": npy_size + json_size
        }
        
    except Exception as e:
        logger.error(f"Failed to get vector store info for {file_id}: {e}")
        return None
