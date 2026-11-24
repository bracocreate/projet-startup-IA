from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.models import Availability, Condition
from app.services.normalization import (
    NormalizationError,
    clean_text,
    convert_to_eur,
    normalize_amount,
    normalize_availability,
    normalize_condition,
    normalize_country,
    normalize_currency,
    normalize_gtin,
    normalize_url,
    text_key,
    to_utc,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2000000000015", "02000000000015"),  # EAN-13 valide, complété à 14 chiffres
        ("200-0000-000015", "02000000000015"),  # tirets tolérés
        ("96385074", "00000096385074"),  # EAN-8 valide
        ("2000000000016", None),  # clé de contrôle fausse
        ("12345", None),  # longueur invalide
        ("ABC0000000015", None),
        (None, None),
    ],
)
def test_normalize_gtin(raw, expected):
    assert normalize_gtin(raw) == expected


def test_text_helpers():
    assert clean_text("  Veste   DEMO \n B7 ") == "Veste DEMO B7"
    assert clean_text("   ") is None
    assert clean_text("abcdef", 3) == "abc"
    assert text_key(" Beta  DEMO ") == text_key("beta demo") == "beta demo"


def test_currency_and_country():
    assert normalize_currency(" usd ") == "USD"
    with pytest.raises(NormalizationError):
        normalize_currency("EURO")
    assert normalize_country("uk") == "GB"
    assert normalize_country("fr") == "FR"
    assert normalize_country("France") is None
    assert normalize_country(None) is None


def test_amounts():
    assert normalize_amount(Decimal("10.005")) == Decimal("10.01")
    assert normalize_amount(None) is None
    with pytest.raises(NormalizationError):
        normalize_amount(None, required=True)
    with pytest.raises(NormalizationError):
        normalize_amount(Decimal("-1"))
    with pytest.raises(NormalizationError):
        normalize_amount(Decimal("NaN"))


def test_dates_are_utc_and_naive_dates_refused():
    paris = timezone(timedelta(hours=1))
    assert to_utc(datetime(2026, 11, 24, 7, 0, tzinfo=paris)) == datetime(
        2026, 11, 24, 6, 0, tzinfo=UTC
    )
    with pytest.raises(NormalizationError):
        to_utc(datetime(2026, 11, 24, 7, 0))


def test_availability_and_condition():
    assert normalize_availability("In Stock") == Availability.in_stock
    assert normalize_availability("sold-out") == Availability.out_of_stock
    assert normalize_availability("bientôt") == Availability.unknown
    assert normalize_availability(None) == Availability.unknown
    assert normalize_condition("Reconditionné") == Condition.refurbished
    assert normalize_condition("neuf") == Condition.new
    assert normalize_condition("???") == Condition.unknown


def test_url_must_be_http():
    assert normalize_url(" https://example.com/x ") == "https://example.com/x"
    for bad in ("javascript:alert(1)", "ftp://x", ""):
        with pytest.raises(NormalizationError):
            normalize_url(bad)


def test_currency_conversion_never_invents_a_rate():
    assert convert_to_eur(Decimal("10.00"), "EUR", {}) == (Decimal("10.00"), Decimal(1))
    assert convert_to_eur(Decimal("10.00"), "USD", {}) == (None, None)
    assert convert_to_eur(Decimal("10.00"), "USD", {"USD": Decimal("0.95")}) == (
        Decimal("9.50"),
        Decimal("0.95"),
    )
    assert convert_to_eur(None, "USD", {"USD": Decimal("0.95")}) == (None, None)


def test_fx_rates_setting_parsing():
    assert Settings(fx_rates_to_eur="").fx_rate_map == {}
    assert Settings(fx_rates_to_eur="usd=0.95, GBP=1.18").fx_rate_map == {
        "USD": Decimal("0.95"),
        "GBP": Decimal("1.18"),
    }
    for bad in ("USD=abc", "USD=-1", "DOLLAR=1"):
        with pytest.raises(ValueError):
            _ = Settings(fx_rates_to_eur=bad).fx_rate_map
