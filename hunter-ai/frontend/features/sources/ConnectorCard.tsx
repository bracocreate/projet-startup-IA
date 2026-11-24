"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { CollectForm } from "@/features/sources/CollectForm";
import { NOT_TESTED, STATUS_LABELS } from "@/features/sources/status";
import { api, ApiError, type ConnectorInfo, type SourceTestResult } from "@/lib/api";

type Props = { connector: ConnectorInfo; onChanged: () => void };

export function ConnectorCard({ connector, onChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);
  const isDemo = connector.slug === "demo";
  const demoLabel = connector.status
    ? { text: "Chargée", cls: "bg-fuchsia-100 text-fuchsia-800", help: "" }
    : { text: "Non chargée", cls: "bg-slate-100 text-slate-700", help: "" };
  const label = isDemo
    ? demoLabel
    : connector.status
      ? (STATUS_LABELS[connector.status] ?? NOT_TESTED)
      : NOT_TESTED;

  const runTest = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const r = await api.post<SourceTestResult>(`/sources/${connector.slug}/test`);
      setMessage({ tone: r.ok ? "ok" : "error", text: r.detail });
      onChanged();
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof ApiError ? e.message : "Erreur inattendue." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={connector.name}>
      <p className="text-sm text-slate-600">{connector.description}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className={`rounded px-2 py-0.5 ${label.cls}`}>{label.text}</span>
        {!connector.configured && <span className="text-amber-700">Identifiants absents du fichier .env</span>}
        {connector.daily_call_budget !== null && (
          <span className="text-slate-500">
            Quota du jour : {connector.calls_used_today} / {connector.daily_call_budget} appels
          </span>
        )}
      </div>
      {label.help && <p className="mt-2 text-xs text-slate-500">{label.help}</p>}

      {isDemo ? (
        <p className="mt-3 text-sm text-slate-600">Se gère depuis la vue d&apos;ensemble (« Charger les données DEMO »).</p>
      ) : (
        <button
          type="button"
          disabled={busy}
          onClick={() => void runTest()}
          className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-100 disabled:opacity-50"
        >
          {busy ? "Test en cours…" : "Tester la connexion"}
        </button>
      )}
      {message && (
        <p role={message.tone === "error" ? "alert" : "status"} className={`mt-2 text-sm ${message.tone === "error" ? "text-red-700" : "text-emerald-700"}`}>
          {message.text}
        </p>
      )}
      {!isDemo && connector.status === "active" && <CollectForm slug={connector.slug} onDone={onChanged} />}
    </Card>
  );
}
