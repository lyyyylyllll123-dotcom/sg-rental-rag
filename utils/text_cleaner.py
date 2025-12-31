"""
Text Cleaning Utility Module
Used to clean and normalize text extracted from web pages
"""
import re


def clean_text(text: str) -> str:
    """
    Clean text content
    
    Args:
        text: Original text
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace (but keep line breaks as they may contain important structure)
    # First normalize line breaks
    text = re.sub(r'\r\n', '\n', text)  # Windows line break
    text = re.sub(r'\r', '\n', text)     # Mac line break
    
    # Remove excessive consecutive spaces (but keep single spaces and line breaks)
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs become single space
    
    # Remove excessive line breaks (keep paragraph separators)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading and trailing whitespace from lines
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # Remove leading and trailing whitespace
    text = text.strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace characters
    
    Args:
        text: Original text
    
    Returns:
        Normalized text
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple line breaks with at most two line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

