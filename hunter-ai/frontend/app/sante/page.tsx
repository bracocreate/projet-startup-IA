import type { Metadata } from "next";
import { HealthView } from "@/features/health/HealthView";
import type { SystemStatus } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Santé du système" };

export default async function HealthPage() {
  const initialData = await fetchInitial<SystemStatus>("/system/status");
  return <HealthView initialData={initialData} />;
}
