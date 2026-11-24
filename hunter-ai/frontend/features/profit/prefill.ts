import { EMPTY_FORM, type ProfitForm } from "@/features/profit/form";

/** Les 27 États membres de l'UE (codes ISO) : pas de droits de douane entre eux. */
export const EU_COUNTRIES = new Set([
  "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU",
  "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
]);

type Params = Record<string, string | string[] | undefined>;
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? "";
const decimal = (v: string) => (/^\d+(\.\d{1,2})?$/.test(v) ? v : "");

/** Pré-remplissage depuis l'URL (lien « Calculer la rentabilité » d'une offre). */
export function prefillFromParams(sp: Params): { form: ProfitForm; title: string } {
  const country = one(sp.country).toUpperCase();
  const origin: ProfitForm["origin"] =
    country === "" ? EMPTY_FORM.origin : EU_COUNTRIES.has(country) ? "eu" : "non_eu";
  return {
    form: {
      ...EMPTY_FORM,
      unit_price: decimal(one(sp.unit_price)),
      shipping_cost: decimal(one(sp.shipping_cost)),
      origin,
    },
    title: one(sp.title).slice(0, 200),
  };
}

export function calculatorHref(offer: {
  title: string;
  price_eur: string | null;
  shipping_amount: string | null;
  currency: string;
  country: string | null;
}): string | null {
  if (offer.price_eur === null) return null; // prix EUR inconnu : rien à pré-remplir honnêtement
  const params = new URLSearchParams({ unit_price: offer.price_eur, title: offer.title });
  // Frais de port connus seulement s'ils sont en euros (sinon : « inconnus » dans le calculateur).
  if (offer.shipping_amount !== null && offer.currency === "EUR") params.set("shipping_cost", offer.shipping_amount);
  if (offer.country) params.set("country", offer.country);
  return `/rentabilite?${params.toString()}`;
}
