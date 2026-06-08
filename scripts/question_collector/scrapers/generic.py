"""
通用页面解析器 - 处理其他平台/来源

对于没有专门解析器的平台（小红书、高校论坛、雅思口语等），
使用基础抓取逻辑提取正文。
"""

from .base import fetch_page


def scrape(url: str) -> dict:
    """
    通用页面抓取

    Returns:
        {"title": "...", "content": "...", "platform": "generic", "success": bool}
    """
    return fetch_page(url)
