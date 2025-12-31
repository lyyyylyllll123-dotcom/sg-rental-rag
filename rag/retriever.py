"""
RAG Retriever 模块
负责从向量库中检索相关文档
"""
import os
import traceback
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document


def get_embeddings(model_name: Optional[str] = None) -> HuggingFaceEmbeddings:
    """
    获取 Embedding 模型实例
    
    Args:
        model_name: Embedding 模型名称（默认使用多语言模型）
    
    Returns:
        HuggingFaceEmbeddings 实例
    """
    if model_name is None:
        # 默认使用多语言模型，支持中英文
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    return embeddings


def load_vectorstore(
    persist_directory: str = "./data/faiss",
    index_name: str = "singapore_rental",
    embeddings: Optional[HuggingFaceEmbeddings] = None,
) -> Optional[FAISS]:
    """
    加载已存在的向量库
    
    Args:
        persist_directory: 向量库持久化目录
        index_name: 索引名称（FAISS 使用文件名）
        embeddings: Embedding 模型实例（如果为 None，将创建默认实例）
    
    Returns:
        FAISS 向量库实例，如果不存在则返回 None
    """
    # FAISS 保存的文件是 .faiss 和 .pkl
    faiss_path = os.path.join(persist_directory, f"{index_name}.faiss")
    pkl_path = os.path.join(persist_directory, f"{index_name}.pkl")
    
    if not os.path.exists(faiss_path) or not os.path.exists(pkl_path):
        return None
    
    if embeddings is None:
        embeddings = get_embeddings()
    
    try:
        # FAISS.load_local 需要指定 index_name
        vectorstore = FAISS.load_local(
            persist_directory,
            embeddings,
            allow_dangerous_deserialization=True,
            index_name=index_name,
        )
        # 检查向量库是否为空
        if vectorstore.index.ntotal == 0:
            return None
        return vectorstore
    except Exception as e:
        # 打印错误信息以便调试
        print(f"加载向量库失败: {e}")
        print(traceback.format_exc())
        return None


def create_retriever(
    vectorstore: FAISS,
    k: int = 6,
    search_type: str = "similarity",
) -> BaseRetriever:
    """
    创建检索器
    
    Args:
        vectorstore: FAISS 向量库实例
        k: 检索的文档数量（top-k）
        search_type: 检索类型（"similarity" 或 "mmr"）
    
    Returns:
        BaseRetriever 实例
    """
    search_kwargs = {"k": k}
    
    if search_type == "mmr":
        # MMR (Maximum Marginal Relevance) 检索，平衡相关性和多样性
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": k * 2},
        )
    else:
        # 相似度检索
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )
    
    return retriever


