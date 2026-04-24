import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

const mockedProspectsApi = vi.hoisted(() => ({
  listProspects: vi.fn(async () => ({
    items: [
      {
        id: "lead-1",
        company_name: "深圳云帆 SaaS 科技",
        region: "深圳",
        industry: "SaaS",
        role: "CTO",
        website: "yunfan.example.com",
        contact_email: "cto@yunfan.example.com",
        bant: {
          score: 87,
          priority: "A",
          budget: 24,
          authority: 22,
          need: 23,
          timeline: 18,
        },
        profile: {
          industry: "SaaS",
          company_scale: "100-300 人",
          pain_points: ["线索分散"],
          needs: ["统一线索池"],
        },
      },
    ],
  })),
  listAvailableDataSources: vi.fn(async () => ({
    items: [
      {
        key: "mock_seed",
        label: "Mock seed",
        type: "seed",
        status: "available",
        description: "内置示例线索数据，可直接用于 Phase 0/1 MVP 验证。",
      },
      {
        key: "csv_import",
        label: "CSV import",
        type: "import",
        status: "available",
        description: "上传企业名单 CSV，走最小导入闭环并生成线索画像。",
      },
    ],
  })),
}));

vi.mock("@/lib/prospects-api", () => mockedProspectsApi);

import ProspectsPage from "@/app/prospects/page";

describe("ProspectsPage", () => {
  it("renders backend-driven prospect list", async () => {
    render(await ProspectsPage({ searchParams: {} }));

    expect(screen.getByRole("heading", { name: /线索采集任务/i })).toBeInTheDocument();
    expect(screen.getByText(/深圳云帆 SaaS 科技/i)).toBeInTheDocument();
    expect(screen.getByText(/角色：CTO/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /查看报告/i })).toHaveAttribute("href", "/prospects/lead-1");
  });

  it("renders available data sources for phase zero visibility", async () => {
    render(await ProspectsPage({ searchParams: {} }));

    expect(screen.getByRole("heading", { name: /可用数据源/i })).toBeInTheDocument();
    expect(screen.getByText(/Mock seed/i)).toBeInTheDocument();
    expect(screen.getByText(/CSV import/i)).toBeInTheDocument();
    expect(screen.getByText(/内置示例线索数据，可直接用于 Phase 0\/1 MVP 验证。/i)).toBeInTheDocument();
    expect(screen.getByText(/上传企业名单 CSV，走最小导入闭环并生成线索画像。/i)).toBeInTheDocument();
  });

  it("uses search params as form values and request filters", async () => {
    render(
      await ProspectsPage({
        searchParams: {
          industry: "跨境电商",
          region: "深圳,杭州",
          roles: "创始人,销售总监",
          limit: "20",
        },
      }),
    );

    expect(mockedProspectsApi.listProspects).toHaveBeenLastCalledWith({
      industry: "跨境电商",
      region: "深圳,杭州",
      roles: "创始人,销售总监",
      limit: "20",
    });
    expect(screen.getByDisplayValue("跨境电商")).toBeInTheDocument();
    expect(screen.getByDisplayValue("深圳,杭州")).toBeInTheDocument();
    expect(screen.getByDisplayValue("创始人,销售总监")).toBeInTheDocument();
    expect(screen.getByDisplayValue("20")).toBeInTheDocument();
  });

  it("uses first non-empty array search params as form values", async () => {
    render(
      await ProspectsPage({
        searchParams: {
          industry: ["", "跨境电商"],
          region: ["深圳,杭州"],
          roles: ["创始人,销售总监"],
          limit: ["20"],
        },
      }),
    );

    expect(mockedProspectsApi.listProspects).toHaveBeenLastCalledWith({
      industry: "跨境电商",
      region: "深圳,杭州",
      roles: "创始人,销售总监",
      limit: "20",
    });
    expect(screen.getByDisplayValue("跨境电商")).toBeInTheDocument();
  });

  it("encodes unsafe prospect ids in report links", async () => {
    mockedProspectsApi.listProspects.mockResolvedValueOnce({
      items: [
        {
          id: "segment/with spaces?x=1",
          company_name: "编码测试企业",
          region: "深圳",
          industry: "SaaS",
          role: "CTO",
          website: "encode.example.com",
          contact_email: "encode@example.com",
          bant: {
            score: 70,
            priority: "B",
            budget: 18,
            authority: 18,
            need: 18,
            timeline: 16,
          },
          profile: {
            industry: "SaaS",
            company_scale: "50-100 人",
            pain_points: ["链接编码"],
            needs: ["安全跳转"],
          },
        },
      ],
    });

    render(await ProspectsPage({ searchParams: {} }));

    expect(screen.getByRole("link", { name: /查看报告/i })).toHaveAttribute(
      "href",
      "/prospects/segment%2Fwith%20spaces%3Fx%3D1",
    );
  });

});

