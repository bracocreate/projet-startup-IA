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
