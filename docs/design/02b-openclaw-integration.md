# OpenClaw 集成可行性评估报告

> **评估日期**: 2026-03-10  
> **评估人**: 小code (Agent Code)  
> **状态**: 初稿完成

---

## 1. 执行摘要

### 核心结论

| 评估项 | 可行性 | 推荐方案 |
|--------|--------|----------|
| OpenClaw 作为执行引擎 | ✅ 高度可行 | 使用子 Agent 架构 |
| 多 Agent 协作编排 | ✅ 原生支持 | sessions_spawn + subagents |
| Skill 机制复用 | ✅ 完全兼容 | 组合现有 Skills + 自定义 Skill |
| 架构选型 | ⭐ 推荐 | **OpenClaw + FastAPI** (见 4.3) |

### 一句话总结

**OpenClaw 完全具备作为拓客执行引擎的能力，建议采用 "OpenClaw + FastAPI" 混合架构：OpenClaw 负责 AI 决策与任务编排，FastAPI 提供稳定的外部 API 层和业务状态管理。**

---

## 2. OpenClaw 作为拓客执行引擎的可行性

### 2.1 核心能力映射

| 拓客业务需求 | OpenClaw 能力 | 实现方式 |
|-------------|---------------|----------|
| 潜在客户识别 | 浏览器自动化 + 网页采集 | playwright-automation / web-scraping-automation |
| 客户信息采集 | 多源数据整合 | feishu-automation + notion-automation |
| 个性化触达 | AI 内容生成 | multimodal-gen + seo-content-writing |
| 多渠道发布 | 平台集成 | telegram-push / media-auto-publisher |
| 任务调度 | 定时任务 | cron-manager + heartbeat |
| 状态监控 | 会话管理 | sessions_list + session_status |

### 2.2 技术优势

#### ✅ 优势一：原生多 Agent 支持

```javascript
// 采集 Agent
sessions_spawn({
  task: "从 LinkedIn 采集目标客户信息",
  label: "tuoke-collector",
  model: "zai47",  // 轻量模型，成本低
  timeoutSeconds: 600
})

// 触达 Agent
sessions_spawn({
  task: "生成个性化触达内容并发送",
  label: "tuoke-reacher", 
  model: "opus46",  // 强模型，内容质量高
  timeoutSeconds: 300
})

// 分析 Agent
sessions_spawn({
  task: "分析触达效果并生成报告",
  label: "tuoke-analyzer",
  model: "glm5",  // 推理模型
  timeoutSeconds: 180
})
```

#### ✅ 优势二：Skill 扩展机制

- **现有 Skills 可直接复用**:
  - `web-scraping-automation` → 数据采集
  - `playwright-automation` → 浏览器操作
  - `feishu-automation` → 飞书协同
  - `telegram-push` → 消息推送

- **自定义 Skill 拓展**:
  - 创建 `tuoke-skill` 专门处理拓客逻辑
  - 参考 `skill-creator` 或 `skillforge` 创建新 Skill

#### ✅ 优势三：模型成本优化

```json5
// 子 Agent 用便宜模型，主 Agent 用强模型
{
  "agents": {
    "defaults": {
      "model": { "primary": "opus46" },  // 主 Agent 决策
      "subagents": {
        "model": "zai47",  // 子 Agent 执行
        "maxConcurrent": 8
      }
    }
  }
}
```

#### ✅ 优势四：稳定性和容错

- **模型 Fallback**: 主模型故障自动切换到备用模型
- **子 Agent 隔离**: 单个任务失败不影响整体
- **心跳监控**: 30 分钟心跳检查，异常自动告警

### 2.3 潜在限制

| 限制 | 影响程度 | 解决方案 |
|------|----------|----------|
| 无持久化状态层 | ⚠️ 中 | 外接 PostgreSQL/Redis |
| 无原生队列系统 | ⚠️ 中 | 集成 Celery/RQ 或使用 Temporal |
| Webhook 依赖外部 | ⚠️ 低 | FastAPI 封装 |
| 高并发场景 | ⚠️ 中 | 横向扩展子 Agent 数量 |

---

## 3. 多 Agent 协作编排方案

### 3.1 三 Agent 架构

```
┌────────────────────────────────────────────────────────────┐
│                    🧠 主控 Agent (Orchestrator)            │
│                    模型: opus46 / glm5                     │
│                    职责: 任务分发、状态协调、异常处理        │
└───────────┬────────────────┬────────────────┬──────────────┘
            │                │                │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │ 📊 采集 Agent │  │ 📩 触达 Agent │  │ 📈 分析 Agent │
    │   Collector  │  │   Reacher   │  │   Analyzer  │
    │   zai47      │  │   opus46    │  │   glm5      │
    └──────────────┘  └─────────────┘  └─────────────┘
           │                │                │
    ┌──────▼────────────────▼────────────────▼──────┐
    │              📦 共享状态层                      │
    │        PostgreSQL + Redis + 文件存储           │
    └────────────────────────────────────────────────┘
```

### 3.2 协作流程示例

```python
# 主控 Agent 工作流
async def tuoke_workflow(target_industry: str):
    # Step 1: 启动采集 Agent
    collector = sessions_spawn(
        task=f"采集 {target_industry} 行业潜在客户信息",
        label="tuoke-collector",
        model="zai47",
        timeoutSeconds=600
    )
    
    # Step 2: 等待采集完成，获取结果
    collected_data = await wait_for_agent(collector)
    save_to_db(collected_data)  # 持久化
    
    # Step 3: 并行启动触达 Agent（每个客户一个）
    reach_tasks = []
    for customer in collected_data:
        task = sessions_spawn(
            task=f"为 {customer.name} 生成个性化触达内容",
            label=f"reach-{customer.id}",
            model="opus46",
            timeoutSeconds=120
        )
        reach_tasks.append(task)
    
    # Step 4: 等待所有触达完成
    reach_results = await wait_for_all(reach_tasks)
    
    # Step 5: 启动分析 Agent
    analyzer = sessions_spawn(
        task="分析本次拓客效果并生成报告",
        label="tuoke-analyzer",
        model="glm5",
        timeoutSeconds=180
    )
    
    report = await wait_for_agent(analyzer)
    return report
```

### 3.3 Agent 职责明细

| Agent | 模型 | Skill 依赖 | 输出 |
|-------|------|-----------|------|
| **Collector** | zai47 (便宜) | web-scraping, playwright | 客户信息 JSON |
| **Reacher** | opus46 (质量) | multimodal-gen, seo-writing | 触达内容 + 发送记录 |
| **Analyzer** | glm5 (推理) | xlsx, docx | 效果报告 PDF |

### 3.4 状态管理策略

由于 OpenClaw 本身无持久化状态层，需要外接存储：

```yaml
状态层设计:
  客户数据:
    存储: PostgreSQL
    字段: [id, name, industry, contact, status, created_at]
    
  任务状态:
    存储: Redis
    字段: [task_id, agent_id, status, progress, result]
    
  触达记录:
    存储: PostgreSQL
    字段: [id, customer_id, content, channel, sent_at, response]
    
  文件资源:
    存储: MinIO / S3
    类型: 报告、图片、附件
```

---

## 4. 架构对比分析

### 4.1 方案一：纯 OpenClaw

```
┌────────────────────────────────────────────┐
│              OpenClaw Gateway              │
│         (Agent 调度 + 模型路由)            │
└────────────────────┬───────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐      ┌─────▼─────┐    ┌─────▼─────┐
│Agent 1│      │ Agent 2   │    │ Agent 3   │
└───────┘      └───────────┘    └───────────┘
```

#### ✅ 优点
- 架构简单，部署快
- 原生 AI 能力，无需额外开发
- 模型管理开箱即用
- Skill 生态丰富

#### ❌ 缺点
- 无持久化状态，重启丢失
- 无 REST API，外部系统难集成
- 无任务队列，高并发挑战
- 监控和告警能力有限

#### 适用场景
- 内部工具，小规模使用
- 快速原型验证
- 纯 AI 决策场景

---

### 4.2 方案二：OpenClaw + FastAPI ⭐ 推荐

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Layer                       │
│         (REST API + Webhook + 任务队列)                 │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP/gRPC
┌───────────────────────────▼─────────────────────────────┐
│                   OpenClaw Gateway                      │
│              (Agent 调度 + AI 推理)                      │
└───────────────────────────┬─────────────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
┌───▼────────┐        ┌─────▼─────┐         ┌───────▼────┐
│ Collector  │        │  Reacher  │         │  Analyzer  │
│   Agent    │        │   Agent   │         │   Agent    │
└────────────┘        └───────────┘         └────────────┘

┌─────────────────────────────────────────────────────────┐
│                   状态层                                 │
│        PostgreSQL + Redis + Celery                      │
└─────────────────────────────────────────────────────────┘
```

#### ✅ 优点
- **最佳平衡**: AI 能力 + 工程能力
- **外部集成**: 标准 REST API，方便对接 CRM/飞书等
- **任务队列**: Celery/RQ 处理高并发
- **状态持久化**: PostgreSQL 存储业务数据
- **可观测性**: FastAPI + Prometheus + Grafana

#### ❌ 缺点
- 需要额外开发 FastAPI 层
- 部署复杂度略高
- 需要维护两套系统

#### 实现示例

```python
# main.py - FastAPI 层
from fastapi import FastAPI, BackgroundTasks
from openclaw_client import OpenClawClient

app = FastAPI(title="拓客 Agent API")
claw = OpenClawClient()

@app.post("/api/v1/tuoke/start")
async def start_tuoke_task(
    industry: str,
    background_tasks: BackgroundTasks
):
    """启动拓客任务"""
    task_id = create_task_record(industry)
    
    # 异步启动 OpenClaw Agent
    background_tasks.add_task(
        run_tuoke_workflow,
        task_id=task_id,
        industry=industry
    )
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/v1/tuoke/{task_id}/status")
async def get_task_status(task_id: str):
    """查询任务状态"""
    return get_status_from_db(task_id)

async def run_tuoke_workflow(task_id: str, industry: str):
    """调用 OpenClaw 执行拓客流程"""
    # 启动采集 Agent
    collector = await claw.spawn_agent(
        task=f"采集 {industry} 客户",
        label=f"collector-{task_id}",
        model="zai47"
    )
    
    # 等待结果
    result = await claw.wait_for_result(collector)
    
    # 持久化
    save_customers_to_db(task_id, result)
    
    # 更新状态
    update_task_status(task_id, "collected")
    
    # 继续触达流程...
```

#### 适用场景
- **生产环境** ✅
- 需要外部 API 集成
- 高并发场景
- 需要完整监控告警

---

### 4.3 方案三：OpenClaw + LangGraph

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Layer                      │
│           (状态机 + 复杂流程编排)                        │
└───────────────────────────┬─────────────────────────────┘
                            │ LangChain
┌───────────────────────────▼─────────────────────────────┐
│                   OpenClaw Gateway                      │
│              (Agent 调度 + AI 推理)                      │
└─────────────────────────────────────────────────────────┘
```

#### ✅ 优点
- **复杂流程**: 状态机支持复杂业务逻辑
- **条件分支**: if-else / 循环 / 并行
- **可视化**: LangGraph Studio 图形化调试
- **回溯**: 支持状态回滚和时间旅行

#### ❌ 缺点
- 学习曲线陡峭
- 与 OpenClaw 有功能重叠（都有 Agent 编排）
- 可能过度设计（拓客场景不一定需要状态机）

#### 适用场景
- 超复杂业务流程
- 需要可视化编排
- 需要状态回滚

---

### 4.4 方案对比总结

| 维度 | 纯 OpenClaw | OpenClaw + FastAPI ⭐ | OpenClaw + LangGraph |
|------|-------------|----------------------|---------------------|
| **开发速度** | ⚡ 最快 | 🔸 中等 | 🐢 较慢 |
| **生产就绪** | ❌ 不推荐 | ✅ 推荐 | 🔸 可用 |
| **外部集成** | ❌ 困难 | ✅ 标准 REST API | 🔸 需封装 |
| **状态管理** | ❌ 无 | ✅ PostgreSQL | ✅ 内置 |
| **并发能力** | ❌ 有限 | ✅ Celery 队列 | 🔸 中等 |
| **监控告警** | ❌ 基础 | ✅ Prometheus | 🔸 需配置 |
| **学习成本** | ✅ 低 | 🔸 中等 | ❌ 高 |
| **适用规模** | 小型 | **中大型** | 复杂场景 |

---

## 5. 推荐架构：OpenClaw + FastAPI

### 5.1 架构图

```
┌────────────────────────────────────────────────────────────────┐
│                        客户端 / 外部系统                         │
│              (CRM / 飞书 / 小程序 / Web)                        │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼───────────────────────────────────┐
│                      🌐 Nginx 反向代理                          │
│                   (SSL 终止 / 负载均衡)                         │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                    🚀 FastAPI 服务层                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ REST API    │ │  Webhook    │ │  WebSocket  │              │
│  │ /api/v1/*   │ │  /wh/*      │ │  /ws/*      │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌──────────────────────────────────────────────┐              │
│  │  Celery 任务队列                              │              │
│  │  - tuoke.collect (采集任务)                   │              │
│  │  - tuoke.reach (触达任务)                     │              │
│  │  - tuoke.analyze (分析任务)                   │              │
│  └──────────────────────────────────────────────┘              │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTP/gRPC
┌────────────────────────────▼───────────────────────────────────┐
│                    🤖 OpenClaw Gateway                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ 主控 Agent  │ │ 采集 Agent  │ │ 触达 Agent  │              │
│  │  (Orchestrator)│ (Collector) │ │ (Reacher)   │              │
│  │  opus46     │ │  zai47      │ │  opus46     │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐                                              │
│  │ 分析 Agent  │   Skills: web-scraping, playwright, etc.     │
│  │ (Analyzer)  │                                              │
│  │  glm5       │                                              │
│  └─────────────┘                                              │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                        📦 状态层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ PostgreSQL  │ │   Redis     │ │   MinIO     │              │
│  │ (业务数据)  │ │ (缓存/队列) │ │ (文件存储)  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **反向代理** | Nginx | SSL、负载均衡 |
| **API 层** | FastAPI | 高性能异步 Python 框架 |
| **任务队列** | Celery + Redis | 异步任务处理 |
| **AI 层** | OpenClaw | Agent 编排 + 模型管理 |
| **数据库** | PostgreSQL | 业务数据持久化 |
| **缓存** | Redis | 任务状态 + 热数据缓存 |
| **文件存储** | MinIO / S3 | 报告、图片等文件 |
| **监控** | Prometheus + Grafana | 指标监控 + 可视化 |
| **日志** | Loki | 日志聚合 |

### 5.3 目录结构

```
tuoke-agent/
├── api/                      # FastAPI 服务
│   ├── main.py               # 入口
│   ├── routers/
│   │   ├── tuoke.py          # 拓客 API
│   │   ├── webhook.py        # Webhook 接收
│   │   └── status.py         # 状态查询
│   ├── models/               # Pydantic 模型
│   ├── services/
│   │   ├── openclaw_client.py  # OpenClaw 调用封装
│   │   └── tuoke_service.py    # 拓客业务逻辑
│   └── tasks/
│       ├── collector.py      # 采集 Celery 任务
│       ├── reacher.py        # 触达 Celery 任务
│       └── analyzer.py       # 分析 Celery 任务
├── openclaw/
│   ├── skills/
│   │   └── tuoke-skill/      # 自定义拓客 Skill
│   └── agents/
│       ├── orchestrator/     # 主控 Agent 配置
│       ├── collector/        # 采集 Agent 配置
│       ├── reacher/          # 触达 Agent 配置
│       └── analyzer/         # 分析 Agent 配置
├── db/
│   ├── migrations/           # 数据库迁移
│   └── models.py             # ORM 模型
├── docs/                     # 文档
│   ├── 02b-openclaw-integration.md
│   └── ...
├── docker-compose.yml        # 容器编排
├── Dockerfile
└── README.md
```

### 5.4 核心代码示例

#### FastAPI 路由

```python
# api/routers/tuoke.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tuoke", tags=["拓客"])

class TuokeRequest(BaseModel):
    industry: str
    region: str = None
    limit: int = 100

class TuokeResponse(BaseModel):
    task_id: str
    status: str

@router.post("/start", response_model=TuokeResponse)
async def start_tuoke(request: TuokeRequest):
    """启动拓客任务"""
    from api.tasks.tuoke import run_tuoke_pipeline
    task = run_tuoke_pipeline.delay(
        industry=request.industry,
        region=request.region,
        limit=request.limit
    )
    return TuokeResponse(task_id=task.id, status="started")

@router.get("/{task_id}/status")
async def get_status(task_id: str):
    """查询任务状态"""
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
```

#### Celery 任务

```python
# api/tasks/tuoke.py
from celery import Celery
from api.services.openclaw_client import OpenClawClient

app = Celery('tuoke', broker='redis://localhost:6379/0')
claw = OpenClawClient()

@app.task(bind=True)
def run_tuoke_pipeline(self, industry: str, region: str, limit: int):
    """完整拓客流程"""
    # Step 1: 采集
    collect_result = claw.spawn_and_wait(
        task=f"采集 {industry} 行业 {limit} 个客户",
        agent_type="collector",
        model="zai47",
        timeout=600
    )
    
    # 持久化采集结果
    customers = save_customers(collect_result)
    
    # Step 2: 触达 (并行)
    reach_tasks = [
        claw.spawn_async(
            task=f"为 {c.name} 生成触达内容",
            agent_type="reacher",
            model="opus46"
        )
        for c in customers
    ]
    
    reach_results = claw.wait_all(reach_tasks, timeout=300)
    save_reach_records(reach_results)
    
    # Step 3: 分析
    analyze_result = claw.spawn_and_wait(
        task="分析本次拓客效果",
        agent_type="analyzer",
        model="glm5",
        timeout=180
    )
    
    # 生成报告
    report_url = generate_report(analyze_result)
    
    return {
        "customers_collected": len(customers),
        "reach_sent": len(reach_results),
        "report_url": report_url
    }
```

#### OpenClaw 调用封装

```python
# api/services/openclaw_client.py
import httpx
from typing import Dict, List, Any

class OpenClawClient:
    """OpenClaw Gateway 调用客户端"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def spawn_agent(
        self,
        task: str,
        label: str,
        model: str = "zai47",
        timeout: int = 300
    ) -> str:
        """启动子 Agent"""
        # 调用 sessions_spawn
        resp = await self.client.post(
            f"{self.base_url}/api/sessions/spawn",
            json={
                "task": task,
                "label": label,
                "model": model,
                "timeoutSeconds": timeout
            }
        )
        return resp.json()["sessionKey"]
    
    async def spawn_and_wait(
        self,
        task: str,
        agent_type: str,
        model: str,
        timeout: int
    ) -> Dict:
        """启动 Agent 并等待结果"""
        session_key = await self.spawn_agent(
            task=task,
            label=f"{agent_type}-{uuid.uuid4()}",
            model=model,
            timeout=timeout
        )
        
        # 轮询等待完成
        while True:
            status = await self.get_session_status(session_key)
            if status["completed"]:
                return status["result"]
            await asyncio.sleep(5)
    
    async def get_session_status(self, session_key: str) -> Dict:
        """获取 Session 状态"""
        resp = await self.client.get(
            f"{self.base_url}/api/sessions/{session_key}/status"
        )
        return resp.json()
```

---

## 6. OpenClaw Skill 复用方案

### 6.1 可直接复用的 Skills

| Skill | 用途 | 在拓客场景的应用 |
|-------|------|-----------------|
| `web-scraping-automation` | 网页数据采集 | 采集潜在客户信息 |
| `playwright-automation` | 浏览器自动化 | 自动登录平台、模拟操作 |
| `feishu-automation` | 飞书集成 | 推送拓客报告到飞书群 |
| `telegram-push` | Telegram 推送 | 通知拓客进度 |
| `xlsx` | Excel 处理 | 生成客户清单表格 |
| `docx` | Word 处理 | 生成触达模板 |
| `cron-manager` | 定时任务 | 定时执行拓客任务 |
| `multimodal-gen` | 多模态生成 | 生成触达图片/内容 |

### 6.2 自定义 Skill: tuoke-skill

建议创建专门的拓客 Skill，封装拓客相关逻辑：

```
~/.openclaw/skills/tuoke-skill/
├── SKILL.md              # Skill 定义
├── references/
│   ├── linkedin-scraper.md    # LinkedIn 采集指南
│   ├── email-template.md      # 邮件模板
│   └── report-format.md       # 报告格式
└── scripts/
    └── validate-customer.sh   # 客户信息验证脚本
```

**SKILL.md 示例**:

```markdown
# tuoke-skill

拓客智能体专用 Skill，封装拓客业务逻辑。

## 触发场景
- "拓客" "采集客户" "触达"
- "客户开发" "获客"

## 能力

### 1. 客户采集 (Collector)
- 从 LinkedIn/企查查/天眼查 采集企业信息
- 提取关键人联系方式
- 去重和清洗

### 2. 个性化触达 (Reacher)
- 根据客户画像生成个性化内容
- 支持邮件、微信、LinkedIn 多渠道
- 遵守反垃圾邮件法规

### 3. 效果分析 (Analyzer)
- 追踪触达响应率
- 生成效果报告
- 优化建议

## 工作流

1. 采集 Agent 启动 → 2. 数据清洗 → 3. 触达 Agent 并行 → 4. 效果分析

## 参考文档
- LinkedIn API 使用规范
- GDPR 合规指南
- 中国个人信息保护法
```

---

## 7. 风险与缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 模型故障 | 高 | 中 | 配置 fallback 模型链 |
| 并发过载 | 中 | 中 | Celery 限流 + 子 Agent 数量限制 |
| 状态丢失 | 高 | 低 | PostgreSQL 持久化 + 定期备份 |
| API 被封 | 高 | 中 | 代理池 + 请求频率控制 |
| 数据泄露 | 极高 | 低 | 敏感信息加密 + 访问控制 |

---

## 8. 实施建议

### 8.1 分阶段实施

| 阶段 | 目标 | 时间 |
|------|------|------|
| **Phase 1** | 纯 OpenClaw 原型 | 1 周 |
| **Phase 2** | FastAPI 层开发 | 2 周 |
| **Phase 3** | 多 Agent 编排 | 1 周 |
| **Phase 4** | 生产部署 + 监控 | 1 周 |

### 8.2 优先级

1. **P0**: 定义拓客业务流程 → 确定 Agent 职责
2. **P0**: 搭建 FastAPI + PostgreSQL 基础
3. **P1**: 集成 OpenClaw，实现单 Agent 采集
4. **P1**: 实现多 Agent 并行触达
5. **P2**: 添加监控告警
6. **P2**: 开发自定义 tuoke-skill

---

## 9. 结论

### 核心建议

1. **采用 "OpenClaw + FastAPI" 混合架构**
   - OpenClaw 负责 AI 决策和任务编排
   - FastAPI 提供稳定的 REST API 和状态管理

2. **多 Agent 协作设计**
   - Collector (zai47) → 采集，成本低
   - Reacher (opus46) → 内容生成，质量高
   - Analyzer (glm5) → 效果分析，推理强

3. **复用现有 Skills + 自定义 tuoke-skill**
   - 直接使用 web-scraping、playwright 等现有 Skills
   - 创建 tuoke-skill 封装业务逻辑

4. **状态外置**
   - PostgreSQL 存储业务数据
   - Redis 缓存任务状态
   - MinIO 存储报告文件

### 下一步行动

- [ ] 补充 PRD 业务需求细节
- [ ] 确定 Agent 职责边界
- [ ] 设计数据库 Schema
- [ ] 搭建 FastAPI 项目骨架
- [ ] 实现 OpenClaw 调用封装

---

**报告完成时间**: 2026-03-10 01:20  
**评估人**: 小code (Agent Code)
