"""
爬虫解析器 - 各平台页面内容抓取

每个平台单独一个模块，统一接口：
    scrape(url: str) -> dict
    返回: {"title": "...", "content": "...", "platform": "...", "success": bool}
"""
