"""
RAG Retriever Module
Responsible for retrieving relevant documents from vector store
"""
import os
import traceback
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document


# Global singleton for embeddings to avoid reloading
_embeddings_instance = None
_embeddings_model_name = None

def get_embeddings(model_name: Optional[str] = None) -> HuggingFaceEmbeddings:
    """
    Get Embedding model instance (cached singleton)
    
    Args:
        model_name: Embedding model name (default uses multilingual model)
    
    Returns:
        HuggingFaceEmbeddings instance
    """
    global _embeddings_instance, _embeddings_model_name
    
    if model_name is None:
        # Default to multilingual model, supports Chinese and English
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Return cached instance if model name matches
    if _embeddings_instance is not None and _embeddings_model_name == model_name:
        return _embeddings_instance
    
    # Create new instance and cache it
    _embeddings_instance = HuggingFaceEmbeddings(model_name=model_name)
    _embeddings_model_name = model_name
    return _embeddings_instance


def load_vectorstore(
    persist_directory: str = "./data/faiss",
    index_name: str = "singapore_rental",
    embeddings: Optional[HuggingFaceEmbeddings] = None,
) -> Optional[FAISS]:
    """
    Load existing vector store
    
    Args:
        persist_directory: Vector store persistence directory
        index_name: Index name (FAISS uses file name)
        embeddings: Embedding model instance (if None, will create default instance)
    
    Returns:
        FAISS vector store instance, returns None if it doesn't exist
    """
    # FAISS saves files as .faiss and .pkl
    faiss_path = os.path.join(persist_directory, f"{index_name}.faiss")
    pkl_path = os.path.join(persist_directory, f"{index_name}.pkl")
    
    if not os.path.exists(faiss_path) or not os.path.exists(pkl_path):
        missing_files = []
        if not os.path.exists(faiss_path):
            missing_files.append(faiss_path)
        if not os.path.exists(pkl_path):
            missing_files.append(pkl_path)
        print(f"FAISS files not found: {missing_files}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking in: {persist_directory}")
        return None
    
    if embeddings is None:
        embeddings = get_embeddings()
    
    try:
        # FAISS.load_local requires index_name to be specified
        vectorstore = FAISS.load_local(
            persist_directory,
            embeddings,
            allow_dangerous_deserialization=True,
            index_name=index_name,
        )
        # Check if vector store is empty
        if vectorstore.index.ntotal == 0:
            return None
        return vectorstore
    except Exception as e:
        # Print error message for debugging
        print(f"Failed to load vector store: {e}")
        print(traceback.format_exc())
        return None


def create_retriever(
    vectorstore: FAISS,
    k: int = 6,
    search_type: str = "similarity",
) -> BaseRetriever:
    """
    Create retriever
    
    Args:
        vectorstore: FAISS vector store instance
        k: Number of documents to retrieve (top-k)
        search_type: Retrieval type ("similarity" or "mmr")
    
    Returns:
        BaseRetriever instance
    """
    search_kwargs = {"k": k}
    
    if search_type == "mmr":
        # MMR (Maximum Marginal Relevance) retrieval, balances relevance and diversity
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": k * 2},
        )
    else:
        # Similarity retrieval
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )
    
    return retriever


