"use client";

import { type FormEvent, type ReactNode, useState } from "react";
import { Banner, Card, PageHeader } from "@/components/ui";
import { EMPTY_FORM, type ProfitForm, toRequest } from "@/features/profit/form";
import { ProfitResultView } from "@/features/profit/ProfitResultView";
import { api, ApiError, type ProfitResult, type ResaleReference } from "@/lib/api";

const inputCls = "w-full rounded-md border border-slate-300 px-3 py-2";

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{label}</span>
      {children}
      {hint && <span className="mt-0.5 block text-xs text-slate-500">{hint}</span>}
    </label>
  );
}

type Props = { initialForm?: ProfitForm; sourceTitle?: string };

export function ProfitCalculator({ initialForm = EMPTY_FORM, sourceTitle = "" }: Props) {
  const [form, setForm] = useState<ProfitForm>(initialForm);
  const [result, setResult] = useState<ProfitResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [refQuery, setRefQuery] = useState({ brand: "", q: "" });
  const [refMessage, setRefMessage] = useState<string | null>(null);

  const set = <K extends keyof ProfitForm>(key: K, value: ProfitForm[K]) => setForm((f) => ({ ...f, [key]: value }));
  const text = (key: keyof ProfitForm, props: Record<string, string> = {}) => (
    <input
      className={inputCls}
      inputMode="decimal"
      value={String(form[key])}
      onChange={(e) => set(key, e.target.value as never)}
      {...props}
    />
  );

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setResult(await api.post<ProfitResult>("/profit/calculate", toRequest(form)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur inattendue.");
    } finally {
      setBusy(false);
    }
  };

  const loadReference = async () => {
    setRefMessage(null);
    const params = new URLSearchParams();
    if (refQuery.brand.trim()) params.set("brand", refQuery.brand.trim());
    if (refQuery.q.trim()) params.set("q", refQuery.q.trim());
    try {
      const ref = await api.get<ResaleReference>(`/resale-records/reference?${params.toString()}`);
      if (!ref.enough) {
        setRefMessage(`${ref.count} vente(s) correspondante(s) : il en faut au moins 3 pour proposer une référence fiable.`);
        return;
      }
      setForm((f) => ({ ...f, resale_low: ref.low ?? "", resale_central: ref.median ?? "", resale_high: ref.high ?? "" }));
      setRefMessage(`Référence tirée de ${ref.count} vente(s) réelle(s) : 1er quartile, médiane, 3e quartile.`);
    } catch (err) {
      setRefMessage(err instanceof ApiError ? err.message : "Erreur inattendue.");
    }
  };

  const nonEu = form.origin === "non_eu";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lots et achats — calculateur de rentabilité"
        subtitle="Coût rendu complet (import compris), bénéfice, ROI et marge par scénario. Montants en euros ; un champ vide reste « inconnu »."
      />
      {sourceTitle && (
        <Banner tone="info">
          Pré-rempli depuis l&apos;offre « {sourceTitle} » : prix en euros, frais de port s&apos;ils sont connus,
          origine selon le pays d&apos;expédition. Vérifiez et complétez avant de calculer.
        </Banner>
      )}
      <form onSubmit={onSubmit} className="space-y-4">
        <Card title="1. Achat">
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Prix unitaire (€)">{text("unit_price", { required: "true" })}</Field>
            <Field label="Quantité">{text("quantity", { inputMode: "numeric" })}</Field>
            <Field label="Transport total jusqu'à vous (€)" hint="Vide = inconnu · 0 = gratuit">
              {text("shipping_cost")}
            </Field>
            <Field label="Origine">
              <select className={inputCls} value={form.origin} onChange={(e) => set("origin", e.target.value as ProfitForm["origin"])}>
                <option value="eu">Union européenne</option>
                <option value="non_eu">Hors UE (Chine, États-Unis…)</option>
              </select>
            </Field>
            <label className="flex items-center gap-2 text-sm sm:col-span-2 sm:mt-6">
              <input type="checkbox" checked={form.branded} onChange={(e) => set("branded", e.target.checked)} />
              Article d&apos;une marque connue
            </label>
          </div>
        </Card>

        {nonEu && (
          <Card title="2. Importation hors UE">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Catégories d'articles dans le colis" hint="Ex. 3 t-shirts + 1 paire de chaussures = 2">
                {text("article_categories", { inputMode: "numeric" })}
              </Field>
              <Field label="TVA dans le prix affiché ?">
                <select className={inputCls} value={form.vat_status} onChange={(e) => set("vat_status", e.target.value as ProfitForm["vat_status"])}>
                  <option value="unknown">Je ne sais pas</option>
                  <option value="included">Oui, déjà incluse (vendeur IOSS)</option>
                  <option value="not_included">Non, à payer à l&apos;import</option>
                </select>
              </Field>
              <Field label="Droits de douane si envoi > 150 € (%)" hint="Taux du tarif douanier ; vide = inconnu">
                {text("customs_duty_rate_pct")}
              </Field>
            </div>
          </Card>
        )}

        <Card title={`${nonEu ? "3" : "2"}. Autres frais`}>
          <div className="grid gap-3 sm:grid-cols-4">
            <Field label="Frais de paiement / change (%)">{text("payment_fee_pct")}</Field>
            <Field label="Autres frais fixes (€)" hint="Inspection, échantillons…">{text("other_fixed_costs")}</Field>
            <Field label="Préparation par unité (€)">{text("prep_cost_per_unit")}</Field>
            <Field label="Taux de défaut / invendus (%)">{text("defect_rate_pct")}</Field>
          </div>
        </Card>

        <Card title={`${nonEu ? "4" : "3"}. Revente`}>
          <div className="mb-3 grid gap-3 rounded-md bg-slate-50 p-3 sm:grid-cols-3">
            <Field label="Marque (vos ventes)">
              <input className={inputCls} value={refQuery.brand} onChange={(e) => setRefQuery({ ...refQuery, brand: e.target.value })} />
            </Field>
            <Field label="Mots du titre">
              <input className={inputCls} value={refQuery.q} onChange={(e) => setRefQuery({ ...refQuery, q: e.target.value })} />
            </Field>
            <div className="sm:mt-6">
              <button type="button" onClick={() => void loadReference()} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-100">
                Proposer depuis mes ventes
              </button>
            </div>
            {refMessage && <p className="text-sm text-slate-700 sm:col-span-3" role="status">{refMessage}</p>}
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Prix de revente bas (€)">{text("resale_low")}</Field>
            <Field label="Prix de revente central (€)">{text("resale_central")}</Field>
            <Field label="Prix de revente haut (€)">{text("resale_high")}</Field>
            <Field label="Commission de vente (%)">{text("selling_fee_pct")}</Field>
            <Field label="Frais fixes de vente par unité (€)">{text("selling_fee_fixed_per_unit")}</Field>
            <Field label="Port payé par vous par vente (€)">{text("selling_shipping_per_unit")}</Field>
            <Field label="ROI visé (%)">{text("target_roi_pct")}</Field>
          </div>
        </Card>

        <button type="submit" disabled={busy} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
          {busy ? "Calcul…" : "Calculer"}
        </button>
      </form>
      {error && <Banner tone="error">{error}</Banner>}
      {result && <ProfitResultView result={result} />}
    </div>
  );
}
