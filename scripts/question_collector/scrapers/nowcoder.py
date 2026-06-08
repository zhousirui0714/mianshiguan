"""
牛客网面经解析器

牛客网面经 URL 格式:
    https://www.nowcoder.com/feed/main/detail/xxx
    https://www.nowcoder.com/discuss/xxx

注意：牛客网部分内容需要登录。这里尝试直接抓取公开内容。
"""

import re
from typing import Optional

from .base import fetch_page


def scrape(url: str) -> dict:
    """
    抓取牛客网面经页面

    Returns:
        {"title": "...", "content": "...", "platform": "nowcoder", "success": bool}
    """
    result = fetch_page(url)
    if not result["success"]:
        return result

    # 牛客网特殊处理
    content = result["content"]

    # 尝试提取面经正文（通常在 feed-detail 等容器中）
    # 查找常见面经关键词开头
    keywords = [
        "面经", "一面", "二面", "三面", "面试", "面试题",
        "自我介绍", "项目", "算法题",
    ]

    # 截取有效内容：从第一个面经关键词开始
    lines = content.split("\n")
    start_idx = 0
    for i, line in enumerate(lines):
        if any(kw in line for kw in keywords):
            start_idx = max(0, i - 2)
            break

    # 截取到 "分享"、"收藏"、"举报" 等结尾标记
    end_idx = len(lines)
    for i in range(len(lines) - 1, start_idx, -1):
        if any(kw in lines[i] for kw in ["收藏", "举报", "分享", "评论", "回复"]):
            if len(lines) - i < 20:  # 只在靠近末尾时截断
                end_idx = i
                break

    result["content"] = "\n".join(lines[start_idx:end_idx])
    return result
