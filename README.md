# 百工 — 多场景 AI 面试模拟平台

模拟真实面试场景，与 AI 考官进行多轮对话练习，获得即时评分反馈和成长档案。

---

## 功能特性

- **6 大面试场景** — 求职面试、教资面试、雅思口语、公务员面试、考研复试、MBA 面试
- **AI 考官对话** — 基于 LLM 的真实考官人设，多轮追问，上下文感知，5 种面试风格可选
- **防幻觉机制** — 最高优先级规则，绝对禁止编造用户简历内容，只引用用户实际说过的信息
- **多 Agent 委员会评审** — 3 位不同立场 AI 评审员并行打分 + 主席合成 + 评分一致性分析
- **Skill 系统** — 可扩展的场景配置，自定义评分维度和考官人设，YAML 驱动
- **6 阶段面试流程** — 自我介绍 → 项目深挖 → 基础考察 → 进阶能力 → 系统设计 → 行为面试
- **技术深挖模式** — 检测 Redis / Kafka / RAG 等关键词自动进入专题追问
- **题库中心** — 328+ 道题目，S/A/B/C 四级评分，真实面经 > 开源 > AI 生成分层召回
- **成长档案** — 练习记录、各维度得分趋势、场景排行榜
- **成就徽章** — 12 种徽章（新手入门 / 坚持打卡 / 场景挑战 / 特殊成就），自动解锁判定
- **面试记录回溯** — 查看过往每一次完整对话 + 评分报告
- **数字人考官** — 2D 立绘 + 5 种表情切换，6 套场景匹配形象
- **语音交互** — 阿里云 NLS 语音识别 + TTS（雅思口语全流程支持）
- **韧性保障** — 20s 超时 + 2 次重试 + 三级降级（API → 题库兜底 → 硬编码预案）

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 3.x + Flask-SocketIO |
| 数据库 | SQLite (WAL) / Supabase PostgreSQL |
| AI 模型 | DeepSeek Chat API |
| 语音 | 阿里云 NLS SDK |
| 配置系统 | YAML (Skill / Tool / Agent 定义) |
| 前端 | Jinja2 模板 + 原生 CSS/JS + Chart.js |
| 部署 | Render + Gunicorn |

---

## 项目结构

```
mianshiguan/
├── app.py                         # 应用入口
├── src/
│   ├── agents/                    # 多 Agent 协作系统
│   │   ├── base_agent.py          #   Agent 抽象基类
│   │   ├── reviewer_agent.py      #   评审 Agent（5 种立场）
│   │   ├── orchestrator.py        #   并行编排引擎
│   │   ├── committee.py           #   委员会管理器（桥接层）
│   │   ├── llm_adapter.py         #   LLM 适配器（共享）
│   │   └── types.py               #   类型定义
│   ├── web/                       # Web 层
│   │   ├── __init__.py            #   应用工厂 + 依赖初始化
│   │   ├── dependencies.py        #   共享依赖注入
│   │   ├── websocket_handler.py   #   WebSocket 实时对话
│   │   └── blueprints/
│   │       ├── web.py             #     页面路由
│   │       ├── api_examiner.py    #     AI 考官 + 场景 API
│   │       ├── api_questions.py   #     题库 API
│   │       ├── api_badges.py      #     徽章 API
│   │       ├── api_progress.py    #     成长档案 API
│   │       ├── api_skills.py      #     Skill + Tool API
│   │       ├── api_spider.py      #     面经搜索 API
│   │       └── api_auth.py        #     登录注册 API
│   ├── core/                      # 核心引擎
│   │   ├── database/              #   数据库层（SQLite + PG 双后端）
│   │   ├── skill/                 #   Skill 注册中心 + 执行器
│   │   ├── tool/                  #   Tool Calling 系统
│   │   ├── workflow/              #   面试后流水线（5 阶段）
│   │   └── deep_dive/             #   技术深挖引擎
│   ├── services/                  # 业务服务
│   │   ├── llm_client.py          #   LLM API 客户端（1023 行）
│   │   ├── interview_service.py   #   面试编排
│   │   ├── speech_service.py      #   语音服务（STT + TTS）
│   │   ├── review_service.py      #   翻车复盘
│   │   └── database_service.py    #   内存数据库（Legacy）
│   ├── skills/                    # 6 个场景 Skill 实现
│   ├── tools/                     # 18 个 Tool 注册
│   ├── spider/                    # 题库爬虫（牛客网/知乎/CSDN）
│   └── scenarios/                 # 场景元数据
├── config/
│   ├── skills/                    # 6 个场景 YAML 配置
│   ├── agents/                    # 委员会评审配置
│   └── scenario_config.yaml       # 全局场景配置
├── templates/                     # 31 个 Jinja2 前端页面
├── static/                        # CSS / JS / 数字人立绘（21 张）
├── scripts/                       # 数据审计 & 题库管理脚本
├── data/                          # SQLite 数据库 + 题目 JSON
└── docs/                          # PRD / ADR / 路演文档
```

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 3. 启动
python app.py
# 访问 http://127.0.0.1:5000
```

---

## API 概览

| 端点 | 说明 |
|------|------|
| `GET /api/scenarios` | 获取所有面试场景 |
| `POST /api/examiner/start` | 开始 AI 面试（创建会话） |
| `POST /api/examiner/chat` | 发送消息给 AI 考官 |
| `POST /api/examiner/finish` | 结束面试并获取报告（支持 `review_mode: committee`） |
| `GET /api/result/<id>` | 获取面试结果（对话 + 报告 + 排名） |
| `GET/POST /api/questions` | 题库管理 |
| `GET /api/badges` | 徽章系统 |
| `GET /api/user/<id>/progress` | 用户成长档案 |
| `GET /api/skills` | 已注册的 Skill 列表 |
| `GET /api/health` | 健康检查 |

---

## License

MIT
