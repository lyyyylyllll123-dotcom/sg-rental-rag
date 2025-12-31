"""
Reranking Module
Rerank retrieval results using CrossEncoder
"""
from typing import List
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


class DocumentReranker:
    """Document reranker"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranking model
        
        Args:
            model_name: CrossEncoder model name
        """
        self.reranker = CrossEncoder(model_name)
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 8
    ) -> List[Document]:
        """
        Rerank documents
        
        Args:
            query: User question
            documents: Retrieved document list
            top_k: Return top k documents
        
        Returns:
            Reranked document list (sorted by relevance from high to low)
        """
        if not documents:
            return []
        
        # Limit document length to avoid slow computation due to excessive length
        pairs = [[query, doc.page_content[:500]] for doc in documents]
        
        # Calculate relevance scores
        scores = self.reranker.predict(pairs)
        
        # Sort by score (from high to low)
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k
        return [doc for doc, score in scored_docs[:top_k]]


# Global singleton to avoid reloading model
_reranker_instance = None


def get_reranker() -> DocumentReranker:
    """Get reranker singleton"""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = DocumentReranker()
    return _reranker_instance






