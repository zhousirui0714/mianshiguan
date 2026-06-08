"""
Playwright 爬虫 - 处理 JS 渲染的页面

用于 知乎、牛客网、小红书 等需要 JavaScript 渲染的网站。
作为 curl 的补充，当 curl 无法获取足够内容时自动启用。
"""

import time
from typing import Optional

from ..config import SCRAPER_CONFIG


def fetch_page_playwright(
    url: str,
    timeout: int = 30,
    wait_selector: Optional[str] = None,
    scroll: bool = True,
) -> Optional[str]:
    """
    使用 Playwright 渲染并获取页面 HTML

    Args:
        url: 目标 URL
        timeout: 超时秒数
        wait_selector: 等待指定 CSS 选择器出现
        scroll: 是否滚动页面以触发懒加载

    Returns:
        HTML 文本，或 None
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = context.new_page()

            # 设置超时
            page.set_default_timeout(timeout * 1000)

            # 访问页面
            page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)

            # 等待特定选择器
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=10000)
                except Exception:
                    pass  # 超时后继续

            # 滚动页面
            if scroll:
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 800)")
                    time.sleep(0.5)

            # 额外等待动态内容加载
            time.sleep(2)

            html = page.content()
            browser.close()
            return html

    except Exception:
        return None


def fetch_with_fallback(url: str, curl_html: Optional[str] = None) -> dict:
    """
    智能抓取：先用 curl，如果内容不足则使用 Playwright

    Args:
        url: 目标 URL
        curl_html: curl 已获取的 HTML（可选）

    Returns:
        {"html": "...", "source": "curl" | "playwright" | "failed"}
    """
    MIN_CONTENT_LENGTH = 500

    if curl_html and len(curl_html) > MIN_CONTENT_LENGTH:
        return {"html": curl_html, "source": "curl"}

    # 尝试 Playwright
    print(f"    curl 内容不足 ({len(curl_html or '')} chars)，尝试 Playwright...")
    pw_html = fetch_page_playwright(url)
    if pw_html and len(pw_html) > MIN_CONTENT_LENGTH:
        return {"html": pw_html, "source": "playwright"}

    # 返回最好的结果
    if curl_html:
        return {"html": curl_html, "source": "curl"}
    return {"html": "", "source": "failed"}
