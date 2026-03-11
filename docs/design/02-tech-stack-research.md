# 拓客智能体 - 技术栈调研

> 作者：Research Agent | 日期：2026-03-10
> 状态：V1.0

---

## 一、技术栈选型原则

### 1.1 项目特性分析

基于拓客 Agent 的业务需求，技术栈需满足：

| 需求维度 | 具体要求 | 优先级 |
|----------|----------|--------|
| **AI 集成** | 深度集成 LLM（OpenAI/Claude/本地模型），支持流式响应 | P0 |
| **数据处理** | 大规模 B2B 数据存储、向量检索（RAG）、实时同步 | P0 |
| **并发性能** | 邮件发送、API 调用高并发（1000+ QPS） | P0 |
| **可扩展性** | 支持多租户、水平扩展 | P1 |
| **开发效率** | 快速迭代 MVP，2-4 周上线 | P1 |
| **成本控制** | 初期预算有限，按需付费 | P1 |
| **团队技能** | 团队熟悉 Python/JS，有 AI 开发经验 | - |

### 1.2 评估维度

| 维度 | 权重 | 说明 |
|------|------|------|
| **开发效率** | 25% | 框架成熟度、生态丰富度、学习曲线 |
| **成本** | 20% | 云服务费用、运维成本 |
| **扩展性** | 20% | 水平扩展、多租户支持 |
| **可维护性** | 20% | 代码规范、调试工具、社区支持 |
| **性能** | 15% | 响应时间、并发能力 |

---

## 二、后端框架对比

### 2.1 对比总表

| 框架 | 语言 | 开发效率 | 性能 | AI 生态 | 成本 | 扩展性 | 可维护性 | 总分 |
|------|------|----------|------|---------|------|--------|----------|------|
| **FastAPI** | Python | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **92** |
| **NestJS** | TypeScript | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **88** |
| **Go (Gin/Fiber)** | Go | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **82** |
| **Django** | Python | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **80** |
| **Express.js** | JavaScript | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **75** |

### 2.2 深度分析

#### FastAPI（推荐 ⭐）

**优势**：
- **AI 生态最佳**：Python 是 AI/ML 的首选语言，所有主流 LLM SDK（OpenAI、Anthropic、LangChain）都优先支持 Python
- **异步原生**：基于 Starlette + Pydantic，异步性能优秀
- **自动文档**：OpenAPI/Swagger 自动生成
- **类型安全**：Pydantic 强类型校验，减少运行时错误
- **开发效率高**：装饰器语法简洁，代码量少

**劣势**：
- 性能不如 Go（但对拓客场景足够）
- 并非全栈框架，需搭配其他库

**适用场景**：
- AI Agent 核心逻辑
- LLM 调用编排
- 数据处理管道

**示例代码**：
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ProspectRequest(BaseModel):
    target_industry: str
    target_role: str
    company_size: str

@app.post("/api/v1/prospects/search")
async def search_prospects(request: ProspectRequest):
    # AI Agent 处理
    result = await agent.find_prospects(request)
    return result
```

---

#### NestJS

**优势**：
- **企业级架构**：依赖注入、模块化、装饰器，架构清晰
- **TypeScript 原生**：类型安全，前后端共享类型
- **生态丰富**：集成 GraphQL、WebSocket、微服务
- **可维护性强**：强制性模块化，适合大型项目

**劣势**：
- AI 生态不如 Python（需要调用 Python 服务）
- 学习曲线较陡

**适用场景**：
- 企业级 BFF（Backend for Frontend）
- 多租户架构
- 复杂业务逻辑

---

#### Go (Gin/Fiber)

**优势**：
- **性能最强**：原生并发（goroutine），内存占用低
- **部署简单**：单二进制文件，无运行时依赖
- **成本低**：同等性能下资源消耗最少

**劣势**：
- AI 生态最弱（需要调用外部 Python 服务）
- 开发效率较低（样板代码多）
- 错误处理繁琐

**适用场景**：
- 高并发 API 网关
- 邮件发送服务
- 数据同步服务

---

### 2.3 推荐方案

**主服务：FastAPI（Python）**
- AI Agent 核心逻辑
- LLM 调用
- 数据处理

**可选：Go 微服务**
- 邮件发送服务（高并发）
- API 网关（如需要）

---

## 三、数据库对比

### 3.1 对比总表

| 数据库 | 类型 | 开发效率 | 性能 | 向量支持 | 成本 | 扩展性 | 可维护性 | 总分 |
|--------|------|----------|------|----------|------|--------|----------|------|
| **PostgreSQL + pgvector** | 关系型+向量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **93** |
| **Supabase** | BaaS | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **91** |
| **MongoDB + Atlas Vector** | 文档型+向量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **85** |
| **Pinecone** | 纯向量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **83** |
| **MySQL** | 关系型 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **75** |

### 3.2 深度分析

#### PostgreSQL + pgvector（推荐 ⭐）

**优势**：
- **一站式解决方案**：关系型数据 + 向量检索 + JSON 支持
- **pgvector 扩展**：原生支持向量相似度搜索，无需额外向量库
- **成熟稳定**：30+ 年历史，ACID 事务，企业级可靠性
- **成本低**：开源免费，云服务价格低
- **生态丰富**：SQLAlchemy、Prisma 等ORM支持

**劣势**：
- 向量性能不如专用向量库（Pinecone、Milvus）
- 水平分片需要额外配置

**向量检索示例**：
```sql
-- 创建向量索引
CREATE INDEX ON prospects USING ivfflat (embedding vector_cosine_ops);

-- 相似度搜索
SELECT company_name, contact_email
FROM prospects
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

---

#### Supabase

**优势**：
- **全托管 BaaS**：PostgreSQL + Auth + Storage + Realtime
- **内置 pgvector**：开箱即用的向量支持
- **开发效率最高**：自动生成 REST API，实时订阅
- **定价友好**：免费套餐 500MB，适合 MVP

**劣势**：
- 依赖第三方服务
- 大规模数据成本上升

**适用场景**：
- MVP 快速开发
- 小团队全栈开发
- 需要实时同步

---

#### MongoDB + Atlas Vector Search

**优势**：
- **灵活 Schema**：B2B 数据结构多变，文档型更灵活
- **Atlas Vector Search**：云端向量检索
- **水平扩展**：分片简单

**劣势**：
- 成本较高（Atlas 不便宜）
- 向量性能不如 pgvector（小规模数据）
- 事务支持弱于 PostgreSQL

---

### 3.3 推荐方案

**主数据库：PostgreSQL + pgvector**
- 自托管或云服务（Neon、Railway、AWS RDS）
- 关系型数据 + 向量检索一体化
- 成本可控

**MVP 阶段：Supabase**
- 最快上线
- 免费套餐
- 后续可迁移到自托管 PG

---

## 四、前端框架对比

### 4.1 对比总表

| 框架 | 语言 | 开发效率 | 性能 | SEO | 生态 | 可维护性 | 总分 |
|------|------|----------|------|-----|------|----------|------|
| **Next.js** | TypeScript/React | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **96** |
| **Nuxt** | TypeScript/Vue | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **92** |
| **Remix** | TypeScript/React | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **88** |
| **Vite + React** | TypeScript/React | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **85** |
| **Astro** | TypeScript/Multi | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **85** |

### 4.2 深度分析

#### Next.js（推荐 ⭐）

**优势**：
- **全栈能力**：SSR + SSG + ISR + API Routes
- **Vercel 原生**：部署体验最佳
- **生态最强**：React 生态，组件库丰富
- **App Router**：React Server Components，性能优秀
- **AI 集成**：Vercel AI SDK 原生支持

**劣势**：
- 框架复杂度增加（App Router）
- Vercel 托管成本较高

**适用场景**：
- SaaS Dashboard
- 营销落地页
- AI Chat 界面

---

#### Nuxt

**优势**：
- Vue 生态，学习曲线平缓
- SSR/SSG 开箱即用
- Nitro 引擎，部署灵活

**劣势**：
- 生态小于 React/Next.js
- AI 集成案例较少

---

### 4.3 推荐方案

**前端：Next.js 14+ (App Router)**
- TypeScript
- TailwindCSS + Shadcn/UI
- Vercel 部署

---

## 五、AI 技术栈

### 5.1 LLM 选择

| 模型 | 提供商 | 成本 | 质量 | 速度 | 推荐 |
|------|--------|------|------|------|------|
| **Claude 3.5 Sonnet** | Anthropic | 中 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Agent 推理 |
| **GPT-4o** | OpenAI | 中 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 通用 |
| **GPT-4o-mini** | OpenAI | 低 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高频调用 |
| **DeepSeek V3** | DeepSeek | 极低 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中文/成本优化 |
| **GLM-4** | 智谱 | 低 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中文 |
| **Qwen 2.5** | 阿里云 | 低 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中文 |

### 5.2 AI 框架

| 框架 | 语言 | 特点 | 推荐场景 |
|------|------|------|----------|
| **LangChain** | Python/JS | 生态最大，组件最多 | 复杂 Agent |
| **LangGraph** | Python | 状态机 Agent，可控性强 | Agent 工作流 |
| **LlamaIndex** | Python | RAG 专用，数据索引强 | 知识库问答 |
| **Vercel AI SDK** | TypeScript | 前端集成简单 | 流式 Chat |
| **AutoGen** | Python | 多 Agent 协作 | Agent 编排 |

### 5.3 推荐方案

**Agent 框架：LangGraph**
- 状态机模式，可控性强
- 支持循环、分支、人工介入
- 与 LangChain 生态兼容

**LLM 策略**：
- Agent 推理：Claude 3.5 Sonnet / GPT-4o
- 高频任务：GPT-4o-mini / DeepSeek V3
- 中文场景：GLM-4 / Qwen 2.5

---

## 六、部署架构

### 6.1 部署方案对比

| 方案 | 成本 | 易用性 | 可扩展性 | 推荐场景 |
|------|------|--------|----------|----------|
| **Vercel + Railway** | 低-中 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | MVP/中小规模 |
| **AWS (ECS/Fargate + RDS)** | 中-高 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 企业级 |
| **阿里云 (ACK + RDS)** | 中-高 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 国内企业 |
| **自托管 (Docker + K8s)** | 低 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 大规模/成本敏感 |

### 6.2 推荐架构（MVP）

```
┌─────────────────────────────────────────────────────────────┐
│                        用户端                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Web App    │  │  API SDK    │  │  CLI Tool   │         │
│  │ (Next.js)   │  │  (Python)   │  │  (Python)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                             │
│                   (Vercel/Railway)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Agent API │ │Data API  │ │Email API │ │LLM API   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PostgreSQL   │ │ Redis        │ │ LLM APIs     │
│ + pgvector   │ │ (Queue/Cache)│ │ (OpenAI/Claude)│
└──────────────┘ └──────────────┘ └──────────────┘
```

### 6.3 推荐部署方案

**MVP 阶段（成本优化）**：
- 前端：Vercel（免费）
- 后端：Railway（$5/月起）
- 数据库：Supabase（免费500MB）或 Neon（免费）
- Redis：Upstash（免费）
- 总成本：$0-10/月

**正式阶段（稳定性优化）**：
- 前端：Vercel Pro（$20/月）
- 后端：Railway Pro 或 AWS ECS
- 数据库：AWS RDS PostgreSQL
- Redis：AWS ElastiCache
- 总成本：$100-500/月

---

## 七、推荐技术栈总结

### 7.1 最终推荐

| 层级 | 技术 | 理由 |
|------|------|------|
| **前端** | Next.js 14 + TypeScript + TailwindCSS | 生态最强，Vercel 部署无缝 |
| **后端** | FastAPI + Python | AI 生态最佳，开发效率高 |
| **Agent 框架** | LangGraph | 可控 Agent 工作流 |
| **数据库** | PostgreSQL + pgvector | 关系型+向量一体化，成本低 |
| **缓存/队列** | Redis (Upstash) | 异步任务队列 |
| **LLM** | Claude 3.5 + GPT-4o-mini | 质量与成本平衡 |
| **部署** | Vercel + Railway + Supabase | MVP 最快上线 |
| **监控** | Langfuse + Sentry | LLM 可观测性 |

### 7.2 目录结构建议

```
tuoke-agent/
├── apps/
│   ├── web/                    # Next.js 前端
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── api/                    # FastAPI 后端
│       ├── app/
│       │   ├── agents/         # AI Agent
│       │   ├── api/            # REST API
│       │   ├── models/         # 数据模型
│       │   ├── services/       # 业务逻辑
│       │   └── workers/        # 异步任务
│       ├── tests/
│       └── pyproject.toml
├── packages/
│   ├── shared/                 # 共享类型/工具
│   └── ui/                     # UI 组件库
├── infra/
│   ├── docker/
│   └── terraform/
├── docs/
└── README.md
```

### 7.3 开发路线图

| 阶段 | 时间 | 目标 | 技术重点 |
|------|------|------|----------|
| **Phase 1** | 2周 | MVP 上线 | Next.js + FastAPI + Supabase |
| **Phase 2** | 2周 | Agent 核心 | LangGraph + pgvector |
| **Phase 3** | 2周 | 邮件自动化 | Redis Queue + SMTP |
| **Phase 4** | 2周 | 多租户 | 认证 + 权限 + 数据隔离 |
| **Phase 5** | 持续 | 优化迭代 | 性能 + 成本 + 体验 |

---

## 八、风险评估

### 8.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| LLM API 成本失控 | 中 | 高 | 使用 GPT-4o-mini、DeepSeek；实现缓存 |
| 邮件到达率低 | 中 | 高 | 使用专业邮件服务（SendGrid、Resend） |
| 数据库性能瓶颈 | 低 | 中 | pgvector 索引优化；考虑分库 |
| 第三方 API 限流 | 中 | 中 | 实现请求队列、重试机制 |

### 8.2 成本估算（MVP）

| 服务 | 月费用 | 说明 |
|------|--------|------|
| Vercel | $0-20 | 免费 tier 够用 |
| Railway | $5-20 | 后端托管 |
| Supabase | $0 | 免费 500MB |
| Upstash Redis | $0 | 免费 tier |
| OpenAI API | $50-200 | 按用量 |
| Anthropic API | $50-200 | 按用量 |
| 域名 + SSL | $1 | .com 域名 |
| **总计** | **$100-450/月** | MVP 阶段 |

---

> **总结**：推荐 FastAPI + PostgreSQL/pgvector + Next.js + LangGraph 技术栈，MVP 阶段使用 Vercel + Railway + Supabase 部署，月成本控制在 $200 以内。该方案兼顾开发效率、成本控制和扩展性，适合快速迭代验证产品。
