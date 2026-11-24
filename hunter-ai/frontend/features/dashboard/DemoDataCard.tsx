"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { api, ApiError, type ConnectorRun } from "@/lib/api";

type Props = { hasDemo: boolean; onChanged: () => void };

export function DemoDataCard({ hasDemo, onChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  const run = async (action: () => Promise<string>) => {
    setBusy(true);
    setMessage(null);
    try {
      setMessage({ tone: "ok", text: await action() });
      onChanged();
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof ApiError ? e.message : "Erreur inattendue." });
    } finally {
      setBusy(false);
    }
  };

  const loadDemo = () =>
    run(async () => {
      const r = await api.post<ConnectorRun>("/demo/load");
      return `Collecte DEMO terminée : ${r.offers_received} offre(s) reçue(s), ${r.offers_created} nouvelle(s), ${r.observations_created} observation(s) de prix enregistrée(s).`;
    });

  const removeDemo = () => {
    if (!window.confirm("Supprimer toutes les données DEMO (offres, produits, marchands fictifs) ?")) return;
    void run(async () => {
      const r = await api.delete<{ offers_deleted: number }>("/demo");
      return `${r.offers_deleted} offre(s) DEMO supprimée(s).`;
    });
  };

  return (
    <Card title="Données de démonstration">
      <p className="text-sm text-slate-600">
        Des offres <strong>fictives</strong>, marquées DEMO, pour essayer l&apos;interface sans connecteur réel. Elles ne
        reflètent aucun prix ni stock réel et se suppriment entièrement.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void loadDemo()}
          className="rounded-md border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-100 disabled:opacity-50"
        >
          {hasDemo ? "Relancer la collecte DEMO" : "Charger les données DEMO"}
        </button>
        {hasDemo && (
          <button
            type="button"
            disabled={busy}
            onClick={removeDemo}
            className="rounded-md border border-red-300 bg-white px-3 py-1 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            Supprimer les données DEMO
          </button>
        )}
      </div>
      {message && (
        <p role={message.tone === "error" ? "alert" : "status"} className={`mt-3 text-sm ${message.tone === "error" ? "text-red-700" : "text-emerald-700"}`}>
          {message.text}
        </p>
      )}
    </Card>
  );
}
