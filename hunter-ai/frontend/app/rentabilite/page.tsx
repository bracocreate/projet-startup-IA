import type { Metadata } from "next";
import { ProfitCalculator } from "@/features/profit/ProfitCalculator";

export const metadata: Metadata = { title: "Lots et achats" };

export default function ProfitPage() {
  return <ProfitCalculator />;
}
