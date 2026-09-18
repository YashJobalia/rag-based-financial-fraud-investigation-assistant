let sessionToken = "";
export function setSessionToken(value: string) {
  sessionToken = value;
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `Request failed (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}
export type Session = {
  actor: string;
  role: string;
  live_available: boolean;
  retrieval_modes: string[];
};
export type Case = {
  id: string;
  title: string;
  account_id: string;
  cutoff_at: string;
  opened_at: string;
  status: string;
  display_name: string;
};
export type Evidence = {
  id: string;
  title: string;
  description?: string;
  passage?: string;
  occurred_at?: string;
  recorded_at?: string;
  source?: string;
  source_uri?: string;
  evidence_type?: string;
  kind: string;
  version: string;
  section?: string;
  published_at?: string;
  content_hash?: string;
  source_ids?: string[];
  parameters?: Record<string, unknown>;
  score?: number;
};
export type Detail = {
  case: Case;
  timeline: Evidence[];
  evidence: Evidence[];
  totals: { currency: string; total_minor: number; count: number }[];
  baseline: { max_minor: number; count: number }[];
  alerts: {
    id: string;
    description: string;
    rule_id: string;
    rule_version: string;
  }[];
};
export type Retrieval = {
  results: Evidence[];
  duration_ms: number;
  mode: string;
  run_id: string;
  corpus_hash: string;
  abstained: boolean;
  explanation: string;
};
export type Brief = {
  id: string;
  mode: string;
  created_at: string;
  model: string | null;
  duration_ms: number;
  validation: string;
  retrieval: Retrieval;
  usage: {
    input_tokens: number;
    output_tokens: number;
    estimated_cost_usd: number | null;
  };
  content: {
    sections: {
      heading: string;
      claims: { kind: string; text: string; evidence_ids: string[] }[];
    }[];
    conclusion: string;
  };
};
