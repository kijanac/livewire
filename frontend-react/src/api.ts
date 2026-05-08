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
  CoalitionsResponse,
  StoryListResponse,
  StoryFilters,
} from "./types";

const BASE_URL = "";

export class ApiError extends Error {
  readonly status: number;
  readonly url: string;
  constructor(message: string, status: number, url: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.url = url;
  }
}

async function failFromResponse(
  response: Response,
  url: string,
  fallback: string
): Promise<never> {
  let detail: string | null = null;
  try {
    const body = await response.json();
    if (body && typeof body === "object" && typeof body.detail === "string") {
      detail = body.detail;
    }
  } catch {
    // body wasn't JSON or already consumed
  }
  const message = detail
    ? `${fallback}: ${detail}`
    : `${fallback}: ${response.statusText || `HTTP ${response.status}`}`;
  throw new ApiError(message, response.status, url);
}

let citiesPromise: Promise<City[]> | null = null;
let topicsPromise: Promise<string[]> | null = null;

interface FetchBillsParams {
  city?: string;
  status?: string;
  type_name?: string;
  topic?: string;
  urgency?: string;
  search?: string;
  jurisdiction_level?: string;
  page?: number;
  per_page?: number;
}

export async function fetchBills(
  params: FetchBillsParams = {},
  signal?: AbortSignal
): Promise<BillListResponse> {
  const searchParams = new URLSearchParams();

  if (params.city) searchParams.set("city", params.city);
  if (params.status) searchParams.set("status", params.status);
  if (params.type_name) searchParams.set("type_name", params.type_name);
  if (params.topic) searchParams.set("topic", params.topic);
  if (params.urgency) searchParams.set("urgency", params.urgency);
  if (params.search) searchParams.set("search", params.search);
  if (params.jurisdiction_level) searchParams.set("jurisdiction_level", params.jurisdiction_level);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));

  const query = searchParams.toString();
  const url = `${BASE_URL}/api/bills${query ? `?${query}` : ""}`;

  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch bills");
  }
  return response.json();
}

export async function fetchCities(signal?: AbortSignal): Promise<City[]> {
  if (citiesPromise) return citiesPromise;
  const url = `${BASE_URL}/api/cities`;
  citiesPromise = (async () => {
    const response = await fetch(url, { signal });
    if (!response.ok) {
      await failFromResponse(response, url, "Failed to fetch cities");
    }
    return response.json() as Promise<City[]>;
  })().catch((err) => {
    citiesPromise = null;
    throw err;
  });
  return citiesPromise;
}

export async function fetchStats(
  signal?: AbortSignal
): Promise<StatsResponse> {
  const url = `${BASE_URL}/api/stats`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch stats");
  }
  return response.json();
}

export async function fetchTopics(signal?: AbortSignal): Promise<string[]> {
  if (topicsPromise) return topicsPromise;
  const url = `${BASE_URL}/api/topics`;
  topicsPromise = (async () => {
    const response = await fetch(url, { signal });
    if (!response.ok) {
      await failFromResponse(response, url, "Failed to fetch topics");
    }
    return response.json() as Promise<string[]>;
  })().catch((err) => {
    topicsPromise = null;
    throw err;
  });
  return topicsPromise;
}

export async function fetchUpcoming(
  limit: number = 20,
  signal?: AbortSignal
): Promise<Bill[]> {
  const url = `${BASE_URL}/api/bills/upcoming?limit=${limit}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch upcoming bills");
  }
  return response.json();
}

export async function fetchRadar(
  topic?: string,
  signal?: AbortSignal
): Promise<RadarResponse> {
  const params = new URLSearchParams();
  if (topic) params.set("topic", topic);
  const query = params.toString();
  const url = `${BASE_URL}/api/bills/radar${query ? `?${query}` : ""}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch radar");
  }
  return response.json();
}

export async function fetchCoalitions(
  signal?: AbortSignal
): Promise<CoalitionsResponse> {
  const url = `${BASE_URL}/api/coalitions`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch coalitions");
  }
  return response.json();
}

export async function fetchBriefing(
  billId: number,
  signal?: AbortSignal
): Promise<BillBriefing> {
  const url = `${BASE_URL}/api/bills/${billId}/briefing`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch briefing");
  }
  return response.json();
}

export async function triggerIngest(
  city?: string,
  signal?: AbortSignal
): Promise<IngestResponse> {
  const url = `${BASE_URL}/api/ingest`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(city ? { city } : {}),
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to trigger ingest");
  }
  return response.json();
}

export async function createCollection(
  data: { name: string; description?: string },
  signal?: AbortSignal
): Promise<Collection> {
  const url = `${BASE_URL}/api/collections`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to create collection");
  }
  return response.json();
}

export async function fetchCollection(
  slug: string,
  signal?: AbortSignal
): Promise<Collection> {
  const url = `${BASE_URL}/api/collections/${slug}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch collection");
  }
  return response.json();
}

export async function updateCollection(
  slug: string,
  data: { name?: string; description?: string },
  signal?: AbortSignal
): Promise<Collection> {
  const url = `${BASE_URL}/api/collections/${slug}`;
  const response = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to update collection");
  }
  return response.json();
}

export async function deleteCollection(
  slug: string,
  signal?: AbortSignal
): Promise<void> {
  const url = `${BASE_URL}/api/collections/${slug}`;
  const response = await fetch(url, {
    method: "DELETE",
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to delete collection");
  }
}

export async function addBillToCollection(
  slug: string,
  billId: number,
  note?: string,
  signal?: AbortSignal
): Promise<CollectionItem> {
  const url = `${BASE_URL}/api/collections/${slug}/items`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bill_id: billId, note }),
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to add bill to collection");
  }
  return response.json();
}

export async function updateCollectionItem(
  slug: string,
  itemId: number,
  note: string,
  signal?: AbortSignal
): Promise<CollectionItem> {
  const url = `${BASE_URL}/api/collections/${slug}/items/${itemId}`;
  const response = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to update collection item");
  }
  return response.json();
}

interface FetchStoriesParams extends Partial<StoryFilters> {
  page?: number;
  per_page?: number;
}

export async function fetchStories(
  params: FetchStoriesParams = {},
  signal?: AbortSignal
): Promise<StoryListResponse> {
  const searchParams = new URLSearchParams();

  if (params.city) searchParams.set("city", params.city);
  if (params.category) searchParams.set("category", params.category);
  if (params.topic) searchParams.set("topic", params.topic);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));

  const query = searchParams.toString();
  const url = `${BASE_URL}/api/stories${query ? `?${query}` : ""}`;

  const response = await fetch(url, { signal });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to fetch stories");
  }
  return response.json();
}

export async function removeBillFromCollection(
  slug: string,
  itemId: number,
  signal?: AbortSignal
): Promise<void> {
  const url = `${BASE_URL}/api/collections/${slug}/items/${itemId}`;
  const response = await fetch(url, {
    method: "DELETE",
    signal,
  });
  if (!response.ok) {
    await failFromResponse(response, url, "Failed to remove bill from collection");
  }
}
