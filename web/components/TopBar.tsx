"use client";

import Image from "next/image";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function TopBar() {
  const locale = useLocale();
  const t = useTranslations("Nav");

  const items = [
    { href: `/${locale}/home`, label: t("home") },
    { href: `/${locale}/upload`, label: t("upload") },
    { href: `/${locale}/contract-qa`, label: t("qa") },
    { href: `/${locale}/summary`, label: t("summary") },
    { href: `/${locale}/general`, label: t("general") }
  ];

  return (
    <header className="sticky top-0 z-20 border-b bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-6xl px-6 py-3 flex flex-wrap items-center gap-2 justify-between">
        <Link href={`/${locale}/home`} className="flex items-center gap-2">
          <Image src="/daleel-logo.png" alt="Daleel" width={34} height={34} />
          <span className="font-extrabold text-[color:var(--primary)]">دليل</span>
        </Link>

        <nav className="flex flex-wrap gap-2">
          {items.map((it) => (
            <Link
              key={it.href}
              href={it.href}
              className="rounded-xl px-4 py-2 text-sm font-bold border transition hover:bg-gray-50"
              style={{ borderColor: "var(--border)", color: "var(--primary)" }}
            >
              {it.label}
            </Link>
          ))}
        </nav>

        {/* language icon/button */}
        <div className="flex items-center">
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
