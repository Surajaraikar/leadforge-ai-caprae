import type { DiscoveryResponse, LeadPage, Stats } from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const LEADS_PER_PAGE = 10;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    const headers = new Headers(init?.headers);
    if (init?.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    });
  } catch {
    throw new Error("Could not reach the API. Confirm that the FastAPI server is running.");
  }
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
  }
  return (await response.json()) as T;
}

export function discoverLeads(keyword: string, location: string): Promise<DiscoveryResponse> {
  return request("/api/leads/discover", {
    method: "POST",
    body: JSON.stringify({ keyword, location, limit: 40 }),
  });
}

export type LeadQuery = {
  page: number;
  minScore: number;
  completeOnly: boolean;
  query: string;
  sort: string;
};

export function getLeads(filters: LeadQuery, signal?: AbortSignal): Promise<LeadPage> {
  const params = new URLSearchParams({
    page: String(filters.page),
    page_size: String(LEADS_PER_PAGE),
    min_score: String(filters.minScore),
    complete_only: String(filters.completeOnly),
    sort: filters.sort,
  });
  if (filters.query.trim()) params.set("query", filters.query.trim());
  return request(`/api/leads?${params}`, { signal });
}

export function getStats(signal?: AbortSignal): Promise<Stats> {
  return request("/api/stats", { signal });
}

export function exportUrl(selected: Set<string>): string {
  const params = new URLSearchParams();
  if (selected.size) params.set("ids", Array.from(selected).join(","));
  return `${API_URL}/api/leads/export${params.size ? `?${params}` : ""}`;
}
