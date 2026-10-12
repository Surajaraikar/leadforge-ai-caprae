"use client";

import { FormEvent, useState } from "react";
import { Building2, LoaderCircle, MapPin, Search, Sparkles } from "lucide-react";

type Props = {
  loading: boolean;
  onSearch: (keyword: string, location: string) => Promise<void>;
};

export function SearchPanel({ loading, onSearch }: Props) {
  const [keyword, setKeyword] = useState("coffee");
  const [location, setLocation] = useState("Austin, Texas");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSearch(keyword, location);
  }

  return (
    <section className="search-panel" aria-labelledby="search-title">
      <div className="search-copy">
        <span className="eyebrow"><Sparkles size={14} /> Live business discovery</span>
        <h1 id="search-title">Build a sharper prospect list.</h1>
        <p>Find real businesses, see exactly why they rank, and export a clean shortlist.</p>
      </div>
      <form className="search-form" onSubmit={submit}>
        <label>
          <span>Industry or keyword</span>
          <span className="input-wrap"><Building2 size={18} /><input required minLength={2} maxLength={80} value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="e.g. coffee" /></span>
        </label>
        <label>
          <span>Location</span>
          <span className="input-wrap"><MapPin size={18} /><input required minLength={2} maxLength={120} value={location} onChange={(event) => setLocation(event.target.value)} placeholder="e.g. Austin, Texas" /></span>
        </label>
        <button className="primary-button" disabled={loading} type="submit">
          {loading ? <LoaderCircle className="spin" size={18} /> : <Search size={18} />}
          {loading ? "Searching public data…" : "Find leads"}
        </button>
      </form>
    </section>
  );
}
