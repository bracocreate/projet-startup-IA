export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError("Le serveur HUNTER AI est injoignable. Vérifiez que le backend est démarré.", 0);
  }
  if (!res.ok) {
    // Erreur serveur sans message JSON : typiquement le relais Next.js quand le backend est arrêté.
    let detail =
      res.status >= 500
        ? `Le serveur HUNTER AI ne répond pas correctement (erreur ${res.status}). Vérifiez qu'il est démarré : make ps, puis make logs.`
        : `Erreur ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = "Données invalides : vérifiez les champs saisis.";
    } catch {
      /* réponse non JSON */
    }
    throw new ApiError(detail, res.status);
  }
  // 204 « Aucun contenu » (ex. suppression) : rien à lire.
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// --- Types alignés sur les schémas Pydantic du backend ---

export type SourceSummary = {
  id: string;
  slug: string;
  name: string;
  family: string;
  country: string | null;
  access_method: string;
  status: string;
  is_demo: boolean;
};

export type RankingSection = {
  key: "best_deals" | "emerging_trends" | "new_markets";
  title: string;
  status: "empty" | "not_implemented";
  message: string;
  items: Record<string, unknown>[];
};

export type DashboardSummary = {
  generated_at: string;
  data_mode: "empty" | "demo" | "live";
  last_refresh_at: string | null;
  is_stale: boolean;
  stale_after_hours: number;
  sources_total: number;
  offers_total: number;
  sources_by_status: Record<string, number>;
  sources_in_error: SourceSummary[];
  pending_discoveries: number;
  rankings: RankingSection[];
};

export type ComponentStatus = {
  name: string;
  status: "ok" | "warning" | "error" | "not_configured" | "not_implemented";
  detail: string;
};

export type SystemStatus = {
  version: string;
  environment: string;
  timezone: string;
  time_utc: string;
  db_revision: string | null;
  db_revision_expected: string | null;
  components: ComponentStatus[];
};

export type UserSettings = {
  id: string;
  app_name: string;
  language: string;
  currency: string;
  timezone: string;
  max_item_budget_eur: string | null;
  max_lot_budget_eur: string | null;
  daily_collection_start: string;
  daily_collection_duration_min: number;
  markets: string[];
  priority_brands: string[];
  buy_unit: boolean;
  buy_lots: boolean;
  telegram_enabled: boolean;
  auto_purchase_allowed: boolean;
  updated_at: string;
};

export type SourceRef = { slug: string; name: string; is_demo: boolean };

export type Offer = {
  id: string;
  title: string;
  url: string;
  source: SourceRef;
  merchant: { name: string; country: string | null } | null;
  product_id: string;
  brand: string | null;
  gtin: string | null;
  mpn: string | null;
  size: string | null;
  color: string | null;
  condition: string;
  country: string | null;
  price_amount: string;
  currency: string;
  /** null = conversion EUR impossible (aucun taux configuré). */
  price_eur: string | null;
  fx_rate_to_eur: string | null;
  /** null = frais inconnus ; "0.00" = livraison gratuite. */
  shipping_amount: string | null;
  price_with_shipping_eur: string | null;
  availability: "in_stock" | "out_of_stock" | "unknown";
  first_seen_at: string;
  last_verified_at: string;
  is_stale: boolean;
  access_method: string;
  match_method: "gtin" | "brand_mpn" | "new_product";
  match_confidence: string;
  is_demo: boolean;
};

export type OfferPage = { items: Offer[]; total: number; limit: number; offset: number };

export type ConnectorRun = {
  id: string;
  source: SourceRef;
  status: "running" | "success" | "partial" | "error";
  actor: string;
  started_at: string;
  finished_at: string | null;
  offers_received: number;
  offers_created: number;
  offers_updated: number;
  observations_created: number;
  api_calls: number;
  errors: string[];
  is_demo: boolean;
};

export type ConnectorInfo = {
  slug: string;
  name: string;
  description: string;
  configured: boolean;
  /** null = jamais testé (aucune source enregistrée). */
  status: string | null;
  daily_call_budget: number | null;
  calls_used_today: number;
};

export type SourceTestResult = {
  ok: boolean;
  status: string;
  detail: string;
  sample_count: number;
  api_calls: number;
};

export type AmountRange = { low: string; high: string };

export type ProfitResult = {
  lines: { key: string; label: string; status: "known" | "range" | "unknown"; amount: AmountRange | null; basis: string }[];
  landed_cost: AmountRange | null;
  landed_cost_per_unit: AmountRange | null;
  sellable_units: string;
  cost_per_sellable_unit: AmountRange | null;
  scenarios: {
    key: "pessimistic" | "central" | "optimistic";
    resale_price: string;
    cost_used: string;
    revenue: string;
    selling_costs: string;
    profit: string;
    roi_pct: string | null;
    margin_pct: string | null;
  }[];
  break_even_price: string | null;
  max_unit_price_for_target: string | null;
  missing: string[];
  warnings: string[];
  rules_version: string;
};

export type ResaleRecord = {
  id: string;
  title: string;
  brand: string | null;
  category: string | null;
  size: string | null;
  condition: string | null;
  channel: "vinted" | "ebay" | "leboncoin" | "other";
  sale_price: string;
  platform_fees: string | null;
  shipping_paid: string | null;
  purchase_cost: string | null;
  real_profit: string | null;
  sold_on: string;
  notes: string | null;
  created_at: string;
};

export type ResaleReference = {
  count: number;
  enough: boolean;
  minimum: string | null;
  low: string | null;
  median: string | null;
  high: string | null;
  maximum: string | null;
};
