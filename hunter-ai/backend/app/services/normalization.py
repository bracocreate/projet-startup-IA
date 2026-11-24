"""Normalisation des offres brutes : textes, codes GTIN, devises, dates, disponibilité.

Fonctions pures et testables. Règle centrale : une valeur inconnue reste inconnue (None) ;
aucune conversion ni valeur n'est inventée pour compléter un calcul.
"""

import re
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from app.models.catalog import Availability, Condition

_SPACES = re.compile(r"\s+")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_COUNTRY = re.compile(r"^[A-Z]{2}$")
CENT = Decimal("0.01")

_AVAILABILITY = {
    "in_stock": Availability.in_stock,
    "instock": Availability.in_stock,
    "available": Availability.in_stock,
    "out_of_stock": Availability.out_of_stock,
    "outofstock": Availability.out_of_stock,
    "sold_out": Availability.out_of_stock,
}
_CONDITION = {
    "new": Condition.new,
    "neuf": Condition.new,
    "used": Condition.used,
    "occasion": Condition.used,
    "refurbished": Condition.refurbished,
    "reconditionne": Condition.refurbished,
}


class NormalizationError(ValueError):
    """Offre inutilisable (champ obligatoire absent ou invalide)."""


def clean_text(value: str | None, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    text = _SPACES.sub(" ", value).strip()
    if not text:
        return None
    return text[:max_len] if max_len else text


def text_key(value: str | None) -> str | None:
    """Clé de comparaison : minuscules, espaces normalisés (marques, références, marchands)."""
    text = clean_text(value)
    return text.casefold() if text else None


def gtin_check_digit(body: str) -> int:
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10


def normalize_gtin(value: str | None) -> str | None:
    """GTIN-8/12/13/14 valide (clé de contrôle vérifiée), complété à 14 chiffres. Sinon None."""
    if value is None:
        return None
    digits = re.sub(r"[\s-]", "", value)
    if not digits.isdigit() or len(digits) not in (8, 12, 13, 14):
        return None
    if gtin_check_digit(digits[:-1]) != int(digits[-1]):
        return None
    return digits.zfill(14)


def normalize_currency(value: str) -> str:
    code = (value or "").strip().upper()
    if not _CURRENCY.match(code):
        raise NormalizationError(f"Devise invalide : {value!r}")
    return code


def normalize_country(value: str | None) -> str | None:
    code = (value or "").strip().upper()
    if code == "UK":  # usage courant, code ISO officiel : GB
        code = "GB"
    return code if _COUNTRY.match(code) else None


def normalize_amount(value: Decimal | None, *, required: bool = False) -> Decimal | None:
    if value is None:
        if required:
            raise NormalizationError("Prix absent")
        return None
    amount = Decimal(value)
    if not amount.is_finite() or amount < 0:
        raise NormalizationError(f"Montant invalide : {value}")
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise NormalizationError("Date sans fuseau horaire : refusée (ambiguë)")
    return value.astimezone(UTC)


def normalize_availability(value: str | None) -> Availability:
    key = re.sub(r"[\s-]", "_", (value or "").strip().casefold())
    return _AVAILABILITY.get(key, Availability.unknown)


def normalize_condition(value: str | None) -> Condition:
    key = (value or "").strip().casefold().replace("é", "e")
    return _CONDITION.get(key, Condition.unknown)


def normalize_url(value: str) -> str:
    url = (value or "").strip()
    if not url.lower().startswith("https://") and not url.lower().startswith("http://"):
        raise NormalizationError("URL source absente ou non HTTP(S)")
    return url[:2000]


def convert_to_eur(
    amount: Decimal | None, currency: str, rates_to_eur: dict[str, Decimal]
) -> tuple[Decimal | None, Decimal | None]:
    """Renvoie (montant EUR, taux utilisé). (None, None) si le taux est inconnu."""
    if amount is None:
        return None, None
    if currency == "EUR":
        return amount, Decimal(1)
    rate = rates_to_eur.get(currency)
    if rate is None:
        return None, None
    return (amount * rate).quantize(CENT, rounding=ROUND_HALF_UP), rate
