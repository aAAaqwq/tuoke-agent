import React from "react";
import Link from "next/link";

import {
  listAvailableDataSources,
  listProspects,
  type ProspectDataSourceItem,
  type ProspectFilters,
  type ProspectItem,
} from "@/lib/prospects-api";

interface ProspectsPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

const DEFAULT_FILTERS: Required<ProspectFilters> = {
  industry: "SaaS",
  region: "深圳, 广州",
  roles: "CTO, 技术副总裁",
  limit: "100",
};

function readSearchParam(
  value: string | string[] | undefined,
  fallback: string,
): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (Array.isArray(value)) {
    const firstString = value.find((item) => item.trim());
    if (firstString) {
      return firstString;
    }
  }

  return fallback;
}

function normalizeFilters(
  searchParams: Record<string, string | string[] | undefined> = {},
): Required<ProspectFilters> {
  return {
    industry: readSearchParam(searchParams.industry, DEFAULT_FILTERS.industry),
    region: readSearchParam(searchParams.region, DEFAULT_FILTERS.region),
    roles: readSearchParam(searchParams.roles, DEFAULT_FILTERS.roles),
    limit: readSearchParam(searchParams.limit, DEFAULT_FILTERS.limit),
  };
}

async function loadProspects(filters: ProspectFilters): Promise<ProspectItem[]> {
  try {
    const result = await listProspects(filters);
    return result.items;
  } catch {
    return [];
  }
}

async function loadDataSources(): Promise<ProspectDataSourceItem[]> {
  try {
    const result = await listAvailableDataSources();
    return result.items;
  } catch {
    return [];
  }
}

export default async function ProspectsPage({ searchParams }: ProspectsPageProps) {
  const filters = normalizeFilters(searchParams);
  const [items, dataSources] = await Promise.all([loadProspects(filters), loadDataSources()]);

  return (
    <main>
      <section>
        <h1>线索采集任务</h1>
        <p>当前列表已切到后端 prospects 契约，先用 Mock 接口跑通 MVP。</p>
      </section>

      <section>
        <h2>可用数据源</h2>
        {dataSources.length === 0 ? (
          <p>当前暂无可见数据源，请稍后重试。</p>
        ) : (
          <ul>
            {dataSources.map((source) => (
              <li key={source.key}>
                <strong>{source.label}</strong>
                <p>
                  类型：{source.type} / 状态：{source.status}
                </p>
                <p>{source.description}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>采集条件</h2>
        <form method="get">
          <label>
            行业
            <input name="industry" defaultValue={filters.industry} />
          </label>
          <label>
            地区
            <input name="region" defaultValue={filters.region} />
          </label>
          <label>
            角色
            <input name="roles" defaultValue={filters.roles} />
          </label>
          <label>
            数量
            <input name="limit" type="number" defaultValue={Number(filters.limit)} min={1} />
          </label>
          <button type="submit">生成线索报告</button>
        </form>
      </section>

      <section>
        <h2>最近任务</h2>
        {items.length === 0 ? (
          <p>当前列表暂时不可用，请稍后重试。</p>
        ) : (
          <ul>
            {items.map((item) => (
              <li key={item.id}>
                <h3>{item.company_name}</h3>
                <p>
                  行业：{item.industry} / 地区：{item.region} / 角色：{item.role}
                </p>
                <p>优先级：{item.bant.priority}</p>
                <p>评分：{item.bant.score}</p>
                <Link href={`/prospects/${encodeURIComponent(item.id)}`}>查看报告</Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
