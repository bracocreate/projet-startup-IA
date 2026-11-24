import type { Metadata } from "next";
import { SourcesView } from "@/features/sources/SourcesView";
import type { ConnectorInfo } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Sites et fournisseurs" };

export default async function SourcesPage() {
  const initialData = await fetchInitial<ConnectorInfo[]>("/connectors");
  return <SourcesView initialData={initialData} />;
}
