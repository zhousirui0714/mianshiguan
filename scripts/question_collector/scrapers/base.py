"""
基础爬虫 - 通用页面抓取器

使用 subprocess + curl 进行 HTTPS 请求以解决 Windows OpenSSL 兼容性问题。
"""

import time
import subprocess
import re
from typing import Optional

from bs4 import BeautifulSoup

from ..config import SCRAPER_CONFIG


# ================================================================
# HTTP 工具函数
# ================================================================

def http_get(url: str, timeout: int = 20) -> Optional[str]:
    """
    通过 curl 执行 HTTP GET 请求

    curl 使用系统 SSL（Schannel），在 Windows 下更可靠。

    Returns:
        HTML 文本，或 None（失败时）
    """
    cmd = [
        "curl", "-s", "-L",
        "--max-time", str(timeout),
        "-H", f"User-Agent: {SCRAPER_CONFIG['user_agent']}",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 5,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")
        else:
            return None
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


# ================================================================
# 页面抓取
# ================================================================

def fetch_page(
    url: str,
    timeout: Optional[int] = None,
    delay: Optional[float] = None,
) -> dict:
    """
    通用页面抓取

    Args:
        url: 目标 URL
        timeout: 超时秒数
        delay: 请求前延迟

    Returns:
        {"title": "...", "content": "...", "html": "...",
         "platform": "...", "success": bool, "error": ""}
    """
    if timeout is None:
        timeout = SCRAPER_CONFIG["request_timeout"]
    if delay is None:
        delay = SCRAPER_CONFIG["request_delay"]

    # 请求前延时
    if delay > 0:
        time.sleep(delay)

    result = {
        "title": "",
        "content": "",
        "html": "",
        "platform": _detect_platform(url),
        "url": url,
        "success": False,
        "error": "",
    }

    html = http_get(url, timeout)

    # 如果 curl 内容不足，尝试 Playwright 渲染
    if html is None or len(html) < 300:
        from .playwright_scraper import fetch_with_fallback
        fallback = fetch_with_fallback(url, curl_html=html)
        html = fallback.get("html", "")
        if fallback["source"] == "failed":
            result["error"] = "请求失败 (curl + playwright)"
            return result

    if not html:
        result["error"] = "请求失败 (empty response)"
        return result

    result["html"] = html
    soup = BeautifulSoup(html, "html.parser")

    # 提取标题
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else ""

    # 移除无用标签
    for tag in soup(["script", "style", "nav", "footer", "header",
                      "aside", "noscript", "iframe", "svg", "form",
                      "button", "select", "input", "textarea"]):
        tag.decompose()

    # 提取正文
    body = soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        result["content"] = "\n".join(lines)

    result["success"] = True
    return result


def _detect_platform(url: str) -> str:
    """检测 URL 所属平台"""
    url_lower = url.lower()
    if "nowcoder.com" in url_lower:
        return "nowcoder"
    elif "zhihu.com" in url_lower:
        return "zhihu"
    elif "blog.csdn.net" in url_lower:
        return "csdn"
    elif "xiaohongshu.com" in url_lower:
        return "xiaohongshu"
    elif "kaoyan" in url_lower or "yanzhao" in url_lower:
        return "gaoxiao"
    else:
        return "generic"


def extract_text_content(html: str, min_paragraph_length: int = 20) -> str:
    """从 HTML 中提取纯文本"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header",
                      "aside", "noscript", "iframe"]):
        tag.decompose()

    paragraphs = []
    for tag in soup.find_all(["p", "div", "section", "article", "li",
                               "h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if len(text) >= min_paragraph_length:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)
