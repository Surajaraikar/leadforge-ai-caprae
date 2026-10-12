export type ScoreBreakdown = {
  relevance: number;
  proximity: number;
  completeness: number;
  business_signals: number;
  reasons: string[];
};

export type Lead = {
  id: string;
  source_id: string;
  name: string;
  category: string;
  address: string | null;
  city: string | null;
  region: string | null;
  country: string | null;
  latitude: number;
  longitude: number;
  distance_km: number | null;
  website: string | null;
  phone: string | null;
  email: string | null;
  opening_hours: string | null;
  score: number;
  score_breakdown: ScoreBreakdown;
  source_url: string;
  search_keyword: string;
  search_location: string;
  discovered_at: string;
};

export type LeadPage = {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type Stats = {
  total_leads: number;
  qualified_leads: number;
  complete_leads: number;
  average_score: number;
  searches_run: number;
  last_search_at: string | null;
};

export type DiscoveryResponse = {
  search_id: string;
  leads: Lead[];
  raw_count: number;
  duplicate_count: number;
  excluded_count: number;
  source: "OpenStreetMap";
  searched_at: string;
};
