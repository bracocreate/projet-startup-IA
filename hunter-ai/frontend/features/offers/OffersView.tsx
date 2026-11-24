"use client";

import { usePathname, useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import { Banner, Loading, PageHeader } from "@/components/ui";
import { OfferCard } from "@/features/offers/OfferCard";
import { apiPath, filtersToQuery, type OfferFilters, PAGE_SIZE } from "@/features/offers/filters";
import { api, ApiError, type OfferPage } from "@/lib/api";

// La page remonte ce composant (clé = filtres) à chaque navigation : le brouillon repart des filtres.
export function OffersView({ filters, initialData = null }: { filters: OfferFilters; initialData?: OfferPage | null }) {
  const router = useRouter();
  const pathname = usePathname();
  const [clientData, setClientData] = useState<OfferPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState(filters);
  const data = initialData ?? clientData;
  const path = apiPath(filters);

  useEffect(() => {
    if (initialData !== null) return;
    setError(null);
    api
      .get<OfferPage>(path)
      .then(setClientData)
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : "Erreur inattendue."));
  }, [initialData, path]);

  // Les filtres vivent dans l'URL : ils survivent au rechargement et peuvent être partagés.
  const navigate = (f: OfferFilters) => {
    const qs = filtersToQuery(f);
    router.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    navigate({ ...draft, q: draft.q.trim(), offset: 0 });
  };

  const renderResults = () => {
    if (!data) return null;
    if (data.total === 0) {
      return (
        <Banner tone="info">
          Aucune offre ne correspond. Les offres apparaissent ici après une collecte : chargez les données DEMO depuis
          la vue d&apos;ensemble, ou attendez l&apos;activation du premier connecteur réel.
        </Banner>
      );
    }
    const last = Math.min(data.offset + data.items.length, data.total);
    return (
      <>
        <p className="text-sm text-slate-600" aria-live="polite">
          {data.offset + 1}–{last} sur {data.total} offre(s)
        </p>
        <div className="space-y-3">
          {data.items.map((o) => (
            <OfferCard key={o.id} offer={o} />
          ))}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={filters.offset === 0}
            onClick={() => navigate({ ...filters, offset: Math.max(0, filters.offset - PAGE_SIZE) })}
            className="rounded-md border border-slate-300 bg-white px-3 py-1 text-sm disabled:opacity-40"
          >
            ← Précédentes
          </button>
          <button
            type="button"
            disabled={last >= data.total}
            onClick={() => navigate({ ...filters, offset: filters.offset + PAGE_SIZE })}
            className="rounded-md border border-slate-300 bg-white px-3 py-1 text-sm disabled:opacity-40"
          >
            Suivantes →
          </button>
        </div>
      </>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recherche mondiale"
        subtitle="Offres déjà collectées dans les sources autorisées. La recherche en direct dans les sources arrivera avec le premier connecteur réel."
      />
      <form onSubmit={onSubmit} className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-4">
        <label className="text-sm sm:col-span-2">
          <span className="mb-1 block font-medium">Mots-clés</span>
          <input
            type="search"
            value={draft.q}
            maxLength={200}
            onChange={(e) => setDraft({ ...draft, q: e.target.value })}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium">Disponibilité</span>
          <select
            value={draft.availability}
            onChange={(e) => setDraft({ ...draft, availability: e.target.value as OfferFilters["availability"] })}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="">Toutes</option>
            <option value="in_stock">En stock</option>
            <option value="out_of_stock">Rupture</option>
            <option value="unknown">À confirmer</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium">Tri</span>
          <select
            value={draft.sort}
            onChange={(e) => setDraft({ ...draft, sort: e.target.value as OfferFilters["sort"] })}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="recent">Vérifiées récemment</option>
            <option value="price_eur_asc">Prix EUR croissant</option>
            <option value="price_eur_desc">Prix EUR décroissant</option>
          </select>
        </label>
        <div className="sm:col-span-4">
          <button
            type="submit"
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Rechercher
          </button>
        </div>
      </form>
      {error && <Banner tone="error">{error}</Banner>}
      {!data && !error && <Loading label="Chargement des offres…" />}
      {renderResults()}
    </div>
  );
}
