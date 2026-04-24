import type { ProspectReportView } from "@/lib/prospects-api";

export const demoReport: ProspectReportView = {
  id: "demo-report",
  company_name: "深圳出海增长科技有限公司",
  region: "深圳",
  industry: "跨境电商 SaaS",
  role: "销售负责人",
  priority: "A",
  bant_score: 86,
  summary_text: "深圳出海增长科技有限公司属于跨境电商 SaaS 行业，当前优先级 A，建议优先跟进。",
  bant: {
    score: 86,
    priority: "A",
    budget: 22,
    authority: 22,
    need: 24,
    timeline: 18,
  },
  profile: {
    industry: "跨境电商 SaaS",
    company_scale: "100-300 人",
    pain_points: [
      "销售线索来源分散，人工筛选成本高",
      "缺少统一的客户画像与优先级机制",
    ],
    needs: [
      "希望快速定位高潜客户并输出可执行名单",
      "希望销售团队获得结构化画像报告辅助跟进",
    ],
  },
};

export function getDemoReportById(id: string): ProspectReportView | null {
  if (id === demoReport.id) {
    return demoReport;
  }

  return null;
}
