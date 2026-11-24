export type NavItem = {
  label: string;
  href: string;
  /** Phase de la roadmap où la page devient fonctionnelle. */
  phase: number;
  available: boolean;
};

const soon = (label: string, slug: string, phase: number): NavItem => ({
  label,
  href: `/bientot/${slug}`,
  phase,
  available: false,
});

export const NAV_ITEMS: NavItem[] = [
  { label: "Vue d'ensemble", href: "/", phase: 1, available: true },
  soon("Meilleures affaires", "meilleures-affaires", 4),
  { label: "Recherche mondiale", href: "/recherche", phase: 3, available: true },
  soon("Market Intelligence", "market-intelligence", 6),
  soon("Tendances", "tendances", 6),
  soon("Découvertes IA", "decouvertes", 7),
  { label: "Sites et fournisseurs", href: "/sources", phase: 3, available: true },
  soon("Comparateur de prix", "comparateur", 4),
  soon("Listes de surveillance", "surveillance", 3),
  soon("Lots et achats", "lots", 5),
  soon("Résultats de revente", "revente", 9),
  soon("Historique", "historique", 4),
  soon("Notifications", "notifications", 8),
  { label: "Paramètres", href: "/parametres", phase: 1, available: true },
  { label: "Santé du système", href: "/sante", phase: 1, available: true },
];

export function findNavItemBySlug(slug: string): NavItem | undefined {
  return NAV_ITEMS.find((i) => i.href === `/bientot/${slug}`);
}
