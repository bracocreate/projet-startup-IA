"use client";

import { useEffect, useState } from "react";
import { Banner, Card, Loading, PageHeader } from "@/components/ui";
import { api, ApiError, type ComponentStatus, type SystemStatus } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

const LABELS: Record<ComponentStatus["status"], { text: string; cls: string }> = {
  ok: { text: "OK", cls: "bg-emerald-100 text-emerald-800" },
  warning: { text: "Attention", cls: "bg-amber-100 text-amber-800" },
  error: { text: "Erreur", cls: "bg-red-100 text-red-800" },
  not_configured: { text: "Non configuré", cls: "bg-slate-100 text-slate-700" },
  not_implemented: { text: "Pas encore disponible", cls: "bg-slate-100 text-slate-700" },
};

export function HealthView() {
  const [data, setData] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<SystemStatus>("/system/status")
      .then(setData)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : "Erreur inattendue."));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader title="Santé du système" subtitle="État des composants de HUNTER AI." />
      {error && <Banner tone="error">{error}</Banner>}
      {!data && !error && <Loading />}
      {data && (
        <Card>
          <p className="mb-4 text-sm text-slate-600">
            Version {data.version} · environnement {data.environment} · contrôle du{" "}
            {formatDateTime(data.time_utc, data.timezone)}
          </p>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th scope="col" className="py-2">Composant</th>
                <th scope="col" className="py-2">État</th>
                <th scope="col" className="py-2">Détail</th>
              </tr>
            </thead>
            <tbody>
              {data.components.map((c) => (
                <tr key={c.name} className="border-b border-slate-100 align-top">
                  <td className="py-2 font-medium">{c.name}</td>
                  <td className="py-2">
                    <span className={`rounded px-2 py-0.5 text-xs ${LABELS[c.status].cls}`}>
                      {LABELS[c.status].text}
                    </span>
                  </td>
                  <td className="py-2 text-slate-600">{c.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
