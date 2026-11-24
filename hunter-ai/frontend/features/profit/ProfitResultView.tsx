import { Banner, Card } from "@/components/ui";
import type { ProfitResult } from "@/lib/api";
import { formatMoney, formatPct, formatRange } from "@/lib/format";

const SCENARIO_LABELS = { pessimistic: "Pessimiste", central: "Central (prudent)", optimistic: "Optimiste" };
const STATUS_CLS = { known: "", range: "text-amber-700", unknown: "font-medium text-red-700" };

export function ProfitResultView({ result }: { result: ProfitResult }) {
  const eur = (v: string | null) => (v === null ? "à vérifier" : formatMoney(v, "EUR"));
  return (
    <div className="space-y-4">
      {result.warnings.map((w) => (
        <Banner key={w} tone="warning">
          {w}
        </Banner>
      ))}
      {result.missing.length > 0 && (
        <Banner tone="info">
          <strong>Informations manquantes :</strong> {result.missing.join(" · ")}. Les totaux concernés restent « à
          vérifier » : aucune valeur n&apos;est inventée.
        </Banner>
      )}

      <Card title="Coût rendu">
        <table className="w-full text-left text-sm">
          <tbody>
            {result.lines.map((l) => (
              <tr key={l.key} className="border-b border-slate-100 align-top">
                <td className="py-1.5 pr-2 font-medium">{l.label}</td>
                <td className={`py-1.5 pr-2 text-right whitespace-nowrap ${STATUS_CLS[l.status]}`}>{formatRange(l.amount)}</td>
                <td className="py-1.5 text-xs text-slate-500">{l.basis}</td>
              </tr>
            ))}
            <tr className="font-semibold">
              <td className="pt-2">Total</td>
              <td className="pt-2 text-right whitespace-nowrap">{formatRange(result.landed_cost)}</td>
              <td />
            </tr>
          </tbody>
        </table>
        <p className="mt-3 text-sm">
          Par unité achetée : <strong>{formatRange(result.landed_cost_per_unit)}</strong> · par unité vendable (
          {result.sellable_units}) : <strong>{formatRange(result.cost_per_sellable_unit)}</strong>
        </p>
      </Card>

      <Card title="Rentabilité estimée">
        {result.scenarios.length === 0 ? (
          <p className="text-sm text-slate-600">
            Renseignez au moins un prix de revente et complétez le coût rendu pour obtenir les scénarios.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th scope="col" className="py-1.5 pr-2">Scénario</th>
                  <th scope="col" className="py-1.5 pr-2 text-right">Revente/u.</th>
                  <th scope="col" className="py-1.5 pr-2 text-right">Bénéfice</th>
                  <th scope="col" className="py-1.5 pr-2 text-right">ROI</th>
                  <th scope="col" className="py-1.5 text-right">Marge</th>
                </tr>
              </thead>
              <tbody>
                {result.scenarios.map((s) => (
                  <tr key={s.key} className="border-b border-slate-100">
                    <td className="py-1.5 pr-2">{SCENARIO_LABELS[s.key]}</td>
                    <td className="py-1.5 pr-2 text-right">{eur(s.resale_price)}</td>
                    <td className={`py-1.5 pr-2 text-right font-medium ${Number(s.profit) < 0 ? "text-red-700" : "text-emerald-700"}`}>
                      {eur(s.profit)}
                    </td>
                    <td className="py-1.5 pr-2 text-right">{formatPct(s.roi_pct)}</td>
                    <td className="py-1.5 text-right">{formatPct(s.margin_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Prix de revente minimum (seuil de rentabilité)</dt>
            <dd className="font-semibold">{eur(result.break_even_price)} / unité</dd>
          </div>
          <div>
            <dt className="text-slate-500">Prix d&apos;achat maximum pour le ROI visé</dt>
            <dd className="font-semibold">{eur(result.max_unit_price_for_target)} / unité</dd>
          </div>
        </dl>
        <p className="mt-3 text-xs text-slate-500">
          ROI = bénéfice ÷ coût engagé · Marge = bénéfice ÷ chiffre d&apos;affaires · Estimations, pas des garanties ·
          Règles du {result.rules_version}.
        </p>
      </Card>
    </div>
  );
}
