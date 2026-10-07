"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/rbac", label: "RBAC" },
  { href: "/abac", label: "ABAC" },
  { href: "/pbac", label: "PBAC" },
];

export function ModelTabs() {
  const pathname = usePathname();
  return (
    <div className="model-tabs">
      {TABS.map((t) => (
        <Link
          key={t.href}
          href={t.href}
          className={pathname === t.href ? "active" : ""}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}
