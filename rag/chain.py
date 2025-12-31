"""
RAG Chain 模块
构建和运行 RAG 问答链
"""
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
    构建 RAG 问答链（使用 LangChain LCEL 方式）
    
    Args:
        llm: LangChain ChatModel 实例
        retriever: 检索器实例
    
    Returns:
        可调用的 RAG 链函数，接受 {"question": str} 并返回回答
    """
    # 获取 Prompt 模板
    prompt = get_rag_prompt()
    
    # 格式化检索到的文档
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # 使用 LangChain LCEL (LangChain Expression Language) 构建链
    # 注意：需要正确处理输入格式
    def create_rag_input(input_dict):
        """处理输入，确保格式正确"""
        question = input_dict.get("question", input_dict.get("input", ""))
        
        # 第一步：初始检索（取更多候选文档）
        initial_docs = retriever.invoke(question)
        
        # 第二步：重排序（选择最相关的文档）
        reranker = get_reranker()
        reranked_docs = reranker.rerank(question, initial_docs, top_k=FINAL_RETRIEVAL_K)
        
        # 第三步：格式化上下文
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
    运行 RAG 查询
    
    Args:
        question: 用户问题
        llm: LangChain ChatModel 实例
        retriever: 检索器实例
    
    Returns:
        包含以下字段的字典：
        {
            "answer": str,  # LLM 生成的回答
            "citations": [  # 引用来源列表
                {
                    "title": str,
                    "url": str,
                    "snippet": str,  # 相关文本片段
                }
            ]
        }
    """
    # 构建 RAG 链
    rag_chain = build_rag_chain(llm, retriever)
    
    # 先检索文档（用于引用）
    # 使用相同的重排序逻辑，确保引用和回答使用相同的文档
    initial_docs = retriever.invoke(question)
    reranker = get_reranker()
    retrieved_docs = reranker.rerank(question, initial_docs, top_k=FINAL_RETRIEVAL_K)
    
    # Execute query
    try:
        answer = rag_chain.invoke({"question": question})
    except Exception as e:
        # If RAG chain execution fails, return error message
        answer = f"Error generating answer: {e}"
        retrieved_docs = []
    
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

