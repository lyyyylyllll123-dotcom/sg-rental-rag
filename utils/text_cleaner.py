"""
文本清理工具模块
用于清理和规范化从网页提取的文本
"""
import re


def clean_text(text: str) -> str:
    """
    清理文本内容
    
    Args:
        text: 原始文本
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符（但保留换行，因为可能包含重要结构）
    # 先规范化换行
    text = re.sub(r'\r\n', '\n', text)  # Windows 换行
    text = re.sub(r'\r', '\n', text)     # Mac 换行
    
    # 移除多余的连续空格（但保留单个空格和换行）
    text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符变为单个空格
    
    # 移除多余的换行符（保留段落分隔）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 移除行首行尾的空白
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # 移除首尾空白
    text = text.strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    规范化空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        规范化后的文本
    """
    # 将多个空格替换为单个空格
    text = re.sub(r' +', ' ', text)
    
    # 将多个换行符替换为最多两个换行符
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

