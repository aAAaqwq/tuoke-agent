# 拓客智能体 - 产品需求文档 (PRD)

> **协作团队**: Daniel 团队 & Peter 团队
> **创建日期**: 2026-03-06
> **更新日期**: 2026-03-10
> **状态**: ✅ 完整版（基于7轮Agent调研）

---

## 1. 项目概述

### 1.1 项目名称
拓客智能体 (Tuoke Agent)

### 1.2 项目目标
打造**中文市场首个AI Agent自主拓客平台**：用户用自然语言定义目标客户 → AI Agent自主完成发现→筛选→画像→触达→分析全闭环。

### 1.3 目标用户
- **主要**: 中国B2B企业销售团队（SaaS/科技/制造，50-1000人规模）
- **次要**: 出海企业（中英双语拓客）、外企进入中国

### 1.4 核心价值
- **AI Agent自主拓客** — Level 3（非辅助/非自动化，是真正自主）
- **中文原生** — 深度理解中文商业语境 + 企微集成
- **透明定价** — $29-99/月，与客户利益绑定
- **Peter团队产品力** × **Daniel团队AI+开发力** = 差异化壁垒

### 1.5 竞品定位

| 竞品 | 定价 | AI能力 | 中文 | 差距 |
|------|------|--------|------|------|
| Apollo.io | $49-99/月 | AI辅助 | ❌ | 无中文，无企微 |
| Clay | $149-349/月 | AI Agent | ❌ | 贵，无中文 |
| ZoomInfo | $15K/年 | AI情报 | ❌ | 极贵 |
| 探迹 | 不透明 | 弱AI | ✅ | AI弱，定价不透明 |
| **拓客Agent** | **$29-99/月** | **AI Agent** | **✅** | **目标填补空白** |

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Next.js 14 + TailwindCSS + Shadcn/UI | SSR + Vercel AI SDK |
| 后端 | FastAPI (Python 3.11+) | AI生态最佳，异步原生 |
| Agent | OpenClaw (5个专用Agent) | 原生多Agent + Skills |
| 数据库 | PostgreSQL 16 + pgvector | 关系+向量一体化 |
| 缓存/队列 | Redis + Celery | 异步任务队列 |
| LLM | GPT-4o-mini(主) + GPT-4o + DeepSeek V3 | 分层成本优化 |
| 邮件 | Resend / SendGrid | 专业邮件服务 |
| 部署 | Vercel + Railway + Supabase (MVP) | 最快上线 |

### 2.2 系统架构图

```
客户端 (Next.js) → Nginx → FastAPI → OpenClaw Agent层 → 数据层(PG+Redis+MinIO)
                                    ↕
                               Celery Workers
                                    ↕
                          外部服务(LLM/邮件/数据源)
```

详见: `docs/03-system-architecture.md`

---

## 3. 功能模块

### 3.1 核心模块 (5个)

| 模块 | 优先级 | 核心价值 | 工作量 |
|------|--------|----------|--------|
| 线索采集 | P0 | 多源采集→清洗→评分 | 5天 |
| 客户画像 | P0 | AI角色/需求/意向分析 | 4天 |
| 智能触达 | P0 | 个性化邮件/企微序列 | 6天 |
| 效果追踪 | P1 | 漏斗/ROI/A/B测试 | 3天 |
| 管理后台 | P1 | Dashboard+权限+配置 | 4天 |

详见: `docs/04-feature-design.md`

### 3.2 功能优先级

| 功能 | 优先级 | Phase | 负责团队 |
|------|--------|-------|----------|
| 线索采集(单源) | P0 | Phase 1 | Daniel |
| 数据清洗去重 | P0 | Phase 1 | Daniel |
| AI邮件生成 | P0 | Phase 1 | Daniel |
| 邮件触达 | P0 | Phase 1 | Peter |
| 基础Dashboard | P0 | Phase 1 | Peter |
| 用户认证(JWT) | P0 | Phase 1 | Daniel+Peter |
| 客户画像 | P0 | Phase 2 | Daniel |
| 企微触达 | P1 | Phase 2 | Peter |
| 触达序列 | P1 | Phase 2 | Daniel |
| 效果追踪 | P1 | Phase 2 | Peter |
| 多租户 | P1 | Phase 3 | Daniel |
| 开放API | P1 | Phase 3 | Daniel |
| CRM集成 | P1 | Phase 3 | Peter |
| 自动调优 | P2 | Phase 4 | Daniel |
| 预测分析 | P2 | Phase 4 | Daniel |

---

## 4. 开发计划

### 4.1 里程碑

| 阶段 | 目标 | 截止日期 | 状态 |
|------|------|----------|------|
| Phase 1 MVP | 采集+邮件+Dashboard | 2026-03-30 | ⏳ 待开始 |
| Phase 2 增强 | 画像+企微+追踪 | 2026-04-13 | ⏳ 待开始 |
| Phase 3 企业 | 多租户+API+CRM | 2026-04-27 | ⏳ 待开始 |
| Phase 4 智能 | 调优+预测+报告 | 2026-05-11 | ⏳ 待开始 |

详见: `docs/07b-dev-plan.md`

### 4.2 资源需求

#### Daniel 团队 Agent 资源

| Agent | 职责 | 已完成任务 |
|-------|------|-----------|
| 小research | 行业竞品调研 | ✅ 01-industry-research.md + 06b-llm-cases.md |
| 小code | 技术架构+OpenClaw集成 | ✅ 02-tech-stack.md + 02b-openclaw.md + 03-architecture.md + 06-ai-integration.md |
| 小pm | 功能设计+开发计划 | ✅ 04-feature-design.md + 07b-dev-plan.md |
| 小data | 数据方案 | ✅ 05-data-pipeline.md |
| 小ops | 部署方案 | ✅ 07-deployment.md |
| 小a (CEO) | 综合总结 | ✅ 08-final-report.md |

#### 所需密钥/配置

| 服务 | 用途 | 状态 |
|------|------|------|
| 企查查 API Key | 企业数据采集 | ⏳ 待开通 |
| Resend API Key | 邮件发送 | ⏳ 待注册 |
| OpenAI API Key | LLM调用 | ✅ 已有 |
| Vercel 账号 | 前端部署 | ⏳ 待确认 |
| Railway 账号 | 后端部署 | ⏳ 待确认 |
| Supabase 账号 | 数据库 | ⏳ 待确认 |

---

## 5. 验收标准

### 5.1 功能验收 (MVP)
- [ ] 输入行业+职位 → 采集100+线索
- [ ] 自动清洗去重 → 有效率≥80%
- [ ] AI生成个性化邮件 → 每封有2+个性化元素
- [ ] 发送50+封邮件 → 送达率≥90%
- [ ] Dashboard显示核心指标

### 5.2 性能验收
- [ ] API P95 响应时间 < 200ms
- [ ] 前端 LCP < 2s
- [ ] 并发支持 1000 QPS
- [ ] 可用性 99.9% SLA

### 5.3 安全验收
- [ ] JWT认证+RBAC权限
- [ ] 数据加密(AES-256 at rest, TLS 1.3 in transit)
- [ ] SQL注入/XSS防护
- [ ] 个保法合规(同意管理+脱敏)

---

## 6. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| LLM成本失控 | 中 | 高 | 三层模型+缓存+限额 |
| 邮件到达率低 | 中 | 高 | 专业服务+域名预热+SPF/DKIM |
| 数据合规风险 | 中 | 极高 | 公开数据源API+同意管理+脱敏 |
| 竞品跟进 | 高 | 中 | 快速迭代+中文本地化+企微集成 |
| AI幻觉 | 中 | 高 | Prompt约束+安全检查+人工审核 |

---

## 7. 协作机制

### 7.1 沟通渠道
- 飞书群：`oc_45acc85cad802bf6cf21ed24e25465e9`
- Telegram 群：Daniel's super agents Center
- GitHub：https://github.com/opencaio/tuoke-agent

### 7.2 团队分工

| 领域 | Daniel团队 | Peter团队 |
|------|-----------|-----------|
| 后端API + AI Agent + 数据 | ✅ 主导 | — |
| 前端UI + 外部集成 + 运维 | — | ✅ 主导 |
| 测试 | 单元测试 | E2E+集成 |

### 7.3 文档清单

| 文档 | 路径 | 状态 |
|------|------|------|
| PRD | `PRD.md` | ✅ |
| 行业调研 | `docs/01-industry-research.md` | ✅ |
| 技术栈调研 | `docs/02-tech-stack-research.md` | ✅ |
| OpenClaw集成 | `docs/02b-openclaw-integration.md` | ✅ |
| 系统架构 | `docs/03-system-architecture.md` | ✅ |
| 功能设计 | `docs/04-feature-design.md` | ✅ |
| 数据方案 | `docs/05-data-pipeline.md` | ✅ |
| AI集成 | `docs/06-ai-integration.md` | ✅ |
| LLM案例 | `docs/06b-llm-cases.md` | ✅ |
| 部署方案 | `docs/07-deployment.md` | ✅ |
| 开发计划 | `docs/07b-dev-plan.md` | ✅ |
| CEO总结 | `docs/08-final-report.md` | ✅ |

---

## 8. 成本与收益

### 8.1 成本

| 阶段 | 月成本 |
|------|--------|
| MVP | ~$200 |
| 成长期(1K用户) | ~$2,000 |

### 8.2 定价

| 套餐 | 月费 | 功能 |
|------|------|------|
| Basic | $29 | 500线索/月，邮件触达 |
| Pro | $49 | 2000线索/月，多渠道，画像 |
| Enterprise | $99 | 无限线索，API，CRM集成 |

### 8.3 Break-even
**3-7个付费用户即可Break-even。**

---

## 📝 更新日志

| 日期 | 更新内容 | 更新人 |
|------|----------|--------|
| 2026-03-06 | 创建 PRD 模板 | 小a (CEO) |
| 2026-03-10 | 基于7轮调研完善完整PRD | 小a (CEO) |

---

> **下一步**: Daniel审阅 → 与Peter同步 → 启动Phase 1 MVP开发
