"""
GitHub 题库数据源 — 远程 raw 下载 + 本地数据回退

远程源（已验证可下载）:
  - DolbyUUU/Awesome-LLM-Interview-Questions-and-Answers
  - azl397985856/fe-interview
  - datawhalechina/hello-agents

本地回退源（预整理数据）:
  - Snailclimb/JavaGuide
  - CyC2018/CS-Notes
  - youngyangyang04/leetcode-master
"""

import json
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import List, Dict, Optional

from src.spider.config import SKIP_FILE_KEYWORDS, REQUEST_TIMEOUT, REQUEST_DELAY
from src.spider.local_data import SOURCES_LOCAL

# SSL context without verification (Windows Python has SSL issues with GitHub CDN)
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ================================================================
# 远程源配置（已验证 raw.githubusercontent.com 可访问）
# ================================================================
REMOTE_SOURCES = [
    {
        "repo": "DolbyUUU/Awesome-LLM-Interview-Questions-and-Answers",
        "branch": "main",
        "files": ["README.md"],
        "default_cat": "AI/大模型",
    },
    {
        "repo": "azl397985856/fe-interview",
        "branch": "master",
        "files": ["docs/README.md"],
        "default_cat": "前端",
    },
    {
        "repo": "datawhalechina/hello-agents",
        "branch": "main",
        "files": ["docs/README.md"],
        "default_cat": "AI/大模型",
    },
]


class GitHubSource:
    """下载远程 + 加载本地题库数据"""

    def fetch_all(self) -> List[Dict]:
        """获取所有数据源（远程+本地）"""
        results = []
        # 远程源
        print("\n[远程源]")
        for idx, src in enumerate(REMOTE_SOURCES):
            print(f"  [{idx+1}/{len(REMOTE_SOURCES)}] {src['repo']}")
            files = self._fetch_remote(src)
            results.extend(files)
            time.sleep(REQUEST_DELAY)

        # 本地源
        print("\n[本地源]")
        for idx, src in enumerate(SOURCES_LOCAL):
            print(f"  [{idx+1}/{len(SOURCES_LOCAL)}] {src['repo']}/{src['file_path']}")
            results.append({
                "source_name": src["repo"],
                "file_path": src["file_path"],
                "content": src["content"],
                "scenario": src.get("scenario", "job_interview"),
                "default_cat": src["default_cat"],
            })

        return results

    def fetch_source(self, source: Dict) -> List[Dict]:
        """兼容接口 — 实际会使用 fetch_all"""
        return self.fetch_all()

    def _fetch_remote(self, src: Dict) -> List[Dict]:
        """从 raw.githubusercontent.com 下载"""
        results = []
        repo = src["repo"]
        branch = src["branch"]

        for file_path in src["files"]:
            content = self._download_file(repo, branch, file_path)
            if content:
                results.append({
                    "source_name": repo,
                    "file_path": file_path,
                    "content": content,
                    "scenario": "job_interview",
                    "default_cat": src["default_cat"],
                })
                print(f"    OK: {file_path} ({len(content)} bytes)")
            else:
                print(f"    SKIP: {file_path} (下载失败)")
        return results

    def _download_file(self, repo: str, branch: str, path: str) -> Optional[str]:
        """下载单个文件，自动处理路径编码"""
        parts = path.split("/")
        encoded = "/".join(urllib.parse.quote(p, safe="") for p in parts)
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{encoded}"

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT,
                                         context=_ssl_ctx) as resp:
                raw = resp.read()
                for enc in ["utf-8", "gbk", "latin-1"]:
                    try:
                        return raw.decode(enc)
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                return raw.decode("utf-8", errors="replace")
        except Exception:
            return None

    def _should_skip(self, filename: str) -> bool:
        name = filename.lower().replace(" ", "-")
        return any(kw in name for kw in SKIP_FILE_KEYWORDS)

    def _looks_like_content(self, content: str) -> bool:
        if not content or len(content) < 200:
            return False
        chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
        return chinese > 30 or len(content) > 1000
