import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OfferCard } from "@/features/offers/OfferCard";
import { ProfitCalculator } from "@/features/profit/ProfitCalculator";
import { calculatorHref, prefillFromParams } from "@/features/profit/prefill";
import type { Offer } from "@/lib/api";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }), usePathname: () => "/" }));

const offer = (over: Partial<Offer> = {}): Offer => ({
  id: "o1", title: "Coque iPhone 16 antichoc", url: "https://www.aliexpress.com/item/1.html",
  source: { slug: "aliexpress", name: "AliExpress", is_demo: false },
  merchant: { name: "Case Factory Store", country: null }, product_id: "p1", brand: null, gtin: null,
  mpn: null, size: null, color: null, condition: "new", country: "CN", price_amount: "1.89",
  currency: "EUR", price_eur: "1.89", fx_rate_to_eur: "1", shipping_amount: "2.49",
  price_with_shipping_eur: "4.38", availability: "unknown", first_seen_at: "2026-11-24T06:00:00Z",
  last_verified_at: "2026-11-24T06:00:00Z", is_stale: false, access_method: "official_api",
  match_method: "new_product", match_confidence: "1.00", is_demo: false, ...over,
});

describe("Pré-remplissage du calculateur", () => {
  it("construit le lien depuis une offre : prix, port connu, pays", () => {
    const href = calculatorHref(offer());
    expect(href).toContain("/rentabilite?");
    const params = new URLSearchParams(href!.split("?")[1]);
    expect(Object.fromEntries(params)).toMatchObject({ unit_price: "1.89", shipping_cost: "2.49", country: "CN" });
  });

  it("ne transmet pas un port inconnu ni un prix EUR inconnu", () => {
    const noShipping = new URLSearchParams(calculatorHref(offer({ shipping_amount: null }))!.split("?")[1]);
    expect(noShipping.has("shipping_cost")).toBe(false);
    expect(calculatorHref(offer({ price_eur: null }))).toBeNull();
  });

  it("déduit l'origine du pays d'expédition (entrepôt UE = pas de douane)", () => {
    expect(prefillFromParams({ country: "CN" }).form.origin).toBe("non_eu");
    expect(prefillFromParams({ country: "es" }).form.origin).toBe("eu");
    expect(prefillFromParams({}).form.origin).toBe("eu");
  });

  it("ignore les valeurs invalides de l'URL", () => {
    const { form } = prefillFromParams({ unit_price: "abc", shipping_cost: "-3" });
    expect(form.unit_price).toBe("");
    expect(form.shipping_cost).toBe("");
  });

  it("la fiche offre affiche le pays d'expédition et le lien vers le calculateur", () => {
    render(<OfferCard offer={offer()} />);
    expect(screen.getByText("expédié depuis CN")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Calculer la rentabilité" })).toHaveAttribute(
      "href",
      expect.stringContaining("shipping_cost=2.49"),
    );
  });

  it("le calculateur annonce le pré-remplissage et affiche les champs d'import", () => {
    const { form, title } = prefillFromParams({ unit_price: "1.89", shipping_cost: "2.49", country: "CN", title: "Coque" });
    render(<ProfitCalculator initialForm={form} sourceTitle={title} />);
    expect(screen.getByText(/Pré-rempli depuis l.offre « Coque »/)).toBeInTheDocument();
    expect(screen.getByLabelText("Prix unitaire (€)")).toHaveValue("1.89");
    expect(screen.getByText("2. Importation hors UE")).toBeInTheDocument();
  });
});
