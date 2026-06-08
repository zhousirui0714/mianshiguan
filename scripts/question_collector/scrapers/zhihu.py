"""
知乎文章/回答解析器

知乎 URL 格式:
    https://zhuanlan.zhihu.com/p/xxx       (文章)
    https://www.zhihu.com/question/xxx/answer/xxx (回答)
    https://www.zhihu.com/question/xxx      (问题页)

注意：知乎对爬虫限制较严，可能返回登录页面。
"""

import re
from typing import Optional

from .base import fetch_page


def scrape(url: str) -> dict:
    """
    抓取知乎面经/复试经验页面

    Returns:
        {"title": "...", "content": "...", "platform": "zhihu", "success": bool}
    """
    result = fetch_page(url)
    if not result["success"]:
        return result

    # 知乎返回的内容可能包含登录遮挡
    # 检查是否被重定向到登录页
    if "登录" in result["content"][:500] and len(result["content"]) < 2000:
        # 尝试使用不同的 User-Agent 重试
        pass

    # 清理内容
    content = result["content"]

    # 知乎内容通常包含大量元信息，尝试提取正文
    lines = content.split("\n")

    # 过滤掉太短的行和明显不是正文的行
    filtered = []
    for line in lines:
        if len(line) < 10:
            continue
        if any(kw in line for kw in [
            "赞同", "评论", "分享", "收藏", "感谢", "举报",
            "关注", "发布于", "编辑于", "阅读", "转发",
            "非法请求", "验证",
        ]):
            continue
        filtered.append(line)

    result["content"] = "\n".join(filtered)
    return result
