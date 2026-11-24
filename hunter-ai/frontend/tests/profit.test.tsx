import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EMPTY_FORM, num, toRequest } from "@/features/profit/form";
import { ProfitCalculator } from "@/features/profit/ProfitCalculator";
import { ProfitResultView } from "@/features/profit/ProfitResultView";
import { ResaleView } from "@/features/resale/ResaleView";
import type { ProfitResult, ResaleRecord } from "@/lib/api";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
afterEach(() => vi.unstubAllGlobals());

const result = (over: Partial<ProfitResult> = {}): ProfitResult => ({
  lines: [
    { key: "purchase", label: "Prix d'achat", status: "known", amount: { low: "28.00", high: "28.00" }, basis: "20 × 1,40 €" },
    { key: "import_vat", label: "TVA à l'importation", status: "range", amount: { low: "0.00", high: "9.00" }, basis: "Statut inconnu" },
  ],
  landed_cost: { low: "45.00", high: "54.00" },
  landed_cost_per_unit: { low: "2.25", high: "2.70" },
  sellable_units: "19.00",
  cost_per_sellable_unit: { low: "2.37", high: "2.84" },
  scenarios: [
    { key: "central", resale_price: "8.00", cost_used: "54.00", revenue: "152.00", selling_costs: "7.60", profit: "90.40", roi_pct: "167.41", margin_pct: "59.47" },
    { key: "pessimistic", resale_price: "2.00", cost_used: "54.00", revenue: "38.00", selling_costs: "1.90", profit: "-17.90", roi_pct: "-33.15", margin_pct: "-47.11" },
  ],
  break_even_price: "3.00",
  max_unit_price_for_target: "4.50",
  missing: [],
  warnings: ["Estimation indicative — validation douanière nécessaire."],
  rules_version: "2026-11-24",
  ...over,
});

describe("Formulaire de rentabilité", () => {
  it("accepte la virgule et garde le vide comme inconnu (jamais 0)", () => {
    expect(num(" 1,40 ")).toBe("1.40");
    expect(num("")).toBeNull();
    const req = toRequest({ ...EMPTY_FORM, unit_price: "1,40", quantity: "20" });
    expect(req.unit_price).toBe("1.40");
    expect(req.quantity).toBe(20);
    expect(req.shipping_cost).toBeNull();
    expect(req.resale_central).toBeNull();
    expect(req.payment_fee_pct).toBe("0");
  });
});

describe("Résultat", () => {
  it("affiche fourchettes, pertes, seuils et avertissements", () => {
    render(<ProfitResultView result={result()} />);
    expect(screen.getByText(/validation douanière/)).toBeInTheDocument();
    expect(screen.getByText(/0,00\s€ à 9,00\s€/)).toBeInTheDocument();
    expect(screen.getByText(/-17,90\s€/)).toHaveClass("text-red-700");
    expect(screen.getByText(/3,00\s€ \/ unité/)).toBeInTheDocument();
  });

  it("explique les informations manquantes et n'affiche pas de total inventé", () => {
    render(<ProfitResultView result={result({ landed_cost: null, scenarios: [], missing: ["Transport jusqu'à vous"] })} />);
    expect(screen.getByText(/Informations manquantes/).parentElement).toHaveTextContent("Transport jusqu'à vous");
    expect(screen.getAllByText("à vérifier").length).toBeGreaterThan(0);
    expect(screen.getByText(/Renseignez au moins un prix de revente/)).toBeInTheDocument();
  });
});

describe("Calculateur", () => {
  it("affiche les champs d'import seulement hors UE et envoie la requête", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(json(result()));
    vi.stubGlobal("fetch", fetch);
    render(<ProfitCalculator />);
    expect(screen.queryByText("2. Importation hors UE")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Origine"), { target: { value: "non_eu" } });
    expect(screen.getByText("2. Importation hors UE")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Prix unitaire (€)"), { target: { value: "1,40" } });
    fireEvent.click(screen.getByText("Calculer"));
    expect(await screen.findByText("Coût rendu")).toBeInTheDocument();
    const [url, init] = fetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/profit/calculate");
    expect(JSON.parse(init.body as string)).toMatchObject({ unit_price: "1.40", origin: "non_eu", shipping_cost: null });
  });

  it("propose les prix de revente depuis les ventes réelles, ou explique pourquoi pas", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(json({ count: 1, enough: false, minimum: "9", low: null, median: "9", high: null, maximum: "9" }))
      .mockResolvedValueOnce(json({ count: 5, enough: true, minimum: "5", low: "6.00", median: "8.00", high: "10.00", maximum: "12" }));
    vi.stubGlobal("fetch", fetch);
    render(<ProfitCalculator />);
    fireEvent.change(screen.getByLabelText("Mots du titre"), { target: { value: "coque" } });
    fireEvent.click(screen.getByText("Proposer depuis mes ventes"));
    expect(await screen.findByText(/il en faut au moins 3/)).toBeInTheDocument();
    expect(screen.getByLabelText("Prix de revente central (€)")).toHaveValue("");
    fireEvent.click(screen.getByText("Proposer depuis mes ventes"));
    await waitFor(() => expect(screen.getByLabelText("Prix de revente central (€)")).toHaveValue("8.00"));
    expect(screen.getByLabelText("Prix de revente bas (€)")).toHaveValue("6.00");
    expect(fetch.mock.calls[1][0]).toBe("/api/v1/resale-records/reference?q=coque");
  });
});

describe("Résultats de revente", () => {
  const rec: ResaleRecord = {
    id: "r1", title: "Coque iPhone 16", brand: null, category: null, size: null, condition: null,
    channel: "vinted", sale_price: "8.00", platform_fees: null, shipping_paid: null, purchase_cost: "2.50",
    real_profit: null, sold_on: "2026-11-20", notes: null, created_at: "2026-11-20T10:00:00Z",
  };

  it("liste les ventes et n'invente pas de bénéfice si les coûts sont incomplets", () => {
    render(<ResaleView initialData={{ items: [rec], total: 1 }} />);
    expect(screen.getByText("Coque iPhone 16")).toBeInTheDocument();
    expect(screen.getByText("coûts incomplets")).toBeInTheDocument();
  });

  it("enregistre une vente puis recharge la liste", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(json(rec, 201)).mockResolvedValueOnce(json({ items: [rec], total: 1 }));
    vi.stubGlobal("fetch", fetch);
    render(<ResaleView initialData={{ items: [], total: 0 }} />);
    fireEvent.change(screen.getByLabelText("Article"), { target: { value: "Coque iPhone 16" } });
    fireEvent.change(screen.getByLabelText("Prix de vente (€)"), { target: { value: "8" } });
    fireEvent.click(screen.getByText("Enregistrer la vente"));
    expect(await screen.findByText("Vente enregistrée.")).toBeInTheDocument();
    const body = JSON.parse((fetch.mock.calls[0][1] as RequestInit).body as string);
    expect(body).toMatchObject({ title: "Coque iPhone 16", sale_price: "8", platform_fees: null, channel: "vinted" });
  });

  it("demande confirmation avant suppression", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(new Response(null, { status: 204 })).mockResolvedValueOnce(json({ items: [], total: 0 }));
    vi.stubGlobal("fetch", fetch);
    vi.stubGlobal("confirm", vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true));
    render(<ResaleView initialData={{ items: [rec], total: 1 }} />);
    fireEvent.click(screen.getByText("Supprimer"));
    expect(fetch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Supprimer"));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect((fetch.mock.calls[0][1] as RequestInit).method).toBe("DELETE");
  });
});
