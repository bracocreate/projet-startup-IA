import type { Metadata } from "next";
import { apiPath, parseFilters } from "@/features/offers/filters";
import { OffersView } from "@/features/offers/OffersView";
import type { OfferPage } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Recherche mondiale" };

type SearchParams = Record<string, string | string[] | undefined>;

export default async function SearchPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const filters = parseFilters(await searchParams);
  const path = apiPath(filters);
  const initialData = await fetchInitial<OfferPage>(path);
  return <OffersView key={path} filters={filters} initialData={initialData} />;
}
