import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DemoDataCard } from "@/features/dashboard/DemoDataCard";
import { apiPath, filtersToQuery, parseFilters } from "@/features/offers/filters";
import { OfferCard } from "@/features/offers/OfferCard";
import { OffersView } from "@/features/offers/OffersView";
import type { Offer, OfferPage } from "@/lib/api";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }), usePathname: () => "/recherche" }));

const offer = (over: Partial<Offer> = {}): Offer => ({
  id: "o1",
  title: "[DEMO] Polo DEMO Gamma G2",
  url: "https://example.com/demo/offre/D-005",
  source: { slug: "demo", name: "Source DEMO", is_demo: true },
  merchant: { name: "Store DEMO New York", country: "US" },
  product_id: "p1",
  brand: "Gamma DEMO",
  gtin: null,
  mpn: null,
  size: "L",
  color: null,
  condition: "new",
  country: "US",
  price_amount: "35.00",
  currency: "USD",
  price_eur: null,
  fx_rate_to_eur: null,
  shipping_amount: null,
  price_with_shipping_eur: null,
  availability: "unknown",
  first_seen_at: "2026-11-24T06:00:00Z",
  last_verified_at: "2026-11-24T06:00:00Z",
  is_stale: false,
  access_method: "manual_import",
  match_method: "new_product",
  match_confidence: "1.00",
  is_demo: true,
  ...over,
});

const page = (items: Offer[], over: Partial<OfferPage> = {}): OfferPage => ({
  items,
  total: items.length,
  limit: 20,
  offset: 0,
  ...over,
});

const noFilters = { q: "", availability: "" as const, sort: "recent" as const, offset: 0 };

afterEach(() => {
  vi.unstubAllGlobals();
  push.mockReset();
});

describe("Fiche offre", () => {
  it("n'invente rien : EUR non déterminé, livraison inconnue, disponibilité à confirmer, badge DEMO", () => {
    render(<OfferCard offer={offer()} />);
    expect(screen.getByText("DEMO")).toBeInTheDocument();
    expect(screen.getByText(/non déterminé \(aucun taux de change configuré\)/)).toBeInTheDocument();
    expect(screen.getByText("frais de livraison inconnus")).toBeInTheDocument();
    expect(screen.getByText("Disponibilité à confirmer")).toBeInTheDocument();
  });

  it("le lien ouvre seulement le site marchand, dans un nouvel onglet isolé", () => {
    render(<OfferCard offer={offer()} />);
    const link = screen.getByRole("link", { name: /Ouvrir le site marchand/ });
    expect(link).toHaveAttribute("href", "https://example.com/demo/offre/D-005");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("distingue livraison gratuite et signale une offre non revérifiée", () => {
    render(<OfferCard offer={offer({ currency: "EUR", price_amount: "89.00", shipping_amount: "0.00", is_stale: true })} />);
    expect(screen.getByText("livraison gratuite")).toBeInTheDocument();
    expect(screen.getByText(/Non revérifiée récemment/)).toBeInTheDocument();
    expect(screen.queryByText(/non déterminé/)).not.toBeInTheDocument();
  });
});

describe("Filtres d'offres", () => {
  it("ignorent les valeurs inattendues de l'URL", () => {
    expect(parseFilters({ q: "veste", availability: "hack", sort: "drop", offset: "-5" })).toEqual({
      q: "veste",
      availability: "",
      sort: "recent",
      offset: 0,
    });
  });

  it("produisent une URL et un appel API cohérents", () => {
    const f = { q: "veste bleue", availability: "in_stock" as const, sort: "price_eur_asc" as const, offset: 20 };
    expect(filtersToQuery(f)).toBe("q=veste+bleue&availability=in_stock&sort=price_eur_asc&offset=20");
    expect(apiPath(noFilters)).toBe("/offers?limit=20");
  });
});

describe("Liste des offres", () => {
  it("affiche les offres rendues par le serveur, sans appel supplémentaire", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<OffersView filters={noFilters} initialData={page([offer()])} />);
    expect(screen.getByText("1–1 sur 1 offre(s)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Précédentes/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Suivantes/ })).toBeDisabled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("explique l'état vide", () => {
    render(<OffersView filters={noFilters} initialData={page([])} />);
    expect(screen.getByText(/Aucune offre ne correspond/)).toBeInTheDocument();
  });

  it("place les filtres dans l'URL à la recherche et à la pagination", () => {
    render(<OffersView filters={noFilters} initialData={page([offer()], { total: 45 })} />);
    fireEvent.change(screen.getByLabelText("Mots-clés"), { target: { value: "  polo " } });
    fireEvent.click(screen.getByText("Rechercher"));
    expect(push).toHaveBeenLastCalledWith("/recherche?q=polo");
    fireEvent.click(screen.getByRole("button", { name: /Suivantes/ }));
    expect(push).toHaveBeenLastCalledWith("/recherche?offset=20");
  });

  it("charge depuis le navigateur si le serveur n'a rien fourni, et affiche les erreurs", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce(new TypeError("network")));
    render(<OffersView filters={noFilters} initialData={null} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/injoignable/);
  });
});

describe("Données DEMO", () => {
  it("charge les données DEMO puis rafraîchit le tableau de bord", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ offers_received: 6, offers_created: 6, observations_created: 6 })),
    );
    vi.stubGlobal("fetch", fetch);
    const onChanged = vi.fn();
    render(<DemoDataCard hasDemo={false} onChanged={onChanged} />);
    fireEvent.click(screen.getByText("Charger les données DEMO"));
    expect(await screen.findByText(/6 offre\(s\) reçue\(s\)/)).toBeInTheDocument();
    expect(fetch.mock.calls[0][0]).toBe("/api/v1/demo/load");
    expect((fetch.mock.calls[0][1] as RequestInit).method).toBe("POST");
    expect(onChanged).toHaveBeenCalled();
  });

  it("demande confirmation avant de supprimer, et ne fait rien si l'on annule", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ offers_deleted: 6 })));
    vi.stubGlobal("fetch", fetch);
    vi.stubGlobal("confirm", vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true));
    render(<DemoDataCard hasDemo onChanged={vi.fn()} />);
    fireEvent.click(screen.getByText("Supprimer les données DEMO"));
    expect(fetch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Supprimer les données DEMO"));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect((fetch.mock.calls[0][1] as RequestInit).method).toBe("DELETE");
    expect(await screen.findByText("6 offre(s) DEMO supprimée(s).")).toBeInTheDocument();
  });
});
