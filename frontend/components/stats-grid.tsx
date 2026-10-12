import { CheckCircle2, Gauge, ListChecks, Search } from "lucide-react";
import type { Stats } from "@/lib/types";

export function StatsGrid({ stats }: { stats: Stats | null }) {
  const items = [
    { label: "Saved leads", value: stats?.total_leads ?? 0, icon: ListChecks, tone: "violet" },
    { label: "Qualified (65+)", value: stats?.qualified_leads ?? 0, icon: Gauge, tone: "mint" },
    { label: "Complete profiles", value: stats?.complete_leads ?? 0, icon: CheckCircle2, tone: "blue" },
    { label: "Searches run", value: stats?.searches_run ?? 0, icon: Search, tone: "amber" },
  ];
  return (
    <section className="stats-grid" aria-label="Lead statistics">
      {items.map((item) => <article className="stat-card" key={item.label}><span className={`stat-icon ${item.tone}`}><item.icon size={18} /></span><div><strong>{item.value}</strong><span>{item.label}</span></div></article>)}
    </section>
  );
}
