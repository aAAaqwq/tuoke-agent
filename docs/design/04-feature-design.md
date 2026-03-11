# 拓客Agent - 核心功能模块详细设计

> 文档版本：V1.0 | 日期：2026-03-10
> 设计人：小pm | 基于系统架构文档 V1.0

---

## 概述

本文档详细设计拓客Agent的5大核心功能模块，每个模块包含：
- 功能描述
- 用户故事
- 技术实现要点
- 优先级（P0/P1/P2）

---

## 模块总览

| 模块 | 优先级 | 核心价值 | 预估工作量 |
|------|--------|----------|-----------|
| 1. 线索采集模块 | P0 | 自动化获取潜在客户数据 | 5天 |
| 2. 客户画像模块 | P0 | 深度理解客户，精准触达 | 4天 |
| 3. 智能触达模块 | P0 | 多渠道个性化触达 | 6天 |
| 4. 效果追踪模块 | P1 | 数据驱动优化 | 3天 |
| 5. 管理后台 | P1 | 可视化+权限管理 | 4天 |

---

## 模块1：线索采集模块

### 1.1 功能描述

**核心目标**：从多个数据源自动采集潜在客户信息，清洗去重，并评分排序。

**子功能**：
- 多渠道数据采集（工商数据、B2B数据库、社交平台、公开网页）
- 数据清洗标准化（字段规范、格式统一）
- 去重机制（基于邮箱+公司、基于手机号、基于姓名+公司）
- 线索评分算法（基于多维度的质量评估）

### 1.2 用户故事

```
US-1.1: 创建采集任务
作为 销售经理
我想要 用自然语言定义目标客户画像（行业、规模、职位）
以便于 AI 自动理解并采集符合条件的线索
验收标准：输入"帮我找SaaS公司CTO"，系统能理解并执行采集

US-1.2: 多渠道采集
作为 销售经理
我想要 同时从企查查、天眼查、LinkedIn采集线索
以便于 获得更全面的数据覆盖
验收标准：采集任务显示各渠道采集数量和成功率

US-1.3: 数据清洗
作为 销售经理
我想要 自动清洗无效邮箱和重复数据
以便于 节省触达资源，提高到达率
验收标准：清洗后数据质量分≥80分

US-1.4: 线索评分
作为 销售经理
我想要 系统自动给线索打分排序
以便于 优先触达高价值客户
验收标准：A类线索（高分）优先展示在列表顶部

US-1.5: 导出线索
作为 销售经理
我想要 导出清洗后的线索列表（Excel/CSV）
以便于 在其他系统使用或手动跟进
验收标准：支持筛选导出，包含完整字段
```

### 1.3 技术实现要点

#### 1.3.1 多渠道采集架构

```
┌─────────────────────────────────────────────────────────────┐
│                    采集协调器 (Collector Orchestrator)        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 任务队列管理   │  │ 渠道选择策略  │  │ 进度监控     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 企查查Adapter │  │ 天眼查Adapter │  │ LinkedIn Adapter│
│ (API/爬虫)   │  │ (API/爬虫)   │  │ (Playwright)  │
└──────────────┘  └──────────────┘  └──────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据处理管道                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 字段映射 │→│ 格式清洗 │→│ 去重处理 │→│ 质量评分 │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
```

#### 1.3.2 采集任务配置示例

```yaml
collect_task:
  task_id: "task_001"
  campaign_id: "camp_001"
  
  # 目标定义
  target:
    industries: ["SaaS", "云计算", "企业服务"]
    company_sizes: ["50-200人", "200-500人"]
    roles: ["CTO", "VP Engineering", "技术总监"]
    regions: ["北京", "上海", "深圳", "杭州"]
    
  # 数据源配置
  sources:
    - name: "qichacha"
      enabled: true
      priority: 1
      config:
        api_key: "${QICHACHA_API_KEY}"
        daily_limit: 1000
        
    - name: "tianyancha"
      enabled: true
      priority: 2
      config:
        api_key: "${TIANYANCHA_API_KEY}"
        daily_limit: 500
        
    - name: "linkedin"
      enabled: false  # 需要代理
      priority: 3
      config:
        use_proxy: true
        
  # 处理配置
  processing:
    dedup_strategy: "email_company"  # email_company, phone, name_company
    validate_email: true
    enrich_company: true
    score_leads: true
    
  # 输出配置
  output:
    save_to_db: true
    notify_on_complete: true
```

#### 1.3.3 去重算法

```python
# api/services/collector/deduplication.py
from typing import List, Dict
import hashlib
from datetime import datetime

class DeduplicationEngine:
    """线索去重引擎"""
    
    def __init__(self, strategy: str = "email_company"):
        self.strategy = strategy
    
    def deduplicate(self, prospects: List[Dict]) -> List[Dict]:
        """执行去重"""
        seen = set()
        unique = []
        duplicates = []
        
        for p in prospects:
            key = self._generate_key(p)
            if key not in seen:
                seen.add(key)
                unique.append(p)
            else:
                duplicates.append(p)
        
        # 记录去重统计
        self._log_stats(len(prospects), len(unique), len(duplicates))
        
        return unique
    
    def _generate_key(self, prospect: Dict) -> str:
        """生成去重键"""
        if self.strategy == "email_company":
            # 邮箱 + 公司（忽略大小写和常见后缀）
            email = (prospect.get("email") or "").lower().strip()
            company = self._normalize_company(prospect.get("company", ""))
            return f"{email}|{company}"
            
        elif self.strategy == "phone":
            # 手机号（去除格式差异）
            phone = self._normalize_phone(prospect.get("phone", ""))
            return phone
            
        elif self.strategy == "name_company":
            # 姓名 + 公司
            name = (prospect.get("name") or "").strip()
            company = self._normalize_company(prospect.get("company", ""))
            return f"{name}|{company}"
            
        else:
            # 默认：所有字段组合哈希
            return hashlib.md5(
                str(prospect).encode()
            ).hexdigest()
    
    def _normalize_company(self, company: str) -> str:
        """公司名标准化"""
        if not company:
            return ""
        # 移除常见后缀
        suffixes = [
            "有限公司", "有限责任公司", "股份有限公司",
            "Ltd", "Inc", "Corp", "Co.", "集团"
        ]
        normalized = company.strip()
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized.lower().strip()
    
    def _normalize_phone(self, phone: str) -> str:
        """手机号标准化"""
        if not phone:
            return ""
        # 只保留数字
        digits = "".join(c for c in phone if c.isdigit())
        # 中国号码统一格式
        if digits.startswith("86"):
            digits = digits[2:]
        return digits
```

#### 1.3.4 线索评分算法

```python
# api/services/collector/lead_scorer.py
from typing import Dict, List

class LeadScorer:
    """线索评分引擎"""
    
    # 评分权重配置
    WEIGHTS = {
        "contact_quality": 0.30,    # 联系方式质量
        "company_fit": 0.25,        # 公司匹配度
        "role_relevance": 0.20,     # 角色相关性
        "data_completeness": 0.15,  # 数据完整度
        "engagement_potential": 0.10 # 互动潜力
    }
    
    def score(self, prospect: Dict, target_criteria: Dict) -> Dict:
        """计算线索综合得分"""
        scores = {}
        
        # 1. 联系方式质量（0-100）
        scores["contact_quality"] = self._score_contact_quality(prospect)
        
        # 2. 公司匹配度（0-100）
        scores["company_fit"] = self._score_company_fit(prospect, target_criteria)
        
        # 3. 角色相关性（0-100）
        scores["role_relevance"] = self._score_role_relevance(prospect, target_criteria)
        
        # 4. 数据完整度（0-100）
        scores["data_completeness"] = self._score_completeness(prospect)
        
        # 5. 互动潜力（0-100）
        scores["engagement_potential"] = self._score_engagement_potential(prospect)
        
        # 加权计算总分
        total_score = sum(
            scores[k] * self.WEIGHTS[k] 
            for k in self.WEIGHTS
        )
        
        # 确定等级
        grade = self._determine_grade(total_score)
        
        return {
            "total_score": round(total_score, 1),
            "grade": grade,
            "dimension_scores": scores
        }
    
    def _score_contact_quality(self, prospect: Dict) -> float:
        """联系方式质量评分"""
        score = 0
        
        # 邮箱质量
        email = prospect.get("email", "")
        if email:
            score += 40
            # 企业邮箱加分
            if not any(d in email for d in ["qq.com", "163.com", "gmail.com"]):
                score += 20
            # 邮箱验证通过
            if prospect.get("email_verified"):
                score += 10
        
        # 电话质量
        phone = prospect.get("phone", "")
        if phone:
            score += 20
            if prospect.get("phone_verified"):
                score += 10
        
        return min(score, 100)
    
    def _score_company_fit(self, prospect: Dict, target: Dict) -> float:
        """公司匹配度评分"""
        score = 50  # 基础分
        
        # 行业匹配
        if prospect.get("industry") in target.get("industries", []):
            score += 25
        
        # 规模匹配
        company_size = prospect.get("company_size", "")
        if company_size in target.get("company_sizes", []):
            score += 15
        
        # 地区匹配
        if prospect.get("region") in target.get("regions", []):
            score += 10
        
        return min(score, 100)
    
    def _score_role_relevance(self, prospect: Dict, target: Dict) -> float:
        """角色相关性评分"""
        title = (prospect.get("title") or "").lower()
        target_roles = [r.lower() for r in target.get("roles", [])]
        
        if not target_roles:
            return 50
        
        # 完全匹配
        for role in target_roles:
            if role in title:
                return 100
        
        # 部分匹配（关键词）
        keywords = {
            "cto": ["技术总监", "首席技术", "cto"],
            "vp": ["副总裁", "vp", "副总"],
            "director": ["总监", "director"],
            "manager": ["经理", "manager"]
        }
        
        for role in target_roles:
            for keyword in keywords.get(role, []):
                if keyword in title:
                    return 75
        
        return 30
    
    def _score_completeness(self, prospect: Dict) -> float:
        """数据完整度评分"""
        required_fields = [
            "name", "email", "company", "title", 
            "phone", "industry", "company_size"
        ]
        
        filled = sum(1 for f in required_fields if prospect.get(f))
        return (filled / len(required_fields)) * 100
    
    def _score_engagement_potential(self, prospect: Dict) -> float:
        """互动潜力评分"""
        score = 50
        
        # 有LinkedIn
        if prospect.get("linkedin_url"):
            score += 15
        
        # 有公司网站
        if prospect.get("company_website"):
            score += 10
        
        # 公司规模适中（更容易触达）
        size = prospect.get("company_size", "")
        if "50-200" in size or "200-500" in size:
            score += 15
        elif "500-1000" in size:
            score += 10
        
        return min(score, 100)
    
    def _determine_grade(self, score: float) -> str:
        """确定等级"""
        if score >= 80:
            return "A"  # 高价值
        elif score >= 60:
            return "B"  # 中等价值
        elif score >= 40:
            return "C"  # 低价值
        else:
            return "D"  # 不推荐
```

### 1.4 优先级

| 功能 | 优先级 | 理由 |
|------|--------|------|
| 多渠道采集 | P0 | 核心功能，无数据无法后续 |
| 数据清洗去重 | P0 | 必需，影响触达效果 |
| 线索评分 | P0 | 提升效率，优先触达高价值线索 |
| 邮箱验证 | P1 | 提高到达率，可后续增强 |
| 数据增强 | P1 | 提升数据质量，可后续增强 |
| 定时采集 | P2 | 自动化增强，非必需 |

---

## 模块2：客户画像模块

### 2.1 功能描述

**核心目标**：基于采集的线索数据，利用AI生成深度客户画像，包括企业标签、决策链分析、需求预测。

**子功能**：
- 企业标签体系（行业、规模、发展阶段、技术栈等）
- 决策链分析（角色权限、关注点、KPI）
- 需求预测（痛点、购买动机、预期方案）
- 个性化触达建议（渠道偏好、沟通风格、最佳时机）

### 2.2 用户故事

```
US-2.1: 自动生成画像
作为 销售经理
我想要 系统自动为每个线索生成客户画像
以便于 快速了解客户背景，准备话术
验收标准：画像包含角色特征、需求分析、意向评估、触达建议

US-2.2: 决策链可视化
作为 销售经理
我想要 查看目标公司的决策链结构
以便于 找到关键决策人和影响者
验收标准：显示公司组织架构图，标注各角色决策权限

US-2.3: 需求预测
作为 销售经理
我想要 AI预测客户可能的痛点和需求
以便于 准备针对性的解决方案
验收标准：预测准确率>70%（基于历史反馈）

US-2.4: 优先级排序
作为 销售经理
我想要 系统根据画像自动排序线索优先级
以便于 优先跟进高意向客户
验收标准：A类客户排在列表顶部

US-2.5: 画像编辑
作为 销售经理
我想要 手动补充或修正客户画像信息
以便于 记录实际接触后的真实洞察
验收标准：修改后画像同步更新评分
```

### 2.3 技术实现要点

#### 2.3.1 画像数据结构

```python
# api/models/prospect_profile.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RoleCharacteristics(BaseModel):
    """角色特征"""
    decision_level: str  # high, medium, low
    focus_areas: List[str]  # ["技术架构", "团队管理", "成本控制"]
    possible_kpis: List[str]  # ["研发效率", "系统稳定性", "人才留存"]
    typical_concerns: List[str]  # 常见关注点

class NeedsAnalysis(BaseModel):
    """需求分析"""
    pain_points: List[str]  # ["数据孤岛", "流程低效", "协作困难"]
    buying_motivations: List[str]  # ["提升效率", "降低成本", "合规要求"]
    expected_solutions: List[str]  # 预期解决方案
    budget_indicator: Optional[str]  # high, medium, low, unknown

class IntentAssessment(BaseModel):
    """意向评估"""
    buying_signal_score: int  # 0-100
    engagement_score: int  # 0-100
    priority_level: str  # A, B, C, D
    confidence: float  # 0-1

class ReachSuggestion(BaseModel):
    """触达建议"""
    preferred_channel: str  # email, wechat, phone, linkedin
    communication_style: str  # formal, casual, technical
    best_reach_time: str  # morning, afternoon, evening
    recommended_topics: List[str]  # 建议话题
    avoid_topics: List[str]  # 避免话题

class ProspectProfile(BaseModel):
    """客户画像完整模型"""
    prospect_id: str
    
    # 角色特征
    role_characteristics: RoleCharacteristics
    
    # 需求分析
    needs_analysis: NeedsAnalysis
    
    # 意向评估
    intent_assessment: IntentAssessment
    
    # 触达建议
    reach_suggestion: ReachSuggestion
    
    # 元数据
    generated_at: datetime
    model_version: str
    confidence_score: float
    
    # 原始AI分析（可追溯）
    raw_ai_analysis: Optional[str]
```

#### 2.3.2 画像生成Agent Prompt

```markdown
# 客户画像生成任务

## 输入数据
```json
{
  "name": "张三",
  "title": "技术副总裁",
  "company": "某某科技有限公司",
  "industry": "SaaS",
  "company_size": "200-500人",
  "company_website": "https://example.com",
  "region": "北京"
}
```

## 分析任务

请基于以上信息，生成客户画像。分析应基于：
1. 行业特点和发展趋势
2. 职位的典型职责和关注点
3. 公司规模对应的挑战
4. 地域特点（如适用）

## 输出格式

```json
{
  "role_characteristics": {
    "decision_level": "high|medium|low",
    "focus_areas": ["关注点1", "关注点2", "关注点3"],
    "possible_kpis": ["KPI1", "KPI2"],
    "typical_concerns": ["关注1", "关注2"]
  },
  "needs_analysis": {
    "pain_points": ["痛点1", "痛点2", "痛点3"],
    "buying_motivations": ["动机1", "动机2"],
    "expected_solutions": ["方案1", "方案2"],
    "budget_indicator": "high|medium|low|unknown"
  },
  "intent_assessment": {
    "buying_signal_score": 0-100,
    "engagement_score": 0-100,
    "priority_level": "A|B|C|D",
    "confidence": 0.0-1.0
  },
  "reach_suggestion": {
    "preferred_channel": "email|wechat|phone|linkedin",
    "communication_style": "formal|casual|technical",
    "best_reach_time": "morning|afternoon|evening",
    "recommended_topics": ["话题1", "话题2"],
    "avoid_topics": ["避免1"]
  }
}
```

## 注意事项
- 基于公开信息合理推断，不要过度猜测
- 评分要有依据，置信度反映不确定性
- 触达建议要具体可操作
```

#### 2.3.3 企业标签体系

```yaml
# config/tag_system.yaml
enterprise_tags:
  # 行业标签
  industry:
    level_1:  # 一级行业
      - "互联网"
      - "制造业"
      - "金融"
      - "零售"
      - "教育"
      - "医疗"
    level_2:  # 二级行业
      "互联网":
        - "SaaS"
        - "电商"
        - "社交"
        - "内容"
        - "工具"
      "制造业":
        - "电子"
        - "机械"
        - "汽车"
        - "化工"
  
  # 规模标签
  company_size:
    - "1-50人"
    - "50-200人"
    - "200-500人"
    - "500-1000人"
    - "1000-5000人"
    - "5000人以上"
  
  # 发展阶段
  development_stage:
    - "种子期"
    - "天使期"
    - "A轮"
    - "B轮"
    - "C轮及以后"
    - "已上市"
    - "成熟企业"
  
  # 技术栈（根据行业）
  tech_stack:
    "互联网":
      frontend: ["React", "Vue", "Angular"]
      backend: ["Node.js", "Python", "Java", "Go"]
      cloud: ["AWS", "阿里云", "腾讯云"]
      database: ["MySQL", "PostgreSQL", "MongoDB"]
  
  # 业务模式
  business_model:
    - "B2B"
    - "B2C"
    - "B2B2C"
    - "平台"
    - "SaaS订阅"
    - "项目制"
  
  # 特征标签
  characteristics:
    - "高增长"
    - "融资中"
    - "扩张期"
    - "数字化转型"
    - "出海"
    - "新零售"
```

#### 2.3.4 决策链分析模型

```python
# api/services/profiler/decision_chain.py
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DecisionNode:
    """决策节点"""
    name: str
    title: str
    decision_level: str  # final, influencer, gatekeeper
    focus_areas: List[str]
    relationship: str  # peer, subordinate, superior

class DecisionChainAnalyzer:
    """决策链分析器"""
    
    # 决策权限映射
    DECISION_AUTHORITY = {
        "ceo": "final",
        "cto": "final",
        "cio": "final",
        "coo": "final",
        "vp": "influencer",
        "总监": "influencer",
        "经理": "gatekeeper",
        "主管": "gatekeeper"
    }
    
    def analyze(self, company_info: Dict) -> Dict:
        """分析公司决策链"""
        
        # 1. 推断组织结构
        org_structure = self._infer_org_structure(company_info)
        
        # 2. 识别关键角色
        key_roles = self._identify_key_roles(company_info)
        
        # 3. 构建决策链
        chain = self._build_decision_chain(org_structure, key_roles)
        
        return {
            "org_structure": org_structure,
            "key_roles": key_roles,
            "decision_chain": chain,
            "recommended_approach": self._recommend_approach(chain)
        }
    
    def _infer_org_structure(self, company_info: Dict) -> Dict:
        """推断组织结构"""
        size = company_info.get("company_size", "")
        
        if "1-50" in size or "50-200" in size:
            return {
                "type": "flat",
                "levels": 2,
                "description": "扁平化组织，决策链条短"
            }
        elif "200-500" in size or "500-1000" in size:
            return {
                "type": "medium",
                "levels": 3,
                "description": "中等规模，有明确管理层级"
            }
        else:
            return {
                "type": "hierarchical",
                "levels": 4,
                "description": "层级较多，需多级审批"
            }
    
    def _identify_key_roles(self, company_info: Dict) -> List[Dict]:
        """识别关键角色"""
        industry = company_info.get("industry", "")
        
        # 根据行业和产品类型，推断关键决策者
        key_roles_map = {
            "SaaS": [
                {"role": "CTO", "level": "final", "focus": "技术架构"},
                {"role": "VP Engineering", "level": "influencer", "focus": "团队效率"},
                {"role": "IT总监", "level": "influencer", "focus": "系统运维"}
            ],
            "制造业": [
                {"role": "CIO", "level": "final", "focus": "数字化战略"},
                {"role": "IT经理", "level": "influencer", "focus": "系统选型"},
                {"role": "生产总监", "level": "influencer", "focus": "生产效率"}
            ]
        }
        
        return key_roles_map.get(industry, key_roles_map["SaaS"])
    
    def _build_decision_chain(
        self, 
        org_structure: Dict, 
        key_roles: List[Dict]
    ) -> List[Dict]:
        """构建决策链"""
        chain = []
        
        for role in key_roles:
            node = {
                "role": role["role"],
                "decision_level": role["level"],
                "focus_areas": [role["focus"]],
                "approach_strategy": self._get_approach_strategy(
                    role["level"], 
                    org_structure["type"]
                )
            }
            chain.append(node)
        
        return chain
    
    def _get_approach_strategy(
        self, 
        level: str, 
        org_type: str
    ) -> str:
        """获取触达策略"""
        strategies = {
            ("final", "flat"): "直接触达，强调价值",
            ("final", "medium"): "先找influencer背书",
            ("final", "hierarchical"): "需要多层级沟通",
            ("influencer", "flat"): "技术交流为主",
            ("influencer", "medium"): "案例驱动",
            ("gatekeeper", "flat"): "提供试用或Demo",
        }
        return strategies.get((level, org_type), "标准触达")
```

### 2.4 优先级

| 功能 | 优先级 | 理由 |
|------|--------|------|
| AI画像生成 | P0 | 核心价值，差异化能力 |
| 角色特征分析 | P0 | 基础功能，必需 |
| 需求预测 | P0 | 核心价值 |
| 意向评分 | P0 | 优先级排序基础 |
| 触达建议 | P0 | 直接指导触达 |
| 决策链分析 | P1 | 增值功能，大客户必需 |
| 企业标签体系 | P1 | 可后续完善 |
| 画像编辑 | P1 | 人工干预 |

---

## 模块3：智能触达模块

### 3.1 功能描述

**核心目标**：基于客户画像，自动生成个性化触达内容，选择最优渠道和时机执行触达。

**子功能**：
- 多渠道触达（邮件、电话、企业微信、LinkedIn）
- LLM话术生成（个性化邮件、消息、话术）
- 触达序列编排（多步骤跟进流程）
- 时机优化（最佳发送时间预测）
- A/B测试（内容效果对比）

### 3.2 用户故事

```
US-3.1: 自动生成邮件
作为 销售经理
我想要 AI根据客户画像自动生成个性化邮件
以便于 提高邮件打开率和回复率
验收标准：邮件包含个性化元素，与客户背景相关

US-3.2: 触达序列
作为 销售经理
我想要 系统自动执行多步骤触达序列
以便于 持续跟进，提高转化
验收标准：序列自动执行，根据反馈调整后续步骤

US-3.3: 最佳时机
作为 销售经理
我想要 系统在最佳时间发送触达
以便于 最大化打开率
验收标准：发送时间在客户工作时间段

US-3.4: 多渠道触达
作为 销售经理
我想要 通过邮件和企微双渠道触达客户
以便于 提高触达覆盖
验收标准：支持配置主渠道和备选渠道

US-3.5: A/B测试
作为 销售经理
我想要 对比不同邮件模板的效果
以便于 找到最优话术
验收标准：能看到A/B两组的打开率和回复率对比
```

### 3.3 技术实现要点

#### 3.3.1 触达序列编排

```yaml
# config/reach_sequences/default_saas.yaml
name: "SaaS默认触达序列"
description: "适用于SaaS行业的标准触达流程"
version: "1.0"

channels:
  - email
  - wechat

steps:
  # Step 1: 介绍邮件
  - step: 1
    name: "intro_email"
    channel: "email"
    delay: "0h"
    template: "intro_saas"
    personalization:
      - "recipient_name"
      - "company_name"
      - "industry_insight"
      - "pain_point_1"
    subject_template: "{{company_name}}的数字化转型思考"
    content_template: |
      {{recipient_name}}你好，
      
      我注意到{{company_name}}在{{industry}}领域的布局，特别是在{{focus_area}}方面的投入。
      
      很多类似规模的企业在{{pain_point_1}}方面遇到挑战，我们帮助{{case_company}}解决了类似问题，效果是{{case_result}}。
      
      有兴趣聊聊吗？
      
      {{sender_name}}

  # Step 2: 跟进邮件（未打开）
  - step: 2
    name: "follow_up_email"
    channel: "email"
    delay: "48h"
    condition:
      type: "not_opened"
      ref_step: 1
    template: "follow_up_brief"
    subject_template: "Re: {{company_name}}的数字化转型思考"

  # Step 3: 价值内容（未回复）
  - step: 3
    name: "value_add_email"
    channel: "email"
    delay: "72h"
    condition:
      type: "not_replied"
      ref_step: 1
    template: "case_study"
    attachment: "case_study.pdf"

  # Step 4: 企微好友请求
  - step: 4
    name: "wechat_request"
    channel: "wechat"
    delay: "24h"
    condition:
      type: "always"
    template: "wx_intro"
    content_template: |
      你好{{recipient_name}}，我是{{sender_company}}的{{sender_name}}。
      刚给你发了封关于{{topic}}的邮件，想加个微信方便交流。

  # Step 5: 企微跟进（已通过）
  - step: 5
    name: "wechat_follow"
    channel: "wechat"
    delay: "48h"
    condition:
      type: "wechat_accepted"
      ref_step: 4
    template: "wx_case_share"

  # Step 6: 结束邮件
  - step: 6
    name: "break_up_email"
    channel: "email"
    delay: "168h"  # 7天后
    condition:
      type: "not_replied"
      ref_step: 1
    template: "break_up"
    content_template: |
      {{recipient_name}}，
      
      最后跟进一次，如果现在不是合适时机，完全没问题。
      
      如果以后有需要，随时联系我。
      
      祝好，
      {{sender_name}}

settings:
  max_daily_reach: 50
  min_interval_minutes: 30
  respect_timezone: true
  quiet_hours: "22:00-08:00"
  stop_on_reply: true
  stop_on_meeting: true
```

#### 3.3.2 LLM话术生成

```python
# api/services/reach/content_generator.py
from typing import Dict, List
from openai import AsyncOpenAI

class ContentGenerator:
    """个性化内容生成器"""
    
    SYSTEM_PROMPT = """你是一位专业的B2B销售文案专家。
你的任务是撰写个性化、高转化率的销售邮件。

核心原则：
1. 开头抓住注意力 - 用客户关心的话题切入
2. 展示对客户痛点的理解 - 不要泛泛而谈
3. 提供具体的价值主张 - 用数据和案例说话
4. 使用清晰的CTA - 不要让客户猜下一步
5. 避免营销腔调 - 像专业人士之间的交流
6. 语气专业但友好 - 不要太正式或太随意

禁忌：
- 不要使用"我们公司是行业领先"等空洞表述
- 不要开头就介绍产品功能
- 不要使用过多的感叹号
- 不要写超过200字的邮件"""

    def __init__(self):
        self.client = AsyncOpenAI()
    
    async def generate_email(
        self,
        prospect: Dict,
        profile: Dict,
        template_type: str,
        previous_interactions: List[Dict] = None
    ) -> Dict:
        """生成个性化邮件"""
        
        prompt = self._build_prompt(
            prospect, profile, template_type, previous_interactions
        )
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        return self._parse_email(content)
    
    def _build_prompt(
        self,
        prospect: Dict,
        profile: Dict,
        template_type: str,
        previous: List[Dict]
    ) -> str:
        """构建生成提示"""
        
        prompt = f"""## 任务
为以下潜在客户生成一封{template_type}邮件。

## 客户信息
- 姓名: {prospect.get('name', '未知')}
- 职位: {prospect.get('title', '未知')}
- 公司: {prospect.get('company', '未知')}
- 行业: {prospect.get('industry', '未知')}
- 公司规模: {prospect.get('company_size', '未知')}

## 客户画像
- 决策级别: {profile.get('role_characteristics', {}).get('decision_level', '未知')}
- 关注重点: {', '.join(profile.get('role_characteristics', {}).get('focus_areas', []))}
- 潜在痛点: {', '.join(profile.get('needs_analysis', {}).get('pain_points', []))}
- 沟通风格偏好: {profile.get('reach_suggestion', {}).get('communication_style', '专业')}

## 邮件类型
{self._get_template_instruction(template_type)}

## 输出格式
Subject: [邮件主题，不超过50字]

[邮件正文，150-200字]

---
请在正文中包含至少2个个性化元素（客户名字、公司名、行业洞察等）。
"""
        
        if previous:
            prompt += f"\n## 历史互动\n"
            for i, interaction in enumerate(previous[-3:], 1):
                prompt += f"{i}. {interaction['type']}: {interaction['summary']}\n"
        
        return prompt
    
    def _get_template_instruction(self, template_type: str) -> str:
        """获取模板类型说明"""
        instructions = {
            "intro": """介绍邮件 - 首次触达
目标：建立联系，引发兴趣
要点：用行业洞察或共同话题开头，简要说明价值，提出简单的CTA""",
            
            "follow_up": """跟进邮件 - 客户未回复
目标：唤起注意，提供新价值
要点：简短，提及上一封邮件，提供新的切入点""",
            
            "value_add": """价值邮件 - 提供有用内容
目标：建立专业形象，提供价值
要点：分享案例、数据、洞察，不要硬推销""",
            
            "break_up": """结束邮件 - 最后一次触达
目标：保持良好印象，留有余地
要点：简短、真诚、不强求"""
        }
        return instructions.get(template_type, instructions["intro"])
    
    def _parse_email(self, content: str) -> Dict:
        """解析邮件内容"""
        lines = content.strip().split('\n')
        subject = ""
        body_lines = []
        in_body = False
        
        for line in lines:
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()
            elif in_body or (subject and line.strip()):
                in_body = True
                body_lines.append(line)
        
        return {
            "subject": subject,
            "body": '\n'.join(body_lines).strip()
        }
```

#### 3.3.3 时机优化

```python
# api/services/reach/timing_optimizer.py
from typing import Dict, List
from datetime import datetime, time
import pytz

class TimingOptimizer:
    """触达时机优化器"""
    
    # 默认最佳发送时间（根据渠道）
    DEFAULT_BEST_TIMES = {
        "email": [
            (9, 30),   # 早上9:30
            (14, 0),   # 下午2:00
            (16, 30),  # 下午4:30
        ],
        "wechat": [
            (9, 0),    # 早上9:00
            (12, 30),  # 中午12:30
            (18, 0),   # 下午6:00
        ],
        "phone": [
            (10, 0),   # 上午10:00
            (15, 0),   # 下午3:00
        ]
    }
    
    def optimize_send_time(
        self,
        channel: str,
        prospect: Dict,
        profile: Dict
    ) -> datetime:
        """计算最佳发送时间"""
        
        # 1. 获取客户时区
        timezone = self._get_timezone(prospect)
        
        # 2. 获取推荐时间段
        preferred_time = profile.get("reach_suggestion", {}).get(
            "best_reach_time", "morning"
        )
        
        # 3. 获取渠道默认最佳时间
        default_times = self.DEFAULT_BEST_TIMES.get(channel, [(10, 0)])
        
        # 4. 根据偏好调整
        if preferred_time == "morning":
            hour, minute = default_times[0]
        elif preferred_time == "afternoon":
            hour, minute = default_times[1] if len(default_times) > 1 else default_times[0]
        else:  # evening
            hour, minute = default_times[-1]
        
        # 5. 计算下一次发送时间
        now = datetime.now(timezone)
        send_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 如果已过今天的最佳时间，推到明天
        if send_time <= now:
            send_time = send_time.replace(day=now.day + 1)
        
        # 6. 避开周末
        if send_time.weekday() >= 5:  # 周六或周日
            send_time = send_time.replace(day=send_time.day + (7 - send_time.weekday()))
        
        return send_time
    
    def _get_timezone(self, prospect: Dict) -> pytz.timezone:
        """获取客户时区"""
        region = prospect.get("region", "北京")
        
        timezone_map = {
            "北京": "Asia/Shanghai",
            "上海": "Asia/Shanghai",
            "深圳": "Asia/Shanghai",
            "广州": "Asia/Shanghai",
            "杭州": "Asia/Shanghai",
            "成都": "Asia/Shanghai",
            "香港": "Asia/Hong_Kong",
            "台北": "Asia/Taipei",
            "新加坡": "Asia/Singapore",
            "东京": "Asia/Tokyo",
        }
        
        tz_name = timezone_map.get(region, "Asia/Shanghai")
        return pytz.timezone(tz_name)
    
    def get_quiet_hours(self) -> List[time]:
        """获取静默时段"""
        # 默认22:00-08:00不发送
        return [
            (time(22, 0), time(23, 59)),
            (time(0, 0), time(8, 0))
        ]
    
    def is_quiet_time(self, dt: datetime, timezone: pytz.timezone) -> bool:
        """检查是否在静默时段"""
        local_time = dt.astimezone(timezone).time()
        
        for start, end in self.get_quiet_hours():
            if start <= end:
                if start <= local_time <= end:
                    return True
            else:  # 跨午夜
                if local_time >= start or local_time <= end:
                    return True
        
        return False
```

#### 3.3.4 多渠道适配器

```python
# api/services/reach/channel_adapters.py
from abc import ABC, abstractmethod
from typing import Dict, Optional
import httpx

class ChannelAdapter(ABC):
    """渠道适配器基类"""
    
    @abstractmethod
    async def send(self, to: str, content: Dict) -> Dict:
        """发送消息"""
        pass
    
    @abstractmethod
    async def get_status(self, message_id: str) -> Dict:
        """获取消息状态"""
        pass


class EmailAdapter(ChannelAdapter):
    """邮件适配器（SendGrid/Resend）"""
    
    def __init__(self, provider: str = "resend", api_key: str = None):
        self.provider = provider
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def send(self, to: str, content: Dict) -> Dict:
        """发送邮件"""
        if self.provider == "resend":
            return await self._send_via_resend(to, content)
        else:
            return await self._send_via_sendgrid(to, content)
    
    async def _send_via_resend(self, to: str, content: Dict) -> Dict:
        """通过Resend发送"""
        resp = await self.client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": content["from"],
                "to": [to],
                "subject": content["subject"],
                "html": content["body"],
                "headers": {
                    "X-Entity-Ref-ID": content.get("tracking_id", "")
                }
            }
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "message_id": data["id"],
                "provider": "resend"
            }
        else:
            return {
                "success": False,
                "error": resp.text
            }
    
    async def get_status(self, message_id: str) -> Dict:
        """获取邮件状态（通过webhook更新）"""
        # Resend通过webhook通知状态
        # 这里返回缓存的状态
        return {
            "message_id": message_id,
            "status": "sent"  # sent, delivered, opened, clicked, bounced
        }


class WeChatAdapter(ChannelAdapter):
    """企业微信适配器"""
    
    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self.access_token = None
        self.client = httpx.AsyncClient()
    
    async def send(self, to: str, content: Dict) -> Dict:
        """发送企微消息"""
        # 获取access_token
        if not self.access_token:
            await self._refresh_token()
        
        # 发送消息
        resp = await self.client.post(
            f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}",
            json={
                "touser": to,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content["body"]
                }
            }
        )
        
        data = resp.json()
        if data.get("errcode") == 0:
            return {
                "success": True,
                "message_id": data.get("msgid"),
                "provider": "wechat"
            }
        else:
            return {
                "success": False,
                "error": data.get("errmsg")
            }
    
    async def _refresh_token(self):
        """刷新access_token"""
        resp = await self.client.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            params={
                "corpid": self.corp_id,
                "corpsecret": self.secret
            }
        )
        data = resp.json()
        self.access_token = data.get("access_token")
    
    async def get_status(self, message_id: str) -> Dict:
        """获取消息状态"""
        # 企微消息状态需要通过回调获取
        return {
            "message_id": message_id,
            "status": "sent"
        }


class ChannelManager:
    """渠道管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, ChannelAdapter] = {}
    
    def register(self, channel: str, adapter: ChannelAdapter):
        """注册渠道适配器"""
        self.adapters[channel] = adapter
    
    async def send(
        self,
        channel: str,
        to: str,
        content: Dict
    ) -> Dict:
        """发送消息"""
        adapter = self.adapters.get(channel)
        if not adapter:
            return {
                "success": False,
                "error": f"Unknown channel: {channel}"
            }
        
        return await adapter.send(to, content)
```

### 3.4 优先级

| 功能 | 优先级 | 理由 |
|------|--------|------|
| LLM话术生成 | P0 | 核心差异化能力 |
| 邮件触达 | P0 | 主要触达渠道 |
| 触达序列编排 | P0 | 自动化核心 |
| 时机优化 | P0 | 提升效果 |
| 企微触达 | P1 | 国内重要渠道 |
| A/B测试 | P1 | 优化工具 |
| 电话触达 | P2 | 需要更多集成 |
| LinkedIn触达 | P2 | 出海场景 |

---

## 模块4：效果追踪模块

### 4.1 功能描述

**核心目标**：追踪所有触达的效果，分析转化漏斗，计算ROI，支持A/B测试。

**子功能**：
- 转化漏斗分析（发送→送达→打开→点击→回复→会议→成交）
- ROI分析（成本、收益、投资回报率）
- A/B测试（不同内容效果对比）
- 实时仪表盘（关键指标可视化）

### 4.2 用户故事

```
US-4.1: 查看漏斗数据
作为 销售经理
我想要 查看完整的转化漏斗
以便于 了解哪个环节流失最严重
验收标准：漏斗显示各阶段数量和转化率

US-4.2: ROI分析
作为 销售总监
我想要 查看活动的ROI
以便于 评估投入产出
验收标准：显示成本、收入、ROI百分比

US-4.3: A/B测试结果
作为 销售经理
我想要 对比两个邮件模板的效果
以便于 选择最优模板
验收标准：显示打开率、回复率对比，有统计显著性标识

US-4.4: 实时仪表盘
作为 销售经理
我想要 实时查看活动执行进度
以便于 及时发现问题
验收标准：数据延迟<5分钟

US-4.5: 导出报告
作为 销售总监
我想要 导出效果分析报告
以便于 向上级汇报
验收标准：支持PDF/Excel格式
```

### 4.3 技术实现要点

#### 4.3.1 转化漏斗模型

```python
# api/services/analytics/funnel.py
from typing import Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class FunnelStage:
    """漏斗阶段"""
    name: str
    count: int
    conversion_rate: float  # 从上一阶段转化率
    drop_rate: float  # 流失率

class ConversionFunnel:
    """转化漏斗分析"""
    
    STAGES = [
        "prospects",      # 线索
        "reached",        # 已触达
        "delivered",      # 已送达
        "opened",         # 已打开
        "clicked",        # 已点击
        "replied",        # 已回复
        "meeting",        # 已预约会议
        "opportunity",    # 已创建商机
        "closed"          # 已成交
    ]
    
    def analyze(
        self,
        campaign_id: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """分析转化漏斗"""
        
        # 获取各阶段数据
        stage_counts = self._get_stage_counts(campaign_id, start_date, end_date)
        
        # 计算漏斗
        funnel = []
        prev_count = None
        
        for stage in self.STAGES:
            count = stage_counts.get(stage, 0)
            
            if prev_count is not None and prev_count > 0:
                conversion_rate = (count / prev_count) * 100
                drop_rate = 100 - conversion_rate
            else:
                conversion_rate = 100.0 if stage == "prospects" else 0
                drop_rate = 0
            
            funnel.append(FunnelStage(
                name=stage,
                count=count,
                conversion_rate=round(conversion_rate, 1),
                drop_rate=round(drop_rate, 1)
            ))
            
            prev_count = count
        
        # 计算总体转化率
        total_conversion = 0
        if stage_counts.get("prospects", 0) > 0:
            total_conversion = (
                stage_counts.get("closed", 0) / 
                stage_counts.get("prospects", 1) * 100
            )
        
        return {
            "campaign_id": campaign_id,
            "funnel": [{"name": s.name, "count": s.count, 
                       "conversion_rate": s.conversion_rate, 
                       "drop_rate": s.drop_rate} for s in funnel],
            "total_conversion": round(total_conversion, 2),
            "analysis": self._analyze_drop_offs(funnel)
        }
    
    def _get_stage_counts(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """获取各阶段数量"""
        # 实际实现中从数据库查询
        # 这里返回模拟数据
        return {
            "prospects": 1000,
            "reached": 950,
            "delivered": 900,
            "opened": 450,
            "clicked": 180,
            "replied": 45,
            "meeting": 15,
            "opportunity": 8,
            "closed": 3
        }
    
    def _analyze_drop_offs(self, funnel: List[FunnelStage]) -> List[Dict]:
        """分析流失点"""
        drop_offs = []
        
        for i, stage in enumerate(funnel[1:], 1):
            if stage.drop_rate > 50:  # 流失率超过50%
                drop_offs.append({
                    "stage": stage.name,
                    "drop_rate": stage.drop_rate,
                    "suggestion": self._get_improvement_suggestion(stage.name)
                })
        
        return drop_offs
    
    def _get_improvement_suggestion(self, stage: str) -> str:
        """获取改进建议"""
        suggestions = {
            "delivered": "检查邮箱列表质量，验证邮箱有效性",
            "opened": "优化邮件主题，提升吸引力",
            "clicked": "优化CTA按钮，提供更有价值的内容",
            "replied": "改进邮件内容个性化，增加互动元素",
            "meeting": "简化预约流程，提供多个时间选择",
            "opportunity": "加强需求挖掘，展示更多价值",
            "closed": "优化报价策略，加强信任建立"
        }
        return suggestions.get(stage, "分析数据找出原因")
```

#### 4.3.2 ROI分析

```python
# api/services/analytics/roi.py
from typing import Dict
from datetime import datetime

class ROIAnalyzer:
    """ROI分析器"""
    
    def calculate(
        self,
        campaign_id: str,
        costs: Dict,
        revenue: Dict
    ) -> Dict:
        """计算ROI"""
        
        # 总成本
        total_cost = sum(costs.values())
        
        # 总收入
        total_revenue = revenue.get("total", 0)
        
        # ROI
        roi = 0
        if total_cost > 0:
            roi = ((total_revenue - total_cost) / total_cost) * 100
        
        # 各项指标
        metrics = {
            "cost_per_prospect": self._calc_per_unit(
                total_cost, costs.get("prospects_count", 1)
            ),
            "cost_per_reach": self._calc_per_unit(
                costs.get("reach_cost", 0), costs.get("reaches_sent", 1)
            ),
            "cost_per_meeting": self._calc_per_unit(
                total_cost, revenue.get("meetings", 1)
            ),
            "cost_per_opportunity": self._calc_per_unit(
                total_cost, revenue.get("opportunities", 1)
            ),
            "cost_per_closed": self._calc_per_unit(
                total_cost, max(revenue.get("closed_count", 1), 1)
            ),
        }
        
        # 收入分解
        revenue_breakdown = {
            "new_customers": revenue.get("new_customers", 0),
            "expansion": revenue.get("expansion", 0),
            "total": total_revenue
        }
        
        return {
            "campaign_id": campaign_id,
            "summary": {
                "total_cost": round(total_cost, 2),
                "total_revenue": round(total_revenue, 2),
                "net_profit": round(total_revenue - total_cost, 2),
                "roi_percentage": round(roi, 1)
            },
            "costs": costs,
            "revenue": revenue_breakdown,
            "metrics": metrics,
            "payback_period": self._calc_payback_period(total_cost, total_revenue)
        }
    
    def _calc_per_unit(self, total: float, count: int) -> float:
        """计算单位成本"""
        if count <= 0:
            return 0
        return round(total / count, 2)
    
    def _calc_payback_period(self, cost: float, revenue: float) -> str:
        """计算回本周期"""
        if revenue <= 0:
            return "无法计算"
        
        # 假设活动持续30天
        daily_revenue = revenue / 30
        if daily_revenue <= 0:
            return "无法计算"
        
        days = cost / daily_revenue
        
        if days < 1:
            return "< 1天"
        elif days < 7:
            return f"{int(days)}天"
        elif days < 30:
            return f"{int(days/7)}周"
        else:
            return f"{int(days/30)}个月"
```

#### 4.3.3 A/B测试

```python
# api/services/analytics/ab_test.py
from typing import Dict, List
from dataclasses import dataclass
import math

@dataclass
class ABTestVariant:
    """A/B测试变体"""
    name: str
    sent: int
    opened: int
    clicked: int
    replied: int
    
    @property
    def open_rate(self) -> float:
        return (self.opened / self.sent * 100) if self.sent > 0 else 0
    
    @property
    def click_rate(self) -> float:
        return (self.clicked / self.sent * 100) if self.sent > 0 else 0
    
    @property
    def reply_rate(self) -> float:
        return (self.replied / self.sent * 100) if self.sent > 0 else 0

class ABTestAnalyzer:
    """A/B测试分析器"""
    
    def analyze(
        self,
        test_id: str,
        variants: List[ABTestVariant]
    ) -> Dict:
        """分析A/B测试结果"""
        
        results = []
        
        for v in variants:
            results.append({
                "name": v.name,
                "sent": v.sent,
                "opened": v.opened,
                "clicked": v.clicked,
                "replied": v.replied,
                "open_rate": round(v.open_rate, 2),
                "click_rate": round(v.click_rate, 2),
                "reply_rate": round(v.reply_rate, 2)
            })
        
        # 找出各指标最优变体
        best_open = max(results, key=lambda x: x["open_rate"])
        best_click = max(results, key=lambda x: x["click_rate"])
        best_reply = max(results, key=lambda x: x["reply_rate"])
        
        # 计算统计显著性
        if len(variants) >= 2:
            significance = self._calculate_significance(variants[0], variants[1])
        else:
            significance = {"is_significant": False, "confidence": 0}
        
        return {
            "test_id": test_id,
            "variants": results,
            "winners": {
                "open_rate": best_open["name"],
                "click_rate": best_click["name"],
                "reply_rate": best_reply["name"]
            },
            "statistical_significance": significance,
            "recommendation": self._generate_recommendation(
                best_reply, significance
            )
        }
    
    def _calculate_significance(
        self,
        control: ABTestVariant,
        variant: ABTestVariant
    ) -> Dict:
        """计算统计显著性（简化版Z检验）"""
        
        # 使用回复率计算
        p1 = control.reply_rate / 100
        p2 = variant.reply_rate / 100
        n1 = control.sent
        n2 = variant.sent
        
        if n1 == 0 or n2 == 0:
            return {"is_significant": False, "confidence": 0}
        
        # 合并比例
        p_pooled = (control.replied + variant.replied) / (n1 + n2)
        
        if p_pooled == 0:
            return {"is_significant": False, "confidence": 0}
        
        # 标准误差
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
        
        if se == 0:
            return {"is_significant": False, "confidence": 0}
        
        # Z分数
        z = (p2 - p1) / se
        
        # 置信度（简化计算）
        confidence = min(abs(z) * 30, 95)  # 简化
        
        return {
            "is_significant": abs(z) > 1.96,  # 95%置信水平
            "z_score": round(z, 2),
            "confidence": round(confidence, 1)
        }
    
    def _generate_recommendation(
        self,
        best: Dict,
        significance: Dict
    ) -> str:
        """生成建议"""
        if significance["is_significant"]:
            return f"建议采用变体【{best['name']}】，结果具有统计显著性（置信度{significance['confidence']}%）"
        else:
            return f"变体【{best['name']}】表现最佳，但样本量可能不足，建议继续测试"
```

### 4.4 优先级

| 功能 | 优先级 | 理由 |
|------|--------|------|
| 转化漏斗 | P0 | 核心分析功能 |
| 实时仪表盘 | P0 | 用户必需 |
| 基础指标统计 | P0 | 基础功能 |
| ROI分析 | P1 | 管理层需求 |
| A/B测试 | P1 | 优化工具 |
| 导出报告 | P1 | 汇报需求 |
| 预测分析 | P2 | 高级功能 |

---

## 模块5：管理后台

### 5.1 功能描述

**核心目标**：提供可视化仪表盘和系统管理功能。

**子功能**：
- 仪表盘（关键指标、趋势图、活动概览）
- 权限管理（角色、权限、用户管理）
- 系统配置（渠道配置、模板管理、规则设置）
- 数据管理（导入导出、备份恢复）

### 5.2 用户故事

```
US-5.1: 查看仪表盘
作为 销售经理
我想要 一眼看到所有活动的关键指标
以便于 快速了解整体情况
验收标准：显示线索数、触达数、回复数、会议数

US-5.2: 权限管理
作为 管理员
我想要 给团队成员分配不同权限
以便于 控制数据访问
验收标准：支持角色创建和权限分配

US-5.3: 模板管理
作为 销售经理
我想要 管理邮件和消息模板
以便于 复用和优化
验收标准：支持创建、编辑、删除模板

US-5.4: 数据导入
作为 销售经理
我想要 导入Excel中的线索
以便于 使用现有数据
验收标准：支持Excel/CSV导入，自动去重

US-5.5: 系统配置
作为 管理员
我想要 配置渠道和规则
以便于 定制系统行为
验收标准：支持邮件服务、企微等渠道配置
```

### 5.3 技术实现要点

#### 5.3.1 仪表盘数据结构

```python
# api/models/dashboard.py
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class DashboardMetrics(BaseModel):
    """仪表盘指标"""
    # 线索指标
    total_prospects: int
    new_prospects_today: int
    prospects_by_grade: Dict[str, int]  # {A: 10, B: 50, C: 100}
    
    # 触达指标
    total_reaches: int
    reaches_today: int
    open_rate: float
    reply_rate: float
    
    # 转化指标
    meetings_booked: int
    opportunities_created: int
    deals_closed: int
    revenue: float
    
    # 活动状态
    active_campaigns: int
    pending_tasks: int

class TrendData(BaseModel):
    """趋势数据"""
    date: datetime
    value: float

class DashboardData(BaseModel):
    """仪表盘完整数据"""
    metrics: DashboardMetrics
    trends: Dict[str, List[TrendData]]  # {"prospects": [...], "reaches": [...]}
    recent_activities: List[Dict]
    alerts: List[Dict]
```

#### 5.3.2 权限模型

```python
# api/models/auth.py
from pydantic import BaseModel
from typing import List, Set
from enum import Enum

class Permission(str, Enum):
    """权限枚举"""
    # 线索权限
    PROSPECT_READ = "prospect:read"
    PROSPECT_WRITE = "prospect:write"
    PROSPECT_DELETE = "prospect:delete"
    
    # 活动权限
    CAMPAIGN_READ = "campaign:read"
    CAMPAIGN_WRITE = "campaign:write"
    CAMPAIGN_DELETE = "campaign:delete"
    CAMPAIGN_EXECUTE = "campaign:execute"
    
    # 触达权限
    REACH_READ = "reach:read"
    REACH_WRITE = "reach:write"
    REACH_EXECUTE = "reach:execute"
    
    # 报告权限
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"
    
    # 管理权限
    USER_MANAGE = "user:manage"
    TENANT_MANAGE = "tenant:manage"
    SYSTEM_CONFIG = "system:config"

class Role(BaseModel):
    """角色"""
    id: str
    name: str
    permissions: Set[Permission]
    description: str

# 预定义角色
ROLES = {
    "admin": Role(
        id="admin",
        name="管理员",
        permissions=set(Permission),  # 所有权限
        description="系统管理员，拥有所有权限"
    ),
    "manager": Role(
        id="manager",
        name="销售经理",
        permissions={
            Permission.PROSPECT_READ, Permission.PROSPECT_WRITE,
            Permission.CAMPAIGN_READ, Permission.CAMPAIGN_WRITE, 
            Permission.CAMPAIGN_EXECUTE,
            Permission.REACH_READ, Permission.REACH_WRITE, 
            Permission.REACH_EXECUTE,
            Permission.REPORT_READ, Permission.REPORT_EXPORT
        },
        description="销售经理，可管理活动和触达"
    ),
    "member": Role(
        id="member",
        name="销售成员",
        permissions={
            Permission.PROSPECT_READ,
            Permission.CAMPAIGN_READ,
            Permission.REACH_READ, Permission.REACH_EXECUTE,
            Permission.REPORT_READ
        },
        description="销售成员，可执行触达和查看报告"
    ),
    "viewer": Role(
        id="viewer",
        name="观察者",
        permissions={
            Permission.PROSPECT_READ,
            Permission.CAMPAIGN_READ,
            Permission.REACH_READ,
            Permission.REPORT_READ
        },
        description="只读权限"
    )
}

class User(BaseModel):
    """用户"""
    id: str
    tenant_id: str
    email: str
    name: str
    role: Role
    is_active: bool = True
    created_at: datetime
    
    def has_permission(self, permission: Permission) -> bool:
        """检查是否有权限"""
        return permission in self.role.permissions
```

#### 5.3.3 前端组件示例

```typescript
// components/Dashboard/Dashboard.tsx
'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface DashboardProps {
  metrics: DashboardMetrics
  trends: TrendData[]
}

export function Dashboard({ metrics, trends }: DashboardProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* 线索卡片 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">总线索</CardTitle>
          <svg className="h-4 w-4 text-muted-foreground">...</svg>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.total_prospects}</div>
          <p className="text-xs text-muted-foreground">
            +{metrics.new_prospects_today} 今日新增
          </p>
        </CardContent>
      </Card>
      
      {/* 触达卡片 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">触达数</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.total_reaches}</div>
          <p className="text-xs text-muted-foreground">
            打开率 {metrics.open_rate}%
          </p>
        </CardContent>
      </Card>
      
      {/* 会议卡片 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">预约会议</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.meetings_booked}</div>
          <p className="text-xs text-muted-foreground">
            回复率 {metrics.reply_rate}%
          </p>
        </CardContent>
      </Card>
      
      {/* 收入卡片 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">成单金额</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            ¥{metrics.revenue.toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.deals_closed} 笔成交
          </p>
        </CardContent>
      </Card>
      
      {/* 趋势图 */}
      <Card className="col-span-4">
        <CardHeader>
          <CardTitle>趋势</CardTitle>
        </CardHeader>
        <CardContent className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends}>
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="prospects" stroke="#8884d8" />
              <Line type="monotone" dataKey="reaches" stroke="#82ca9d" />
              <Line type="monotone" dataKey="replies" stroke="#ffc658" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
```

### 5.4 优先级

| 功能 | 优先级 | 理由 |
|------|--------|------|
| 仪表盘 | P0 | 用户首先看到的功能 |
| 用户管理 | P0 | 多租户必需 |
| 角色权限 | P0 | 安全必需 |
| 模板管理 | P1 | 效率工具 |
| 数据导入 | P1 | 数据迁移必需 |
| 系统配置 | P1 | 运维必需 |
| 审计日志 | P2 | 合规需求 |

---

## 总结

### 工作量估算

| 模块 | P0功能 | P1功能 | P2功能 | 总工作量 |
|------|--------|--------|--------|----------|
| 1. 线索采集 | 3天 | 1天 | 1天 | 5天 |
| 2. 客户画像 | 3天 | 1天 | - | 4天 |
| 3. 智能触达 | 4天 | 1.5天 | 0.5天 | 6天 |
| 4. 效果追踪 | 2天 | 1天 | - | 3天 |
| 5. 管理后台 | 2.5天 | 1天 | 0.5天 | 4天 |
| **总计** | **14.5天** | **5.5天** | **2天** | **22天** |

### 技术依赖

```
模块依赖关系：

[线索采集] ──→ [客户画像] ──→ [智能触达] ──→ [效果追踪]
      │              │              │              │
      └──────────────┴──────────────┴──────────────┘
                           │
                    [管理后台]
```

### 下一步

1. 确认优先级排序
2. 搭建开发环境
3. 按Phase 1（MVP）开始实现：
   - 线索采集核心
   - 基础画像
   - 邮件触达
   - 基础仪表盘

---

*文档完成时间：2026-03-10*
*设计人：小pm*
