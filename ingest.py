"""
数据采集与入库模块
从 urls.json 读取 URL，抓取网页，生成 LangChain Document，切分，embedding，写入 FAISS
"""
import json
import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from utils.html_loader import load_webpage
from utils.text_cleaner import clean_text
from rag.retriever import get_embeddings
from config import CHUNK_SIZE, CHUNK_OVERLAP


def load_urls_from_json(json_path: str = "./data/urls.json") -> List[Dict[str, Any]]:
    """
    从 JSON 文件加载 URL 列表
    
    Args:
        json_path: JSON 文件路径
    
    Returns:
        URL 配置列表
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"URL 配置文件不存在: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        urls = json.load(f)
    
    return urls


def check_url_domain_allowed(url: str) -> bool:
    """
    检查 URL 是否在白名单域名中
    
    Args:
        url: 要检查的 URL
    
    Returns:
        如果 URL 在白名单中返回 True，否则返回 False
    """
    allowed_domains = [
        "gov.sg",
        "hdb.gov.sg",
        "cea.gov.sg",
        "ura.gov.sg",
    ]
    
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # 检查是否匹配任何允许的域名
    for allowed in allowed_domains:
        if domain == allowed or domain.endswith("." + allowed):
            return True
    
    return False


def ingest_documents(
    urls: List[Dict[str, Any]] = None,
    chunk_size: int = None,
    chunk_overlap: int = None,
    persist_directory: str = "./data/faiss",
    index_name: str = "singapore_rental",
) -> None:
    """
    执行数据采集与入库流程
    
    Args:
        urls: URL 配置列表（如果为 None，从 urls.json 读取）
        chunk_size: 文档切分大小（如果为 None，使用 config.py 中的默认值）
        chunk_overlap: 文档切分重叠（如果为 None，使用 config.py 中的默认值）
        persist_directory: FAISS 持久化目录
        index_name: FAISS 索引名称
    """
    # 使用 config.py 中的默认值
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = CHUNK_OVERLAP
    # 加载 URL 列表
    if urls is None:
        urls = load_urls_from_json()
    
    print(f"📋 共 {len(urls)} 个 URL 待处理")
    
    # 步骤 1: 抓取网页并生成 Document
    all_documents = []
    failed_urls = []
    
    for i, url_config in enumerate(urls, 1):
        url = url_config.get("url", "")
        title = url_config.get("title", "")
        
        print(f"\n[{i}/{len(urls)}] 处理: {title}")
        print(f"   URL: {url}")
        
        # 检查域名白名单
        if not check_url_domain_allowed(url):
            print(f"   ⚠️  警告: URL 不在白名单中，跳过")
            failed_urls.append({"url": url, "reason": "域名不在白名单"})
            continue
        
        try:
            # 加载网页
            doc = load_webpage(url)
            
            # 清理文本
            cleaned_content = clean_text(doc.page_content)
            print(f"   📏 清理后内容长度: {len(cleaned_content)} 字符")
            if not cleaned_content or len(cleaned_content) < 100:
                print(f"   ⚠️  警告: 提取的内容过短，跳过")
                failed_urls.append({"url": url, "reason": "内容过短"})
                continue
            
            # 更新 metadata
            doc.metadata.update({
                "title": title or doc.metadata.get("title", ""),
                "category": url_config.get("category", ""),
            })
            doc.page_content = cleaned_content
            
            all_documents.append(doc)
            print(f"   ✅ 成功: 提取 {len(cleaned_content)} 字符")
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            failed_urls.append({"url": url, "reason": str(e)})
            # 继续处理下一个 URL，不中断整个流程
            continue
    
    if not all_documents:
        print("\n❌ 没有成功提取任何文档")
        if failed_urls:
            print("\n失败的 URL:")
            for item in failed_urls:
                print(f"  - {item['url']}: {item['reason']}")
        return
    
    print(f"\n✅ 成功提取 {len(all_documents)} 个文档")
    
    # 步骤 2: 文本切分
    print(f"\n✂️  切分文档 (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})...")
    
    # 显示每个文档的长度
    for i, doc in enumerate(all_documents, 1):
        print(f"   文档 {i} ({doc.metadata.get('title', '未知')}): {len(doc.page_content)} 字符")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    split_docs = text_splitter.split_documents(all_documents)
    print(f"✅ 切分为 {len(split_docs)} 个 chunks")
    
    # 显示每个 chunk 的长度分布
    if split_docs:
        chunk_lengths = [len(doc.page_content) for doc in split_docs]
        print(f"   Chunk 长度统计: 最小={min(chunk_lengths)}, 最大={max(chunk_lengths)}, 平均={sum(chunk_lengths)/len(chunk_lengths):.0f}")
    
    # 步骤 3: 生成 Embeddings 并写入 FAISS
    print(f"\n🔢 生成 Embeddings 并写入向量库...")
    print("   (首次运行会下载模型，请耐心等待)")
    
    embeddings = get_embeddings()
    
    # 如果向量库已存在，加载并添加新文档
    # FAISS 保存的文件是 .faiss 和 .pkl
    faiss_path = os.path.join(persist_directory, f"{index_name}.faiss")
    pkl_path = os.path.join(persist_directory, f"{index_name}.pkl")
    if os.path.exists(faiss_path) and os.path.exists(pkl_path):
        print(f"   📂 加载现有向量库: {persist_directory}")
        try:
            vectorstore = FAISS.load_local(
                persist_directory,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            # 添加新文档
            vectorstore.add_documents(split_docs)
            print(f"   ✅ 已添加 {len(split_docs)} 个新 chunks 到现有向量库")
        except Exception as e:
            print(f"   ⚠️  加载现有向量库失败，创建新向量库: {e}")
            vectorstore = FAISS.from_documents(
                documents=split_docs,
                embedding=embeddings,
            )
            print(f"   ✅ 创建新向量库，包含 {len(split_docs)} 个 chunks")
    else:
        # 创建新向量库
        vectorstore = FAISS.from_documents(
            documents=split_docs,
            embedding=embeddings,
        )
        print(f"   ✅ 创建新向量库，包含 {len(split_docs)} 个 chunks")
    
    # 持久化
    os.makedirs(persist_directory, exist_ok=True)
    vectorstore.save_local(persist_directory, index_name=index_name)
    print(f"   💾 向量库已保存到: {persist_directory}")
    
    # 统计信息
    print(f"\n📊 入库完成统计:")
    print(f"   - 成功处理: {len(all_documents)} 个文档")
    print(f"   - 生成 chunks: {len(split_docs)} 个")
    print(f"   - 失败 URL: {len(failed_urls)} 个")
    
    if failed_urls:
        print(f"\n⚠️  失败的 URL:")
        for item in failed_urls:
            print(f"   - {item['url']}: {item['reason']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据采集与入库")
    parser.add_argument(
        "--urls", 
        type=str,
        default="./data/urls.json",
        help="URL 配置文件路径",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help="文档切分大小",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=CHUNK_OVERLAP,
        help="文档切分重叠",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default="./data/faiss",
        help="FAISS 持久化目录",
    )
    
    args = parser.parse_args()
    
    # 从 JSON 文件加载 URLs
    urls = load_urls_from_json(args.urls)
    
    # 执行入库
    ingest_documents(
        urls=urls,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        persist_directory=args.persist_dir,
        index_name="singapore_rental",
    )


