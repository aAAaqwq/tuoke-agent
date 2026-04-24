import React from "react";
import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <section>
        <p>拓客智能体</p>
        <h1>线索报告 MVP</h1>
        <p>输入行业、地区与角色，生成 100+ 线索，并输出可交付的企业画像报告。</p>
      </section>

      <section>
        <h2>当前验收目标</h2>
        <ul>
          <li>自动清洗去重，目标有效率 ≥80%</li>
          <li>企业画像覆盖行业、规模、痛点、需求</li>
          <li>BANT 评分输出优先级排序</li>
        </ul>
      </section>

      <nav>
        <Link href="/prospects">开始采集</Link>
        <Link href="/prospects/demo-report">查看报告示例</Link>
      </nav>
    </main>
  );
}
