"""
URL 处理工具
"""
from urllib.parse import urlparse, urlunparse
from typing import Optional


def normalize_url(url: str, default_scheme: str = "https") -> str:
    """
    规范化 URL，自动添加协议前缀
    
    Args:
        url: 原始 URL
        default_scheme: 默认协议 (http 或 https)
        
    Returns:
        规范化后的 URL
        
    Examples:
        >>> normalize_url("example.com")
        'https://example.com'
        >>> normalize_url("http://example.com")
        'http://example.com'
        >>> normalize_url("https://example.com")
        'https://example.com'
    """
    if not url:
        return url
    
    # 去除首尾空格
    url = url.strip()
    
    # 如果已经有协议，直接返回
    if url.startswith(('http://', 'https://')):
        return url
    
    # 如果以 // 开头，添加默认协议
    if url.startswith('//'):
        return f"{default_scheme}:{url}"
    
    # 否则添加完整的协议前缀
    return f"{default_scheme}://{url}"


def is_valid_url(url: str) -> bool:
    """
    检查 URL 是否有效
    
    Args:
        url: 要检查的 URL
        
    Returns:
        是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_base_url(url: str) -> str:
    """
    获取 URL 的基础部分 (scheme + netloc)
    
    Args:
        url: 完整 URL
        
    Returns:
        基础 URL
        
    Examples:
        >>> get_base_url("https://example.com/path?query=1")
        'https://example.com'
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def ensure_trailing_slash(url: str) -> str:
    """
    确保 URL 以斜杠结尾
    
    Args:
        url: 原始 URL
        
    Returns:
        处理后的 URL
    """
    if not url.endswith('/'):
        return url + '/'
    return url


def remove_trailing_slash(url: str) -> str:
    """
    移除 URL 末尾的斜杠
    
    Args:
        url: 原始 URL
        
    Returns:
        处理后的 URL
    """
    if url.endswith('/'):
        return url.rstrip('/')
    return url

