export interface BANTScore {
  score: number;
  priority: "A" | "B" | "C" | "D";
  budget: number;
  authority: number;
  need: number;
  timeline: number;
}

export interface ProspectProfile {
  industry: string;
  company_scale: string;
  pain_points: string[];
  needs: string[];
}

export interface ProspectItem {
  id: string;
  company_name: string;
  region: string;
  industry: string;
  role: string;
  website: string;
  contact_email: string;
  bant: BANTScore;
  profile: ProspectProfile;
}

export interface ProspectReportView {
  id: string;
  company_name: string;
  industry: string;
  region: string;
  role: string;
  priority: "A" | "B" | "C" | "D";
  bant_score: number;
  summary_text: string;
  bant: BANTScore;
  profile: ProspectProfile;
}

export interface ProspectDataSourceItem {
  key: string;
  label: string;
  type: "seed" | "import";
  status: "available" | "unavailable";
  description: string;
}

interface ProspectListResult {
  items: ProspectItem[];
}

interface ProspectDataSourceListResult {
  items: ProspectDataSourceItem[];
}

export interface ProspectFilters {
  industry?: string;
  region?: string;
  roles?: string;
  limit?: string;
}

class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isBANTScore(value: unknown): value is BANTScore {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.score === "number" &&
    typeof value.priority === "string" &&
    typeof value.budget === "number" &&
    typeof value.authority === "number" &&
    typeof value.need === "number" &&
    typeof value.timeline === "number"
  );
}

function isProspectProfile(value: unknown): value is ProspectProfile {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.industry === "string" &&
    typeof value.company_scale === "string" &&
    isStringArray(value.pain_points) &&
    isStringArray(value.needs)
  );
}

function isProspectItem(value: unknown): value is ProspectItem {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.id === "string" &&
    typeof value.company_name === "string" &&
    typeof value.region === "string" &&
    typeof value.industry === "string" &&
    typeof value.role === "string" &&
    typeof value.website === "string" &&
    typeof value.contact_email === "string" &&
    isBANTScore(value.bant) &&
    isProspectProfile(value.profile)
  );
}

function isProspectDataSourceItem(value: unknown): value is ProspectDataSourceItem {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.key === "string" &&
    typeof value.label === "string" &&
    (value.type === "seed" || value.type === "import") &&
    (value.status === "available" || value.status === "unavailable") &&
    typeof value.description === "string"
  );
}

function isProspectReportView(value: unknown): value is ProspectReportView {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.id === "string" &&
    typeof value.company_name === "string" &&
    typeof value.industry === "string" &&
    typeof value.region === "string" &&
    typeof value.role === "string" &&
    typeof value.priority === "string" &&
    typeof value.bant_score === "number" &&
    typeof value.summary_text === "string" &&
    isBANTScore(value.bant) &&
    isProspectProfile(value.profile)
  );
}

function parseApiEnvelope(value: unknown): { code: string; message: string; data: unknown } {
  if (!isRecord(value) || typeof value.code !== "string" || typeof value.message !== "string" || !("data" in value)) {
    throw new Error("Invalid API response envelope");
  }

  return {
    code: value.code,
    message: value.message,
    data: value.data,
  };
}

function parseProspectListResult(value: unknown): ProspectListResult {
  if (!isRecord(value) || !Array.isArray(value.items) || !value.items.every(isProspectItem)) {
    throw new Error("Invalid prospect list payload");
  }

  return {
    items: value.items,
  };
}

function parseProspectItem(value: unknown): ProspectItem {
  if (!isProspectItem(value)) {
    throw new Error("Invalid prospect payload");
  }

  return value;
}

function parseProspectDataSourceListResult(value: unknown): ProspectDataSourceListResult {
  if (!isRecord(value) || !Array.isArray(value.items) || !value.items.every(isProspectDataSourceItem)) {
    throw new Error("Invalid prospect data source payload");
  }

  return {
    items: value.items,
  };
}

function parseProspectReportView(value: unknown): ProspectReportView {
  if (!isProspectReportView(value)) {
    throw new Error("Invalid prospect report payload");
  }

  return value;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

function buildProspectQuery(filters: ProspectFilters = {}): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    if (!value) {
      continue;
    }

    searchParams.set(key, value);
  }

  const queryString = searchParams.toString();
    return queryString ? `?${queryString}` : "";
}

async function requestJson(path: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status, `Request failed: ${response.status}`);
  }

  const payload = parseApiEnvelope(await response.json());
  return payload.data;
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status, `Request failed: ${response.status}`);
  }

  return response.blob();
}

export async function listProspects(filters: ProspectFilters = {}): Promise<ProspectListResult> {
  return parseProspectListResult(await requestJson(`/prospects${buildProspectQuery(filters)}`));
}

export async function listAvailableDataSources(): Promise<ProspectDataSourceListResult> {
  return parseProspectDataSourceListResult(await requestJson("/prospects/sources"));
}

export async function downloadProspectsCsv(filters: ProspectFilters = {}): Promise<Blob> {
  return requestBlob(`/prospects/export${buildProspectQuery(filters)}`);
}

export async function getProspectReportById(id: string): Promise<ProspectReportView | null> {
  try {
    return parseProspectReportView(await requestJson(`/prospects/${encodeURIComponent(id)}/report`));
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export async function getProspectById(id: string): Promise<ProspectItem | null> {
  try {
    return parseProspectItem(await requestJson(`/prospects/${encodeURIComponent(id)}`));
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    throw error;
  }
}
