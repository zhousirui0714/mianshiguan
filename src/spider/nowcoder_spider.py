#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
牛客网面经爬虫 — NowcoderSpider

爬取牛客网面试经验区的真实面试问题，用于"百工模拟考场"题库数据源。

用法:
    # 爬取指定公司的面经
    python src/spider/nowcoder_spider.py --company "腾讯" --limit 30

    # 爬取多个公司（用逗号分隔）
    python src/spider/nowcoder_spider.py --company "腾讯,阿里,字节" --limit 20

    # 增量更新（只爬取新面经，跳过已存在的）
    python src/spider/nowcoder_spider.py --company "腾讯" --incremental

注意事项:
    - 遵守 robots.txt
    - 请求间隔 2-5 秒
    - 数据仅用于学习项目，不商用
    - 支持 Ctrl+C 暂停
"""
import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.database import DatabaseManager

# ==================== 配置 ====================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
]

BASE_URL = "https://www.nowcoder.com"
INTERVIEW_CENTER_URL = "https://www.nowcoder.com/interview/center"
DETAIL_URL_TEMPLATE = "https://www.nowcoder.com/interview/center/detail?tid={tid}"

# 请求配置
MIN_INTERVAL = 2.0   # 最小请求间隔（秒）
MAX_INTERVAL = 5.0   # 最大请求间隔（秒）
MAX_RETRIES = 3      # 最大重试次数
TIMEOUT = 15         # 超时时间（秒）

# 已知的公司列表（可扩展）
KNOWN_COMPANIES = [
    "腾讯", "阿里", "字节", "百度", "美团", "京东", "华为", "小米",
    "网易", "拼多多", "快手", "滴滴", "哔哩哔哩", "小红书", "知乎",
    "携程", "唯品会", "360", "搜狐", "新浪", "中兴", "海康威视",
    "大疆", "商汤", "旷视", "寒武纪", "中芯国际", "比亚迪",
]


class NowcoderSpider:
    """牛客网面经爬虫"""

    def __init__(self, db: DatabaseManager = None, verbose: bool = True):
        self.verbose = verbose
        self.db = db or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({"Accept-Language": "zh-CN,zh;q=0.9"})
        self._paused = False
        self._stop = False
        self._stats = {"fetched": 0, "new": 0, "skipped": 0, "failed": 0}

    def log(self, msg: str):
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _random_delay(self):
        delay = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
        time.sleep(delay)

    def _request(self, url: str, retry: int = 0) -> requests.Response:
        """带重试和 UA 轮换的请求"""
        try:
            headers = {"User-Agent": self._random_ua()}
            resp = self.session.get(url, headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            # 检查是否被反爬
            if resp.url.endswith(".html") and "验证" in resp.text[:200]:
                raise Exception("触发验证码，请求被拦截")
            return resp
        except Exception as e:
            if retry < MAX_RETRIES:
                wait = (retry + 1) * 3
                self.log(f"  请求失败 ({e}), {wait}s 后重试 ({retry+1}/{MAX_RETRIES})...")
                time.sleep(wait)
                return self._request(url, retry + 1)
            raise

    # ==================== 公开接口 ====================

    def crawl_company(self, company: str, limit: int = 30,
                      incremental: bool = False) -> dict:
        """爬取指定公司的面经"""
        self.log(f"开始爬取 [{company}] 的面经，目标 {limit} 篇")
        self._stats = {"fetched": 0, "new": 0, "skipped": 0, "failed": 0}

        try:
            results = self._crawl_by_search(company, limit, incremental)
        except Exception as e:
            self.log(f"搜索爬取失败: {e}")
            self.log("尝试备选方案：直接解析面经列表页...")
            results = self._crawl_fallback(company, limit, incremental)

        self.log(f"[{company}] 完成: 抓取 {self._stats['fetched']} 篇, "
                 f"新增 {self._stats['new']} 篇, 跳过 {self._stats['skipped']} 篇, "
                 f"失败 {self._stats['failed']} 篇")
        return self._stats

    def crawl_multiple(self, companies: list, limit_per: int = 20,
                       incremental: bool = False):
        """爬取多个公司"""
        total = {"fetched": 0, "new": 0, "skipped": 0, "failed": 0}
        for company in companies:
            stats = self.crawl_company(company, limit_per, incremental)
            for k in total:
                total[k] += stats[k]
            self.log(f"--- 暂停 10 秒，切换公司 ---")
            time.sleep(10)
        self.log(f"全部完成: {total}")
        return total

    # ==================== 核心爬取逻辑 ====================

    def _crawl_by_search(self, company: str, limit: int = 30,
                         incremental: bool = False) -> list:
        """通过搜索页面爬取面经"""
        results = []
        page = 1

        while len(results) < limit and not self._stop:
            url = f"{INTERVIEW_CENTER_URL}?company={company}&page={page}"
            self.log(f"  搜索页 {page}: {url}")

            try:
                resp = self._request(url)
            except Exception as e:
                self.log(f"  搜索页 {page} 失败: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            items = self._parse_list_page(soup)

            if not items:
                self.log(f"  搜索页 {page} 无更多结果")
                break

            for item in items:
                if len(results) >= limit or self._stop:
                    break
                self._stats["fetched"] += 1

                # 跳过已存在的
                if incremental and self._check_exists(item):
                    self._stats["skipped"] += 1
                    continue

                try:
                    detail = self._fetch_detail(item["tid"])
                    self._stats["new"] += 1
                    self.db.save_interview_experience(detail)
                    results.append(detail)
                    self.log(f"  ✓ [{len(results)}/{limit}] {item.get('company','?')} "
                             f"- {item.get('position','?')} - {len(detail.get('questions',[]))} 题")
                except Exception as e:
                    self._stats["failed"] += 1
                    self.log(f"  ✗ 详情失败: {e}")

                self._random_delay()

            page += 1

        return results

    def _parse_list_page(self, soup: BeautifulSoup) -> list:
        """解析面经列表页，提取条目信息"""
        items = []
        # 尝试多种选择器兼容页面改版
        selectors = [
            "div.interview-item", "li.interview-item",
            "div.feed-item", "div.content-item",
            "div[class*='interview']", "div[class*='experience']",
            "table tr", "div.recommend-item",
            "div.post-item", "div.subject-item",
            "div.question-item",
        ]

        containers = []
        for sel in selectors:
            containers = soup.select(sel)
            if containers:
                break

        if not containers:
            # 备用：找所有包含链接的区块
            containers = soup.find_all("div", class_=re.compile("item|card|list|content"))

        for container in containers:
            try:
                # 提取链接和 tid
                link = container.find("a", href=re.compile(r"tid="))
                if not link:
                    link = container.find("a", href=re.compile(r"detail"))
                if not link:
                    continue

                href = link.get("href", "")
                tid_match = re.search(r"tid=(\d+)", href)
                if not tid_match:
                    tid_match = re.search(r"detail[/=](\d+)", href)
                if not tid_match:
                    continue

                tid = tid_match.group(1)

                # 提取公司名
                company_el = container.find(class_=re.compile("company|enterprise|tag"))
                company = company_el.get_text(strip=True) if company_el else ""

                # 提取岗位
                pos_el = container.find(class_=re.compile("position|job|post"))
                position = pos_el.get_text(strip=True) if pos_el else ""

                # 提取标题
                title_el = container.find(class_=re.compile("title|name|subject"))
                title = title_el.get_text(strip=True) if title_el else ""

                # 如果岗位为空，尝试从标题提取
                if not position and title:
                    for c in KNOWN_COMPANIES:
                        title = title.replace(c, "").strip()
                    # 标题剩下的部分可能就是岗位
                    position = title[:20] if title else ""

                items.append({
                    "tid": tid,
                    "company": company,
                    "position": position,
                    "title": title,
                    "url": urljoin(BASE_URL, href),
                })
            except Exception:
                continue

        return items

    def _fetch_detail(self, tid: str) -> dict:
        """爬取面经详情页"""
        url = DETAIL_URL_TEMPLATE.format(tid=tid)
        resp = self._request(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取标题/公司/岗位
        title_text = ""
        title_el = soup.find("title") or soup.find(class_=re.compile("title|head"))
        if title_el:
            title_text = title_el.get_text(strip=True)

        company = ""
        position = ""
        round_text = ""

        # 尝试从标题提取公司名
        for c in KNOWN_COMPANIES:
            if c in title_text:
                company = c
                title_text = title_text.replace(c, "").strip()
                break

        # 从面包屑或标签提取
        breadcrumb = soup.find(class_=re.compile("breadcrumb|nav|crumbs"))
        if breadcrumb:
            texts = [t.get_text(strip=True) for t in breadcrumb.find_all("a")]
            for t in texts:
                for c in KNOWN_COMPANIES:
                    if c in t and not company:
                        company = c

        # 提取正文内容
        content_selectors = [
            "div.post-content", "div.content", "div.detail-content",
            "div.article-content", "div[class*='content']",
            "div[class*='detail']", "article", "div.rich-text",
            "div.post-detail",
        ]
        content_div = None
        for sel in content_selectors:
            content_div = soup.select_one(sel)
            if content_div:
                break

        content = content_div.get_text("\n", strip=True) if content_div else ""

        # 从正文智能提取面试问题
        questions = self._extract_questions(content, title_text)

        # 尝试提取岗位
        position_patterns = [
            r"(产品|运营|前端|后端|算法|测试|开发|数据|设计|市场|销售|HR|人力|行政|财务|Java|Python|C\+\+|Go|安卓|iOS|客户端|服务端|全栈|架构|安全|运维|DBA|项目管理|产品经理|运营经理)",
        ]
        for pat in position_patterns:
            m = re.search(pat, title_text + content[:500])
            if m:
                position = m.group(1)
                break

        # 尝试提取轮次
        round_patterns = [r"([一二三四五六七八九十\d]+面)", r"(HR面|技术面|主管面|综合面|群面|终面)"]
        for pat in round_patterns:
            m = re.search(pat, title_text + content[:300])
            if m:
                round_text = m.group(0)
                break

        return {
            "company_name": company or "未知",
            "position": position or "",
            "round": round_text or "",
            "questions": questions,
            "content": content[:5000],  # 限制正文长度
            "publish_date": "",
            "source_url": url,
        }

    def _extract_questions(self, content: str, title: str = "") -> list:
        """
        从面经正文中智能提取面试问题

        支持多种问题格式：
        - "1. 问题内容"
        - "1、问题内容"
        - "Q1: 问题内容"
        - "- 问题内容"
        """
        questions = []
        if not content:
            return questions

        # 尝试按编号提取
        patterns = [
            # "1. ", "1、", "(1) ", "① "
            r"(?:^|\n)\s*(?:\d+[\.\)、]\s*|[\(\[]\d+[\)\]]\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*)(.{10,200})",
            # "Q1: ", "问题1: "
            r"(?:Q|问题|第\d+题)[：:]\s*(.{10,200})",
            # "- " bullet points (至少 15 字)
            r"(?:^|\n)\s*[-•·*]\s*(.{15,200})",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for m in matches:
                text = m.strip()
                # 过滤非问题（太短、包含太多标点、网址等）
                if len(text) < 8:
                    continue
                if re.search(r"http|\.com|点赞|收藏|回复|关注|分享", text):
                    continue
                # 去重
                if text not in questions:
                    questions.append(text)

        # 如果正则提取不到，用行拆分启发式提取
        if not questions:
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                # 包含问号的行
                if "?" in line or "？" in line:
                    if 8 < len(line) < 200 and "http" not in line:
                        questions.append(line)

        # 最多保留 20 个问题
        return questions[:20]

    def _crawl_fallback(self, company: str, limit: int = 30,
                        incremental: bool = False) -> list:
        """备选方案：直接解析面经中心列表"""
        results = []
        url = INTERVIEW_CENTER_URL

        try:
            resp = self._request(url)
        except Exception:
            return results

        soup = BeautifulSoup(resp.text, "html.parser")
        items = self._parse_list_page(soup)

        for item in items:
            if len(results) >= limit or self._stop:
                break
            self._stats["fetched"] += 1

            if incremental and self._check_exists(item):
                self._stats["skipped"] += 1
                continue

            try:
                detail = self._fetch_detail(item["tid"])
                # 检查是否匹配目标公司
                if company and company not in detail["company_name"]:
                    self._stats["skipped"] += 1
                    continue
                self._stats["new"] += 1
                self.db.save_interview_experience(detail)
                results.append(detail)
                self.log(f"  ✓ [{len(results)}/{limit}] {detail['company_name']} "
                         f"- {detail.get('position','?')} - {len(detail.get('questions',[]))} 题")
            except Exception as e:
                self._stats["failed"] += 1
                self.log(f"  ✗ 详情失败: {e}")

            self._random_delay()

        return results

    def _check_exists(self, item: dict) -> bool:
        """检查面经是否已存在"""
        url = item.get("url", "")
        if not url and item.get("tid"):
            url = DETAIL_URL_TEMPLATE.format(tid=item["tid"])
        return self.db.experience_exists(url) if url else False

    # ==================== 工具方法 ====================

    def stop(self):
        self._stop = True


# ==================== 命令行入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="牛客网面经爬虫 — 为面试模拟系统采集真实面试问题"
    )
    parser.add_argument("--company", "-c", default="腾讯",
                        help="公司名称，多个用逗号分隔 (默认: 腾讯)")
    parser.add_argument("--limit", "-l", type=int, default=30,
                        help="每家公司最多爬取篇数 (默认: 30)")
    parser.add_argument("--incremental", "-i", action="store_true",
                        help="增量模式：跳过已存在的面经")
    parser.add_argument("--db", "-d", default="",
                        help="数据库路径 (默认: 使用项目默认)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="静默模式")
    args = parser.parse_args()

    companies = [c.strip() for c in args.company.split(",") if c.strip()]

    if not companies:
        print("请指定公司名称，例如: --company \"腾讯\"")
        sys.exit(1)

    db = DatabaseManager(args.db) if args.db else DatabaseManager()
    spider = NowcoderSpider(db=db, verbose=not args.quiet)

    # 注册 Ctrl+C 优雅退出
    import signal
    def handle_signal(sig, frame):
        print("\n[!] 收到中断信号，等待当前请求完成后退出...")
        spider.stop()
    signal.signal(signal.SIGINT, handle_signal)

    try:
        print(f"{'='*60}")
        print(f"  牛客网面经爬虫")
        print(f"  目标公司: {', '.join(companies)}")
        print(f"  目标篇数: {args.limit} 篇/家")
        print(f"  增量模式: {'是' if args.incremental else '否'}")
        print(f"  请求间隔: {MIN_INTERVAL}-{MAX_INTERVAL} 秒")
        print(f"{'='*60}\n")

        if len(companies) == 1:
            spider.crawl_company(companies[0], args.limit, args.incremental)
        else:
            spider.crawl_multiple(companies, args.limit, args.incremental)

        print(f"\n爬取完成！")

    except KeyboardInterrupt:
        print("\n\n爬虫已暂停。")
    except Exception as e:
        print(f"\n爬虫异常终止: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
