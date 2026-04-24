# 🤖 拓客智能体 (Tuoke Agent)

AI 驱动的自动化拓客系统 — 基于 OpenClaw 构建，用 AI Agent 替代传统拓客平台，成本降低 90%。

## 📂 项目结构

```
tuoke-agent/
├── README.md                              # 项目总览
├── docs/PRD.md                            # 产品需求文档（主入口）
├── prototype/                             # 🎨 产品原型（待拉取）
├── src/                                   # 💻 源码（开发阶段）
├── docs/                                  # 📋 项目文档
    ├── research/                          # 📚 调研学习
    │   ├── lead-gen-final-summary.md      # ⭐ 最终大总结（推荐先读）
    │   ├── lead-gen-research.md           # 13轮深度研究笔记
    │   ├── customer-acquisition-learning.md  # 完整学习笔记（54,662字）
    │   └── customer-acquisition-report.md # 专项分析报告
    └── design/                            # 🏗️ 系统设计
        ├── 01-industry-research.md        # 行业调研
        ├── 02-tech-stack-research.md      # 技术栈调研
        ├── 02b-openclaw-integration.md    # OpenClaw 集成方案
        ├── 03-system-architecture.md      # 系统架构设计
        ├── 04-feature-design.md           # 功能设计
        ├── 05-data-pipeline.md            # 数据管道
        ├── 06-ai-integration.md           # AI 集成方案
        ├── 06b-llm-cases.md               # LLM 应用案例
        ├── 07-deployment.md               # 部署方案
        ├── 07b-dev-plan.md                # 开发计划
        └── 08-final-report.md             # 最终报告
```

## 🎯 核心理念

```
拓客效果 = 数据质量 × 触达精准度 × 内容个性化 × 时机优化 × 持续迭代
```

**vs 传统平台**：专业拓客平台 8-15万/年 → OpenClaw 方案 1,000-2,500元/月，节省 90%+

## 📊 竞品分析

| 产品 | 价格 | 核心优势 | 推荐场景 |
|------|------|---------|---------|
| 探迹 | 5-20万/年 | AI推荐、全流程自动化 | 中大型企业 |
| 小蓝本 | 3-10万/年 | 关系图谱、股权穿透10层 | 深度背调 |
| 企查查 | API按量计费 | 数据权威、API完善 | 数据源 |
| 天眼查 | 会员制 | 舆情监控、数据丰富 | 商务查询 |
| 励销云 | 2-8万/年 | CRM+销售自动化 | 有销售团队 |
| Zoho CRM | $20-50/月 | 价格亲民、生态完善 | 中小企业 |

## 🚀 实施路线图（14周）

| 阶段 | 周期 | 目标 |
|------|------|------|
| Phase 1 | 2周 | 背景调研 Agent → 企业调研报告 |
| Phase 2 | 3周 | 线索管理 → 自动筛选评分 |
| Phase 3 | 4周 | 触达自动化 → 邮件+LinkedIn |
| Phase 4 | 5周 | 智能推荐 → AI+数据分析 |

## 📖 阅读指南

- **快速了解（30分钟）**：读 [最终大总结](docs/research/lead-gen-final-summary.md)
- **深入学习（2-3小时）**：读 [研究笔记](docs/research/lead-gen-research.md) + [产品架构](docs/product-architecture.md)
- **全面掌握（1天）**：读完 docs/ 全部文档

## 🛠️ 当前开发状态

- 当前开发目标：交付 `docs/PRD.md` Phase 0 + Phase 1 的“线索报告 MVP”
- 当前实现范围：线索采集、清洗去重、BANT 评分、企业画像、报告展示（画像模块已预留可替换的 LLM 生成器接口，前端已支持 query 驱动的采集条件提交、可用数据源显式展示、基础 E2E 主流程；报告页当前已支持按条件导出匹配结果 CSV，并补齐 loading、失败提示与重试反馈）
- 已打通后端接口：`POST /api/v1/prospects/collect`、`POST /api/v1/prospects/import`、`GET /api/v1/prospects`、`GET /api/v1/prospects/export`、`GET /api/v1/prospects/sources`、`GET /api/v1/prospects/{id}`、`GET /api/v1/prospects/{id}/report`
- 已支持 CSV 导入最小闭环：校验必填表头、跳过空值行、返回导入摘要，并补齐 100 条企业样本 CSV fixture；同时已补齐基于当前筛选条件的 CSV 导出下载接口，复用 prospects 列表查询与画像生成链路
- 已打通前端页面：`/prospects` 列表页、`/prospects/[id]` 报告页；列表页已展示 Mock seed / CSV import 数据源，查询参数会实际驱动后端 seed 结果，报告页已对齐后端 `/report` 契约，并补了基础失败兜底；现已进一步接入按当前报告条件导出匹配结果 CSV 的按钮，直接复用后端 `/api/v1/prospects/export` 导出能力
- 当前验证状态：后端已在 `/home/aa/projects/tuoke-agent/src/backend` 目录下通过 `.venv/bin/pytest` 验证（默认启用 `pytest-cov`，覆盖率门槛 `>=80%`，当前 98%）、前端已在 `/home/aa/projects/tuoke-agent/src/frontend` 目录下通过 `npm test`、`npm run e2e`、`npm run typecheck`、`npm run lint`、`npm run build` 验证；Phase 0 已补齐 100 条企业样本 CSV，至少 1 个可用数据源已在系统中可见化，prospects 路由的 400/404/405/422 错误已统一为标准 API envelope，`GET /api/v1/prospects` 的查询参数校验、OpenAPI 错误响应声明和标准 error schema 已对齐，prospects 路由重复错误响应声明也已收敛复用，health 路由 405 标准错误 envelope 已补回归测试保护，prospects CSV 导出接口已补齐下载响应、查询参数校验和 OpenAPI CSV 契约测试，前端报告页导出按钮也已接入真实 CSV 下载闭环，并补齐 loading / 失败提示 / 重试交互测试保护，反爬调研已有文档沉淀，合规正式结论仍待外部法务输入
- 当前验收进度：Phase 1 MVP 核心 5 项中已完成 5 项（含“输入行业 + 地区 → 产出 100+ 线索”），并已完成最终验收收口：后端 `.venv/bin/pytest`、前端 `npm test` / `npm run e2e` / `npm run typecheck` / `npm run lint` / `npm run build` 全部通过
- 暂不实现：邮件触达、企微、多租户、生产部署
- 开发任务清单：见 [docs/task-list.md](docs/task-list.md)
- 架构入口：见 [docs/architecture.md](docs/architecture.md)

## 🔗 相关链接

- [OpenClaw 文档](https://docs.openclaw.ai)
- [Skill 市场](https://clawhub.com)
