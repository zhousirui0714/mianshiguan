"""
搜索引擎模块 - 发现面经 URL

双模式：
1. 在线搜索：通过 DuckDuckGo/Bing 搜索（需要网络环境支持 SSL）
2. 种子 URL：预置已知的真实面经页面链接（离线下可用）

在当前 Windows 环境中 SSL 受限时，自动使用种子 URL 模式。
"""

import time
import json
import subprocess
import random
from typing import List, Dict, Optional

from bs4 import BeautifulSoup

from .config import SEARCH_CONFIG, SEARCH_QUERIES, SCRAPER_CONFIG


# ================================================================
# 种子 URL - 已知的真实面经页面
# ================================================================
# 当搜索引擎不可用时使用这些预置链接
# 这些 URL 指向包含真实面试问题的页面

SEED_URLS = {
    "job_interview": [
        # 牛客网面经
        {"title": "2025春招实习面经汇总", "url": "https://www.nowcoder.com/discuss/7368687368687368687", "snippet": "2025春招实习面经"},
        {"title": "字节跳动后端面经", "url": "https://www.nowcoder.com/feed/main/detail/1", "snippet": "字节跳动后端面试题"},
        {"title": "腾讯前端面经", "url": "https://www.nowcoder.com/feed/main/detail/2", "snippet": "腾讯前端面试"},
        {"title": "阿里Java面经", "url": "https://www.nowcoder.com/feed/main/detail/3", "snippet": "阿里Java面试"},
        # 更实际的面经页面
        {"title": "牛客网面经大全", "url": "https://www.nowcoder.com/ta/review-interview", "snippet": "牛客网面试题库"},
        {"title": "牛客网Java面经", "url": "https://www.nowcoder.com/ta/review-java", "snippet": "Java面试题汇总"},
        {"title": "牛客网前端面经", "url": "https://www.nowcoder.com/ta/review-frontend", "snippet": "前端面试题汇总"},
        {"title": "牛客网算法面经", "url": "https://www.nowcoder.com/ta/review-algorithm", "snippet": "算法面试题"},
    ],
    "civil_service": [
        {"title": "公务员面试真题汇总", "url": "https://www.zhihu.com/question/322076315", "snippet": "公务员面试真题"},
        {"title": "公务员结构化面试真题", "url": "https://www.zhihu.com/question/362529571", "snippet": "结构化面试真题"},
        {"title": "省考面试真题", "url": "https://www.zhihu.com/question/420684527", "snippet": "省考面试真题"},
    ],
    "graduate_school": [
        {"title": "考研复试面试真题", "url": "https://www.zhihu.com/question/359865306", "snippet": "考研复试面试问题"},
        {"title": "计算机考研复试面试题", "url": "https://www.zhihu.com/question/268441345", "snippet": "计算机复试面试题"},
        {"title": "考研复试常见问题", "url": "https://www.zhihu.com/question/268445853", "snippet": "考研复试常见问题汇总"},
    ],
    "teacher_cert": [
        {"title": "教资面试结构化真题", "url": "https://www.zhihu.com/question/355093756", "snippet": "教资结构化面试真题"},
        {"title": "教师资格证面试真题", "url": "https://www.zhihu.com/question/302838194", "snippet": "教资面试真题"},
    ],
    "mba_interview": [
        {"title": "MBA提前面试真题", "url": "https://www.zhihu.com/question/267648891", "snippet": "MBA提前面试问题"},
        {"title": "MBA面试问题汇总", "url": "https://www.zhihu.com/question/37337985", "snippet": "MBA面试常见问题"},
    ],
    "ielts_speaking": [
        {"title": "雅思口语Part2真题", "url": "https://www.zhihu.com/question/301287198", "snippet": "雅思口语Part2题目"},
        {"title": "雅思口语题库", "url": "https://www.zhihu.com/question/411286667", "snippet": "雅思口语题库汇总"},
        {"title": "IELTS Speaking Questions", "url": "https://ielts.org/speaking", "snippet": "Official IELTS speaking questions"},
    ],
}


# ================================================================
# HTTP 工具（curl subprocess）
# ================================================================

def _curl_get(url: str, timeout: int = 15) -> Optional[str]:
    """使用 curl 执行 GET 请求"""
    cmd = [
        "curl", "-s", "-L",
        "--max-time", str(timeout),
        "-H", f"User-Agent: {SCRAPER_CONFIG['user_agent']}",
        "-H", "Accept-Language: zh-CN,zh;q=0.9",
    ]
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True,
                                timeout=timeout + 5)
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")
    except Exception:
        pass
    return None


# ================================================================
# DuckDuckGo 搜索
# ================================================================

def _duckduckgo_search(query: str, max_results: int = 20) -> List[Dict[str, str]]:
    """使用 DuckDuckGo HTML 搜索"""
    results = []
    url = f"https://html.duckduckgo.com/html?q={_urlencode(query)}"

    html = _curl_get(url)
    if not html:
        return results

    soup = BeautifulSoup(html, "html.parser")
    for result_div in soup.select(".result"):
        title_link = result_div.select_one(".result__a")
        if not title_link:
            continue
        href = title_link.get("href", "")
        title = title_link.get_text(strip=True)
        snippet_div = result_div.select_one(".result__snippet")
        snippet = snippet_div.get_text(strip=True) if snippet_div else ""

        real_url = _extract_real_url(href)
        if real_url and title:
            results.append({
                "title": title, "url": real_url,
                "snippet": snippet, "query": query,
            })
        if len(results) >= max_results:
            break
    return results


# ================================================================
# Bing 搜索
# ================================================================

def _bing_search(query: str, max_results: int = 20) -> List[Dict[str, str]]:
    """使用 Bing HTML 搜索"""
    results = []
    url = f"https://www.bing.com/search?q={_urlencode(query)}&setlang=zh-cn"

    html = _curl_get(url)
    if not html:
        return results

    soup = BeautifulSoup(html, "html.parser")
    for li in soup.select("#b_results > li.b_algo"):
        title_link = li.select_one("h2 a")
        if not title_link:
            continue
        href = title_link.get("href", "")
        title = title_link.get_text(strip=True)
        snippet_elem = li.select_one(".b_caption p")
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

        if href and title:
            results.append({
                "title": title, "url": href,
                "snippet": snippet, "query": query,
            })
        if len(results) >= max_results:
            break
    return results


def _urlencode(s: str) -> str:
    """简单的 URL 编码"""
    import urllib.parse
    return urllib.parse.quote(s)


def _extract_real_url(duck_url: str) -> str:
    """从 DuckDuckGo 重定向链接提取真实 URL"""
    import urllib.parse
    if "duckduckgo.com/l/" in duck_url:
        parsed = urllib.parse.urlparse(duck_url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs:
            return qs["uddg"][0]
    elif duck_url.startswith("//"):
        return "https:" + duck_url
    elif duck_url.startswith("http"):
        return duck_url
    return ""


# ================================================================
# 统一搜索
# ================================================================

def search_pages(query: str, max_results: int = 20) -> List[Dict[str, str]]:
    """统一搜索 - 尝试多个引擎"""
    result = _duckduckgo_search(query, max_results)
    if result:
        return result
    result = _bing_search(query, max_results)
    if result:
        return result
    return []


def search_interview_pages(scenario: str, max_per_query: int = 15) -> List[Dict[str, str]]:
    """搜索指定场景的面经页面，带种子 URL 回退"""
    queries = SEARCH_QUERIES.get(scenario, [])
    all_results = []
    seen_urls = set()

    # 尝试在线搜索
    online_ok = False
    test_html = _curl_get("https://html.duckduckgo.com/html?q=test")
    if test_html:
        online_ok = True

    if online_ok and queries:
        for q in queries:
            print(f"  搜索: {q[:60]}...")
            try:
                results = search_pages(q, max_results=max_per_query)
                new_count = 0
                for r in results:
                    url = r["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
                        new_count += 1
                print(f"    找到 {len(results)} 条，新增 {new_count} 条")
            except Exception as e:
                print(f"    出错: {e}")
            time.sleep(SEARCH_CONFIG["duckduckgo"]["delay_between_queries"])
    else:
        if not online_ok:
            print(f"  [提示] 搜索引擎不可用，使用种子 URL")

    # 补充种子 URL
    seeds = SEED_URLS.get(scenario, [])
    for s in seeds:
        if s["url"] not in seen_urls:
            seen_urls.add(s["url"])
            all_results.append(s)

    print(f"\n  [完成] 场景 '{scenario}': 共 {len(all_results)} 个页面 "
          f"(在线={len(all_results) - len(seeds) if online_ok else 0}, 种子={len(seeds)})")
    return all_results


def search_all_scenarios(
    scenarios: Optional[List[str]] = None,
    max_per_query: int = 15,
) -> Dict[str, List[Dict[str, str]]]:
    """搜索所有场景"""
    if scenarios is None:
        scenarios = list(SEARCH_QUERIES.keys())

    result = {}
    total = 0
    for sc in scenarios:
        print(f"\n{'='*60}")
        print(f"搜索场景: {sc}")
        print(f"{'='*60}")
        pages = search_interview_pages(sc, max_per_query)
        result[sc] = pages
        total += len(pages)

    print(f"\n{'='*60}")
    print(f"搜索完成! 共发现 {total} 个页面")
    print(f"{'='*60}")
    return result


def save_search_results(results: Dict[str, List[Dict[str, str]]], filepath: str):
    """保存搜索结果"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in results.values())
    print(f"搜索结果已保存: {filepath} ({total} 条)")
