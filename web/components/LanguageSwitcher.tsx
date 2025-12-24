"use client";

import {usePathname, useRouter} from "next/navigation";
import {useLocale} from "next-intl";
import {Languages} from "lucide-react";

const LOCALES = [
  {code: "ar", label: "العربية"},
  {code: "en", label: "English"},
  {code: "ur", label: "Urdu"},
  {code: "hi", label: "Hindi"},
  {code: "fil", label: "Filipino"}
];

export default function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const locale = useLocale();

  function changeLocale(nextLocale: string) {
    // pathname looks like: /ar/home or /en/upload ...
    const segments = pathname.split("/");
    segments[1] = nextLocale; // replace locale segment
    router.push(segments.join("/"));
  }

  return (
    <div className="flex items-center gap-2">
      <Languages className="h-5 w-5 text-[color:var(--primary)]" />
      <select
        value={locale}
        onChange={(e) => changeLocale(e.target.value)}
        className="rounded-xl border border-[color:var(--border)] bg-white px-3 py-2 text-sm text-[color:var(--text)] outline-none focus:ring-2 focus:ring-[color:var(--ai)]"
      >
        {LOCALES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </div>
  );
}
