import type { Offer } from "@/lib/api";
import { AVAILABILITY_LABELS, formatDateTime, formatMoney, formatShipping } from "@/lib/format";

const MATCH_LABELS: Record<Offer["match_method"], string> = {
  gtin: "Rattachée à un produit existant par code-barres (GTIN)",
  brand_mpn: "Rattachée à un produit existant par marque + référence fabricant",
  new_product: "Fiche produit créée à partir de cette offre",
};

const AVAILABILITY_STYLES: Record<Offer["availability"], string> = {
  in_stock: "bg-emerald-100 text-emerald-800",
  out_of_stock: "bg-red-100 text-red-800",
  unknown: "bg-amber-100 text-amber-800",
};

export function OfferCard({ offer }: { offer: Offer }) {
  const converted = offer.currency !== "EUR";
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" aria-label={offer.title}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h2 className="break-words text-sm font-semibold">
            {offer.is_demo && (
              <span className="mr-2 rounded bg-fuchsia-100 px-1.5 py-0.5 text-[10px] font-bold text-fuchsia-800">
                DEMO
              </span>
            )}
            {offer.title}
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            {offer.merchant ? `${offer.merchant.name}${offer.merchant.country ? ` (${offer.merchant.country})` : ""}` : "Marchand inconnu"}
            {" · "}source : {offer.source.name}
            {offer.brand ? ` · ${offer.brand}` : ""}
            {offer.size ? ` · taille ${offer.size}` : ""}
          </p>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold">{formatMoney(offer.price_amount, offer.currency)}</p>
          {converted && (
            <p className="text-xs text-slate-600">
              {offer.price_eur === null
                ? "Prix en EUR : non déterminé (aucun taux de change configuré)"
                : `≈ ${formatMoney(offer.price_eur, "EUR")}`}
            </p>
          )}
          <p className="text-xs text-slate-600">{formatShipping(offer.shipping_amount, offer.currency)}</p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className={`rounded px-2 py-0.5 ${AVAILABILITY_STYLES[offer.availability]}`}>
          {AVAILABILITY_LABELS[offer.availability]}
        </span>
        <span className={offer.is_stale ? "font-medium text-amber-700" : "text-slate-500"}>
          {offer.is_stale ? "Non revérifiée récemment — " : ""}vérifiée le {formatDateTime(offer.last_verified_at)}
        </span>
        <span className="text-slate-500">{MATCH_LABELS[offer.match_method]}</span>
      </div>

      <div className="mt-3">
        {/* Ouvre uniquement le site marchand : aucune commande n'est jamais passée par HUNTER AI. */}
        <a
          href={offer.url}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="text-sm font-medium text-indigo-700 underline"
        >
          Ouvrir le site marchand ↗
        </a>
      </div>
    </article>
  );
}
