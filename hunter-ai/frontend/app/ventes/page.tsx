import type { Metadata } from "next";
import { ResaleView } from "@/features/resale/ResaleView";
import type { ResaleRecord } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Résultats de revente" };

export default async function ResalePage() {
  const initialData = await fetchInitial<{ items: ResaleRecord[]; total: number }>("/resale-records?limit=100");
  return <ResaleView initialData={initialData} />;
}
