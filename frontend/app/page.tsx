"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Filters } from "@/components/filters";
import { LeadsTable } from "@/components/leads-table";
import { SearchPanel } from "@/components/search-panel";
import { Sidebar } from "@/components/sidebar";
import { StatsGrid } from "@/components/stats-grid";
import { discoverLeads, exportUrl, getLeads, getStats, type LeadQuery } from "@/lib/api";
import type { LeadPage, Stats } from "@/lib/types";

const initialFilters: LeadQuery = { page: 1, minScore: 0, completeOnly: false, query: "", sort: "score_desc" };

export default function Dashboard() {
  const [filters, setFilters] = useState(initialFilters);
  const [data, setData] = useState<LeadPage | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const loadDashboard = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const [leads, currentStats] = await Promise.all([getLeads(filters, signal), getStats(signal)]);
      setData(leads);
      setStats(currentStats);
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return;
      setError(caught instanceof Error ? caught.message : "Could not load the dashboard.");
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => void loadDashboard(controller.signal), filters.query ? 250 : 0);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [loadDashboard, filters.query]);

  async function handleDiscovery(keyword: string, location: string) {
    setDiscovering(true);
    setError(null);
    setNotice(null);
    try {
      const result = await discoverLeads(keyword, location);
      setFilters(initialFilters);
      setSelected(new Set());
      const qualityNotes = [
        result.duplicate_count
          ? `${result.duplicate_count} duplicate${result.duplicate_count === 1 ? "" : "s"}`
          : null,
        result.excluded_count
          ? `${result.excluded_count} non-business match${result.excluded_count === 1 ? "" : "es"}`
          : null,
      ].filter(Boolean);
      setNotice(
        `Added ${result.leads.length} unique leads from OpenStreetMap${
          qualityNotes.length ? `; removed ${qualityNotes.join(" and ")}` : ""
        }.`
      );
      await loadDashboard();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Discovery failed. Please try again.");
    } finally {
      setDiscovering(false);
    }
  }

  const downloadUrl = useMemo(() => exportUrl(selected), [selected]);
  return (
    <div className="app-shell">
      <Sidebar />
      <main>
        <header className="topbar"><div><span className="breadcrumb">Workspace / <strong>Lead discovery</strong></span></div><a className="source-link" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a></header>
        <div className="content">
          <SearchPanel loading={discovering} onSearch={handleDiscovery} />
          {error && <div className="message error" role="alert"><AlertCircle size={18} /><span>{error}</span><button type="button" onClick={() => void loadDashboard()}>Retry</button></div>}
          {notice && <div className="message success" role="status"><CheckCircle2 size={18} /><span>{notice}</span><button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}>×</button></div>}
          <StatsGrid stats={stats} />
          <Filters filters={filters} onChange={setFilters} />
          <LeadsTable data={data} loading={loading} selected={selected} onSelectedChange={setSelected} page={filters.page} onPageChange={(page) => setFilters({ ...filters, page })} exportHref={downloadUrl} />
          <footer><span>LeadForge AI demo • Data is saved locally</span><span>No fabricated enrichment</span></footer>
        </div>
      </main>
    </div>
  );
}
