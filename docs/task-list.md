# 开发任务清单

> 当前目标：交付符合 `docs/PRD.md` Phase 0 + Phase 1 验收要求的“线索报告 MVP”。
>
> 范围收敛：先做线索采集、清洗去重、BANT 评分、企业画像、报告展示；暂不做邮件触达、企微、多租户、生产部署。

## 0. 文档与范围对齐

- [x] 确认 MVP 范围为“线索报告 only”
- [x] 建立 `docs/architecture.md` 统一架构入口
- [x] 修正 README 文档路径与当前开发状态
- [x] 建立开发进度与验收对照区块

## 1. 项目骨架

### 后端（FastAPI）
- [x] 初始化 Python 项目与依赖管理
- [x] 创建应用入口与健康检查接口
- [x] 建立 `api / domain / services / repositories / tests` 目录结构
- [x] 定义统一 API 响应格式

### 前端（Next.js）
- [x] 初始化 Next.js 14 + TypeScript 项目
- [x] 建立基础布局与首页
- [x] 建立采集任务表单页
- [x] 建立线索列表页
- [x] 建立线索详情 / 报告页

## 2. 线索报告 MVP 核心能力

### 采集
- [x] 定义采集条件模型（行业、地区、角色、数量）
- [x] 实现 Mock 数据源适配器
- [x] 实现 CSV 导入适配器
- [x] 实现采集任务创建与结果查询接口

### 清洗去重
- [x] 实现字段标准化
- [x] 实现企业名 / 域名 / 联系方式去重规则
- [x] 输出有效率统计

### BANT 评分
- [x] 定义评分输入结构与等级规则
- [x] 实现规则引擎评分
- [x] 输出优先级排序

### 企业画像
- [x] 定义画像结构（行业 / 规模 / 痛点 / 需求）
- [x] 实现规则版 / Mock 画像生成
- [x] 为后续 LLM 接入预留接口

### 报告展示
- [x] 汇总线索、评分、画像生成报告视图模型
- [x] 前端展示报告页
- [x] 补充导出能力（可后置）
- [x] 新增 `GET /api/v1/prospects/export` CSV 导出接口

## 3. 测试与验证

### 验证前提
- [x] 后端在 `/home/aa/projects/tuoke-agent/src/backend` 目录下使用项目虚拟环境执行 `.venv/bin/pytest`
- [x] 前端在 `/home/aa/projects/tuoke-agent/src/frontend` 目录下执行 `npm test`、`npm run e2e`、`npm run typecheck`、`npm run lint`、`npm run build`
- [x] 本清单中的“已完成”指功能已实现，且已按上述目录与环境前提完成验证

### 后端测试
- [x] 先写单元测试：采集条件、去重、评分、画像
- [x] 编写 API 集成测试：创建任务、查询列表、查询详情
- [x] 补齐画像生成器扩展点的 service / API 注入测试矩阵
- [x] prospects 路由 400/404/405/422 错误统一为标准响应 envelope
- [x] GET /prospects 查询参数校验与 OpenAPI 错误响应声明对齐
- [x] prospects 路由 OpenAPI 错误响应补齐标准 error schema
- [x] prospects 路由重复错误响应声明已收敛复用
- [x] health 路由 405 错误标准响应 envelope 已补回归测试
- [x] 覆盖率达到 80%+

### 前端测试
- [x] 组件测试：表单、列表、报告页
- [x] 基础 E2E：提交条件 → 查看线索 → 查看报告
- [x] 类型检查、lint、构建通过
- [x] 列表页基础失败兜底
- [x] 报告页导出按钮已接入真实 CSV 下载测试
- [x] 报告页导出按钮补齐 loading / 失败提示 / 重试测试与实现

## 4. PRD 验收对照

### Phase 0
- [x] 确定至少 1 个可用数据源（当前已显式支持 Mock seed / CSV import 可见化）
- [x] 准备 100 条企业样本数据
- [x] 标记合规审查为外部待补
- [x] 标记反爬调研为文档已完成

### Phase 1 MVP
- [x] 输入行业 + 地区 → 产出 100+ 线索
- [x] 自动清洗去重 → 有效率 ≥80%
- [x] 企业画像包含行业 / 规模 / 痛点 / 需求
- [x] BANT 评分输出优先级排序
- [x] 输出企业画像报告
- [x] 最终验收收口完成：后端 `.venv/bin/pytest`、前端 `npm test` / `npm run e2e` / `npm run typecheck` / `npm run lint` / `npm run build` 全部通过

## 5. 当前阻塞项

- [ ] 真实企查查 / 天眼查账号与密钥（非当前 MVP 必需）
- [ ] 邮件服务账号与域名配置（Phase 2）
- [ ] 合规审查正式结论（需外部输入，当前仅完成文档方案与待法务意见）
