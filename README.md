# 面试成长伴侣 — 多场景 AI 面试模拟平台

模拟真实面试场景，与 AI 考官进行多轮对话练习，获得即时评分反馈和成长档案。

## 功能特性

- **6 大面试场景** — 求职面试、教资面试、雅思口语、公务员面试、考研复试、MBA 面试
- **AI 考官对话** — 基于 LLM 的真实考官人设，模拟多轮面试追问
- **Skill 系统** — 可扩展的场景配置，自定义评分维度和考官人设
- **题库中心** — 预置 16+ 道分类题目，支持搜索、筛选、CRUD
- **成长档案** — 练习记录、各维度得分趋势、场景排行榜
- **成就徽章** — 8 种徽章，支持自动解锁条件判定
- **韧性保障** — LLM 超时保护 + 自动重试 + 降级方案

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 3.x |
| 数据库 | SQLite (WAL 模式) |
| AI 模型 | DeepSeek Chat API |
| 配置系统 | YAML (Skill / Tool 定义) |
| 前端 | Jinja2 模板 + 原生 CSS/JS |

## 项目结构

```
mianshiguan/
├── app.py                    # 应用入口
├── src/
│   ├── web/                  # Web 层（Flask Blueprints）
│   │   ├── __init__.py       # 应用工厂
│   │   ├── dependencies.py   # 依赖注入
│   │   └── blueprints/       # 路由模块
│   │       ├── web.py           # 页面路由
│   │       ├── api_examiner.py  # AI考官 + 场景 API
│   │       ├── api_questions.py # 题库 API
│   │       ├── api_badges.py    # 徽章 API
│   │       ├── api_progress.py  # 成长档案 API
│   │       └── api_skills.py    # Skill + Tool API
│   ├── core/                 # 核心模块
│   │   ├── database/         # SQLite 数据库
│   │   ├── skill/            # Skill 系统引擎
│   │   ├── tool/             # Tool Calling 系统
│   │   └── workflow/         # 面试流水线
│   ├── services/             # 业务服务
│   │   └── llm_client.py     # LLM API 客户端
│   ├── skills/               # 场景 Skill 实现
│   ├── tools/                # Tool 注册
│   └── scenarios/            # 场景元数据
├── config/
│   ├── skills/               # Skill YAML 配置（6个场景）
│   └── scenario_config.yaml
├── templates/                # Jinja2 前端模板（26个）
└── data/                     # SQLite 数据库文件
```

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env   # 填入 DEEPSEEK_API_KEY
python app.py          # http://127.0.0.1:5000
```

## API 概览

| 端点 | 说明 |
|------|------|
| `GET /api/scenarios` | 获取所有场景 |
| `POST /api/examiner/start` | 开始 AI 面试对话 |
| `POST /api/examiner/chat` | 发送消息给 AI 考官 |
| `POST /api/examiner/finish` | 结束面试并获取报告 |
| `GET/POST /api/questions` | 题库管理 |
| `GET /api/badges` | 徽章系统 |
| `GET /api/user/<id>/progress` | 用户成长档案 |
| `GET /api/skills` | 已注册的 Skill 列表 |
| `GET /api/health` | 健康检查 |
# auto-push test
