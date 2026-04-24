"use client";

import React from "react";

import { downloadProspectsCsv, type ProspectFilters } from "@/lib/prospects-api";

interface ReportExportButtonProps {
  prospectId: string;
  filters: ProspectFilters;
}

const EXPORT_ERROR_MESSAGE = "导出失败，请稍后重试";
const EXPORT_BUTTON_LABEL = "导出当前条件 CSV";
const EXPORT_LOADING_LABEL = "导出中...";

export function ReportExportButton({ prospectId, filters }: ReportExportButtonProps) {
  const [isExporting, setIsExporting] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const handleExport = async () => {
    if (isExporting) {
      return;
    }

    setIsExporting(true);
    setErrorMessage(null);

    try {
      const blob = await downloadProspectsCsv(filters);
      const downloadUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = downloadUrl;
      anchor.download = `prospect-${prospectId}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(downloadUrl);
    } catch {
      setErrorMessage(EXPORT_ERROR_MESSAGE);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div aria-busy={isExporting}>
      <button
        type="button"
        data-prospect-id={prospectId}
        aria-busy={isExporting}
        disabled={isExporting}
        onClick={() => void handleExport()}
      >
        {isExporting ? EXPORT_LOADING_LABEL : EXPORT_BUTTON_LABEL}
      </button>
      {errorMessage ? <p role="alert">{errorMessage}</p> : null}
    </div>
  );
}
