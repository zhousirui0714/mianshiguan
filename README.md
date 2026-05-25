# 个人极简面试官

一个帮助求职者准备面试的AI工具，基于简历项目生成刁钻追问。

## 功能特性

- 📄 **简历PDF上传解析** - 支持简历上传和项目经历提取
- 🧠 **RAG知识库构建** - 构建个人简历私有向量知识库
- 👨‍💼 **大厂面试官角色** - 刁钻、深挖、抠细节的提问风格
- 🎯 **自动生成刁钻追问** - 针对项目生成3条高难度追问
- 📊 **轻量化结果展示** - 直接展示解析项目和追问

## 技术栈

- Python 3.10+
- FastAPI (后端框架)
- Pydantic (数据验证)
- httpx (HTTP客户端)
- tenacity (重试机制)

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python main.py --iterations 3
```

### 运行Evals评估

```bash
python evals.py
```

## 项目结构

```
mianshiguan/
├── src/                    # 源代码目录
│   ├── models/             # 数据模型定义
│   ├── services/           # 业务服务层
│   └── utils/              # 工具类
├── prd.md                  # 产品需求文档
├── database-design.md      # 数据库设计文档
├── evals.py                # Evals评估脚本
├── main.py                 # 测试入口
└── requirements.txt        # 依赖配置
```

## 核心功能

### 1. 简历解析
- 支持PDF文件上传
- 自动提取项目经历模块
- 结构化解析简历内容

### 2. 追问生成
- 基于RAG检索项目信息
- 模拟大厂面试官风格
- 生成3条刁钻技术追问

### 3. 系统韧性
- LLM API超时保护（20秒）
- 自动重试机制（2次）
- 降级方案（预设问题库）

## 许可证

MIT License