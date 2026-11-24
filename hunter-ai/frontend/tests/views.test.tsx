import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DashboardView } from "@/features/dashboard/DashboardView";
import { HealthView } from "@/features/health/HealthView";
import { SettingsView } from "@/features/settings/SettingsView";
import type { DashboardSummary, UserSettings } from "@/lib/api";
import { NAV_ITEMS } from "@/lib/nav";

const summary = (over: Partial<DashboardSummary> = {}): DashboardSummary => ({
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
    { key: "emerging_trends", title: "Tendances et opportunités émergentes", status: "not_implemented", message: "x", items: [] },
    { key: "new_markets", title: "Nouveaux marchés à explorer", status: "not_implemented", message: "y", items: [] },
  ],
  ...over,
});

function mockFetch(...responses: Array<{ status?: number; body: unknown } | Error>) {
  const fn = vi.fn();
  for (const r of responses) {
    if (r instanceof Error) fn.mockRejectedValueOnce(r);
    else fn.mockResolvedValueOnce(new Response(JSON.stringify(r.body), { status: r.status ?? 200 }));
  }
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("Tableau de bord", () => {
  it("affiche un état vide explicite et les trois classements", async () => {
    mockFetch({ body: summary() });
    render(<DashboardView />);
    expect(await screen.findByText(/Aucune donnée collectée/)).toBeInTheDocument();
    expect(screen.getByText("Meilleures affaires immédiates")).toBeInTheDocument();
    expect(screen.getByText("Tendances et opportunités émergentes")).toBeInTheDocument();
    expect(screen.getByText("Nouveaux marchés à explorer")).toBeInTheDocument();
    expect(screen.getByText("jamais")).toBeInTheDocument();
  });

  it("identifie visuellement les données DEMO", async () => {
    mockFetch({ body: summary({ data_mode: "demo", sources_total: 1 }) });
    render(<DashboardView />);
    expect(await screen.findByText("DEMO")).toBeInTheDocument();
  });

  it("signale les données périmées et les sources en erreur", async () => {
    mockFetch({
      body: summary({
        data_mode: "live",
        last_refresh_at: "2026-11-20T05:00:00Z",
        sources_total: 1,
        sources_in_error: [
          { id: "1", slug: "x", name: "Source X", family: "api", country: null, access_method: "official_api", status: "error", is_demo: false },
        ],
      }),
    });
    render(<DashboardView />);
    expect(await screen.findByText(/Données périmées/)).toBeInTheDocument();
    expect(screen.getByText(/Source X — en erreur/)).toBeInTheDocument();
  });

  it("affiche une erreur API et permet de réessayer", async () => {
    const fetch = mockFetch(new TypeError("network"), { body: summary() });
    render(<DashboardView />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/injoignable/);
    fireEvent.click(screen.getByText("Réessayer"));
    expect(await screen.findByText(/Aucune donnée collectée/)).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});

describe("Erreurs serveur", () => {
  it("explique quoi faire quand le relais renvoie une erreur 500 sans détail (backend arrêté)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(new Response("Internal Server Error", { status: 500 })));
    render(<DashboardView />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/ne répond pas correctement.*make ps/);
  });
});

describe("Santé du système", () => {
  it("liste les composants avec leur état", async () => {
    mockFetch({
      body: {
        version: "0.1.0", environment: "development", timezone: "Europe/Paris", time_utc: "2026-11-24T09:00:00Z",
        db_revision: "0001", db_revision_expected: "0001",
        components: [
          { name: "Base de données", status: "ok", detail: "PostgreSQL joignable" },
          { name: "Planificateur", status: "not_implemented", detail: "Phase 8" },
        ],
      },
    });
    render(<HealthView />);
    expect(await screen.findByText("Base de données")).toBeInTheDocument();
    expect(screen.getByText("OK")).toBeInTheDocument();
    expect(screen.getByText("Pas encore disponible")).toBeInTheDocument();
  });
});

describe("Paramètres", () => {
  const s: UserSettings = {
    id: "1", app_name: "HUNTER AI", language: "fr", currency: "EUR", timezone: "Europe/Paris",
    max_item_budget_eur: "100.00", max_lot_budget_eur: null, daily_collection_start: "06:00:00",
    daily_collection_duration_min: 120, markets: ["FR"], priority_brands: ["Nike", "Adidas"],
    buy_unit: true, buy_lots: true, telegram_enabled: false, auto_purchase_allowed: false,
    updated_at: "2026-11-24T09:00:00Z",
  };

  it("charge, modifie et enregistre via PATCH", async () => {
    const fetch = mockFetch({ body: s }, { body: { ...s, max_item_budget_eur: "150.00" } });
    render(<SettingsView />);
    const input = await screen.findByLabelText(/Budget max. par article/);
    expect(input).toHaveValue("100.00");
    fireEvent.change(input, { target: { value: "150" } });
    fireEvent.click(screen.getByText("Enregistrer"));
    expect(await screen.findByText("Paramètres enregistrés.")).toBeInTheDocument();
    const [url, init] = fetch.mock.calls[1] as [string, RequestInit];
    expect(url).toBe("/api/v1/settings");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toMatchObject({ max_item_budget_eur: "150", priority_brands: ["Nike", "Adidas"] });
  });

  it("affiche l'erreur de validation renvoyée par l'API", async () => {
    mockFetch({ body: s }, { status: 422, body: { detail: [{ msg: "x" }] } });
    render(<SettingsView />);
    fireEvent.click(await screen.findByText("Enregistrer"));
    expect(await screen.findByRole("alert")).toHaveTextContent(/Données invalides/);
  });
});

describe("Navigation", () => {
  it("contient les 15 entrées du cahier des charges", () => {
    expect(NAV_ITEMS).toHaveLength(15);
    expect(NAV_ITEMS.filter((i) => i.available).map((i) => i.label)).toEqual([
      "Vue d'ensemble",
      "Recherche mondiale",
      "Paramètres",
      "Santé du système",
    ]);
  });
});
