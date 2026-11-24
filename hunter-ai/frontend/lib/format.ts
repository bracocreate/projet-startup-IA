export function formatDateTime(iso: string | null, timeZone = "Europe/Paris"): string {
  if (!iso) return "jamais";
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
  }).format(new Date(iso));
}

export function formatEur(value: string | number | null): string {
  if (value === null || value === "") return "non défini";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(Number(value));
}

export function formatMoney(value: string | null, currency: string): string {
  if (value === null) return "non déterminé";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency }).format(Number(value));
}

export function formatShipping(value: string | null, currency: string): string {
  if (value === null) return "frais de livraison inconnus";
  if (Number(value) === 0) return "livraison gratuite";
  return `+ ${formatMoney(value, currency)} de livraison`;
}

export const AVAILABILITY_LABELS = {
  in_stock: "En stock",
  out_of_stock: "Rupture",
  unknown: "Disponibilité à confirmer",
} as const;

export function formatRange(r: { low: string; high: string } | null): string {
  if (r === null) return "à vérifier";
  if (r.low === r.high) return formatMoney(r.low, "EUR");
  return `${formatMoney(r.low, "EUR")} à ${formatMoney(r.high, "EUR")}`;
}

export function formatPct(value: string | null): string {
  if (value === null) return "non calculable";
  return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(Number(value))} %`;
}
