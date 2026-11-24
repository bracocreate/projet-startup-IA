import type { Metadata } from "next";
import { SettingsView } from "@/features/settings/SettingsView";
import type { UserSettings } from "@/lib/api";
import { fetchInitial } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Paramètres" };

export default async function SettingsPage() {
  const initialData = await fetchInitial<UserSettings>("/settings");
  return <SettingsView initialData={initialData} />;
}
