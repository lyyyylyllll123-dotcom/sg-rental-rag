"""
RAG Chain Module
Build and run RAG Q&A chain
"""
import time
from typing import Dict, List, Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from rag.prompt import get_rag_prompt
from rag.retriever import create_retriever
from rag.reranker import get_reranker
from config import INITIAL_RETRIEVAL_K, FINAL_RETRIEVAL_K


def build_rag_chain(
    llm: BaseChatModel,
    retriever: BaseRetriever,
) -> callable:
    """
    Build RAG Q&A chain (using LangChain LCEL)
    
    Args:
        llm: LangChain ChatModel instance
        retriever: Retriever instance
    
    Returns:
        Callable RAG chain function that accepts {"question": str} and returns answer
    """
    # Get Prompt template
    prompt = get_rag_prompt()
    
    # Format retrieved documents
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Build chain using LangChain LCEL (LangChain Expression Language)
    # Note: Need to properly handle input format
    def create_rag_input(input_dict):
        """Process input, ensure correct format"""
        question = input_dict.get("question", input_dict.get("input", ""))
        
        # Step 1: Initial retrieval (get more candidate documents)
        initial_docs = retriever.invoke(question)
        
        # Step 2: Rerank (select most relevant documents)
        reranker = get_reranker()
        reranked_docs = reranker.rerank(question, initial_docs, top_k=FINAL_RETRIEVAL_K)
        
        # Step 3: Format context
        context = format_docs(reranked_docs)
        return {
            "context": context,
            "question": question
        }
    
    rag_chain = (
        RunnablePassthrough() | create_rag_input
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain


def run_rag_query(
    question: str,
    llm: BaseChatModel,
    retriever: BaseRetriever,
) -> Dict[str, Any]:
    """
    Run RAG query
    
    Args:
        question: User question
        llm: LangChain ChatModel instance
        retriever: Retriever instance
    
    Returns:
        Dictionary containing the following fields:
        {
            "answer": str,  # LLM generated answer
            "citations": [  # Citation source list
                {
                    "title": str,
                    "url": str,
                    "snippet": str,  # Relevant text snippet
                }
            ]
        }
    """
    # PERFORM RETRIEVAL AND RERANKING ONLY ONCE (performance optimization)
    start_time = time.time()
    
    # Step 1: Initial retrieval (get more candidate documents)
    retrieval_start = time.time()
    initial_docs = retriever.invoke(question)
    retrieval_time = time.time() - retrieval_start
    print(f"[Performance] Retrieval took {retrieval_time:.2f}s, retrieved {len(initial_docs)} docs")
    
    # Step 2: Rerank (select most relevant documents)
    rerank_start = time.time()
    reranker = get_reranker()
    retrieved_docs = reranker.rerank(question, initial_docs, top_k=FINAL_RETRIEVAL_K)
    rerank_time = time.time() - rerank_start
    print(f"[Performance] Reranking took {rerank_time:.2f}s, selected {len(retrieved_docs)} docs")
    
    # Step 3: Format context for LLM
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    context = format_docs(retrieved_docs)
    
    # Step 4: Build prompt and execute LLM query
    prompt = get_rag_prompt()
    
    try:
        # Format prompt with context and question
        llm_start = time.time()
        formatted_prompt = prompt.format_messages(context=context, question=question)
        # Invoke LLM
        response = llm.invoke(formatted_prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        llm_time = time.time() - llm_start
        print(f"[Performance] LLM generation took {llm_time:.2f}s")
    except Exception as e:
        # If LLM execution fails, return error message
        answer = f"Error generating answer: {e}"
        retrieved_docs = []
    
    total_time = time.time() - start_time
    print(f"[Performance] Total query time: {total_time:.2f}s")
    
    # Step 5: Build citations from retrieved documents
    citations = []
    for doc in retrieved_docs:
        if isinstance(doc, Document):
            metadata = doc.metadata
            citations.append({
                "title": metadata.get("title", "Unknown Title"),
                "url": metadata.get("url", ""),
                "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            })
    
    # If no documents are retrieved, return a prompt
    if not citations:
        answer = "The knowledge base does not cover this question. Please consult official agencies (HDB, CEA, or URA)."
    # If documents are retrieved but answer is empty or still says "not covered", check if it's LLM's judgment
    elif not answer or "knowledge base does not cover" in answer.lower() or "not covered" in answer.lower():
        # Even if LLM judges it's not covered, still show retrieved documents as reference
        pass  # Keep original answer but show citations
    
    return {
        "answer": answer,
        "citations": citations,
    }

