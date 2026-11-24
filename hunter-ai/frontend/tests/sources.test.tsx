import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConnectorCard } from "@/features/sources/ConnectorCard";
import { SourcesView } from "@/features/sources/SourcesView";
import type { ConnectorInfo } from "@/lib/api";

const ebay = (over: Partial<ConnectorInfo> = {}): ConnectorInfo => ({
  slug: "ebay",
  name: "eBay (Browse API officielle)",
  description: "Annonces à prix fixe.",
  configured: false,
  status: null,
  daily_call_budget: 4500,
  calls_used_today: 0,
  ...over,
});

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

afterEach(() => vi.unstubAllGlobals());

describe("Sites et fournisseurs", () => {
  it("signale les identifiants manquants et le quota, sans formulaire de collecte", () => {
    render(<ConnectorCard connector={ebay()} onChanged={vi.fn()} />);
    expect(screen.getByText("Jamais testée")).toBeInTheDocument();
    expect(screen.getByText("Identifiants absents du fichier .env")).toBeInTheDocument();
    expect(screen.getByText("Quota du jour : 0 / 4500 appels")).toBeInTheDocument();
    expect(screen.queryByText("Collecter")).not.toBeInTheDocument();
  });

  it("le test de connexion affiche le résultat réel renvoyé par le serveur", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(
      json({ ok: false, status: "needs_approval", detail: "Accès à la Browse API refusé par eBay.", sample_count: 0, api_calls: 2 }),
    );
    vi.stubGlobal("fetch", fetch);
    const onChanged = vi.fn();
    render(<ConnectorCard connector={ebay({ configured: true })} onChanged={onChanged} />);
    fireEvent.click(screen.getByText("Tester la connexion"));
    expect(await screen.findByRole("alert")).toHaveTextContent("refusé par eBay");
    expect(fetch.mock.calls[0][0]).toBe("/api/v1/sources/ebay/test");
    expect(onChanged).toHaveBeenCalled();
  });

  it("une source active propose la collecte et envoie les bons paramètres", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(
      json({ status: "success", offers_received: 12, offers_created: 10, api_calls: 1, errors: [] }),
    );
    vi.stubGlobal("fetch", fetch);
    render(<ConnectorCard connector={ebay({ configured: true, status: "active" })} onChanged={vi.fn()} />);
    expect(screen.getByText("Active")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Mots-clés/), { target: { value: " polo ralph lauren " } });
    fireEvent.change(screen.getByLabelText(/Prix max/), { target: { value: "30" } });
    fireEvent.click(screen.getByText("Collecter"));
    expect(await screen.findByText(/12 annonce\(s\) reçue\(s\), 10 nouvelle\(s\), 1 appel\(s\) API/)).toBeInTheDocument();
    const [url, init] = fetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/sources/ebay/collect");
    expect(JSON.parse(init.body as string)).toEqual({ keywords: "polo ralph lauren", max_price: "30", limit: 50 });
  });

  it("la source DEMO ne propose pas de test externe", () => {
    render(<ConnectorCard connector={ebay({ slug: "demo", name: "DEMO", daily_call_budget: null })} onChanged={vi.fn()} />);
    expect(screen.queryByText("Tester la connexion")).not.toBeInTheDocument();
    expect(screen.getByText("Non chargée")).toBeInTheDocument();
    expect(screen.queryByText("Lancez le test de connexion.")).not.toBeInTheDocument();
  });

  it("la page explique l'absence de Vinted", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json([ebay()])));
    render(<SourcesView />);
    await waitFor(() => expect(screen.getByText("eBay (Browse API officielle)")).toBeInTheDocument());
    expect(screen.getByText(/Vinted n.apparaît pas ici volontairement/)).toBeInTheDocument();
  });
});
