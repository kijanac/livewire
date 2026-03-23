import type {
  Bill,
  BillBriefing,
  BillListResponse,
  City,
  StatsResponse,
  IngestResponse,
  BillFilters,
  Collection,
  CollectionItem,
  RadarResponse,
} from "./types";

const BASE_URL = "";

interface FetchBillsParams extends Partial<BillFilters> {
  page?: number;
  per_page?: number;
}

export async function fetchBills(
  params: FetchBillsParams = {}
): Promise<BillListResponse> {
  const searchParams = new URLSearchParams();

  if (params.city) searchParams.set("city", params.city);
  if (params.status) searchParams.set("status", params.status);
  if (params.type_name) searchParams.set("type_name", params.type_name);
  if (params.topic) searchParams.set("topic", params.topic);
  if (params.urgency) searchParams.set("urgency", params.urgency);
  if (params.search) searchParams.set("search", params.search);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));

  const query = searchParams.toString();
  const url = `${BASE_URL}/api/bills${query ? `?${query}` : ""}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch bills: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchCities(): Promise<City[]> {
  const response = await fetch(`${BASE_URL}/api/cities`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cities: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const response = await fetch(`${BASE_URL}/api/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchTopics(): Promise<string[]> {
  const response = await fetch(`${BASE_URL}/api/topics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch topics: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchUpcoming(limit: number = 20): Promise<Bill[]> {
  const response = await fetch(
    `${BASE_URL}/api/bills/upcoming?limit=${limit}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch upcoming bills: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchRadar(topic?: string): Promise<RadarResponse> {
  const params = new URLSearchParams();
  if (topic) params.set("topic", topic);
  const query = params.toString();
  const url = `${BASE_URL}/api/bills/radar${query ? `?${query}` : ""}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch radar: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchBriefing(billId: number): Promise<BillBriefing> {
  const response = await fetch(
    `${BASE_URL}/api/bills/${billId}/briefing`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch briefing: ${response.statusText}`);
  }
  return response.json();
}

export async function triggerIngest(city?: string): Promise<IngestResponse> {
  const response = await fetch(`${BASE_URL}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(city ? { city } : {}),
  });
  if (!response.ok) {
    throw new Error(`Failed to trigger ingest: ${response.statusText}`);
  }
  return response.json();
}

export async function createCollection(data: {
  name: string;
  description?: string;
}): Promise<Collection> {
  const response = await fetch(`${BASE_URL}/api/collections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create collection: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchCollection(slug: string): Promise<Collection> {
  const response = await fetch(`${BASE_URL}/api/collections/${slug}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch collection: ${response.statusText}`);
  }
  return response.json();
}

export async function updateCollection(
  slug: string,
  data: { name?: string; description?: string }
): Promise<Collection> {
  const response = await fetch(`${BASE_URL}/api/collections/${slug}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update collection: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteCollection(slug: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/api/collections/${slug}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete collection: ${response.statusText}`);
  }
}

export async function addBillToCollection(
  slug: string,
  billId: number,
  note?: string
): Promise<CollectionItem> {
  const response = await fetch(`${BASE_URL}/api/collections/${slug}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bill_id: billId, note }),
  });
  if (!response.ok) {
    throw new Error(
      `Failed to add bill to collection: ${response.statusText}`
    );
  }
  return response.json();
}

export async function updateCollectionItem(
  slug: string,
  itemId: number,
  note: string
): Promise<CollectionItem> {
  const response = await fetch(
    `${BASE_URL}/api/collections/${slug}/items/${itemId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    }
  );
  if (!response.ok) {
    throw new Error(
      `Failed to update collection item: ${response.statusText}`
    );
  }
  return response.json();
}

export async function removeBillFromCollection(
  slug: string,
  itemId: number
): Promise<void> {
  const response = await fetch(
    `${BASE_URL}/api/collections/${slug}/items/${itemId}`,
    {
      method: "DELETE",
    }
  );
  if (!response.ok) {
    throw new Error(
      `Failed to remove bill from collection: ${response.statusText}`
    );
  }
}
