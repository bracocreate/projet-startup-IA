"""Profit Engine : calculs déterministes, inconnus jamais inventés, règles d'import 2026."""

from decimal import Decimal as D  # noqa: N817

import pytest

from app.engines.profit_engine.calculator import ProfitInputs, calculate


def line(result, key):
    return next(x for x in result.lines if x.key == key)


def test_simple_eu_purchase_all_known():
    r = calculate(
        ProfitInputs(
            unit_price=D("20"),
            quantity=5,
            shipping_cost=D("10"),
            origin="eu",
            resale_low=D("30"),
            resale_central=D("35"),
            resale_high=D("40"),
            selling_fee_pct=D("5"),
        )
    )
    assert r.landed_cost.low == r.landed_cost.high == D("110.00")
    assert r.landed_cost_per_unit.high == D("22.00")
    central = next(s for s in r.scenarios if s.key == "central")
    # CA 5×35 = 175 ; frais 5 % = 8,75 ; bénéfice = 175 − 8,75 − 110 = 56,25
    assert (central.revenue, central.selling_costs, central.profit) == (
        D("175.00"),
        D("8.75"),
        D("56.25"),
    )
    assert central.roi_pct == D("51.14")  # 56,25 / 110
    assert central.margin_pct == D("32.14")  # 56,25 / 175 : marge ≠ ROI
    assert r.break_even_price == D("23.16")  # 22 / 0,95
    assert r.missing == [] and r.warnings == []
    assert line(r, "purchase").basis == "5 × 20,00 €"  # format français


def test_unknown_shipping_makes_total_unknown_never_zero():
    r = calculate(ProfitInputs(unit_price=D("10"), resale_central=D("20")))
    assert line(r, "shipping").status == "unknown"
    assert r.landed_cost is None and r.scenarios == [] and r.break_even_price is None
    assert "Transport jusqu'à vous" in r.missing


def test_free_shipping_is_zero_not_unknown():
    r = calculate(ProfitInputs(unit_price=D("10"), shipping_cost=D("0")))
    assert line(r, "shipping").status == "known"
    assert r.landed_cost.high == D("10.00")


def test_non_eu_small_parcel_flat_duty_and_fees_per_category():
    # 3 t-shirts + 1 paire de chaussures = 2 catégories (exemple service-public.gouv.fr).
    r = calculate(
        ProfitInputs(
            unit_price=D("10"),
            quantity=4,
            shipping_cost=D("8"),
            origin="non_eu",
            article_categories=2,
            vat_status="not_included",
        )
    )
    assert line(r, "customs_duty").amount.high == D("6.00")  # 3 € × 2
    assert line(r, "processing_fee").amount.high == D("4.00")  # 2 € × 2
    # TVA 20 % × (40 + 8 + 6) = 10,80
    assert line(r, "import_vat").amount.high == D("10.80")
    assert r.landed_cost.high == D("68.80")
    assert any("validation douanière" in w for w in r.warnings)


def test_vat_included_by_ioss_seller_is_not_added_twice():
    r = calculate(
        ProfitInputs(
            unit_price=D("10"), shipping_cost=D("5"), origin="non_eu", vat_status="included"
        )
    )
    assert line(r, "import_vat").amount.high == D("0.00")
    assert r.landed_cost.high == D("20.00")  # 10 + 5 + 3 + 2


def test_unknown_vat_status_gives_a_range_and_prudent_scenarios():
    r = calculate(
        ProfitInputs(
            unit_price=D("10"),
            shipping_cost=D("5"),
            origin="non_eu",
            resale_low=D("25"),
            resale_central=D("25"),
            resale_high=D("25"),
        )
    )
    vat = line(r, "import_vat")
    assert vat.status == "range" and (vat.amount.low, vat.amount.high) == (D("0.00"), D("3.60"))
    assert (r.landed_cost.low, r.landed_cost.high) == (D("20.00"), D("23.60"))
    by_key = {s.key: s for s in r.scenarios}
    assert by_key["pessimistic"].cost_used == D("23.60")  # coût haut
    assert by_key["central"].cost_used == D("23.60")  # prudent
    assert by_key["optimistic"].cost_used == D("20.00")  # coût bas
    assert any("IOSS" in m for m in r.missing)


def test_large_parcel_requires_customs_rate():
    base = dict(
        unit_price=D("2"),
        quantity=100,
        shipping_cost=D("40"),
        origin="non_eu",
        vat_status="not_included",
    )
    unknown = calculate(ProfitInputs(**base))
    assert line(unknown, "customs_duty").amount is None and unknown.landed_cost is None
    known = calculate(ProfitInputs(**base, customs_duty_rate_pct=D("12")))
    assert line(known, "customs_duty").amount.high == D("28.80")  # 12 % × (200 + 40)
    assert line(known, "processing_fee").amount.high == D("2.00")  # pas de seuil de valeur


def test_defects_reduce_sellable_units():
    r = calculate(
        ProfitInputs(
            unit_price=D("5"),
            quantity=10,
            shipping_cost=D("0"),
            defect_rate_pct=D("20"),
            resale_central=D("10"),
        )
    )
    assert r.sellable_units == D("8.00")
    assert r.cost_per_sellable_unit.high == D("6.25")  # 50 / 8
    assert next(s for s in r.scenarios if s.key == "central").profit == D("30.00")


def test_division_safety():
    r = calculate(
        ProfitInputs(
            unit_price=D("0"),
            shipping_cost=D("0"),
            defect_rate_pct=D("100"),
            resale_central=D("10"),
            selling_fee_pct=D("100"),
        )
    )
    central = r.scenarios[0]
    assert central.roi_pct is None and central.margin_pct is None
    assert r.break_even_price is None and r.cost_per_sellable_unit is None


def test_max_purchase_price_reaches_target_roi():
    inputs = ProfitInputs(
        unit_price=D("10"), shipping_cost=D("0"), resale_central=D("26"), target_roi_pct=D("30")
    )
    r = calculate(inputs)
    # ROI ≥ 30 % : (26 − p) / p ≥ 0,30  ⇔  p ≤ 20
    assert r.max_unit_price_for_target == D("20.00")


def test_branded_non_eu_purchase_warns_counterfeit():
    r = calculate(
        ProfitInputs(unit_price=D("15"), shipping_cost=D("5"), origin="non_eu", branded=True)
    )
    assert any("contrefaçon" in w for w in r.warnings)


@pytest.mark.parametrize("qty", [1, 3, 50])
def test_deterministic(qty):
    inputs = ProfitInputs(
        unit_price=D("3.33"),
        quantity=qty,
        shipping_cost=D("7.77"),
        origin="non_eu",
        vat_status="unknown",
        resale_central=D("9.99"),
    )
    assert calculate(inputs) == calculate(inputs)
