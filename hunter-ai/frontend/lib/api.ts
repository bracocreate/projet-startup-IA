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
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
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
