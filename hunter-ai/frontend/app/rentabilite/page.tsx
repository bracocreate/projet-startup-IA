import type { Metadata } from "next";
import { ProfitCalculator } from "@/features/profit/ProfitCalculator";
import { prefillFromParams } from "@/features/profit/prefill";

export const metadata: Metadata = { title: "Lots et achats" };

type SearchParams = Record<string, string | string[] | undefined>;

export default async function ProfitPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { form, title } = prefillFromParams(await searchParams);
  return <ProfitCalculator key={JSON.stringify(form)} initialForm={form} sourceTitle={title} />;
}
