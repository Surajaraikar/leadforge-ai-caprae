"use client";

import { ChevronLeft, ChevronRight, Download, ExternalLink, Globe2, Inbox, Mail, MapPin, Phone, ShieldCheck } from "lucide-react";
import type { Lead, LeadPage } from "@/lib/types";
import { Score } from "@/components/score";

type Props = {
  data: LeadPage | null;
  loading: boolean;
  selected: Set<string>;
  onSelectedChange: (next: Set<string>) => void;
  page: number;
  onPageChange: (page: number) => void;
  exportHref: string;
};

function safeExternalUrl(value: string | null): string | null {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.toString() : null;
  } catch {
    return null;
  }
}

function LeadCard({ lead, checked, onToggle }: { lead: Lead; checked: boolean; onToggle: () => void }) {
  const website = safeExternalUrl(lead.website);
  return (
    <article className="lead-card">
      <div className="card-top"><label className="check-label"><input type="checkbox" checked={checked} onChange={onToggle} /><span className="sr-only">Select {lead.name}</span></label><Score score={lead.score} breakdown={lead.score_breakdown} /></div>
      <div><h3>{lead.name}</h3><span className="category-chip">{lead.category}</span></div>
      <div className="lead-meta"><span><MapPin size={14} />{lead.address || lead.search_location}</span>{lead.phone && <span><Phone size={14} />{lead.phone}</span>}{lead.email && <span><Mail size={14} />{lead.email}</span>}</div>
      <div className="card-actions">{website ? <a href={website} target="_blank" rel="noreferrer"><Globe2 size={15} /> Website</a> : <span className="missing">Website missing</span>}<a href={lead.source_url} target="_blank" rel="noreferrer">Source <ExternalLink size={14} /></a></div>
    </article>
  );
}

export function LeadsTable({ data, loading, selected, onSelectedChange, page, onPageChange, exportHref }: Props) {
  const items = data?.items ?? [];
  const allVisibleSelected = items.length > 0 && items.every((lead) => selected.has(lead.id));
  function toggleAll() {
    const next = new Set(selected);
    if (allVisibleSelected) items.forEach((lead) => next.delete(lead.id));
    else items.forEach((lead) => next.add(lead.id));
    onSelectedChange(next);
  }
  function toggle(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id); else next.add(id);
    onSelectedChange(next);
  }
  return (
    <section className="table-shell" aria-busy={loading}>
      <div className="table-heading"><div><h2>Lead workspace</h2><p>{data ? `${data.total} saved public listings` : "Your discovered leads will appear here"}</p></div><a className={`export-button ${!data?.total ? "disabled" : ""}`} href={data?.total ? exportHref : undefined} aria-disabled={!data?.total}><Download size={16} />{selected.size ? `Export ${selected.size}` : "Export all"}</a></div>
      {loading ? <div className="loading-state"><span className="skeleton wide" /><span className="skeleton" /><span className="skeleton wide" /><span className="skeleton" /></div> : items.length === 0 ? <div className="empty-state"><span><Inbox size={24} /></span><h3>No leads in this view</h3><p>Run a discovery search or adjust the filters above.</p></div> : <>
        <div className="desktop-table"><table><thead><tr><th><label className="check-label"><input type="checkbox" checked={allVisibleSelected} onChange={toggleAll} /><span className="sr-only">Select all visible leads</span></label></th><th>Company</th><th>Contact data</th><th>Location</th><th>Fit score</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{items.map((lead) => { const website = safeExternalUrl(lead.website); return <tr key={lead.id}><td><label className="check-label"><input type="checkbox" checked={selected.has(lead.id)} onChange={() => toggle(lead.id)} /><span className="sr-only">Select {lead.name}</span></label></td><td><div className="company-cell"><strong>{lead.name}</strong><span>{lead.category}</span></div></td><td><div className="contact-cell">{lead.phone ? <span><Phone size={14} />{lead.phone}</span> : <span className="muted">No phone</span>}{lead.email ? <span><Mail size={14} />{lead.email}</span> : <span className="muted">No email</span>}</div></td><td><div className="location-cell"><span>{lead.address || lead.search_location}</span>{lead.distance_km !== null && <small>{lead.distance_km} km from center</small>}</div></td><td><Score score={lead.score} breakdown={lead.score_breakdown} /></td><td><div className="row-actions">{website && <a href={website} target="_blank" rel="noreferrer" aria-label={`Visit ${lead.name} website`}><Globe2 size={16} /></a>}<a href={lead.source_url} target="_blank" rel="noreferrer" aria-label={`View ${lead.name} source`}><ShieldCheck size={16} /></a></div></td></tr>; })}</tbody></table></div>
        <div className="mobile-cards">{items.map((lead) => <LeadCard key={lead.id} lead={lead} checked={selected.has(lead.id)} onToggle={() => toggle(lead.id)} />)}</div>
        <div className="pagination"><span>Page {data?.page ?? 1} of {data?.pages ?? 1}</span><div><button type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)} aria-label="Previous page"><ChevronLeft size={17} /></button><button type="button" disabled={!data || page >= data.pages} onClick={() => onPageChange(page + 1)} aria-label="Next page"><ChevronRight size={17} /></button></div></div>
      </>}
    </section>
  );
}
