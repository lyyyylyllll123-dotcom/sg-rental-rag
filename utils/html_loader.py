"""
网页内容加载模块
使用 trafilatura 或 readability-lxml 提取网页正文
"""
import requests
from typing import Optional, Dict
from langchain_core.documents import Document
from datetime import datetime
from urllib.parse import urlparse

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

try:
    from readability import Document as ReadabilityDocument
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

from bs4 import BeautifulSoup


def load_webpage(url: str, headers: Optional[Dict[str, str]] = None) -> Document:
    """
    从 URL 加载网页内容并提取正文
    
    Args:
        url: 网页 URL
        headers: 请求头（可选，默认使用浏览器 User-Agent）
    
    Returns:
        LangChain Document 对象，包含：
        - page_content: 提取的正文内容
        - metadata: {url, title, source, fetch_date}
    
    Raises:
        Exception: 如果网页加载失败或内容提取失败
    """
    # 默认请求头（伪装成浏览器）
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    # 发送 HTTP 请求（带重试机制）
    max_retries = 3
    html_content = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=30,
                verify=True,  # 验证 SSL 证书
                allow_redirects=True,
            )
            response.raise_for_status()
            html_content = response.text
            break  # 成功则退出循环
        except requests.exceptions.SSLError as e:
            if attempt < max_retries - 1:
                # 如果是最后一次尝试，尝试禁用 SSL 验证（不推荐，但作为备选）
                if attempt == max_retries - 1:
                    try:
                        response = requests.get(
                            url, 
                            headers=headers, 
                            timeout=30,
                            verify=False,  # 最后一次尝试时禁用 SSL 验证
                            allow_redirects=True,
                        )
                        response.raise_for_status()
                        html_content = response.text
                        break
                    except Exception as e2:
                        raise Exception(f"无法加载网页 {url} (SSL 错误，已重试 {max_retries} 次): {e2}")
                else:
                    # 等待后重试
                    import time
                    time.sleep(2 ** attempt)  # 指数退避：2秒、4秒
                    continue
            else:
                raise Exception(f"无法加载网页 {url} (SSL 错误，已重试 {max_retries} 次): {e}")
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                raise Exception(f"无法加载网页 {url} (已重试 {max_retries} 次): {e}")
    
    if html_content is None:
        raise Exception(f"无法加载网页 {url}")
    
    # 提取正文内容（优先使用 trafilatura）
    text_content = None
    title = None
    
    # 方法 1: 使用 trafilatura（推荐）
    if TRAFILATURA_AVAILABLE:
        try:
            # 使用 trafilatura 提取，配置为提取更多内容
            text_content = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_images=False,
                include_links=False,
            )
            if text_content:
                # trafilatura 也可以提取标题
                metadata_dict = trafilatura.extract_metadata(html_content)
                if metadata_dict:
                    title = metadata_dict.get("title", "")
        except Exception:
            pass
    
    # 方法 2: 使用 readability-lxml
    if not text_content and READABILITY_AVAILABLE:
        try:
            doc = ReadabilityDocument(html_content)
            text_content = doc.summary()
            title = doc.title()
        except Exception:
            pass
    
    # 方法 3: 使用 BeautifulSoup 作为后备
    if not text_content:
        try:
            soup = BeautifulSoup(html_content, "lxml")
            # 移除 script 和 style 标签
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # 提取标题
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()
            
            # 提取正文（尝试多种选择器）
            main_content = None
            selectors = [
                soup.find("main"),
                soup.find("article"),
                soup.find("div", class_="content"),
                soup.find("div", class_="main-content"),
                soup.find("div", id="content"),
            ]
            
            for selector in selectors:
                if selector:
                    text = selector.get_text(separator="\n", strip=True)
                    if len(text) > 500:  # 确保内容足够长
                        main_content = selector
                        break
            
            if main_content:
                text_content = main_content.get_text(separator="\n", strip=True)
            else:
                # 如果找不到特定容器，使用 body
                body = soup.find("body")
                if body:
                    text_content = body.get_text(separator="\n", strip=True)
        except Exception:
            pass
    
    if not text_content:
        raise Exception(f"无法从网页 {url} 提取正文内容")
    
    # 清理文本
    text_content = text_content.strip()
    
    # 如果没有提取到标题，使用 URL
    if not title:
        title = url.split("/")[-1] or url
    
    # 提取域名作为 source
    parsed_url = urlparse(url)
    source = parsed_url.netloc
    
    # 创建 LangChain Document
    doc = Document(
        page_content=text_content,
        metadata={
            "url": url,
            "title": title,
            "source": source,
            "fetch_date": datetime.now().isoformat(),
        }
    )
    
    return doc





