"""
Offline Search Module
Provides similarity-based search through chat history when internet is unavailable.
"""
import json
from typing import List, Dict, Optional
from chat_storage import get_all_chats
import numpy as np

# Load the sentence transformer model (will be cached after first load)
_model = None

def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Using a lightweight model that's already likely installed
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise ImportError("sentence-transformers package is required for semantic search. Install it with: pip install sentence-transformers")
    return _model

def find_similar_chats(query: str, top_k: int = 3, similarity_threshold: float = 0.3) -> List[Dict]:
    """
    Find similar chat interactions using semantic similarity.
    
    Args:
        query: User's query to search for
        top_k: Number of similar results to return
        similarity_threshold: Minimum similarity score (0-1) to consider a match
    
    Returns:
        List of similar chat interactions with similarity scores
    """
    try:
        model = get_model()
        
        # Get all chat history
        all_chats = get_all_chats()
        
        if not all_chats:
            return []
        
        # Extract queries from chat history
        stored_queries = [chat['user_query'] for chat in all_chats]
        
        # Encode the user query and stored queries
        query_embedding = model.encode([query], convert_to_numpy=True)
        stored_embeddings = model.encode(stored_queries, convert_to_numpy=True)
        
        # Calculate cosine similarity
        # Normalize embeddings for cosine similarity
        from numpy.linalg import norm
        query_norm = norm(query_embedding, axis=1, keepdims=True)
        stored_norm = norm(stored_embeddings, axis=1, keepdims=True)
        
        # Avoid division by zero
        query_embedding = query_embedding / (query_norm + 1e-8)
        stored_embeddings = stored_embeddings / (stored_norm + 1e-8)
        
        similarities = np.dot(stored_embeddings, query_embedding.T).flatten()
        
        # Get top-k similar results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity_score = float(similarities[idx])
            if similarity_score >= similarity_threshold:
                chat = all_chats[idx].copy()
                chat['similarity_score'] = similarity_score
                results.append(chat)
        
        return results
    
    except ImportError:
        # Sentence transformers not available, use fallback
        print("Sentence transformers not available, using fallback text search.")
        return fallback_text_search(query, top_k)
    except Exception as e:
        print(f"Error in semantic search: {e}")
        # Fallback to simple text matching
        return fallback_text_search(query, top_k)

def fallback_text_search(query: str, top_k: int = 3) -> List[Dict]:
    """
    Fallback search using simple keyword matching.
    """
    from chat_storage import search_chats_by_query
    
    # Extract key terms from query
    query_terms = query.lower().split()
    
    all_chats = get_all_chats()
    scored_chats = []
    
    for chat in all_chats:
        chat_query_lower = chat['user_query'].lower()
        # Count how many query terms appear in the stored query
        matches = sum(1 for term in query_terms if term in chat_query_lower)
        if matches > 0:
            score = matches / len(query_terms)  # Normalize by query length
            chat_copy = chat.copy()
            chat_copy['similarity_score'] = score
            scored_chats.append(chat_copy)
    
    # Sort by score and return top-k
    scored_chats.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_chats[:top_k]

def get_best_match_response(query: str) -> Optional[str]:
    """
    Get the best matching response from chat history.
    Returns the assistant response from the most similar chat.
    """
    similar_chats = find_similar_chats(query, top_k=1)
    
    if similar_chats and similar_chats[0]['similarity_score'] >= 0.3:
        return similar_chats[0]['assistant_response']
    
    return None

def format_offline_response(similar_chats: List[Dict], user_query: str) -> str:
    """
    Format a response when offline using similar chat history.
    """
    if not similar_chats:
        return (
            "I'm currently offline and couldn't find any similar questions in your chat history. "
            "Please check your internet connection to get real-time answers."
        )
    
    best_match = similar_chats[0]
    similarity = best_match['similarity_score']
    
    response = "**⚠️ Offline Mode**\n\n"
    
    if similarity >= 0.7:
        response += "I found a very similar question in your chat history. Here's what I answered before:\n\n"
    elif similarity >= 0.5:
        response += "I found a related question in your chat history. Here's a similar answer:\n\n"
    else:
        response += "I found a somewhat related question in your chat history. This might help:\n\n"
    
    response += f"**Previous Question:** {best_match['user_query']}\n\n"
    response += f"**Previous Answer:**\n{best_match['assistant_response']}\n\n"
    
    response += "---\n"
    response += "*Note: This is from your chat history. For the most current information, please check your internet connection.*"
    
    # If there are more similar results, mention them
    if len(similar_chats) > 1:
        response += f"\n\n*I also found {len(similar_chats) - 1} other related conversation(s) in your history.*"
    
    return response

