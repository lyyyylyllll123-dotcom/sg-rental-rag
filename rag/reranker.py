"""
重排序模块
使用 CrossEncoder 对检索结果进行重新排序
"""
from typing import List
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


class DocumentReranker:
    """文档重排序器"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        初始化重排序模型
        
        Args:
            model_name: CrossEncoder 模型名称
        """
        self.reranker = CrossEncoder(model_name)
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 8
    ) -> List[Document]:
        """
        对文档进行重排序
        
        Args:
            query: 用户问题
            documents: 检索到的文档列表
            top_k: 返回前 k 个文档
        
        Returns:
            重排序后的文档列表（按相关性从高到低）
        """
        if not documents:
            return []
        
        # 限制文档长度，避免过长导致计算慢
        pairs = [[query, doc.page_content[:500]] for doc in documents]
        
        # 计算相关性分数
        scores = self.reranker.predict(pairs)
        
        # 按分数排序（从高到低）
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 返回 top_k
        return [doc for doc, score in scored_docs[:top_k]]


# 全局单例，避免重复加载模型
_reranker_instance = None


def get_reranker() -> DocumentReranker:
    """获取重排序器单例"""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = DocumentReranker()
    return _reranker_instance






