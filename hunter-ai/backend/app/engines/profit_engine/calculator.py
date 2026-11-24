"""Profit Engine : coût rendu, rentabilité par scénario, seuils (cahier des charges §9).

Fonctions pures et déterministes (aucun accès réseau ni base de données, aucun modèle de langage).
Chaque montant est soit connu, soit une fourchette [bas, haut], soit inconnu (None) : un inconnu
n'est jamais remplacé par une valeur inventée, il rend le total « à vérifier ».

Règles d'importation hors UE retenues (vérifiées le 24/11/2026, douane.gouv.fr et
service-public.gouv.fr — estimation indicative, validation douanière nécessaire) :
- droit de douane forfaitaire de 3 € par catégorie d'article pour un envoi ≤ 150 €
  (depuis le 1er juillet 2026) ; au-delà de 150 €, tarif douanier commun (taux à fournir) ;
- frais de traitement de 2 € par catégorie d'article, sans seuil de valeur (depuis le
  1er novembre 2026) ;
- TVA à l'importation (20 % par défaut) sur marchandise + transport + droits, sauf si elle est
  déjà incluse dans le prix (vendeur sous régime IOSS). Statut inconnu → fourchette.
"""

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Literal

RULES_VERSION = "2026-11-24"
CENT = Decimal("0.01")
HUNDRED = Decimal(100)
ZERO = Decimal(0)

FLAT_DUTY_THRESHOLD_EUR = Decimal(150)
FLAT_DUTY_PER_CATEGORY_EUR = Decimal(3)
PROCESSING_FEE_PER_CATEGORY_EUR = Decimal(2)

Origin = Literal["eu", "non_eu"]
VatStatus = Literal["included", "not_included", "unknown"]
LineStatus = Literal["known", "range", "unknown"]


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def fr(value: Decimal) -> str:
    """Montant au format français pour les explications (1,40)."""
    return str(money(value)).replace(".", ",")


@dataclass(frozen=True)
class Amount:
    """Montant connu (low == high) ou fourchette."""

    low: Decimal
    high: Decimal

    @staticmethod
    def exact(value: Decimal) -> "Amount":
        return Amount(value, value)

    def __add__(self, other: "Amount") -> "Amount":
        return Amount(self.low + other.low, self.high + other.high)

    @property
    def is_exact(self) -> bool:
        return self.low == self.high

    def rounded(self) -> "Amount":
        return Amount(money(self.low), money(self.high))


@dataclass(frozen=True)
class CostLine:
    key: str
    label: str
    amount: Amount | None  # None = inconnu
    basis: str

    @property
    def status(self) -> LineStatus:
        if self.amount is None:
            return "unknown"
        return "known" if self.amount.is_exact else "range"


@dataclass(frozen=True)
class ProfitInputs:
    unit_price: Decimal
    quantity: int = 1
    # Transport total de l'envoi jusqu'à vous. None = inconnu (≠ 0 = gratuit).
    shipping_cost: Decimal | None = None
    origin: Origin = "eu"
    article_categories: int = 1
    vat_status: VatStatus = "unknown"
    vat_rate_pct: Decimal = Decimal(20)
    # Taux du tarif douanier commun pour un envoi > 150 € (None = inconnu).
    customs_duty_rate_pct: Decimal | None = None
    payment_fee_pct: Decimal = ZERO
    other_fixed_costs: Decimal = ZERO
    prep_cost_per_unit: Decimal = ZERO
    defect_rate_pct: Decimal = ZERO
    # Prix de revente unitaire par scénario (None = non renseigné).
    resale_low: Decimal | None = None
    resale_central: Decimal | None = None
    resale_high: Decimal | None = None
    selling_fee_pct: Decimal = ZERO
    selling_fee_fixed_per_unit: Decimal = ZERO
    selling_shipping_per_unit: Decimal = ZERO
    target_roi_pct: Decimal = Decimal(30)
    branded: bool = False


@dataclass(frozen=True)
class Scenario:
    key: Literal["pessimistic", "central", "optimistic"]
    resale_price: Decimal
    cost_used: Decimal
    revenue: Decimal
    selling_costs: Decimal
    profit: Decimal
    roi_pct: Decimal | None
    margin_pct: Decimal | None


@dataclass(frozen=True)
class ProfitResult:
    lines: list[CostLine]
    landed_cost: Amount | None
    landed_cost_per_unit: Amount | None
    sellable_units: Decimal
    cost_per_sellable_unit: Amount | None
    scenarios: list[Scenario]
    break_even_price: Decimal | None
    max_unit_price_for_target: Decimal | None
    missing: list[str]
    warnings: list[str] = field(default_factory=list)
    rules_version: str = RULES_VERSION


def pct(value: Decimal, rate_pct: Decimal) -> Decimal:
    return value * rate_pct / HUNDRED


def cost_lines(i: ProfitInputs) -> list[CostLine]:
    goods = i.unit_price * i.quantity
    lines = [
        CostLine(
            "purchase",
            "Prix d'achat",
            Amount.exact(goods),
            f"{i.quantity} × {fr(i.unit_price)} €",
        ),
        CostLine(
            "shipping",
            "Transport jusqu'à vous",
            None if i.shipping_cost is None else Amount.exact(i.shipping_cost),
            "Montant total de l'envoi" if i.shipping_cost is not None else "Non renseigné",
        ),
    ]
    if i.origin == "non_eu":
        lines += import_lines(i, goods)
    lines += [
        CostLine(
            "payment_fees",
            "Frais de paiement et de change",
            Amount.exact(pct(goods, i.payment_fee_pct)),
            f"{i.payment_fee_pct} % du prix d'achat",
        ),
        CostLine(
            "other_fixed",
            "Inspection, échantillons, autres frais",
            Amount.exact(i.other_fixed_costs),
            "Montant saisi",
        ),
        CostLine(
            "preparation",
            "Préparation et emballage",
            Amount.exact(i.prep_cost_per_unit * i.quantity),
            f"{i.quantity} × {fr(i.prep_cost_per_unit)} €",
        ),
    ]
    return lines


def import_lines(i: ProfitInputs, goods: Decimal) -> list[CostLine]:
    lines: list[CostLine] = []
    cats = i.article_categories
    duty: Amount | None
    if goods <= FLAT_DUTY_THRESHOLD_EUR:
        duty = Amount.exact(FLAT_DUTY_PER_CATEGORY_EUR * cats)
        duty_basis = f"Forfait 3 € × {cats} catégorie(s) d'article (envoi ≤ 150 €)"
    elif i.customs_duty_rate_pct is None or i.shipping_cost is None:
        duty = None
        duty_basis = "Envoi > 150 € : taux du tarif douanier et transport nécessaires"
    else:
        duty = Amount.exact(pct(goods + i.shipping_cost, i.customs_duty_rate_pct))
        duty_basis = f"{i.customs_duty_rate_pct} % de (marchandise + transport), envoi > 150 €"
    lines.append(CostLine("customs_duty", "Droits de douane", duty, duty_basis))
    lines.append(
        CostLine(
            "processing_fee",
            "Frais de traitement UE",
            Amount.exact(PROCESSING_FEE_PER_CATEGORY_EUR * cats),
            f"2 € × {cats} catégorie(s) d'article",
        )
    )
    vat: Amount | None
    if i.vat_status == "included":
        vat = Amount.exact(ZERO)
        vat_basis = "Déjà incluse dans le prix (vendeur IOSS)"
    elif i.shipping_cost is None or duty is None:
        vat = None
        vat_basis = "Base de calcul incomplète (transport ou droits inconnus)"
    else:
        due = pct(goods + i.shipping_cost + duty.high, i.vat_rate_pct)
        if i.vat_status == "not_included":
            vat = Amount.exact(due)
            vat_basis = f"{i.vat_rate_pct} % de (marchandise + transport + droits)"
        else:
            vat = Amount(ZERO, due)
            vat_basis = "Statut inconnu : de 0 (incluse) à la TVA complète (non incluse)"
    lines.append(CostLine("import_vat", "TVA à l'importation", vat, vat_basis))
    return lines


def total(lines: list[CostLine]) -> Amount | None:
    result = Amount.exact(ZERO)
    for line in lines:
        if line.amount is None:
            return None
        result = result + line.amount
    return result


def sellable(i: ProfitInputs) -> Decimal:
    return Decimal(i.quantity) * (HUNDRED - i.defect_rate_pct) / HUNDRED


def scenario(
    key: Literal["pessimistic", "central", "optimistic"],
    price: Decimal,
    cost: Decimal,
    units: Decimal,
    i: ProfitInputs,
) -> Scenario:
    revenue = units * price
    selling = units * (
        pct(price, i.selling_fee_pct) + i.selling_fee_fixed_per_unit + i.selling_shipping_per_unit
    )
    profit = revenue - selling - cost
    return Scenario(
        key=key,
        resale_price=money(price),
        cost_used=money(cost),
        revenue=money(revenue),
        selling_costs=money(selling),
        profit=money(profit),
        # ROI = bénéfice / coût engagé ; marge = bénéfice / chiffre d'affaires. Jamais de /0.
        roi_pct=money(profit / cost * HUNDRED) if cost > 0 else None,
        margin_pct=money(profit / revenue * HUNDRED) if revenue > 0 else None,
    )


def break_even(cost_high: Decimal, units: Decimal, i: ProfitInputs) -> Decimal | None:
    net_share = 1 - i.selling_fee_pct / HUNDRED
    if units <= 0 or net_share <= 0:
        return None
    per_unit = cost_high / units + i.selling_fee_fixed_per_unit + i.selling_shipping_per_unit
    return money(per_unit / net_share)


def central_roi(i: ProfitInputs, unit_price: Decimal) -> Decimal | None:
    """ROI du scénario central (coût prudent) pour un prix d'achat donné."""
    trial = ProfitInputs(**{**i.__dict__, "unit_price": unit_price})
    cost = total(cost_lines(trial))
    units = sellable(trial)
    if cost is None or cost.high <= 0 or units <= 0 or i.resale_central is None:
        return None
    return scenario("central", i.resale_central, cost.high, units, trial).roi_pct


def max_unit_price(i: ProfitInputs) -> Decimal | None:
    """Prix d'achat unitaire maximal pour atteindre le ROI cible (recherche au centime).

    Le coût n'est pas strictement linéaire (seuil de 150 €) : on cherche le plus haut prix,
    par pas de 1 centime, sous le prix de revente central, en vérifiant chaque candidat.
    """
    if i.resale_central is None:
        return None
    low, high = ZERO, i.resale_central
    best: Decimal | None = None
    for _ in range(40):
        mid = ((low + high) / 2).quantize(CENT, rounding=ROUND_DOWN)
        roi = central_roi(i, mid)
        if roi is None:
            return None
        if roi >= i.target_roi_pct:
            best, low = mid, mid + CENT
        else:
            high = mid - CENT
        if low > high:
            break
    # Le seuil de 150 € peut rendre la courbe non monotone : on revérifie le résultat.
    if best is not None:
        roi = central_roi(i, best)
        if roi is None or roi < i.target_roi_pct:
            return None
    return best


def missing_information(i: ProfitInputs, lines: list[CostLine]) -> list[str]:
    missing = [line.label for line in lines if line.amount is None]
    if i.origin == "non_eu" and i.vat_status == "unknown":
        missing.append("TVA incluse ou non dans le prix (régime IOSS du vendeur)")
    if i.resale_central is None:
        missing.append("Prix de revente central")
    return missing


def warnings_for(i: ProfitInputs) -> list[str]:
    warnings: list[str] = []
    if i.origin == "non_eu":
        warnings.append("Estimation indicative — validation douanière nécessaire.")
    if i.origin == "non_eu" and i.branded:
        warnings.append(
            "Article de marque acheté hors UE : risque de contrefaçon élevé (revente illégale, "
            "saisie en douane, suspension de compte). Vérifiez l'authenticité avant tout achat."
        )
    if i.defect_rate_pct >= 30:
        warnings.append("Taux de défaut élevé : la rentabilité dépend fortement de ce chiffre.")
    if i.resale_low and i.resale_high and i.resale_low > i.resale_high:
        warnings.append("Prix de revente bas supérieur au prix haut : vérifiez la saisie.")
    return warnings


def calculate(i: ProfitInputs) -> ProfitResult:
    lines = cost_lines(i)
    landed = total(lines)
    units = sellable(i)
    scenarios: list[Scenario] = []
    if landed is not None:
        plan = [
            ("pessimistic", i.resale_low, landed.high),
            ("central", i.resale_central, landed.high),
            ("optimistic", i.resale_high, landed.low),
        ]
        for key, price, cost in plan:
            if price is not None:
                scenarios.append(scenario(key, price, cost, units, i))  # type: ignore[arg-type]
    return ProfitResult(
        lines=[
            CostLine(
                line.key, line.label, line.amount.rounded() if line.amount else None, line.basis
            )
            for line in lines
        ],
        landed_cost=landed.rounded() if landed else None,
        landed_cost_per_unit=Amount(landed.low / i.quantity, landed.high / i.quantity).rounded()
        if landed
        else None,
        sellable_units=money(units),
        cost_per_sellable_unit=Amount(landed.low / units, landed.high / units).rounded()
        if landed and units > 0
        else None,
        scenarios=scenarios,
        break_even_price=break_even(landed.high, units, i) if landed else None,
        max_unit_price_for_target=max_unit_price(i) if landed else None,
        missing=missing_information(i, lines),
        warnings=warnings_for(i),
    )
