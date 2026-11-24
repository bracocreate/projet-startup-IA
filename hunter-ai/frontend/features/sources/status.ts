export const STATUS_LABELS: Record<string, { text: string; cls: string; help: string }> = {
  active: { text: "Active", cls: "bg-emerald-100 text-emerald-800", help: "Test réel réussi : la collecte est autorisée." },
  needs_credentials: {
    text: "Identifiants requis",
    cls: "bg-amber-100 text-amber-800",
    help: "Renseignez les clés dans le fichier .env, redémarrez (make restart), puis testez.",
  },
  needs_approval: {
    text: "Accès à demander",
    cls: "bg-amber-100 text-amber-800",
    help: "La source refuse l'accès : une approbation de la plateforme est nécessaire (voir docs/connectors.md).",
  },
  error: { text: "Erreur", cls: "bg-red-100 text-red-800", help: "Le dernier test ou la dernière collecte a échoué." },
  degraded: { text: "Dégradée", cls: "bg-amber-100 text-amber-800", help: "Données partiellement invalides lors de la dernière collecte." },
  disabled: { text: "Désactivée", cls: "bg-slate-100 text-slate-700", help: "Collecte suspendue." },
  blocked_by_terms: { text: "Bloquée (CGU)", cls: "bg-red-100 text-red-800", help: "Interdite par les conditions d'utilisation." },
  planned: { text: "Prévue", cls: "bg-slate-100 text-slate-700", help: "Pas encore testée." },
};

export const NOT_TESTED = { text: "Jamais testée", cls: "bg-slate-100 text-slate-700", help: "Lancez le test de connexion." };
