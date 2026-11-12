const BASE = process.env.NEXT_PUBLIC_CLARITY_API_URL || "http://127.0.0.1:8000";

export type Detection = {
  source?: string;
  label: string;
  span?: string | null;
  confidence?: number | null;
  reason?: string;
};

export type Analysis = {
  sentence_id?: string | null;
  text: string;
  detections: Detection[];
  model_predictions?: any[];
  explanation: string;
  readings: string[];
  rewrites: string[];
  mode: string;
  latency_ms: number;
  component_status?: Record<string, string>;
  component_errors?: Record<string, string | null>;
};

export type DocumentResult = {
  sentences: Analysis[];
  sentence_count: number;
  flagged_count: number;
  ambiguity_rate: number;
  type_counts: Record<string, number>;
  latency_ms: number;
  mode: string;
  component_status?: Record<string, string>;
};

export type SavedRecord = {
  id: string;
  kind: "text" | "document";
  createdAt: string;
  input: string;
  result: Analysis | DocumentResult;
};

export const HISTORY_KEY = "clarity-analysis-history-v1";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    },
    cache: "no-store",
  });

  const raw = await response.text();
  let data: any = {};

  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { detail: raw };
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  }

  return data as T;
}

function saveHistory(kind: "text" | "document", input: string, result: Analysis | DocumentResult) {
  if (typeof window === "undefined") return;

  try {
    const old = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    const records: SavedRecord[] = Array.isArray(old) ? old : [];

    const item: SavedRecord = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      kind,
      createdAt: new Date().toISOString(),
      input,
      result,
    };

    localStorage.setItem(HISTORY_KEY, JSON.stringify([item, ...records].slice(0, 100)));
    window.dispatchEvent(new CustomEvent("clarity-history-updated"));
  } catch (error) {
    console.error("Could not save analysis history:", error);
  }
}

export async function analyzeText(text: string): Promise<Analysis> {
  if (!text.trim()) throw new Error("Enter text to analyse.");

  const response = await api<any>("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

  const result = response.result ?? response;

  if (!result || !Array.isArray(result.detections)) {
    throw new Error("Invalid text analysis response.");
  }

  saveHistory("text", text, result);
  return result as Analysis;
}

export async function analyzeDocument(text: string): Promise<DocumentResult> {
  if (!text.trim()) throw new Error("Enter document text.");

  const response = await api<any>("/api/document", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

  const result = response.result ?? response;

  if (!result || !Array.isArray(result.sentences)) {
    throw new Error("Invalid document analysis response.");
  }

  saveHistory("document", text, result);
  return result as DocumentResult;
}

export function getSavedHistory(): SavedRecord[] {
  if (typeof window === "undefined") return [];

  try {
    const data = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export function clearSavedHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(HISTORY_KEY);
  window.dispatchEvent(new CustomEvent("clarity-history-updated"));
}

export const getHealth = () => api<any>("/health");
export const getStatus = () => api<any>("/api/status");
export const getDemoEvaluation = () => api<any>("/api/evaluation/demo");

export async function uploadEvaluation(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api<any>("/api/evaluate", { method: "POST", body: form });
}

export const API_BASE = BASE;
