import React from "react";
import { render, screen } from "@testing-library/react";

import HomePage from "@/app/page";

describe("HomePage", () => {
  it("renders MVP navigation and acceptance summary", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { name: /线索报告 mvp/i })).toBeInTheDocument();
    expect(screen.getByText(/输入行业、地区与角色，生成 100\+ 线索/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /开始采集/i })).toHaveAttribute("href", "/prospects");
    expect(screen.getByRole("link", { name: /查看报告示例/i })).toHaveAttribute("href", "/prospects/demo-report");
  });
});
