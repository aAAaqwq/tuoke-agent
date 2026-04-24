import React from "react";
import { notFound } from "next/navigation";

import { ReportExportButton } from "@/components/report-export-button";
import { getDemoReportById } from "@/lib/demo-report";
import { getProspectReportById } from "@/lib/prospects-api";

interface ProspectReportPageProps {
  params: {
    id: string;
  };
}

export default async function ProspectReportPage({ params }: ProspectReportPageProps) {
  const report = getDemoReportById(params.id) ?? (await getProspectReportById(params.id));

  if (!report) {
    notFound();
  }

  return (
    <main>
      <section>
        <p>优先级：{report.bant.priority}</p>
        <h1>企业画像报告</h1>
        <p>{report.company_name}</p>
        <ReportExportButton
          prospectId={report.id}
          filters={{ industry: report.industry, region: report.region, roles: report.role, limit: "1" }}
        />
        <p>按当前报告条件导出匹配结果 CSV。</p>
      </section>

      <section>
        <h2>行业</h2>
        <p>{report.industry}</p>
      </section>

      <section>
        <h2>规模</h2>
        <p>{report.profile.company_scale}</p>
      </section>

      <section>
        <h2>痛点</h2>
        <ul>
          {report.profile.pain_points.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>需求</h2>
        <ul>
          {report.profile.needs.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>BANT 评分</h2>
        <p>{report.bant.score}</p>
      </section>
    </main>
  );
}
