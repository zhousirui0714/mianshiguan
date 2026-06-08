"""
百工模拟考场 - 自动面试题采集系统

自动搜索、提取、去重、分类、评级真实面经中的面试题。
目标：将题库从 1000+ 扩充到 3000+ 真实题目。

使用方式：
    python -m scripts.question_collector.main

模块结构：
    schema.py          - 数据模型定义
    config.py          - 配置（搜索词、平台规则）
    searcher.py        - 搜索引擎发现面经URL
    scrapers/          - 各平台解析器
    extractor.py       - 从文本提取面试问题
    deduplicator.py    - 去重（内部 + 与现有库）
    classifier.py      - 分类（场景 + 类别）
    grader.py          - 评级（S/A/B/C）
    answer_generator.py - 生成3级答案
    storage.py         - 存储（JSON + SQLite）
    main.py            - 主控流程
"""
