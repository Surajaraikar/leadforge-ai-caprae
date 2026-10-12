"use client";

import { Menu, X, Zap } from "lucide-react";
import { useState } from "react";
import { navItems } from "@/components/icons";

export function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        className="mobile-menu"
        type="button"
        aria-label={open ? "Close navigation" : "Open navigation"}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>
      {open && <button className="nav-backdrop" aria-label="Close navigation" onClick={() => setOpen(false)} />}
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="brand">
          <span className="brand-mark"><Zap size={17} fill="currentColor" /></span>
          <span>LeadForge AI</span>
        </div>
        <nav aria-label="Primary navigation">
          {navItems.map((item) => (
            <button
              key={item.label}
              type="button"
              className={`nav-item ${item.current ? "active" : ""}`}
              aria-current={item.current ? "page" : undefined}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="status-dot" />
          <div><strong>Open data</strong><small>Powered by OpenStreetMap</small></div>
        </div>
      </aside>
    </>
  );
}
