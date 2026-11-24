"use client";

import { Banner } from "@/components/ui";

// Filet de sécurité : une erreur inattendue d'affichage ne laisse jamais une page blanche.
export default function RouteError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Banner tone="error">
      <p>Une erreur inattendue a empêché l&apos;affichage de cette page.</p>
      <button type="button" onClick={reset} className="mt-2 underline">
        Réessayer
      </button>
    </Banner>
  );
}
