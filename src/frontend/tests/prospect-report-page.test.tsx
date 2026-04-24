import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

const mockedNavigation = vi.hoisted(() => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
}));

const mockedProspectsApi = vi.hoisted(() => ({
  getProspectReportById: vi.fn(async (id: string) => {
    if (id === "missing") {
      return null;
    }

    return {
      id: "lead-3",
      company_name: "深圳增长引擎软件",
      region: "深圳",
      industry: "SaaS",
      role: "CTO",
      priority: "B",
      bant_score: 75,
      summary_text: "深圳增长引擎软件属于 SaaS 行业，当前优先级 B，建议优先跟进。",
      bant: {
        score: 75,
        priority: "B",
        budget: 20,
        authority: 20,
        need: 20,
        timeline: 15,
      },
      profile: {
        industry: "SaaS",
        company_scale: "50-100 人",
        pain_points: ["人工筛选效率低"],
        needs: ["画像报告交付"],
      },
    };
  }),
}));

vi.mock("next/navigation", () => mockedNavigation);
vi.mock("@/lib/prospects-api", () => mockedProspectsApi);

import ProspectReportPage from "@/app/prospects/[id]/page";

describe("ProspectReportPage", () => {
  it("renders demo report without calling backend for stable sample route", async () => {
    render(await ProspectReportPage({ params: { id: "demo-report" } }));

    expect(screen.getByRole("heading", { name: /企业画像报告/i })).toBeInTheDocument();
    expect(screen.getByText(/深圳出海增长科技有限公司/i)).toBeInTheDocument();
    expect(mockedProspectsApi.getProspectReportById).not.toHaveBeenCalledWith("demo-report");
  });

  it("renders report sections for industry, scale, pain points and needs", async () => {
    render(await ProspectReportPage({ params: { id: "lead-3" } }));

    expect(screen.getByRole("heading", { name: /企业画像报告/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /导出当前条件 CSV/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /导出当前条件 CSV/i })).toHaveAttribute("data-prospect-id", "lead-3");
    expect(screen.getByText(/按当前报告条件导出匹配结果 CSV/i)).toBeInTheDocument();
    expect(screen.getByText(/深圳增长引擎软件/i)).toBeInTheDocument();
    expect(screen.getByText(/行业/i)).toBeInTheDocument();
    expect(screen.getByText(/规模/i)).toBeInTheDocument();
    expect(screen.getByText(/痛点/i)).toBeInTheDocument();
    expect(screen.getByText(/需求/i)).toBeInTheDocument();
    expect(screen.getByText(/bant 评分/i)).toBeInTheDocument();
  });

  it("requests backend report with encoded route ids decoded by Next params", async () => {
    render(await ProspectReportPage({ params: { id: "lead/with space?x=1" } }));

    expect(mockedProspectsApi.getProspectReportById).toHaveBeenCalledWith("lead/with space?x=1");
    expect(screen.getByRole("heading", { name: /企业画像报告/i })).toBeInTheDocument();
  });

});
