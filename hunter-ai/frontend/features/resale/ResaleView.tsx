"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Banner, Card, Loading, PageHeader } from "@/components/ui";
import { num } from "@/features/profit/form";
import { api, ApiError, type ResaleRecord } from "@/lib/api";
import { formatMoney } from "@/lib/format";

type Page = { items: ResaleRecord[]; total: number };
const inputCls = "w-full rounded-md border border-slate-300 px-3 py-2";
const today = () => new Date().toISOString().slice(0, 10);
const EMPTY = { title: "", brand: "", size: "", channel: "vinted", sale_price: "", platform_fees: "", shipping_paid: "", purchase_cost: "", sold_on: "" };
const CHANNELS: Record<ResaleRecord["channel"], string> = { vinted: "Vinted", ebay: "eBay", leboncoin: "Leboncoin", other: "Autre" };

export function ResaleView({ initialData = null }: { initialData?: Page | null }) {
  const [data, setData] = useState<Page | null>(initialData);
  const [form, setForm] = useState({ ...EMPTY, sold_on: today() });
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    try {
      setData(await api.get<Page>("/resale-records?limit=100"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur inattendue.");
    }
  }, []);

  useEffect(() => {
    if (initialData === null) void load();
  }, [initialData, load]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);
    try {
      await api.post("/resale-records", {
        title: form.title.trim(),
        brand: form.brand.trim() || null,
        size: form.size.trim() || null,
        channel: form.channel,
        sale_price: num(form.sale_price),
        platform_fees: num(form.platform_fees),
        shipping_paid: num(form.shipping_paid),
        purchase_cost: num(form.purchase_cost),
        sold_on: form.sold_on,
      });
      setForm({ ...EMPTY, sold_on: form.sold_on, channel: form.channel });
      setSaved(true);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur inattendue.");
    }
  };

  const remove = async (r: ResaleRecord) => {
    if (!window.confirm(`Supprimer la vente « ${r.title} » ?`)) return;
    try {
      await api.delete(`/resale-records/${r.id}`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur inattendue.");
    }
  };

  const input = (key: keyof typeof EMPTY, label: string, props: Record<string, string> = {}) => (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{label}</span>
      <input className={inputCls} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} {...props} />
    </label>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Résultats de revente"
        subtitle="Vos ventes réellement conclues. Elles servent de référence de prix au calculateur : c'est la donnée la plus fiable."
      />
      <Card title="Ajouter une vente">
        <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-4">
          <div className="sm:col-span-2">{input("title", "Article", { required: "true", maxLength: "300" })}</div>
          {input("brand", "Marque")}
          {input("size", "Taille")}
          <label className="block text-sm">
            <span className="mb-1 block font-medium">Plateforme</span>
            <select className={inputCls} value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })}>
              {Object.entries(CHANNELS).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </label>
          {input("sale_price", "Prix de vente (€)", { required: "true", inputMode: "decimal" })}
          {input("platform_fees", "Frais plateforme (€)", { inputMode: "decimal", placeholder: "inconnu" })}
          {input("shipping_paid", "Port payé par vous (€)", { inputMode: "decimal", placeholder: "inconnu" })}
          {input("purchase_cost", "Coût d'achat (€)", { inputMode: "decimal", placeholder: "inconnu" })}
          {input("sold_on", "Date de vente", { type: "date", required: "true" })}
          <div className="sm:col-span-4">
            <button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              Enregistrer la vente
            </button>
          </div>
        </form>
        {saved && <p role="status" className="mt-2 text-sm text-emerald-700">Vente enregistrée.</p>}
      </Card>
      {error && <Banner tone="error">{error}</Banner>}
      {!data && !error && <Loading />}
      {data && data.total === 0 && <Banner tone="info">Aucune vente enregistrée pour l&apos;instant.</Banner>}
      {data && data.total > 0 && (
        <Card title={`${data.total} vente(s)`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th scope="col" className="py-1.5 pr-2">Date</th>
                  <th scope="col" className="py-1.5 pr-2">Article</th>
                  <th scope="col" className="py-1.5 pr-2">Plateforme</th>
                  <th scope="col" className="py-1.5 pr-2 text-right">Prix</th>
                  <th scope="col" className="py-1.5 pr-2 text-right">Bénéfice réel</th>
                  <th scope="col" className="py-1.5" />
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr key={r.id} className="border-b border-slate-100">
                    <td className="py-1.5 pr-2 whitespace-nowrap">{new Date(r.sold_on).toLocaleDateString("fr-FR")}</td>
                    <td className="py-1.5 pr-2">{r.title}{r.brand ? ` · ${r.brand}` : ""}{r.size ? ` · ${r.size}` : ""}</td>
                    <td className="py-1.5 pr-2">{CHANNELS[r.channel]}</td>
                    <td className="py-1.5 pr-2 text-right">{formatMoney(r.sale_price, "EUR")}</td>
                    <td className="py-1.5 pr-2 text-right">
                      {r.real_profit === null ? <span className="text-slate-500">coûts incomplets</span> : formatMoney(r.real_profit, "EUR")}
                    </td>
                    <td className="py-1.5 text-right">
                      <button type="button" onClick={() => void remove(r)} className="text-xs text-red-700 underline">
                        Supprimer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
