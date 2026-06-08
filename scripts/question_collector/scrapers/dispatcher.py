"""
爬虫调度器 - 根据 URL 自动选择对应解析器
"""

from typing import Optional

from . import base, nowcoder, zhihu, csdn, generic


def scrape_url(url: str) -> dict:
    """
    自动检测平台并抓取页面

    Args:
        url: 页面 URL

    Returns:
        {"title": "...", "content": "...", "platform": "...", "url": "...",
         "success": bool, "error": "..."}
    """
    platform = base._detect_platform(url)

    scrapers = {
        "nowcoder": nowcoder,
        "zhihu": zhihu,
        "csdn": csdn,
    }

    scraper = scrapers.get(platform, generic)

    try:
        result = scraper.scrape(url)
        result["url"] = url
        result["platform"] = platform
        return result
    except Exception as e:
        return {
            "title": "",
            "content": "",
            "platform": platform,
            "url": url,
            "success": False,
            "error": str(e),
        }
