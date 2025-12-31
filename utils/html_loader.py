"""
Web Page Content Loader Module
Extract web page content using trafilatura or readability-lxml
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
    Load web page content from URL and extract main text
    
    Args:
        url: Web page URL
        headers: Request headers (optional, default uses browser User-Agent)
    
    Returns:
        LangChain Document object containing:
        - page_content: Extracted main text content
        - metadata: {url, title, source, fetch_date}
    
    Raises:
        Exception: If web page loading fails or content extraction fails
    """
    # Default request headers (pretend to be a browser)
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    # Send HTTP request (with retry mechanism)
    max_retries = 3
    html_content = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=30,
                verify=True,  # Verify SSL certificate
                allow_redirects=True,
            )
            response.raise_for_status()
            html_content = response.text
            break  # Exit loop on success
        except requests.exceptions.SSLError as e:
            if attempt < max_retries - 1:
                # If this is the last attempt, try disabling SSL verification (not recommended, but as a fallback)
                if attempt == max_retries - 1:
                    try:
                        response = requests.get(
                            url, 
                            headers=headers, 
                            timeout=30,
                            verify=False,  # Disable SSL verification on last attempt
                            allow_redirects=True,
                        )
                        response.raise_for_status()
                        html_content = response.text
                        break
                    except Exception as e2:
                        raise Exception(f"Failed to load web page {url} (SSL error, retried {max_retries} times): {e2}")
                else:
                    # Wait before retrying
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
                    continue
            else:
                raise Exception(f"Failed to load web page {url} (SSL error, retried {max_retries} times): {e}")
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise Exception(f"Failed to load web page {url} (retried {max_retries} times): {e}")
    
    if html_content is None:
        raise Exception(f"Failed to load web page {url}")
    
    # Extract main text content (prefer trafilatura)
    text_content = None
    title = None
    
    # Method 1: Use trafilatura (recommended)
    if TRAFILATURA_AVAILABLE:
        try:
            # Use trafilatura to extract, configured to extract more content
            text_content = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_images=False,
                include_links=False,
            )
            if text_content:
                # trafilatura can also extract title
                metadata_dict = trafilatura.extract_metadata(html_content)
                if metadata_dict:
                    title = metadata_dict.get("title", "")
        except Exception:
            pass
    
    # Method 2: Use readability-lxml
    if not text_content and READABILITY_AVAILABLE:
        try:
            doc = ReadabilityDocument(html_content)
            text_content = doc.summary()
            title = doc.title()
        except Exception:
            pass
    
    # Method 3: Use BeautifulSoup as fallback
    if not text_content:
        try:
            soup = BeautifulSoup(html_content, "lxml")
            # Remove script and style tags
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main text (try multiple selectors)
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
                    if len(text) > 500:  # Ensure content is long enough
                        main_content = selector
                        break
            
            if main_content:
                text_content = main_content.get_text(separator="\n", strip=True)
            else:
                # If specific container not found, use body
                body = soup.find("body")
                if body:
                    text_content = body.get_text(separator="\n", strip=True)
        except Exception:
            pass
    
    if not text_content:
        raise Exception(f"Failed to extract main text content from web page {url}")
    
    # Clean text
    text_content = text_content.strip()
    
    # If title not extracted, use URL
    if not title:
        title = url.split("/")[-1] or url
    
    # Extract domain as source
    parsed_url = urlparse(url)
    source = parsed_url.netloc
    
    # Create LangChain Document
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





