/** État du formulaire (chaînes saisies) et conversion vers la requête API. Vide = inconnu. */
export type ProfitForm = {
  unit_price: string;
  quantity: string;
  shipping_cost: string;
  origin: "eu" | "non_eu";
  article_categories: string;
  vat_status: "included" | "not_included" | "unknown";
  customs_duty_rate_pct: string;
  payment_fee_pct: string;
  other_fixed_costs: string;
  prep_cost_per_unit: string;
  defect_rate_pct: string;
  resale_low: string;
  resale_central: string;
  resale_high: string;
  selling_fee_pct: string;
  selling_fee_fixed_per_unit: string;
  selling_shipping_per_unit: string;
  target_roi_pct: string;
  branded: boolean;
};

export const EMPTY_FORM: ProfitForm = {
  unit_price: "",
  quantity: "1",
  shipping_cost: "",
  origin: "eu",
  article_categories: "1",
  vat_status: "unknown",
  customs_duty_rate_pct: "",
  payment_fee_pct: "0",
  other_fixed_costs: "0",
  prep_cost_per_unit: "0",
  defect_rate_pct: "0",
  resale_low: "",
  resale_central: "",
  resale_high: "",
  selling_fee_pct: "0",
  selling_fee_fixed_per_unit: "0",
  selling_shipping_per_unit: "0",
  target_roi_pct: "30",
  branded: false,
};

/** Accepte la virgule française ; vide → null (inconnu), jamais 0. */
export function num(value: string): string | null {
  const v = value.trim().replace(",", ".");
  return v === "" ? null : v;
}

export function toRequest(f: ProfitForm): Record<string, unknown> {
  const zeroIfEmpty = (v: string) => num(v) ?? "0";
  return {
    unit_price: num(f.unit_price),
    quantity: Number(f.quantity || "1"),
    shipping_cost: num(f.shipping_cost),
    origin: f.origin,
    article_categories: Number(f.article_categories || "1"),
    vat_status: f.vat_status,
    customs_duty_rate_pct: num(f.customs_duty_rate_pct),
    payment_fee_pct: zeroIfEmpty(f.payment_fee_pct),
    other_fixed_costs: zeroIfEmpty(f.other_fixed_costs),
    prep_cost_per_unit: zeroIfEmpty(f.prep_cost_per_unit),
    defect_rate_pct: zeroIfEmpty(f.defect_rate_pct),
    resale_low: num(f.resale_low),
    resale_central: num(f.resale_central),
    resale_high: num(f.resale_high),
    selling_fee_pct: zeroIfEmpty(f.selling_fee_pct),
    selling_fee_fixed_per_unit: zeroIfEmpty(f.selling_fee_fixed_per_unit),
    selling_shipping_per_unit: zeroIfEmpty(f.selling_shipping_per_unit),
    target_roi_pct: zeroIfEmpty(f.target_roi_pct),
    branded: f.branded,
  };
}
