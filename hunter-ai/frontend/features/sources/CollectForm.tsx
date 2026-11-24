"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { api, ApiError, type ConnectorRun } from "@/lib/api";

type Props = { slug: string; onDone: () => void };

export function CollectForm({ slug, onDone }: Props) {
  const [keywords, setKeywords] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [limit, setLimit] = useState("50");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setResult(null);
    try {
      const run = await api.post<ConnectorRun>(`/sources/${slug}/collect`, {
        keywords: keywords.trim(),
        max_price: maxPrice === "" ? null : maxPrice,
        limit: Number(limit),
      });
      const errors = run.errors.length ? ` · ${run.errors.length} erreur(s) : ${run.errors[0]}` : "";
      setResult({
        tone: run.status === "error" ? "error" : "ok",
        text: `Collecte ${run.status === "success" ? "terminée" : run.status === "partial" ? "partielle" : "en erreur"} : ${run.offers_received} annonce(s) reçue(s), ${run.offers_created} nouvelle(s), ${run.api_calls} appel(s) API${errors}`,
      });
      onDone();
    } catch (err) {
      setResult({ tone: "error", text: err instanceof ApiError ? err.message : "Erreur inattendue." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="mt-4 space-y-3 border-t border-slate-100 pt-4">
      <p className="text-sm font-medium">Lancer une collecte (annonces les plus récentes d&apos;abord)</p>
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-sm sm:col-span-3">
          <span className="mb-1 block">Mots-clés (marque, modèle…)</span>
          <input
            required
            maxLength={100}
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block">Prix max. (€, facultatif)</span>
          <input
            inputMode="decimal"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block">Nombre d&apos;annonces (1–200)</span>
          <input
            type="number"
            min={1}
            max={200}
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={busy}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {busy ? "Collecte en cours…" : "Collecter"}
      </button>
      {result && (
        <p role={result.tone === "error" ? "alert" : "status"} className={`text-sm ${result.tone === "error" ? "text-red-700" : "text-emerald-700"}`}>
          {result.text}{" "}
          {result.tone === "ok" && (
            <Link href={`/recherche`} className="underline">
              Voir les offres
            </Link>
          )}
        </p>
      )}
    </form>
  );
}
