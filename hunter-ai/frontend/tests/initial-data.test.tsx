import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DashboardView } from "@/features/dashboard/DashboardView";
import { HealthView } from "@/features/health/HealthView";
import { SettingsView } from "@/features/settings/SettingsView";
import type { DashboardSummary, SystemStatus, UserSettings } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

const summary: DashboardSummary = {
  generated_at: "2026-11-24T09:00:00Z",
  data_mode: "empty",
  last_refresh_at: null,
  is_stale: true,
  stale_after_hours: 24,
  sources_total: 0,
  offers_total: 0,
  sources_by_status: {},
  sources_in_error: [],
  pending_discoveries: 0,
  rankings: [
    { key: "best_deals", title: "Meilleures affaires immédiates", status: "not_implemented", message: "Aucune offre.", items: [] },
  ],
};

const status: SystemStatus = {
  version: "0.1.0", environment: "development", timezone: "Europe/Paris", time_utc: "2026-11-24T09:00:00Z",
  db_revision: "0001", db_revision_expected: "0001",
  components: [{ name: "Base de données", status: "ok", detail: "PostgreSQL joignable" }],
};

const settings: UserSettings = {
  id: "1", app_name: "HUNTER AI", language: "fr", currency: "EUR", timezone: "Europe/Paris",
  max_item_budget_eur: "100.00", max_lot_budget_eur: null, daily_collection_start: "06:00:00",
  daily_collection_duration_min: 120, markets: ["FR"], priority_brands: ["Nike"],
  buy_unit: true, buy_lots: true, telegram_enabled: false, auto_purchase_allowed: false,
  updated_at: "2026-11-24T09:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("Données rendues par le serveur", () => {
  it("le tableau de bord s'affiche immédiatement, sans chargement ni second appel", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<DashboardView initialData={summary} />);
    expect(screen.getByText(/Aucune donnée collectée/)).toBeInTheDocument();
    expect(screen.queryByText(/Chargement/)).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("la santé du système s'affiche immédiatement", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<HealthView initialData={status} />);
    expect(screen.getByText("Base de données")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("le formulaire des paramètres est prérempli immédiatement", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<SettingsView initialData={settings} />);
    expect(screen.getByLabelText(/Budget max. par article/)).toHaveValue("100.00");
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("fetchInitial", () => {
  it("appelle le backend configuré et renvoie les données", async () => {
    vi.stubEnv("BACKEND_URL", "http://backend:8000");
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(summary)));
    vi.stubGlobal("fetch", fetch);
    await expect(fetchInitial<DashboardSummary>("/dashboard/summary")).resolves.toEqual(summary);
    expect(fetch.mock.calls[0][0]).toBe("http://backend:8000/api/v1/dashboard/summary");
  });

  it("renvoie null si le backend est injoignable (le navigateur prendra le relais)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    await expect(fetchInitial("/settings")).resolves.toBeNull();
  });

  it("renvoie null si le backend répond une erreur", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 500 })));
    await expect(fetchInitial("/settings")).resolves.toBeNull();
  });
});
