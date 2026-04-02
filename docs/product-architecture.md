# 拓客智能体 — 产品架构文档

> **版本:** v1.0
> **日期:** 2026-04-02
> **基于:** PRD v1.0 + 落地评估 + 系统架构设计 + 功能设计
> **目标:** 从产品视角定义模块边界、数据流、状态机、接口和扩展点

---

## 1. 模块拆解

### 1.1 模块全景图

```
┌─────────────────────────────────────────────────────────┐
│                    拓客智能体 Platform                     │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  意图解析  │  线索引擎  │  画像引擎  │  触达引擎  │  效果分析    │
│  Intent   │  Lead    │  Profile │  Reach   │  Analytics  │
│  Parser   │  Engine  │  Engine  │  Engine  │  Engine     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                     Agent 调度层                          │
│                   (Orchestrator)                         │
├─────────────────────────────────────────────────────────┤
│              数据层 (PG + Redis + MinIO)                  │
├─────────────────────────────────────────────────────────┤
│              外部集成 (LLM + 邮件 + 数据源)                │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块详细定义

#### M1: 意图解析器 (Intent Parser)

| 维度 | 描述 |
|------|------|
| **职责** | 将用户自然语言描述解析为结构化采集条件 |
| **输入** | 自然语言文本（如"帮我找深圳的SaaS公司CTO"） |
| **输出** | 结构化JSON：`{industry, company_size, roles[], region[], limit}` |
| **依赖** | LLM API (GPT-4o-mini) |
| **技术实现** | Prompt Engineering + JSON Schema约束 |
| **关键质量** | 解析准确率≥95%（通过Few-shot examples保障） |

#### M2: 线索引擎 (Lead Engine)

| 维度 | 描述 |
|------|------|
| **职责** | 根据采集条件，从数据源采集企业/联系人信息，清洗去重并评分 |
| **输入** | 结构化采集条件 + 数据源配置 |
| **输出** | 清洗后的线索列表（含联系方式、公司信息、评分等级） |
| **依赖** | 企查查API / 天眼查API / LinkedIn / 用户CSV导入 |
| **子模块** | 采集适配器层 → 数据清洗管道 → 去重引擎 → 评分引擎 |
| **关键质量** | 有效率≥80%，去重率≥20% |

#### M3: 画像引擎 (Profile Engine)

| 维度 | 描述 |
|------|------|
| **职责** | 基于线索数据+公开信息，AI生成深度客户画像 |
| **输入** | 线索基础信息（公司/职位/行业/规模） |
| **输出** | 客户画像（角色特征+痛点+意向评分+触达建议） |
| **依赖** | LLM API (GPT-4o) |
| **关键质量** | 画像完整度≥80%（含4个维度），人工审核通过率≥70% |

#### M4: 触达引擎 (Reach Engine)

| 维度 | 描述 |
|------|------|
| **职责** | 基于客户画像生成个性化内容，通过多渠道触达，管理触达序列 |
| **输入** | 客户画像 + 触达策略配置 + 模板 |
| **输出** | 触达记录（渠道/内容/状态/时间） |
| **依赖** | LLM API + Resend(邮件) + 企微API |
| **子模块** | 内容生成器 → 渠道适配器 → 序列编排器 → 时机优化器 |
| **关键质量** | 邮件送达率≥90%，个性化元素≥2个/封 |

#### M5: 效果分析引擎 (Analytics Engine)

| 维度 | 描述 |
|------|------|
| **职责** | 追踪触达效果，分析转化漏斗，计算ROI |
| **输入** | 触达记录 + 事件回调（打开/点击/回复） |
| **输出** | 漏斗数据 + ROI报表 + 优化建议 |
| **依赖** | Webhook事件 + 数据库查询 |
| **关键质量** | 数据延迟<5min，漏斗覆盖5+环节 |

#### M6: Agent调度器 (Orchestrator)

| 维度 | 描述 |
|------|------|
| **职责** | 协调各模块执行顺序，管理任务状态，处理异常 |
| **输入** | 用户操作 / 定时触发 / Webhook事件 |
| **输出** | 任务状态更新 + 进度通知 |
| **依赖** | OpenClaw Agent层 + Celery |
| **关键质量** | 任务成功率≥95%，异常恢复时间<5min |

---

## 2. 数据流图

### 2.1 核心业务数据流

```
[用户输入]
    │ "帮我找深圳SaaS公司CTO"
    ▼
[M1 意图解析器]
    │ {industry:"SaaS", region:"深圳", roles:["CTO"]}
    ▼
[M2 线索引擎]
    │ 采集 → 清洗 → 去重 → 评分
    │ 输出: 线索列表 (100条, A/B/C/D分级)
    ▼
[M3 画像引擎] ←── LLM
    │ 为每条线索生成画像
    │ 输出: 角色/痛点/意向/触达建议
    ▼
[M4 触达引擎] ←── LLM + 邮件服务
    │ 生成个性化邮件 → 选择时机 → 发送
    │ 输出: 触达记录 (sent/delivered/...)
    ▼
[M5 效果分析]
    │ 追踪打开/点击/回复 → 漏斗分析 → ROI
    │ 输出: Dashboard + 报告
    ▼
[用户查看]
```

### 2.2 事件驱动数据流

```
外部事件:
  邮件打开 → Webhook → [M5] 更新触达状态 → 触发跟进策略
  邮件回复 → Webhook → [M5] 更新状态 → [M6] 通知用户
  邮件退回 → Webhook → [M5] 标记失败 → [M2] 降低线索质量分

内部事件:
  采集完成 → [M6] 启动画像任务
  画像完成 → [M6] 启动触达任务
  触达完成 → [M6] 更新Dashboard
  定时任务 → [M6] 检查超时 → 触发跟进/取消
```

### 2.3 数据存储流

```
采集阶段:
  原始数据 → PostgreSQL (prospects表)
  清洗后数据 → PostgreSQL + Elasticsearch (全文搜索)
  向量嵌入 → PostgreSQL pgvector (相似度搜索)

画像阶段:
  画像结果 → PostgreSQL (prospect_profiles表)
  AI原始分析 → PostgreSQL (JSONB字段)

触达阶段:
  触达记录 → PostgreSQL (reach_records表)
  邮件内容 → MinIO (可选，大文本存储)

分析阶段:
  聚合指标 → Redis (缓存实时指标)
  历史报告 → PostgreSQL (reports表)
  文件报告 → MinIO (PDF/Excel)
```

---

## 3. 核心状态机

### 3.1 线索生命周期

```
                    ┌─────────┐
                    │  New     │  (采集入库)
                    └────┬────┘
                         │ 评分完成
                    ┌────▼────┐
                    │ Scored   │  (A/B/C/D分级)
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │  Hot   │ │  Warm  │ │  Cold  │
         │  (A级) │ │ (B/C级)│ │ (D级)  │
         └───┬────┘ └───┬────┘ └───┬────┘
             │          │          │
             ▼          ▼          ▼
         立即触达    培育队列    暂不投入
             │          │
             ▼          ▼
         ┌────────┐ ┌────────┐
         │Reached │ │Nurturing│
         └───┬────┘ └───┬────┘
             │          │
       ┌─────┼─────┐    │ 定期触达
       ▼     ▼     ▼    ▼
   Opened Clicked Replied 升温→Hot
       │     │     │
       └─────┼─────┘
             ▼
      ┌────────────┐
      │ Converted   │  (成交/会议)
      └─────────────┘
```

### 3.2 触达序列状态机

```
[PENDING] ──发送──→ [SENT] ──送达──→ [DELIVERED]
                        │                   │
                        │ 退回               ├── [OPENED] ──→ [CLICKED] ──→ [REPLIED]
                        ▼                   │
                     [BOUNCED]              ├── 超时未打开 → 触发follow_up
                                           │
                                           └── 超时未回复 → 触发value_add → [BREAK_UP]
```

### 3.3 拓客活动状态机

```
[DRAFT] ──启动──→ [COLLECTING] ──完成──→ [PROFILING] ──完成──→ [REACHING] ──完成──→ [COMPLETED]
                     │                  │                   │
                     │ 失败             │ 失败              │ 部分完成
                     ▼                  ▼                   ▼
                  [FAILED]          [FAILED]          [PARTIAL]
                     │                  │                   │
                     └──────── 重试 ────────────────────────┘
```

---

## 4. 接口定义

### 4.1 核心API接口

#### 意图解析

```
POST /api/v1/intent/parse
Request:
  { "text": "帮我找深圳的SaaS公司CTO" }
Response:
  {
    "parsed": {
      "industry": "SaaS",
      "region": ["深圳"],
      "roles": ["CTO", "技术副总裁"],
      "company_size": null,
      "limit": 100
    },
    "confidence": 0.92
  }
```

#### 线索管理

```
POST   /api/v1/prospects/collect        # 启动采集任务
GET    /api/v1/prospects                 # 线索列表 (支持筛选/排序/分页)
GET    /api/v1/prospects/{id}            # 线索详情 (含画像)
POST   /api/v1/prospects/import          # CSV批量导入
PUT    /api/v1/prospects/{id}/status     # 更新线索状态
GET    /api/v1/prospects/export          # 导出 (CSV/Excel)
```

#### 画像相关

```
POST   /api/v1/profiles/generate/{prospect_id}  # 生成单条画像
POST   /api/v1/profiles/batch                    # 批量生成画像
GET    /api/v1/profiles/{prospect_id}            # 获取画像
PUT    /api/v1/profiles/{prospect_id}            # 更新画像 (人工修正)
```

#### 触达管理

```
POST   /api/v1/reaches/send                   # 发送单次触达
POST   /api/v1/reaches/sequence/start         # 启动触达序列
GET    /api/v1/reaches                         # 触达记录列表
GET    /api/v1/reaches/{id}                    # 触达详情
POST   /api/v1/reaches/templates               # 创建触达模板
GET    /api/v1/reaches/templates               # 模板列表
```

#### 活动管理

```
POST   /api/v1/campaigns                # 创建活动
GET    /api/v1/campaigns                # 活动列表
GET    /api/v1/campaigns/{id}           # 活动详情
POST   /api/v1/campaigns/{id}/start     # 启动活动
POST   /api/v1/campaigns/{id}/pause     # 暂停活动
GET    /api/v1/campaigns/{id}/status    # 活动状态+进度
```

#### 分析报告

```
GET    /api/v1/analytics/dashboard      # Dashboard数据
GET    /api/v1/analytics/funnel         # 转化漏斗
GET    /api/v1/analytics/roi            # ROI分析
GET    /api/v1/reports                  # 报告列表
GET    /api/v1/reports/{id}/download    # 下载报告
```

### 4.2 Webhook接口

```
POST   /webhooks/email/events           # 邮件事件 (Resend回调)
POST   /webhooks/wechat/events          # 企微事件
```

### 4.3 接口规范

| 规范 | 约定 |
|------|------|
| 认证 | Bearer JWT (Authorization header) |
| 分页 | `?page=1&page_size=20` |
| 排序 | `?sort=created_at&order=desc` |
| 筛选 | `?status=A&industry=SaaS` |
| 错误码 | HTTP标准 + 业务码 (`TUOKE_001`等) |
| 响应格式 | `{code, data, message, pagination?}` |

---

## 5. 扩展点

### 5.1 数据源扩展

```python
# 数据源适配器接口
class DataSourceAdapter(ABC):
    @abstractmethod
    async def collect(self, criteria: CollectCriteria) -> List[RawProspect]
    
    @abstractmethod
    def get_rate_limit(self) -> RateLimitInfo

# 已实现: QichachaAdapter
# 可扩展: TianyanchaAdapter, LinkedInAdapter, CustomCSVAdapter
```

| 扩展点 | 接口 | 实现复杂度 |
|--------|------|-----------|
| 企查查 | REST API | 低 (1天) |
| 天眼查 | REST API | 低 (1天) |
| LinkedIn | Playwright爬虫 | 中 (3天) |
| 工商公示 | Scrapy爬虫 | 中 (3天) |
| 用户CSV | 文件解析 | 低 (0.5天) |

### 5.2 触达渠道扩展

```python
# 渠道适配器接口
class ChannelAdapter(ABC):
    @abstractmethod
    async def send(self, to: str, content: Content) -> SendResult
    
    @abstractmethod
    async def get_status(self, message_id: str) -> MessageStatus

# 已实现: EmailAdapter (Resend)
# 可扩展: WeChatAdapter, SMSAdapter, LinkedInAdapter
```

| 扩展点 | 实现方式 | 复杂度 |
|--------|---------|--------|
| 邮件 (Resend) | API | 低 (1天) ✅ |
| 企业微信 | 企微API | 中 (3天) |
| LinkedIn InMail | Playwright | 高 (5天) |
| 短信 | 阿里云SMS | 低 (1天) |

### 5.3 AI模型扩展

| 场景 | 当前模型 | 可替换 |
|------|---------|--------|
| 意图解析 | GPT-4o-mini | DeepSeek V3 / GLM-4 |
| 画像生成 | GPT-4o | Claude Opus / GLM-5 |
| 邮件生成 | GPT-4o | Claude / 专用fine-tuned |
| 评分模型 | 规则引擎 | ML模型 (XGBoost) |

### 5.4 集成扩展

| 扩展点 | 方向 | 优先级 |
|--------|------|--------|
| CRM集成 | 双向同步 (HubSpot/Salesforce/销帮帮) | P1 |
| BI集成 | 数据导出 (Metabase/Tableau) | P2 |
| 通讯集成 | Slack/飞书通知 | P2 |
| Webhook | 外部系统订阅拓客事件 | P2 |

---

## 6. 技术选型建议

### 6.1 推荐技术栈

| 层级 | 选型 | 理由 | 备选 |
|------|------|------|------|
| **前端** | Next.js 14 + TailwindCSS + Shadcn/UI | SSR + 快速开发 + AI SDK集成 | — |
| **后端API** | FastAPI (Python 3.11+) | AI生态最佳 + 异步原生 | NestJS (TypeScript) |
| **Agent层** | OpenClaw | 原生多Agent + Skills | LangGraph / CrewAI |
| **数据库** | PostgreSQL 16 + pgvector | 关系+向量一体化 | Supabase (托管) |
| **缓存** | Redis 7 | 高性能缓存 + 队列 + Pub/Sub | — |
| **任务队列** | Celery + Redis | Python生态成熟 | Dramatiq / ARQ |
| **搜索引擎** | Elasticsearch | 全文搜索+聚合分析 | Meilisearch (轻量) |
| **对象存储** | MinIO | S3兼容 + 自托管 | AWS S3 |
| **LLM** | GPT-4o-mini(日常) + GPT-4o(画像/内容) | 性价比最优 | DeepSeek V3 / GLM-5 |
| **邮件** | Resend | 开发者友好 + 事件Webhook | SendGrid |
| **部署** | Vercel(前端) + Railway(后端) | MVP最快上线 | Docker + K8s |

### 6.2 LLM分层策略（成本优化）

```
┌─────────────────────────────────────────┐
│  Layer 1: 快/便宜 (GPT-4o-mini)         │
│  意图解析 / 数据清洗 / 基础评分          │
│  成本: ~$0.15/1M tokens                  │
├─────────────────────────────────────────┤
│  Layer 2: 平衡 (GPT-4o / DeepSeek V3)   │
│  画像生成 / 邮件内容生成                  │
│  成本: ~$2-5/1M tokens                  │
├─────────────────────────────────────────┤
│  Layer 3: 高质量 (Opus / GLM-5)         │
│  复杂策略制定 / 异常处理 / 复杂分析       │
│  成本: ~$15/1M tokens                   │
│  仅在需要时调用                          │
└─────────────────────────────────────────┘
```

### 6.3 部署架构建议

**MVP阶段（≤100用户）：**
```
Vercel (前端) + Railway (后端+Worker) + Supabase (数据库)
月成本: ~$50-100
```

**成长阶段（1K用户）：**
```
Vercel (前端) + K8s (后端集群) + RDS (托管PG) + ElastiCache (Redis)
月成本: ~$500-1000
```

**规模化阶段（10K+用户）：**
```
自建K8s集群 + 读写分离PG + Redis Cluster + ES集群
月成本: ~$2000-5000
```

---

## 附：架构决策记录 (ADR)

### ADR-1: 为什么选 FastAPI 而非 Next.js API Routes？

| 维度 | FastAPI | Next.js API Routes |
|------|---------|-------------------|
| AI生态 | ✅ Python原生 | ⚠️ 需调用外部服务 |
| 异步 | ✅ async/await原生 | ✅ 支持 |
| Agent集成 | ✅ 直接调用OpenClaw SDK | ⚠️ 需HTTP中转 |
| 部署复杂度 | ⚠️ 需独立部署 | ✅ 前后端一体 |

**决策：** 选FastAPI。核心原因：拓客Agent重度依赖Python AI生态，与OpenClaw深度集成，FastAPI是最佳选择。

### ADR-2: 为什么MVP只做邮件触达？

| 渠道 | 可行性 | 风险 | 决策 |
|------|--------|------|------|
| 邮件 | ✅ API成熟，合规可控 | 低 | ✅ MVP |
| 企业微信 | ⚠️ 需企业认证 | 中 | Phase 2 |
| 小红书/脉脉 | ❌ 无API，反爬极严 | 极高 | 不做 |
| 电话 | ⚠️ 需语音服务 | 高 | Phase 3+ |

**决策：** MVP只做邮件。理由：合规、可控、API成熟、送达率可衡量。

### ADR-3: 为什么用规则引擎做评分而非ML模型？

**决策：** MVP用BANT规则引擎。理由：
1. 冷启动无历史数据训练模型
2. 规则引擎透明可解释，用户信任度高
3. 后期积累数据后切换ML模型

---

*架构文档完成：2026-04-02 | AI CPO (产品爪)*
