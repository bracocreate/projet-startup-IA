import { notFound } from "next/navigation";
import { Banner, PageHeader } from "@/components/ui";
import { findNavItemBySlug } from "@/lib/nav";

export default async function ComingSoonPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const item = findNavItemBySlug(slug);
  if (!item) notFound();
  return (
    <div className="space-y-6">
      <PageHeader title={item.label} />
      <Banner tone="info">
        Cette section n&apos;est pas encore disponible. Elle est prévue en <strong>Phase {item.phase}</strong> de la
        feuille de route. Aucune donnée n&apos;est affichée tant que la fonctionnalité n&apos;est pas réellement
        implémentée et testée.
      </Banner>
    </div>
  );
}
