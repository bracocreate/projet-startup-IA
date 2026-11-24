export type OfferFilters = {
  q: string;
  availability: "" | "in_stock" | "out_of_stock" | "unknown";
  sort: "recent" | "price_eur_asc" | "price_eur_desc";
  offset: number;
};

export const PAGE_SIZE = 20;

type SearchParams = Record<string, string | string[] | undefined>;

const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? "";

/** Lit les filtres depuis l'URL, en ignorant toute valeur inattendue. */
export function parseFilters(sp: SearchParams): OfferFilters {
  const availability = one(sp.availability);
  const sort = one(sp.sort);
  const offset = Number.parseInt(one(sp.offset), 10);
  return {
    q: one(sp.q).slice(0, 200),
    availability: ["in_stock", "out_of_stock", "unknown"].includes(availability)
      ? (availability as OfferFilters["availability"])
      : "",
    sort: ["price_eur_asc", "price_eur_desc"].includes(sort) ? (sort as OfferFilters["sort"]) : "recent",
    offset: Number.isFinite(offset) && offset > 0 ? offset : 0,
  };
}

export function filtersToQuery(f: OfferFilters): string {
  const params = new URLSearchParams();
  if (f.q) params.set("q", f.q);
  if (f.availability) params.set("availability", f.availability);
  if (f.sort !== "recent") params.set("sort", f.sort);
  if (f.offset > 0) params.set("offset", String(f.offset));
  return params.toString();
}

export function apiPath(f: OfferFilters): string {
  const qs = filtersToQuery(f);
  return `/offers?limit=${PAGE_SIZE}${qs ? `&${qs}` : ""}`;
}
