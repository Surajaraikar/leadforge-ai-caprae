"use client";

import { Search, SlidersHorizontal } from "lucide-react";
import type { LeadQuery } from "@/lib/api";

export function Filters({ filters, onChange }: { filters: LeadQuery; onChange: (value: LeadQuery) => void }) {
  return (
    <section className="filters" aria-label="Lead filters">
      <label className="filter-search"><Search size={16} /><span className="sr-only">Filter saved leads</span><input value={filters.query} onChange={(event) => onChange({ ...filters, page: 1, query: event.target.value })} placeholder="Filter by company or city" /></label>
      <div className="filter-controls"><span className="filter-label"><SlidersHorizontal size={15} /> Filters</span><label>Minimum score<select value={filters.minScore} onChange={(event) => onChange({ ...filters, page: 1, minScore: Number(event.target.value) })}><option value={0}>Any score</option><option value={55}>55+</option><option value={65}>65+</option><option value={75}>75+</option></select></label><label>Sort<select value={filters.sort} onChange={(event) => onChange({ ...filters, page: 1, sort: event.target.value })}><option value="score_desc">Best fit</option><option value="newest">Newest</option><option value="name">Company A–Z</option><option value="score_asc">Lowest score</option></select></label><label className="toggle"><input type="checkbox" checked={filters.completeOnly} onChange={(event) => onChange({ ...filters, page: 1, completeOnly: event.target.checked })} /><span />Complete data only</label></div>
    </section>
  );
}
