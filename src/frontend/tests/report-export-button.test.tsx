import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReportExportButton } from "@/components/report-export-button";

const mockedProspectsApi = vi.hoisted(() => ({
  downloadProspectsCsv: vi.fn(async () => new Blob(["id,company_name\nlead-1,深圳云帆 SaaS 科技\n"], { type: "text/csv" })),
}));

vi.mock("@/lib/prospects-api", () => mockedProspectsApi);

describe("ReportExportButton", () => {
  beforeEach(() => {
    mockedProspectsApi.downloadProspectsCsv.mockReset();
    mockedProspectsApi.downloadProspectsCsv.mockResolvedValue(
      new Blob(["id,company_name\nlead-1,深圳云帆 SaaS 科技\n"], { type: "text/csv" }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("downloads csv when user exports the report", async () => {
    const user = userEvent.setup();
    const createObjectURLSpy = vi.fn(() => "blob:mock-url");
    const revokeObjectURLSpy = vi.fn();
    const anchorClickSpy = vi.fn();
    const anchorRemoveSpy = vi.fn();
    const anchor = document.createElement("a");
    anchor.click = anchorClickSpy;
    anchor.remove = anchorRemoveSpy;

    const originalCreateElement = document.createElement.bind(document);
    const createElementSpy = vi.spyOn(document, "createElement").mockImplementation((tagName: string) => {
      if (tagName === "a") {
        return anchor;
      }

      return originalCreateElement(tagName);
    });

    vi.stubGlobal("URL", {
      createObjectURL: createObjectURLSpy,
      revokeObjectURL: revokeObjectURLSpy,
    });

    render(<ReportExportButton prospectId="lead-1" filters={{ industry: "SaaS", region: "深圳", roles: "CTO", limit: "20" }} />);

    await user.click(screen.getByRole("button", { name: /导出当前条件 csv/i }));

    expect(mockedProspectsApi.downloadProspectsCsv).toHaveBeenCalledWith({
      industry: "SaaS",
      region: "深圳",
      roles: "CTO",
      limit: "20",
    });
    expect(createObjectURLSpy).toHaveBeenCalledTimes(1);
    expect(anchor.href).toBe("blob:mock-url");
    expect(anchor.download).toBe("prospect-lead-1.csv");
    expect(anchorClickSpy).toHaveBeenCalledTimes(1);
    expect(anchorRemoveSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:mock-url");
    expect(screen.getByRole("button", { name: /导出当前条件 csv/i })).not.toBeDisabled();

    createElementSpy.mockRestore();
  });

  it("shows loading state and prevents duplicate clicks while exporting", async () => {
    let resolveDownload: ((value: Blob) => void) | undefined;
    mockedProspectsApi.downloadProspectsCsv.mockImplementationOnce(
      () =>
        new Promise<Blob>((resolve) => {
          resolveDownload = resolve;
        }),
    );

    const user = userEvent.setup();
    render(<ReportExportButton prospectId="lead-1" filters={{ industry: "SaaS" }} />);

    await user.click(screen.getByRole("button", { name: /导出当前条件 csv/i }));

    const loadingButton = screen.getByRole("button", { name: /导出中/i });
    expect(loadingButton).toBeDisabled();

    await user.click(loadingButton);
    expect(mockedProspectsApi.downloadProspectsCsv).toHaveBeenCalledTimes(1);

    resolveDownload?.(new Blob(["id\nlead-1\n"], { type: "text/csv" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /导出当前条件 csv/i })).not.toBeDisabled();
    });
  });

  it("shows error message and allows retry when export fails", async () => {
    mockedProspectsApi.downloadProspectsCsv
      .mockRejectedValueOnce(new Error("network failed"))
      .mockResolvedValueOnce(new Blob(["id\nlead-1\n"], { type: "text/csv" }));

    const user = userEvent.setup();
    const createObjectURLSpy = vi.fn(() => "blob:retry-url");
    const revokeObjectURLSpy = vi.fn();
    const anchorClickSpy = vi.fn();
    const anchorRemoveSpy = vi.fn();
    const anchor = document.createElement("a");
    anchor.click = anchorClickSpy;
    anchor.remove = anchorRemoveSpy;

    const originalCreateElement = document.createElement.bind(document);
    const createElementSpy = vi.spyOn(document, "createElement").mockImplementation((tagName: string) => {
      if (tagName === "a") {
        return anchor;
      }

      return originalCreateElement(tagName);
    });

    vi.stubGlobal("URL", {
      createObjectURL: createObjectURLSpy,
      revokeObjectURL: revokeObjectURLSpy,
    });

    render(<ReportExportButton prospectId="lead-1" filters={{ industry: "SaaS" }} />);

    await user.click(screen.getByRole("button", { name: /导出当前条件 csv/i }));

    expect(await screen.findByText(/导出失败，请稍后重试/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /导出当前条件 csv/i })).not.toBeDisabled();
    expect(anchorClickSpy).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: /导出当前条件 csv/i }));

    await waitFor(() => {
      expect(mockedProspectsApi.downloadProspectsCsv).toHaveBeenCalledTimes(2);
    });
    await waitFor(() => {
      expect(screen.queryByText(/导出失败，请稍后重试/i)).not.toBeInTheDocument();
    });
    expect(anchorClickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:retry-url");

    createElementSpy.mockRestore();
  });
});
