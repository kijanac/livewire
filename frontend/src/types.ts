export interface Bill {
  id: number;
  source_id: string;
  source: string;
  city: string;
  city_name: string;
  state: string;
  file_number: string | null;
  title: string;
  type_name: string | null;
  status: string | null;
  body_name: string | null;
  intro_date: string | null;
  agenda_date: string | null;
  passed_date: string | null;
  enactment_number: string | null;
  enactment_date: string | null;
  url: string | null;
  topics: string[];
  urgency: "urgent" | "soon" | "normal";
  summary: string | null;
  updated_at: string | null;
  created_at: string;
}

export interface BillListResponse {
  bills: Bill[];
  total: number;
  page: number;
  per_page: number;
}

export interface City {
  id: string;
  name: string;
  state: string;
}

export interface StatusCount {
  status: string;
  count: number;
}

export interface CityCount {
  city: string;
  city_name: string;
  count: number;
}

export interface TopicCount {
  topic: string;
  count: number;
}

export interface CityActivity {
  city: string;
  city_name: string;
  upcoming_count: number;
}

export interface StatsResponse {
  moving_this_week: number;
  hot_topics: TopicCount[];
  most_active_city: CityActivity | null;
  new_bills_7d: number;
  by_status: StatusCount[];
  by_city: CityCount[];
}

export interface IngestResponse {
  message: string;
  bills_added: number;
  bills_updated: number;
}

export interface BillFilters {
  city: string;
  status: string;
  type_name: string;
  topic: string;
  urgency: string;
  search: string;
}

export interface CollectionItem {
  id: number;
  bill_id: number;
  bill: Bill;
  note: string | null;
  added_at: string | null;
}

export interface Collection {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  items: CollectionItem[];
  created_at: string | null;
  updated_at: string | null;
}

export interface CollectionCreate {
  name: string;
  description?: string;
}

export interface CollectionStub {
  slug: string;
  name: string;
}

export interface NewsArticle {
  title: string;
  url: string;
  source: string;
  date: string | null;
}

export interface SimilarBill {
  id: number;
  city_name: string;
  state: string;
  title: string;
  status: string | null;
  file_number: string | null;
}

export interface RadarBill {
  id: number;
  city: string;
  city_name: string;
  state: string;
  title: string;
  file_number: string | null;
  status: string | null;
  type_name: string | null;
  topics: string[];
  urgency: "urgent" | "soon" | "normal";
  intro_date: string | null;
  url: string | null;
}

export interface RadarCluster {
  label: string;
  top_terms: string[];
  cities: string[];
  city_count: number;
  bill_count: number;
  bills: RadarBill[];
}

export interface RadarResponse {
  clusters: RadarCluster[];
  total_clusters: number;
  total_bills: number;
}

export interface BillBriefing {
  bill: Bill;
  summary: string | null;
  impact: string | null;
  organizing: string | null;
  reception: string | null;
  news: NewsArticle[];
  similar_bills: SimilarBill[];
  timeline: { event: string; date: string }[];
  collection_notes: { collection_name: string; note: string }[];
}
