"use client";

import { type FormEvent, useEffect, useState } from "react";
import { Banner, Card, Loading, PageHeader } from "@/components/ui";
import { api, ApiError, type UserSettings } from "@/lib/api";

type Form = {
  max_item_budget_eur: string;
  max_lot_budget_eur: string;
  daily_collection_start: string;
  daily_collection_duration_min: string;
  priority_brands: string;
  markets: string;
};

const toForm = (s: UserSettings): Form => ({
  max_item_budget_eur: s.max_item_budget_eur ?? "",
  max_lot_budget_eur: s.max_lot_budget_eur ?? "",
  daily_collection_start: s.daily_collection_start.slice(0, 5),
  daily_collection_duration_min: String(s.daily_collection_duration_min),
  priority_brands: s.priority_brands.join(", "),
  markets: s.markets.join(", "),
});

const splitList = (v: string) =>
  v
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

export function SettingsView() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [form, setForm] = useState<Form | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get<UserSettings>("/settings")
      .then((s) => {
        setSettings(s);
        setForm(toForm(s));
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : "Erreur inattendue."));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await api.patch<UserSettings>("/settings", {
        max_item_budget_eur: form.max_item_budget_eur === "" ? null : form.max_item_budget_eur,
        max_lot_budget_eur: form.max_lot_budget_eur === "" ? null : form.max_lot_budget_eur,
        daily_collection_start: form.daily_collection_start,
        daily_collection_duration_min: Number(form.daily_collection_duration_min),
        priority_brands: splitList(form.priority_brands),
        markets: splitList(form.markets),
      });
      setSettings(updated);
      setForm(toForm(updated));
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur inattendue.");
    } finally {
      setSaving(false);
    }
  }

  const field = (key: keyof Form, label: string, props: Record<string, string> = {}) => (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{label}</span>
      <input
        className="w-full rounded-md border border-slate-300 px-3 py-2"
        value={form?.[key] ?? ""}
        onChange={(e) => setForm((f) => (f ? { ...f, [key]: e.target.value } : f))}
        {...props}
      />
    </label>
  );

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader title="Paramètres" subtitle="Valeurs métier initiales, modifiables à tout moment." />
      {error && <Banner tone="error">{error}</Banner>}
      {saved && <Banner tone="info">Paramètres enregistrés.</Banner>}
      {!form && !error && <Loading />}
      {form && settings && (
        <Card>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              {field("max_item_budget_eur", "Budget max. par article (€)", { inputMode: "decimal" })}
              {field("max_lot_budget_eur", "Budget max. d'un lot (€, vide = non défini)", { inputMode: "decimal" })}
              {field("daily_collection_start", "Début de la collecte quotidienne", { type: "time" })}
              {field("daily_collection_duration_min", "Durée de collecte (minutes)", { type: "number", min: "5", max: "720" })}
            </div>
            {field("priority_brands", "Marques prioritaires (séparées par des virgules)")}
            {field("markets", "Marchés (séparés par des virgules)")}
            <p className="text-xs text-slate-500">
              Devise : {settings.currency} · Fuseau : {settings.timezone} · Achat automatique :{" "}
              <strong>interdit</strong> (non modifiable).
            </p>
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? "Enregistrement…" : "Enregistrer"}
            </button>
          </form>
        </Card>
      )}
    </div>
  );
}
