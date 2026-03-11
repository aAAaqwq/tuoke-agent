# 拓客智能体 - 系统架构设计

> **设计日期**: 2026-03-10  
> **设计人**: 小code (Agent Code)  
> **版本**: V1.0  
> **状态**: 初稿完成

---

## 1. 架构总览

### 1.1 设计原则

| 原则 | 说明 |
|------|------|
| **AI-Native** | 以 AI Agent 为核心，而非传统的规则引擎 |
| **微服务架构** | 各模块独立部署、独立扩展 |
| **事件驱动** | 模块间通过事件总线异步通信 |
| **可观测性** | 全链路追踪、指标监控、日志聚合 |
| **多租户** | 数据隔离、配额管理、计费统计 |

### 1.2 架构全景图

```mermaid
graph TB
    subgraph "客户端层"
        WEB[Web Dashboard]
        SDK[Python/JS SDK]
        CRM[CRM 集成]
        WX[企业微信]
    end

    subgraph "API 网关层"
        GW[Kong / Nginx]
        AUTH[认证授权]
        RATE[限流熔断]
    end

    subgraph "业务服务层"
        API[FastAPI 服务集群]
        WS[WebSocket 服务]
        HOOK[Webhook 接收]
    end

    subgraph "任务调度层"
        CEL[Celery Worker]
        SCH[定时调度器]
        QUEUE[Redis 队列]
    end

    subgraph "AI Agent 层"
        ORCH[主控 Agent<br/>Orchestrator]
        COLL[采集 Agent<br/>Collector]
        REACH[触达 Agent<br/>Reacher]
        ANAL[分析 Agent<br/>Analyzer]
        PROFILE[画像 Agent<br/>Profiler]
    end

    subgraph "数据层"
        PG[(PostgreSQL<br/>+ pgvector)]
        REDIS[(Redis<br/>缓存/队列)]
        MINIO[(MinIO<br/>文件存储)]
        ES[(Elasticsearch<br/>全文搜索)]
    end

    subgraph "外部服务"
        LLM[LLM APIs<br/>OpenAI/Claude/GLM]
        EMAIL[邮件服务<br/>SendGrid/Resend]
        DATA[数据源<br/>Apollo/企查查]
        SOCIAL[社交平台<br/>LinkedIn/企微]
    end

    subgraph "可观测性"
        PROM[Prometheus]
        GRAF[Grafana]
        LOKI[Loki]
        LANG[Langfuse]
    end

    %% 连接关系
    WEB --> GW
    SDK --> GW
    CRM --> GW
    WX --> GW

    GW --> AUTH
    GW --> RATE
    GW --> API
    GW --> WS
    GW --> HOOK

    API --> CEL
    API --> ORCH
    SCH --> CEL
    CEL --> QUEUE

    ORCH --> COLL
    ORCH --> REACH
    ORCH --> ANAL
    ORCH --> PROFILE

    COLL --> DATA
    COLL --> SOCIAL
    REACH --> EMAIL
    REACH --> SOCIAL
    ANAL --> LLM
    PROFILE --> LLM

    API --> PG
    API --> REDIS
    API --> MINIO
    ORCH --> PG
    ORCH --> REDIS

    %% 监控
    API -.-> PROM
    CEL -.-> PROM
    ORCH -.-> LANG
    ORCH -.-> LOKI
```

---

## 2. 微服务划分

### 2.1 服务清单

| 服务名 | 技术栈 | 职责 | 端口 |
|--------|--------|------|------|
| **api-gateway** | Kong / Nginx | 统一入口、认证、限流 | 80/443 |
| **core-api** | FastAPI | 核心业务 API | 8000 |
| **websocket-server** | FastAPI + WebSocket | 实时通信 | 8001 |
| **webhook-receiver** | FastAPI | 接收外部 Webhook | 8002 |
| **celery-worker** | Celery | 异步任务执行 | - |
| **celery-beat** | Celery Beat | 定时任务调度 | - |
| **openclaw-gateway** | OpenClaw | AI Agent 编排 | 3000 |

### 2.2 服务依赖关系

```mermaid
graph LR
    subgraph "前端"
        FE[Next.js App]
    end

    subgraph "网关"
        GW[API Gateway]
    end

    subgraph "核心服务"
        CORE[Core API]
        WS[WebSocket]
        WH[Webhook]
    end

    subgraph "任务层"
        CEL[Celery Workers]
        BEAT[Beat Scheduler]
    end

    subgraph "Agent层"
        CLAW[OpenClaw]
    end

    subgraph "数据层"
        PG[(PostgreSQL)]
        RD[(Redis)]
        MIN[(MinIO)]
    end

    FE --> GW
    GW --> CORE
    GW --> WS
    GW --> WH

    CORE --> CEL
    CORE --> PG
    CORE --> RD
    CORE --> MIN

    CEL --> CLAW
    CLAW --> PG
    CLAW --> RD

    BEAT --> CEL
```

### 2.3 各服务详细设计

#### 2.3.1 Core API（核心服务）

```yaml
服务: core-api
技术栈: FastAPI + Python 3.11+
端口: 8000

模块划分:
  - /api/v1/prospects      # 线索管理
  - /api/v1/campaigns      # 拓客活动
  - /api/v1/contacts       # 联系人
  - /api/v1/reach          # 触达记录
  - /api/v1/analytics      # 数据分析
  - /api/v1/integrations   # 外部集成
  - /api/v1/tenants        # 租户管理

依赖:
  - PostgreSQL (业务数据)
  - Redis (缓存 + 会话)
  - MinIO (文件存储)
  - OpenClaw (Agent 调用)

关键特性:
  - 异步处理 (async/await)
  - 请求验证 (Pydantic)
  - 自动文档 (OpenAPI)
  - JWT 认证
```

#### 2.3.2 Celery Worker（任务执行）

```yaml
服务: celery-worker
技术栈: Celery + Redis
并发模式: prefork (CPU 密集) / gevent (IO 密集)

任务队列:
  - collect:  # 采集任务队列
      priority: 5
      concurrency: 4
  - reach:    # 触达任务队列
      priority: 8
      concurrency: 16
  - analyze:  # 分析任务队列
      priority: 3
      concurrency: 2
  - default:  # 默认队列
      priority: 1
      concurrency: 8

关键任务:
  - tasks.collect.run_collector_agent
  - tasks.reach.send_email_sequence
  - tasks.reach.send_wechat_message
  - tasks.analyze.generate_report
  - tasks.sync.sync_from_crm
```

#### 2.3.3 OpenClaw Gateway（AI 层）

```yaml
服务: openclaw-gateway
技术栈: OpenClaw + Node.js
端口: 3000

Agent 配置:
  orchestrator:
    model: opus46 / glm5
    职责: 任务分发、状态协调、异常处理
    
  collector:
    model: zai47
    skills: [web-scraping, playwright]
    职责: 线索采集、数据清洗
    
  reacher:
    model: opus46
    skills: [multimodal-gen, seo-writing]
    职责: 内容生成、多渠道触达
    
  analyzer:
    model: glm5
    skills: [xlsx, docx]
    职责: 效果分析、报告生成
    
  profiler:
    model: opus46
    skills: [data-analysis]
    职责: 客户画像、意图预测
```

---

## 3. 数据流设计

### 3.1 核心业务数据流

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as Core API
    participant CEL as Celery
    participant COLL as Collector Agent
    participant PROF as Profiler Agent
    participant REACH as Reacher Agent
    participant ANAL as Analyzer Agent
    participant DB as PostgreSQL
    participant ES as Elasticsearch

    U->>API: POST /campaigns (创建拓客活动)
    API->>DB: 保存 Campaign
    API->>CEL: 异步任务: start_campaign
    
    Note over CEL,COLL: 阶段1: 线索采集
    CEL->>COLL: spawn_agent(collector)
    COLL->>DB: 查询目标条件
    COLL->>COLL: 采集外部数据源
    COLL->>DB: 保存 Prospects
    COLL->>ES: 索引 Prospect 文档
    COLL-->>CEL: 返回采集结果
    
    Note over CEL,PROF: 阶段2: 客户画像
    CEL->>PROF: spawn_agent(profiler)
    PROF->>DB: 读取 Prospects
    PROF->>PROF: AI 分析生成画像
    PROF->>DB: 保存 Profile + Score
    PROF-->>CEL: 返回画像结果
    
    Note over CEL,REACH: 阶段3: 智能触达
    CEL->>REACH: spawn_agent(reacher) x N (并行)
    REACH->>DB: 读取 Profile
    REACH->>REACH: AI 生成个性化内容
    REACH->>REACH: 发送邮件/微信
    REACH->>DB: 保存 ReachRecord
    REACH-->>CEL: 返回触达结果
    
    Note over CEL,ANAL: 阶段4: 效果分析
    CEL->>ANAL: spawn_agent(analyzer)
    ANAL->>DB: 读取所有记录
    ANAL->>ANAL: AI 分析效果
    ANAL->>DB: 保存 Report
    ANAL-->>CEL: 返回分析结果
    
    CEL-->>API: 任务完成
    API-->>U: 返回结果/通知
```

### 3.2 实时状态推送流

```mermaid
sequenceDiagram
    participant U as 用户
    participant WS as WebSocket Server
    participant REDIS as Redis Pub/Sub
    participant CEL as Celery Worker
    participant AGENT as Agent

    U->>WS: 连接 WebSocket
    WS->>REDIS: SUBSCRIBE campaign:{id}
    
    CEL->>AGENT: 执行任务
    AGENT->>REDIS: PUBLISH progress
    Note right of AGENT: {"event": "progress", "percent": 30}
    
    REDIS->>WS: 收到消息
    WS->>U: 推送进度更新
    
    AGENT->>REDIS: PUBLISH completed
    REDIS->>WS: 收到消息
    WS->>U: 推送完成通知
```

### 3.3 Webhook 回调流

```mermaid
sequenceDiagram
    participant EXT as 外部服务
    participant WH as Webhook Receiver
    participant API as Core API
    participant DB as PostgreSQL

    EXT->>WH: POST /webhooks/email-opened
    Note right of EXT: {"email_id": "xxx", "opened_at": "..."}
    
    WH->>WH: 验证签名
    WH->>API: 更新触达状态
    API->>DB: UPDATE reach_records
    
    API->>API: 触发后续动作
    Note right of API: 例如: 打开邮件 → 触发跟进邮件
    
    WH-->>EXT: 200 OK
```

---

## 4. Agent 编排架构

### 4.1 多 Agent 协作模型

```mermaid
graph TB
    subgraph "主控层"
        ORCH[🧠 Orchestrator Agent<br/>opus46 / glm5]
    end

    subgraph "执行层"
        COLL[📊 Collector Agent<br/>zai47]
        PROF[👤 Profiler Agent<br/>opus46]
        REACH[📨 Reacher Agent<br/>opus46]
        ANAL[📈 Analyzer Agent<br/>glm5]
    end

    subgraph "状态层"
        PG[(PostgreSQL)]
        RD[(Redis)]
    end

    ORCH -->|任务分发| COLL
    ORCH -->|任务分发| PROF
    ORCH -->|任务分发| REACH
    ORCH -->|任务分发| ANAL

    COLL -->|采集结果| PG
    PROF -->|画像数据| PG
    REACH -->|触达记录| PG
    ANAL -->|分析报告| PG

    ORCH -->|任务状态| RD
    COLL -->|进度| RD
    REACH -->|进度| RD

    ORCH -.->|协调信号| COLL
    ORCH -.->|协调信号| PROF
    ORCH -.->|协调信号| REACH
    ORCH -.->|协调信号| ANAL
```

### 4.2 Agent 工作流状态机

```mermaid
stateDiagram-v2
    [*] --> Pending: 创建任务
    
    Pending --> Collecting: 开始采集
    Collecting --> Collected: 采集完成
    Collecting --> Failed: 采集失败
    
    Collected --> Profiling: 开始画像
    Profiling --> Profiled: 画像完成
    Profiling --> Failed: 画像失败
    
    Profiled --> Reaching: 开始触达
    Reaching --> Reached: 触达完成
    Reaching --> PartialReached: 部分触达
    
    Reached --> Analyzing: 开始分析
    PartialReached --> Analyzing: 开始分析
    Analyzing --> Completed: 分析完成
    
    Failed --> Retrying: 重试
    Retrying --> Collecting: 重新采集
    Retrying --> Failed: 超过重试次数
    
    Completed --> [*]
```

### 4.3 Agent 配置详解

```yaml
# ~/.openclaw/openclaw.json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "xingsuancode/claude-opus-4-6",
        "fallbacks": ["zai/glm-5", "moonshot/kimi-k2.5"]
      },
      "subagents": {
        "model": "zai/glm-4.7",
        "maxConcurrent": 8,
        "runTimeoutSeconds": 600
      }
    },
    "list": [
      {
        "agentId": "tuoke-orchestrator",
        "name": "拓客主控",
        "model": { "primary": "xingsuancode/claude-opus-4-6" },
        "skills": ["tuoke-skill"],
        "description": "拓客流程主控 Agent，负责任务分发和协调"
      },
      {
        "agentId": "tuoke-collector",
        "name": "线索采集",
        "model": { "primary": "zai/glm-4.7" },
        "skills": ["web-scraping-automation", "playwright-automation"],
        "description": "从外部数据源采集潜在客户信息"
      },
      {
        "agentId": "tuoke-profiler",
        "name": "客户画像",
        "model": { "primary": "xingsuancode/claude-opus-4-6" },
        "skills": ["data-analysis"],
        "description": "分析客户数据，生成客户画像和意图预测"
      },
      {
        "agentId": "tuoke-reacher",
        "name": "智能触达",
        "model": { "primary": "xingsuancode/claude-opus-4-6" },
        "skills": ["multimodal-gen", "seo-content-writing"],
        "description": "生成个性化触达内容并执行多渠道触达"
      },
      {
        "agentId": "tuoke-analyzer",
        "name": "效果分析",
        "model": { "primary": "zai/glm-5" },
        "skills": ["xlsx", "docx"],
        "description": "分析触达效果，生成优化报告"
      }
    ]
  }
}
```

### 4.4 Agent 调用示例

```python
# api/services/agent_orchestrator.py
from typing import Dict, List
import httpx

class TuokeAgentOrchestrator:
    """拓客 Agent 编排器"""
    
    def __init__(self, openclaw_url: str = "http://localhost:3000"):
        self.openclaw_url = openclaw_url
        self.client = httpx.AsyncClient()
    
    async def run_campaign(self, campaign_id: str) -> Dict:
        """执行完整的拓客活动"""
        
        # 1. 启动采集 Agent
        collector_session = await self._spawn_agent(
            agent_type="tuoke-collector",
            task=f"为活动 {campaign_id} 采集潜在客户",
            label=f"collect-{campaign_id}"
        )
        
        # 2. 等待采集完成
        prospects = await self._wait_for_result(collector_session)
        await self._save_prospects(campaign_id, prospects)
        
        # 3. 启动画像 Agent (批量)
        profiler_tasks = []
        for prospect in prospects[:100]:  # 限制并发数
            task = await self._spawn_agent(
                agent_type="tuoke-profiler",
                task=f"为 {prospect['name']} 生成客户画像",
                label=f"profile-{prospect['id']}"
            )
            profiler_tasks.append(task)
        
        profiles = await self._wait_for_all(profiler_tasks)
        await self._save_profiles(profiles)
        
        # 4. 启动触达 Agent (并行)
        reacher_tasks = []
        for profile in profiles:
            task = await self._spawn_agent(
                agent_type="tuoke-reacher",
                task=f"为 {profile['name']} 生成并发送个性化触达内容",
                label=f"reach-{profile['id']}"
            )
            reacher_tasks.append(task)
        
        reach_results = await self._wait_for_all(reacher_tasks)
        await self._save_reach_records(reach_results)
        
        # 5. 启动分析 Agent
        analyzer_session = await self._spawn_agent(
            agent_type="tuoke-analyzer",
            task=f"分析活动 {campaign_id} 的触达效果并生成报告",
            label=f"analyze-{campaign_id}"
        )
        
        report = await self._wait_for_result(analyzer_session)
        await self._save_report(campaign_id, report)
        
        return {
            "campaign_id": campaign_id,
            "prospects_collected": len(prospects),
            "profiles_generated": len(profiles),
            "reaches_sent": len(reach_results),
            "report": report
        }
    
    async def _spawn_agent(
        self, 
        agent_type: str, 
        task: str, 
        label: str
    ) -> str:
        """启动子 Agent"""
        resp = await self.client.post(
            f"{self.openclaw_url}/api/sessions/spawn",
            json={
                "task": task,
                "label": label,
                "agentId": agent_type,
                "timeoutSeconds": 300
            }
        )
        return resp.json()["sessionKey"]
    
    async def _wait_for_result(self, session_key: str) -> Dict:
        """等待 Agent 完成"""
        # 实现轮询或 WebSocket 监听
        pass
    
    async def _wait_for_all(self, session_keys: List[str]) -> List[Dict]:
        """等待所有 Agent 完成"""
        # 并行等待
        pass
```

---

## 5. API 网关设计

### 5.1 网关架构

```mermaid
graph TB
    subgraph "客户端"
        WEB[Web App]
        MOB[Mobile App]
        SDK[SDK]
        CRM[CRM Integration]
    end

    subgraph "API Gateway (Kong)"
        SSL[SSL Termination]
        AUTH[JWT Auth]
        RATE[Rate Limiting]
        ROUTE[路由分发]
        LOG[访问日志]
    end

    subgraph "后端服务"
        API[Core API<br/>:8000]
        WS[WebSocket<br/>:8001]
        HOOK[Webhook<br/>:8002]
    end

    WEB --> SSL
    MOB --> SSL
    SDK --> SSL
    CRM --> SSL

    SSL --> AUTH
    AUTH --> RATE
    RATE --> ROUTE
    ROUTE --> LOG

    ROUTE -->|/api/*| API
    ROUTE -->|/ws/*| WS
    ROUTE -->|/webhooks/*| HOOK
```

### 5.2 API 路由设计

```yaml
# API 路由规范
base_path: /api/v1

认证相关:
  POST   /auth/login              # 登录
  POST   /auth/refresh            # 刷新 Token
  POST   /auth/logout             # 登出

租户管理:
  GET    /tenants                 # 租户列表 (Admin)
  POST   /tenants                 # 创建租户 (Admin)
  GET    /tenants/{id}            # 租户详情
  PUT    /tenants/{id}            # 更新租户
  DELETE /tenants/{id}            # 删除租户

拓客活动:
  GET    /campaigns               # 活动列表
  POST   /campaigns               # 创建活动
  GET    /campaigns/{id}          # 活动详情
  PUT    /campaigns/{id}          # 更新活动
  DELETE /campaigns/{id}          # 删除活动
  POST   /campaigns/{id}/start    # 启动活动
  POST   /campaigns/{id}/pause    # 暂停活动
  GET    /campaigns/{id}/status   # 活动状态

线索管理:
  GET    /prospects               # 线索列表
  POST   /prospects               # 创建线索
  POST   /prospects/import        # 批量导入
  GET    /prospects/{id}          # 线索详情
  PUT    /prospects/{id}          # 更新线索
  DELETE /prospects/{id}          # 删除线索
  GET    /prospects/{id}/profile  # 线索画像

触达管理:
  GET    /reaches                 # 触达记录列表
  POST   /reaches                 # 创建触达
  GET    /reaches/{id}            # 触达详情
  GET    /reaches/{id}/events     # 触达事件 (打开/点击)

分析报告:
  GET    /analytics/dashboard     # 仪表盘数据
  GET    /analytics/campaigns     # 活动分析
  GET    /analytics/reaches       # 触达分析
  GET    /reports                 # 报告列表
  GET    /reports/{id}            # 报告详情
  GET    /reports/{id}/download   # 下载报告

集成管理:
  GET    /integrations            # 集成列表
  POST   /integrations            # 创建集成
  GET    /integrations/{id}       # 集成详情
  DELETE /integrations/{id}       # 删除集成
  POST   /integrations/{id}/sync  # 触发同步

Webhook:
  POST   /webhooks/email          # 邮件事件回调
  POST   /webhooks/wechat         # 微信事件回调
  POST   /webhooks/crm            # CRM 事件回调
```

### 5.3 限流策略

```yaml
# Kong 限流配置
rate_limiting:
  # 全局限流
  global:
    minute: 10000
    hour: 100000
    
  # 认证 API
  auth:
    minute: 60
    hour: 1000
    
  # 业务 API
  business:
    minute: 300
    hour: 10000
    
  # 触达 API (更严格)
  reach:
    minute: 100
    hour: 2000
    
  # 租户级别限流
  tenant:
    basic:
      day: 1000
    pro:
      day: 10000
    enterprise:
      day: unlimited
```

### 5.4 认证授权

```yaml
# 认证方案
authentication:
  type: JWT
  algorithm: RS256
  
  token_expiry:
    access_token: 15m
    refresh_token: 7d
    
  claims:
    - sub (user_id)
    - tenant_id
    - role
    - permissions
    - exp
    - iat

authorization:
  model: RBAC
  
  roles:
    admin:
      - 全部权限
    manager:
      - campaigns:read,write
      - prospects:read,write
      - reaches:read
      - reports:read
    member:
      - campaigns:read
      - prospects:read
      - reaches:read
    viewer:
      - 全部只读
```

---

## 6. 核心组件设计

### 6.1 线索采集引擎 (Collector Engine)

#### 架构图

```mermaid
graph TB
    subgraph "采集引擎"
        ORCH[采集协调器]
        QUEUE[采集队列]
        WORKERS[采集 Workers]
    end

    subgraph "数据源适配器"
        AP[Apollo Adapter]
        QCC[企查查 Adapter]
        TYC[天眼查 Adapter]
        LI[LinkedIn Adapter]
        WEB[网页爬虫 Adapter]
    end

    subgraph "数据处理"
        CLEAN[数据清洗]
        DEDUP[去重引擎]
        ENRICH[数据增强]
        VAL[验证引擎]
    end

    subgraph "存储"
        PG[(PostgreSQL)]
        ES[(Elasticsearch)]
    end

    ORCH --> QUEUE
    QUEUE --> WORKERS

    WORKERS --> AP
    WORKERS --> QCC
    WORKERS --> TYC
    WORKERS --> LI
    WORKERS --> WEB

    AP --> CLEAN
    QCC --> CLEAN
    TYC --> CLEAN
    LI --> CLEAN
    WEB --> CLEAN

    CLEAN --> DEDUP
    DEDUP --> ENRICH
    ENRICH --> VAL
    VAL --> PG
    VAL --> ES
```

#### 采集任务配置

```yaml
# 采集任务配置示例
collect_task:
  campaign_id: "camp_001"
  targets:
    - industry: "SaaS"
      company_size: "50-200"
      roles: ["CTO", "VP Engineering", "Engineering Manager"]
      region: "China"
      limit: 1000
      
    - industry: "制造业"
      company_size: "200-1000"
      roles: ["CIO", "IT Director"]
      region: "China"
      limit: 500

  data_sources:
    - name: "企查查"
      priority: 1
      enabled: true
      
    - name: "天眼查"
      priority: 2
      enabled: true
      
    - name: "LinkedIn"
      priority: 3
      enabled: false  # 需要代理

  processing:
    dedup_strategy: "email+company"
    enrichment:
      - "company_info"    # 补充公司信息
      - "contact_verify"  # 验证联系方式
      - "social_links"    # 补充社交链接
    
    validation:
      email_verify: true
      phone_verify: false
```

#### 数据清洗规则

```python
# api/services/collector/data_cleaner.py
from typing import List, Dict
import re

class DataCleaner:
    """数据清洗引擎"""
    
    def clean_prospect(self, raw_data: Dict) -> Dict:
        """清洗单条数据"""
        cleaned = {}
        
        # 1. 标准化字段名
        field_mapping = {
            "姓名": "name",
            "公司": "company",
            "邮箱": "email",
            "电话": "phone",
            "职位": "title"
        }
        for cn_name, en_name in field_mapping.items():
            if cn_name in raw_data:
                cleaned[en_name] = raw_data[cn_name]
        
        # 2. 邮箱标准化
        if "email" in cleaned:
            cleaned["email"] = self._normalize_email(cleaned["email"])
            cleaned["email_valid"] = self._validate_email(cleaned["email"])
        
        # 3. 电话标准化
        if "phone" in cleaned:
            cleaned["phone"] = self._normalize_phone(cleaned["phone"])
        
        # 4. 公司名称标准化
        if "company" in cleaned:
            cleaned["company"] = self._normalize_company_name(cleaned["company"])
        
        # 5. 去除无效数据
        if not cleaned.get("email_valid"):
            return None
            
        return cleaned
    
    def _normalize_email(self, email: str) -> str:
        """邮箱标准化"""
        email = email.lower().strip()
        # 移除常见拼写错误
        email = re.sub(r'\s+', '', email)
        return email
    
    def _validate_email(self, email: str) -> bool:
        """邮箱格式验证"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _normalize_phone(self, phone: str) -> str:
        """电话标准化"""
        # 只保留数字和+号
        phone = re.sub(r'[^\d+]', '', phone)
        # 中国号码加区号
        if phone.startswith('1') and len(phone) == 11:
            phone = '+86' + phone
        return phone
    
    def _normalize_company_name(self, name: str) -> str:
        """公司名称标准化"""
        # 移除常见后缀
        suffixes = ['有限公司', '有限责任公司', '股份有限公司', 'Ltd', 'Inc', 'Corp']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name.strip()
```

### 6.2 客户画像引擎 (Profiler Engine)

#### 画像维度

```yaml
customer_profile:
  # 基础信息
  basic:
    - name
    - title
    - company
    - industry
    - company_size
    - location
    
  # 联系方式
  contact:
    - email (primary)
    - phone
    - linkedin_url
    - wechat
    
  # 行为特征
  behavior:
    - email_open_rate      # 邮件打开率
    - click_patterns       # 点击模式
    - response_time        # 响应时间
    - preferred_channel    # 偏好渠道
    
  # 意图信号
  intent:
    - buying_signal_score  # 购买意向分 (0-100)
    - engagement_score     # 参与度分
    - pain_points          # 痛点关键词
    - interests            # 兴趣标签
    
  # 价值评估
  value:
    - customer_lifetime_value  # 潜在 CLV
    - deal_size_estimate       # 预估交易额
    - priority_level           # 优先级 (A/B/C)
```

#### 画像生成流程

```mermaid
sequenceDiagram
    participant DATA as 原始数据
    participant PROF as Profiler Agent
    participant LLM as LLM API
    participant DB as PostgreSQL

    DATA->>PROF: 输入 Prospect 数据
    PROF->>PROF: 数据预处理
    
    PROF->>LLM: 分析行业/职位特征
    LLM-->>PROF: 返回特征标签
    
    PROF->>LLM: 推断潜在需求/痛点
    LLM-->>PROF: 返回需求分析
    
    PROF->>LLM: 评估购买意向
    LLM-->>PROF: 返回意向分数
    
    PROF->>PROF: 综合评估价值
    PROF->>DB: 保存 Profile
```

#### 画像 Agent Prompt 模板

```markdown
# 客户画像生成任务

## 输入数据
- 姓名: {name}
- 职位: {title}
- 公司: {company}
- 行业: {industry}
- 公司规模: {company_size}
- 地区: {region}

## 分析任务

请根据以上信息，生成客户画像，包括：

### 1. 角色特征
- 决策权限级别 (高/中/低)
- 关注重点 (技术/业务/成本/效率)
- 可能的 KPI

### 2. 需求分析
- 潜在痛点 (3-5个)
- 可能的购买动机
- 预期的解决方案

### 3. 意向评估
- 购买意向分数 (0-100)
- 参与度预测 (高/中/低)
- 最佳触达时机

### 4. 触达建议
- 推荐触达渠道
- 推荐沟通风格
- 建议避开的主题

## 输出格式
返回 JSON 格式的画像数据。
```

### 6.3 智能触达引擎 (Reach Engine)

#### 多渠道触达架构

```mermaid
graph TB
    subgraph "触达协调器"
        COORD[Reach Coordinator]
        SCHED[调度器]
        QUEUE[触达队列]
    end

    subgraph "内容生成"
        CONTENT[Content Generator]
        LLM[LLM API]
        TEMPLATE[模板引擎]
    end

    subgraph "渠道适配器"
        EMAIL[邮件适配器<br/>SendGrid/Resend]
        WECHAT[企微适配器<br/>企微API]
        SMS[短信适配器]
        LI[LinkedIn 适配器]
    end

    subgraph "追踪系统"
        TRACK[追踪服务]
        PIXEL[追踪像素]
        LINKS[追踪链接]
    end

    COORD --> SCHED
    SCHED --> QUEUE
    QUEUE --> CONTENT
    CONTENT --> LLM
    CONTENT --> TEMPLATE
    
    CONTENT --> EMAIL
    CONTENT --> WECHAT
    CONTENT --> SMS
    CONTENT --> LI
    
    EMAIL --> TRACK
    WECHAT --> TRACK
    SMS --> TRACK
    LI --> TRACK
    
    TRACK --> PIXEL
    TRACK --> LINKS
```

#### 触达策略配置

```yaml
# 触达策略配置
reach_strategy:
  campaign_id: "camp_001"
  
  sequences:
    # 邮件序列
    - channel: "email"
      steps:
        - step: 1
          delay: "0h"
          type: "intro"          # 介绍邮件
          template: "intro_saas"
          personalization:
            - "company_name"
            - "recipient_name"
            - "industry_insight"
            
        - step: 2
          delay: "48h"           # 48小时后
          type: "follow_up"      # 跟进邮件
          condition: "not_opened" # 条件: 未打开
          template: "follow_up_saas"
          
        - step: 3
          delay: "72h"
          type: "value_add"      # 价值邮件
          condition: "not_replied"
          template: "case_study"
          
        - step: 4
          delay: "168h"          # 7天后
          type: "break_up"       # 结束邮件
          condition: "not_replied"
          template: "break_up"
    
    # 企微跟进
    - channel: "wechat"
      steps:
        - step: 1
          delay: "24h"
          type: "friend_request"
          template: "wx_intro"
          
        - step: 2
          delay: "48h"
          type: "message"
          condition: "accepted"
          template: "wx_follow"

  limits:
    max_reach_per_day: 50
    min_interval_minutes: 30
    respect_timezone: true
    quiet_hours: "22:00-08:00"
```

#### 内容生成 Agent

```python
# api/services/reach/content_generator.py
from typing import Dict
from openai import AsyncOpenAI

class ContentGenerator:
    """个性化内容生成器"""
    
    def __init__(self):
        self.client = AsyncOpenAI()
    
    async def generate_email(
        self, 
        prospect: Dict,
        profile: Dict,
        template_type: str
    ) -> Dict:
        """生成个性化邮件"""
        
        # 构建提示词
        prompt = self._build_prompt(prospect, profile, template_type)
        
        # 调用 LLM
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # 解析生成的内容
        return self._parse_email_content(content)
    
    def _build_prompt(
        self, 
        prospect: Dict, 
        profile: Dict,
        template_type: str
    ) -> str:
        """构建生成提示"""
        return f"""
为以下潜在客户生成一封{template_type}邮件：

## 客户信息
- 姓名: {prospect['name']}
- 职位: {prospect['title']}
- 公司: {prospect['company']}
- 行业: {prospect['industry']}

## 客户画像
- 关注重点: {profile['focus_areas']}
- 潜在痛点: {profile['pain_points']}
- 沟通风格偏好: {profile['communication_style']}

## 邮件要求
- 邮件类型: {template_type}
- 语气: 专业但不生硬
- 长度: 150-200字
- 包含个性化元素
- 明确的 CTA

## 输出格式
Subject: [邮件主题]

[邮件正文]
"""
    
    def _get_system_prompt(self) -> str:
        return """你是一位专业的 B2B 销售文案专家。
你的任务是撰写个性化、高转化率的销售邮件。
遵循以下原则：
1. 开头抓住注意力
2. 展示对客户痛点的理解
3. 提供具体的价值主张
4. 使用清晰的 CTA
5. 避免营销腔调
6. 语气专业但友好"""
```

### 6.4 效果追踪引擎 (Analytics Engine)

#### 指标体系

```yaml
analytics_metrics:
  # 采集指标
  collection:
    - total_prospects        # 总线索数
    - valid_prospects        # 有效线索数
    - enrichment_rate        # 数据增强率
    - dedup_rate             # 去重率
    
  # 触达指标
  reach:
    - emails_sent            # 发送邮件数
    - emails_delivered       # 送达数
    - delivery_rate          # 送达率
    - emails_opened          # 打开数
    - open_rate              # 打开率
    - links_clicked          # 点击数
    - click_rate             # 点击率
    - replies                # 回复数
    - reply_rate             # 回复率
    - unsubscribes           # 取消订阅数
    
  # 转化指标
  conversion:
    - meetings_booked        # 预约会议数
    - demos_scheduled        # 演示预约数
    - opportunities          # 商机数
    - pipeline_value         # 管道价值
    - closed_won             # 成交数
    - revenue                # 收入
    
  # 效率指标
  efficiency:
    - time_to_first_reach    # 首次触达时间
    - avg_response_time      # 平均响应时间
    - cost_per_lead          # 单线索成本
    - cost_per_meeting       # 单会议成本
    - roi                    # 投资回报率
```

#### 分析报告生成

```mermaid
graph LR
    subgraph "数据采集"
        DB[(PostgreSQL)]
        ES[(Elasticsearch)]
    end

    subgraph "数据处理"
        AGG[聚合计算]
        TREND[趋势分析]
        COMP[对比分析]
    end

    subgraph "报告生成"
        DOCX[Word 报告]
        XLSX[Excel 报告]
        PDF[PDF 报告]
    end

    DB --> AGG
    ES --> AGG
    AGG --> TREND
    AGG --> COMP
    TREND --> DOCX
    TREND --> XLSX
    COMP --> PDF
```

---

## 7. 数据库设计

### 7.1 核心表结构

```sql
-- 租户表
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'basic',  -- basic, pro, enterprise
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 拓客活动表
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, running, paused, completed
    target_criteria JSONB,  -- 目标条件
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 线索表
CREATE TABLE prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    campaign_id UUID REFERENCES campaigns(id),
    
    -- 基础信息
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    title VARCHAR(255),
    
    -- 公司信息
    industry VARCHAR(100),
    company_size VARCHAR(50),
    company_website VARCHAR(255),
    
    -- 社交链接
    linkedin_url VARCHAR(255),
    wechat_id VARCHAR(100),
    
    -- 状态
    status VARCHAR(50) DEFAULT 'new',  -- new, contacted, responded, qualified, converted, churned
    
    -- 元数据
    source VARCHAR(100),  -- 来源
    data_quality_score INTEGER,  -- 数据质量分
    
    -- 向量嵌入 (用于相似度搜索)
    embedding vector(1536),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, email)
);

-- 客户画像表
CREATE TABLE prospect_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID REFERENCES prospects(id),
    
    -- 角色特征
    decision_level VARCHAR(50),  -- high, medium, low
    focus_areas TEXT[],  -- 关注领域
    possible_kpis TEXT[],  -- 可能的 KPI
    
    -- 需求分析
    pain_points TEXT[],  -- 痛点
    buying_motivations TEXT[],  -- 购买动机
    expected_solutions TEXT[],  -- 预期方案
    
    -- 意向评估
    buying_signal_score INTEGER,  -- 0-100
    engagement_score INTEGER,  -- 0-100
    priority_level VARCHAR(10),  -- A, B, C
    
    -- 触达建议
    preferred_channel VARCHAR(50),  -- email, wechat, phone
    communication_style VARCHAR(50),  -- formal, casual, technical
    best_reach_time VARCHAR(50),  -- morning, afternoon, evening
    
    -- AI 生成的原始分析
    raw_analysis JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 触达记录表
CREATE TABLE reach_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    campaign_id UUID REFERENCES campaigns(id),
    prospect_id UUID REFERENCES prospects(id),
    
    -- 触达信息
    channel VARCHAR(50),  -- email, wechat, phone, linkedin
    type VARCHAR(50),  -- intro, follow_up, value_add, break_up
    sequence_step INTEGER,
    
    -- 内容
    subject VARCHAR(500),  -- 邮件主题
    content TEXT,  -- 内容
    
    -- 状态
    status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, delivered, opened, clicked, replied, bounced
    
    -- 时间戳
    scheduled_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    
    -- 追踪数据
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    tracking_data JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 分析报告表
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    campaign_id UUID REFERENCES campaigns(id),
    
    type VARCHAR(50),  -- campaign_summary, reach_analysis, conversion_report
    period_start DATE,
    period_end DATE,
    
    -- 报告数据
    metrics JSONB,  -- 指标数据
    insights TEXT[],  -- AI 洞察
    recommendations TEXT[],  -- AI 建议
    
    -- 文件
    file_url VARCHAR(500),
    file_format VARCHAR(20),  -- pdf, xlsx, docx
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 向量索引
CREATE INDEX ON prospects USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 全文搜索索引
CREATE INDEX idx_prospects_search ON prospects 
    USING GIN (to_tsvector('english', name || ' ' || company || ' ' || title));
```

### 7.2 索引策略

```sql
-- 高频查询索引
CREATE INDEX idx_prospects_tenant ON prospects(tenant_id);
CREATE INDEX idx_prospects_campaign ON prospects(campaign_id);
CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_email ON prospects(email);

CREATE INDEX idx_reach_records_prospect ON reach_records(prospect_id);
CREATE INDEX idx_reach_records_status ON reach_records(status);
CREATE INDEX idx_reach_records_scheduled ON reach_records(scheduled_at);

-- 复合索引
CREATE INDEX idx_prospects_tenant_campaign ON prospects(tenant_id, campaign_id);
CREATE INDEX idx_reach_tenant_campaign ON reach_records(tenant_id, campaign_id);
```

---

## 8. 部署架构

### 8.1 容器编排

```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Gateway
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - core-api
      - websocket-server

  # Core API
  core-api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/tuoke
      - REDIS_URL=redis://redis:6379/0
      - OPENCLAW_URL=http://openclaw:3000
    depends_on:
      - postgres
      - redis
      - openclaw
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # WebSocket Server
  websocket-server:
    build:
      context: ./api
      dockerfile: Dockerfile.ws
    environment:
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis

  # Celery Worker
  celery-worker:
    build:
      context: ./api
      dockerfile: Dockerfile
    command: celery -A app.tasks worker -l info -c 8
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/tuoke
      - REDIS_URL=redis://redis:6379/0
      - OPENCLAW_URL=http://openclaw:3000
    depends_on:
      - postgres
      - redis
      - openclaw
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # Celery Beat
  celery-beat:
    build:
      context: ./api
      dockerfile: Dockerfile
    command: celery -A app.tasks beat -l info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # OpenClaw Gateway
  openclaw:
    image: openclaw/openclaw:latest
    ports:
      - "3000:3000"
    volumes:
      - ./openclaw-config:/root/.openclaw
    environment:
      - NODE_ENV=production

  # PostgreSQL
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=tuoke
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # MinIO (文件存储)
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=password
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 8.2 Kubernetes 部署 (生产)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tuoke-core-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tuoke-core-api
  template:
    metadata:
      labels:
        app: tuoke-core-api
    spec:
      containers:
      - name: api
        image: tuoke/core-api:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tuoke-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tuoke-celery-worker
spec:
  replicas: 4
  selector:
    matchLabels:
      app: tuoke-celery-worker
  template:
    metadata:
      labels:
        app: tuoke-celery-worker
    spec:
      containers:
      - name: worker
        image: tuoke/core-api:v1.0
        command: ["celery", "-A", "app.tasks", "worker", "-l", "info", "-c", "8"]
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 2Gi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tuoke-celery-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tuoke-celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: External
    external:
      metric:
        name: celery_queue_length
      target:
        type: AverageValue
        averageValue: 100
```

---

## 9. 可观测性设计

### 9.1 监控架构

```mermaid
graph TB
    subgraph "数据采集"
        APP[应用指标]
        LOG[日志]
        TRACE[追踪]
    end

    subgraph "存储"
        PROM[(Prometheus)]
        LOKI[(Loki)]
        TEMPO[(Tempo)]
    end

    subgraph "可视化"
        GRAF[Grafana]
        ALERT[AlertManager]
    end

    subgraph "LLM 可观测"
        LANG[Langfuse]
    end

    APP --> PROM
    LOG --> LOKI
    TRACE --> TEMPO

    PROM --> GRAF
    LOKI --> GRAF
    TEMPO --> GRAF

    PROM --> ALERT
    APP --> LANG
```

### 9.2 关键指标

```yaml
# Prometheus 指标
metrics:
  # API 指标
  api:
    - http_requests_total
    - http_request_duration_seconds
    - http_requests_in_progress
    
  # Celery 指标
  celery:
    - celery_tasks_total
    - celery_task_duration_seconds
    - celery_queue_length
    - celery_workers_online
    
  # Agent 指标
  agent:
    - agent_tasks_total
    - agent_task_duration_seconds
    - agent_llm_tokens_total
    - agent_llm_cost_dollars
    
  # 业务指标
  business:
    - tuoke_prospects_total
    - tuoke_reaches_total
    - tuoke_opens_total
    - tuoke_replies_total
```

### 9.3 告警规则

```yaml
# alertmanager/rules.yml
groups:
  - name: tuoke-alerts
    rules:
      # API 响应时间
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API 响应时间过高"
          
      # Celery 队列积压
      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery 队列积压"
          
      # Agent 失败率
      - alert: HighAgentFailureRate
        expr: rate(agent_tasks_total{status="failed"}[5m]) / rate(agent_tasks_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Agent 任务失败率过高"
          
      # LLM 成本异常
      - alert: HighLLMCost
        expr: rate(agent_llm_cost_dollars[1h]) > 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "LLM 成本异常增长"
```

---

## 10. 安全设计

### 10.1 安全架构

```mermaid
graph TB
    subgraph "网络安全"
        FW[防火墙]
        WAF[Web 应用防火墙]
        DDoS[DDoS 防护]
    end

    subgraph "认证授权"
        IAM[身份认证]
        RBAC[角色权限]
        MFA[多因素认证]
    end

    subgraph "数据安全"
        ENC[加密存储]
        MASK[数据脱敏]
        AUDIT[审计日志]
    end

    subgraph "API 安全"
        RATE[限流]
        KEY[API Key]
        SIGN[签名验证]
    end
```

### 10.2 数据安全策略

```yaml
security:
  # 数据加密
  encryption:
    at_rest:
      algorithm: AES-256-GCM
      key_management: AWS KMS / HashiCorp Vault
    in_transit:
      protocol: TLS 1.3
      certificate: Let's Encrypt
    
  # 数据脱敏
  masking:
    email: "a***@example.com"
    phone: "138****1234"
    id_card: "110***********1234"
    
  # 访问控制
  access_control:
    model: RBAC
    principle: least_privilege
    session_timeout: 30m
    
  # 审计日志
  audit:
    events:
      - user_login
      - data_access
      - data_export
      - config_change
      - admin_action
    retention: 90d
    
  # 合规
  compliance:
    - GDPR (欧盟用户)
    - 个人信息保护法 (中国用户)
    - SOC 2 Type II
```

---

## 11. 扩展性设计

### 11.1 水平扩展策略

```yaml
scaling:
  # API 层
  api:
    strategy: horizontal
    min_replicas: 2
    max_replicas: 20
    metric: cpu_usage
    target: 70%
    
  # Worker 层
  celery:
    strategy: queue_based
    queues:
      collect:
        min: 2
        max: 10
        scale_on: queue_length > 100
      reach:
        min: 4
        max: 20
        scale_on: queue_length > 50
        
  # Agent 层
  agent:
    strategy: concurrent_limit
    max_concurrent_per_worker: 8
    max_total_concurrent: 100
    
  # 数据库层
  database:
    strategy: read_replica
    write: primary
    read: replicas (1-3)
    connection_pooling: PgBouncer
```

### 11.2 多租户隔离

```yaml
multi_tenancy:
  # 数据隔离
  data_isolation:
    strategy: shared_database  # shared_database, separate_database, separate_schema
    row_level_security: true
    tenant_column: tenant_id
    
  # 资源隔离
  resource_isolation:
    rate_limits:
      basic: 1000/day
      pro: 10000/day
      enterprise: unlimited
    storage_quotas:
      basic: 1GB
      pro: 10GB
      enterprise: 100GB
    concurrent_tasks:
      basic: 5
      pro: 20
      enterprise: 100
      
  # 计费
  billing:
    model: usage_based
    metrics:
      - prospects_collected
      - reaches_sent
      - api_calls
    billing_cycle: monthly
```

---

## 12. 实施路线图

### 12.1 分阶段实施

| 阶段 | 时间 | 目标 | 关键交付物 |
|------|------|------|-----------|
| **Phase 1: MVP** | 2周 | 核心功能上线 | 线索采集 + 邮件触达 + 基础分析 |
| **Phase 2: 增强版** | 2周 | 多渠道 + 画像 | 企微集成 + 客户画像 + 效果追踪 |
| **Phase 3: 企业版** | 2周 | 多租户 + API | 租户管理 + 开放 API + CRM 集成 |
| **Phase 4: 智能化** | 2周 | AI 优化 | 自动调优 + 预测分析 + 报告生成 |
| **Phase 5: 规模化** | 持续 | 性能 + 稳定 | 监控告警 + 容灾 + 安全加固 |

### 12.2 Phase 1 详细计划

```yaml
phase_1_mvp:
  week_1:
    - 搭建项目骨架 (FastAPI + PostgreSQL)
    - 实现基础 API (CRUD)
    - 集成 OpenClaw
    - 实现 Collector Agent
    
  week_2:
    - 实现 Reacher Agent (邮件)
    - 集成 SendGrid/Resend
    - 实现基础分析报告
    - 前端 Dashboard (Next.js)
    - 部署上线 (Vercel + Railway)
```

---

## 13. 总结

### 13.1 架构亮点

1. **AI-Native**: 以 AI Agent 为核心，实现真正的智能拓客
2. **微服务架构**: 各模块独立部署、独立扩展
3. **事件驱动**: 模块间异步通信，提高系统弹性
4. **多租户支持**: 数据隔离、配额管理、计费统计
5. **可观测性**: 全链路追踪、指标监控、日志聚合

### 13.2 技术选型总结

| 层级 | 技术 | 理由 |
|------|------|------|
| API 层 | FastAPI | Python AI 生态最佳 |
| Agent 层 | OpenClaw | 原生多 Agent 支持 |
| 数据库 | PostgreSQL + pgvector | 关系型 + 向量一体化 |
| 缓存 | Redis | 高性能、多功能 |
| 队列 | Celery | Python 生态成熟 |
| 前端 | Next.js | 全栈、SSR、生态强 |
| 监控 | Prometheus + Grafana | 业界标准 |

### 13.3 下一步行动

- [ ] 搭建项目骨架
- [ ] 实现核心 API
- [ ] 集成 OpenClaw
- [ ] 开发 Collector Agent
- [ ] 开发 Reacher Agent
- [ ] 前端 Dashboard
- [ ] 部署上线

---

**文档版本**: V1.0  
**完成时间**: 2026-03-10 02:30  
**设计人**: 小code (Agent Code)
