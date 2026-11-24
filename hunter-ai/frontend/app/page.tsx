import type { Metadata } from "next";
import { DashboardView } from "@/features/dashboard/DashboardView";
import type { DashboardSummary } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

// Toujours le dernier état connu : rendu à chaque requête, jamais figé au moment du build.
export const dynamic = "force-dynamic";

// Le modèle « %s · HUNTER AI » du layout ne s'applique pas à la page du même segment.
export const metadata: Metadata = { title: { absolute: "Vue d'ensemble · HUNTER AI" } };

export default async function HomePage() {
  const initialData = await fetchInitial<DashboardSummary>("/dashboard/summary");
  return <DashboardView initialData={initialData} />;
}
