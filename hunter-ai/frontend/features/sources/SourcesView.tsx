"use client";

import { useCallback, useEffect, useState } from "react";
import { Banner, Loading, PageHeader } from "@/components/ui";
import { ConnectorCard } from "@/features/sources/ConnectorCard";
import { api, ApiError, type ConnectorInfo } from "@/lib/api";

export function SourcesView({ initialData = null }: { initialData?: ConnectorInfo[] | null }) {
  const [data, setData] = useState<ConnectorInfo[] | null>(initialData);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await api.get<ConnectorInfo[]>("/connectors"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur inattendue.");
    }
  }, []);

  useEffect(() => {
    if (initialData === null) void load();
  }, [initialData, load]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sites et fournisseurs"
        subtitle="Sources de données autorisées. Une source ne collecte qu'après un test réel réussi."
      />
      {error && <Banner tone="error">{error}</Banner>}
      {!data && !error && <Loading />}
      {data && (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.map((c) => (
            <ConnectorCard key={c.slug} connector={c} onChanged={() => void load()} />
          ))}
        </div>
      )}
      <Banner tone="info">
        Vinted n&apos;apparaît pas ici volontairement : aucun accès automatisé autorisé n&apos;existe (pas de scraping,
        conformément au cahier des charges).
      </Banner>
    </div>
  );
}
