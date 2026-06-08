"""
CSDN 博客面经解析器

CSDN 面经 URL 格式:
    https://blog.csdn.net/xxx/article/details/xxx

CSDN 页面通常可以直接抓取，内容较完整。
"""

import re
from typing import Optional

from .base import fetch_page


def scrape(url: str) -> dict:
    """
    抓取 CSDN 面经博客

    Returns:
        {"title": "...", "content": "...", "platform": "csdn", "success": bool}
    """
    result = fetch_page(url)
    if not result["success"]:
        return result

    # CSDN 页面正文通常在 article 标签或 #article_content 中
    # bs4 已经提取了 body 文本
    content = result["content"]

    # 清理 CSDN 特有的干扰内容
    lines = content.split("\n")
    filtered = []
    skip_patterns = [
        "CSDN", "版权声明", "本文为", "博主", "原创",
        "点赞", "收藏", "评论", "关注", "订阅",
        "专栏", "下载", "资源", "VIP", "会员",
        "广告", "推广", "赞助",
    ]

    for line in lines:
        if len(line) < 15:
            continue
        # 跳过包含干扰词的行
        skip = False
        for pat in skip_patterns:
            if pat in line and len(line) < 60:
                skip = True
                break
        if skip:
            continue
        filtered.append(line)

    result["content"] = "\n".join(filtered)
    return result
