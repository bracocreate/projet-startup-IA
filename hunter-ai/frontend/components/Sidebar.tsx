"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { NAV_ITEMS } from "@/lib/nav";

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
        <span className="font-semibold tracking-tight">HUNTER AI</span>
        <button
          type="button"
          className="rounded-md border border-slate-300 px-3 py-1 text-sm"
          aria-expanded={open}
          aria-controls="main-nav"
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>
      <nav
        id="main-nav"
        aria-label="Navigation principale"
        className={`${open ? "block" : "hidden"} w-full shrink-0 border-r border-slate-200 bg-white md:block md:w-64`}
      >
        <div className="hidden px-5 py-5 md:block">
          <p className="text-lg font-bold tracking-tight">HUNTER AI</p>
          <p className="text-xs text-slate-500">Veille commerciale &amp; sourcing</p>
        </div>
        <ul className="space-y-0.5 px-2 pb-4">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  onClick={() => setOpen(false)}
                  className={`flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                    active ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <span>{item.label}</span>
                  {!item.available && (
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
                      Phase {item.phase}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
