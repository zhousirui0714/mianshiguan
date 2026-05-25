# 个人极简面试官 - 数据库设计

## 数据库设计（PostgreSQL / Supabase）

### 核心对象分析

| 核心对象 | 说明 |
|----------|------|
| **User** | 用户账户信息 |
| **Resume** | 用户上传的简历PDF文件及解析后的基础信息 |
| **Project** | 简历中的项目经历（一个简历包含多个项目） |
| **QuestionRecord** | 生成的刁钻追问记录（一个项目可生成多条记录） |

---

### 表1：users（用户表）

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE users IS '用户账户表';
COMMENT ON COLUMN users.email IS '用户邮箱，唯一标识';
COMMENT ON COLUMN users.nickname IS '用户昵称，可用于显示';

-- 索引建议
CREATE INDEX idx_users_email ON users(email);
```

| 字段 | 类型 | 约束 | 可空 | 说明 |
|------|------|------|------|------|
| id | UUID | PRIMARY KEY | 否 | 用户唯一标识 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 否 | 登录邮箱 |
| nickname | VARCHAR(100) | - | 是 | 显示昵称 |
| avatar_url | TEXT | - | 是 | 头像URL |
| created_at | TIMESTAMP | DEFAULT NOW() | 否 | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 否 | 更新时间 |

---

### 表2：resumes（简历表）

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size INTEGER,
    parsed_status VARCHAR(20) DEFAULT 'pending' CHECK (parsed_status IN ('pending', 'processing', 'completed', 'failed')),
    parsed_data JSONB,
    job_position VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE resumes IS '简历表，存储用户上传的PDF简历';
COMMENT ON COLUMN resumes.parsed_status IS '解析状态：pending待处理/processing处理中/completed完成/failed失败';
COMMENT ON COLUMN resumes.parsed_data IS '解析后的结构化数据（JSONB格式）';

-- 索引建议
CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE INDEX idx_resumes_parsed_status ON resumes(parsed_status);
CREATE INDEX idx_resumes_user_created ON resumes(user_id, created_at DESC);
```

| 字段 | 类型 | 约束 | 可空 | 说明 |
|------|------|------|------|------|
| id | UUID | PRIMARY KEY | 否 | 简历唯一标识 |
| user_id | UUID | FOREIGN KEY → users.id | 否 | 所属用户 |
| file_name | VARCHAR(255) | NOT NULL | 否 | 原始文件名 |
| file_url | TEXT | NOT NULL | 否 | 文件存储URL |
| file_size | INTEGER | - | 是 | 文件大小（字节） |
| parsed_status | VARCHAR(20) | DEFAULT 'pending' | 否 | 解析状态 |
| parsed_data | JSONB | - | 是 | 解析后的结构化数据 |
| job_position | VARCHAR(100) | - | 是 | 求职岗位 |
| created_at | TIMESTAMP | DEFAULT NOW() | 否 | 上传时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 否 | 更新时间 |

---

### 表3：projects（项目经历表）

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    project_name VARCHAR(200) NOT NULL,
    project_time VARCHAR(50),
    role_responsibility TEXT,
    tech_stack TEXT[],
    project_result TEXT,
    project_description TEXT,
    vector_embedding_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE projects IS '项目经历表，从简历中抽取的项目模块';
COMMENT ON COLUMN projects.tech_stack IS '技术栈数组，如{Python,React,MySQL}';
COMMENT ON COLUMN projects.vector_embedding_id IS '关联向量数据库中的embedding记录ID';

-- 索引建议
CREATE INDEX idx_projects_resume_id ON projects(resume_id);
CREATE INDEX idx_projects_name ON projects(project_name);
CREATE INDEX idx_projects_resume_created ON projects(resume_id, created_at DESC);
```

| 字段 | 类型 | 约束 | 可空 | 说明 |
|------|------|------|------|------|
| id | UUID | PRIMARY KEY | 否 | 项目唯一标识 |
| resume_id | UUID | FOREIGN KEY → resumes.id | 否 | 所属简历 |
| project_name | VARCHAR(200) | NOT NULL | 否 | 项目名称 |
| project_time | VARCHAR(50) | - | 是 | 项目时间（如"2024.03-2024.06"） |
| role_responsibility | TEXT | - | 是 | 项目职责 |
| tech_stack | TEXT[] | - | 是 | 技术栈数组 |
| project_result | TEXT | - | 是 | 项目成果/数据 |
| project_description | TEXT | - | 是 | 项目描述原文 |
| vector_embedding_id | VARCHAR(100) | - | 是 | 向量embedding ID |
| created_at | TIMESTAMP | DEFAULT NOW() | 否 | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 否 | 更新时间 |

---

### 表4：question_records（追问记录表）

```sql
CREATE TABLE question_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    question_1 TEXT NOT NULL,
    question_1_logic TEXT,
    question_2 TEXT NOT NULL,
    question_2_logic TEXT,
    question_3 TEXT NOT NULL,
    question_3_logic TEXT,
    generation_mode VARCHAR(20) DEFAULT 'auto' CHECK (generation_mode IN ('auto', 'manual')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE question_records IS '追问记录表，存储针对每个项目生成的刁钻追问';

-- 索引建议
CREATE INDEX idx_question_records_project_id ON question_records(project_id);
CREATE INDEX idx_question_records_created ON question_records(created_at DESC);
```

| 字段 | 类型 | 约束 | 可空 | 说明 |
|------|------|------|------|------|
| id | UUID | PRIMARY KEY | 否 | 记录唯一标识 |
| project_id | UUID | FOREIGN KEY → projects.id | 否 | 关联项目 |
| question_1 | TEXT | NOT NULL | 否 | 第1个刁钻追问 |
| question_1_logic | TEXT | - | 是 | 第1个追问的生成逻辑 |
| question_2 | TEXT | NOT NULL | 否 | 第2个刁钻追问 |
| question_2_logic | TEXT | - | 是 | 第2个追问的生成逻辑 |
| question_3 | TEXT | NOT NULL | 否 | 第3个刁钻追问 |
| question_3_logic | TEXT | - | 是 | 第3个追问的生成逻辑 |
| generation_mode | VARCHAR(20) | DEFAULT 'auto' | 否 | 生成模式：auto自动/manual手动 |
| created_at | TIMESTAMP | DEFAULT NOW() | 否 | 生成时间 |

---

### 为什么要拆表？

| 拆表理由 | 说明 |
|----------|------|
| **对象边界清晰** | User、Resume、Project、QuestionRecord 是4个独立业务对象，有各自的生命周期 |
| **一对多关系** | 1个用户 → N份简历 → N个项目 → N条追问记录，层级关系清晰 |
| **数据更新独立** | 用户修改简历只需更新resume表，不影响projects表 |
| **查询灵活** | 可以单独查询某用户的所有简历，或某项目的所有追问 |
| **向量检索解耦** | 向量embedding存在专用的向量数据库（Milvus/Pinecone），表中只存ID引用 |
| **避免NULL填充** | 合并会导致大量NULL字段（如只有项目的用户无需填简历字段） |
| **扩展性** | 未来可单独对projects表做分库分表，或对question_records做冷热分离 |

### 表关系图

```
users (1) ──────< (N) resumes (1) ──────< (N) projects (1) ──────< (N) question_records
   │                   │                      │
   │ 用户上传简历        │ 简历包含项目          │ 项目生成追问
   └────────────────────┴──────────────────────┘
```
