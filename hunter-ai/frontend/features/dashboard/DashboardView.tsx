"use client";

import { useCallback, useEffect, useState } from "react";
import { Banner, Card, Loading, PageHeader } from "@/components/ui";
import { api, ApiError, type DashboardSummary } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

export function DashboardView({ initialData = null }: { initialData?: DashboardSummary | null }) {
  const [data, setData] = useState<DashboardSummary | null>(initialData);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(initialData === null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await api.get<DashboardSummary>("/dashboard/summary"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur inattendue.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Données déjà rendues par le serveur : pas de second chargement. Sinon, chargement dans le navigateur.
  useEffect(() => {
    if (initialData === null) void load();
  }, [initialData, load]);

  return (
    <div className="space-y-6">
      <PageHeader title="Vue d'ensemble" subtitle="Dernier état connu des opportunités, tendances et sources." />

      {loading && !data && <Loading label="Chargement du tableau de bord…" />}

      {error && (
        <Banner tone="error">
          <p>{error}</p>
          <button type="button" onClick={() => void load()} className="mt-2 underline">
            Réessayer
          </button>
        </Banner>
      )}

      {data && (
        <>
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
            <span>
              Dernière actualisation : <strong>{formatDateTime(data.last_refresh_at)}</strong>
            </span>
            <button
              type="button"
              onClick={() => void load()}
              disabled={loading}
              className="rounded-md border border-slate-300 bg-white px-3 py-1 hover:bg-slate-100 disabled:opacity-50"
            >
              {loading ? "Actualisation…" : "Actualiser l'affichage"}
            </button>
          </div>

          {data.data_mode === "demo" && (
            <Banner tone="demo">
              <strong>DEMO</strong> — des données de démonstration sont présentes. Elles ne reflètent aucun prix ni
              stock réel.
            </Banner>
          )}

          {data.data_mode === "empty" && (
            <Banner tone="info">
              <strong>Aucune donnée collectée pour l&apos;instant.</strong> Le socle est opérationnel, mais aucun
              connecteur de données n&apos;est encore actif. Les premières offres réelles arriveront avec le premier
              connecteur autorisé (Phase 3).
            </Banner>
          )}

          {data.is_stale && data.last_refresh_at && (
            <Banner tone="warning">
              Données périmées : plus de {data.stale_after_hours} h depuis la dernière actualisation.
            </Banner>
          )}

          <div className="grid gap-4 lg:grid-cols-3">
            {data.rankings.map((r) => (
              <Card key={r.key} title={r.title}>
                {r.items.length === 0 ? (
                  <p className="text-sm text-slate-500">{r.message}</p>
                ) : (
                  <p className="text-sm">{r.items.length} élément(s)</p>
                )}
              </Card>
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Sources">
              <p className="text-sm">
                {data.sources_total === 0
                  ? "Aucune source enregistrée."
                  : `${data.sources_total} source(s) enregistrée(s).`}
              </p>
              {data.sources_in_error.length > 0 && (
                <ul className="mt-3 space-y-1 text-sm text-red-700" aria-label="Sources en erreur">
                  {data.sources_in_error.map((s) => (
                    <li key={s.id}>
                      ⚠ {s.name} — {s.status === "error" ? "en erreur" : "dégradée"}
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="Découvertes à valider">
              <p className="text-sm text-slate-500">
                {data.pending_discoveries === 0
                  ? "Aucune proposition en attente."
                  : `${data.pending_discoveries} proposition(s) en attente.`}
              </p>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
