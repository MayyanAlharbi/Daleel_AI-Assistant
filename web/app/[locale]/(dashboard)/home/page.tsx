import Image from "next/image";
import Link from "next/link";
import {getTranslations} from "next-intl/server";

export default async function HomePage() {
  const t = await getTranslations("Home");

  const chips = [
    { text: t("chip1"), icon: "📄" },
    { text: t("chip2"), icon: "✨" },
    { text: t("chip3"), icon: "💬" }
  ];

  const features = [
    { title: t("f1Title"), desc: t("f1Desc"), href: "/upload", icon: "⬆️" },
    { title: t("f2Title"), desc: t("f2Desc"), href: "/contract-qa", icon: "❓" },
    { title: t("f3Title"), desc: t("f3Desc"), href: "/summary", icon: "🧾" },
    { title: t("f4Title"), desc: t("f4Desc"), href: "/general", icon: "💬" }
  ];

  return (
    <main className="min-h-screen">
      {/* HERO */}
      <section className="relative">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-24 right-24 h-72 w-72 rounded-full blur-3xl opacity-20"
               style={{ background: "var(--ai)" }} />
          <div className="absolute top-24 left-24 h-72 w-72 rounded-full blur-3xl opacity-15"
               style={{ background: "var(--gold)" }} />
        </div>

        <div className="mx-auto max-w-6xl px-6 pt-16 pb-10 text-center relative">
          <div className="flex justify-center">
            <Image src="/daleel-logo.png" alt="Daleel" width={140} height={140} priority />
          </div>

          <h1 className="mt-8 text-4xl md:text-6xl font-extrabold tracking-tight text-[color:var(--primary)]">
            {t("heroTitle1")}{" "}
            <span className="text-[color:var(--ai)]">{t("heroTitle2")}</span>
          </h1>

          <p className="mt-5 text-lg md:text-xl leading-relaxed text-[color:rgba(28,28,28,0.70)] max-w-3xl mx-auto">
            {t("heroDesc")}
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            {chips.map((c) => (
              <div key={c.text}
                className="flex items-center gap-2 rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm text-[color:rgba(28,28,28,0.80)] shadow-sm"
              >
                <span>{c.icon}</span>
                <span>{c.text}</span>
              </div>
            ))}
          </div>

          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/upload" className="rounded-2xl px-8 py-4 font-bold shadow-lg"
              style={{ background: "var(--primary)", color: "white" }}
            >
              {t("ctaUpload")}
            </Link>

            <Link href="/general" className="rounded-2xl px-8 py-4 font-bold border bg-white shadow-sm"
              style={{ borderColor: "var(--border)", color: "var(--primary)" }}
            >
              {t("ctaAsk")}
            </Link>
          </div>

          <div className="mt-10 h-px w-full bg-[color:var(--border)]" />
        </div>
      </section>

      {/* FEATURES */}
      <section className="mx-auto max-w-6xl px-6 pb-14">
        <div className="text-center mt-10">
          <h2 className="text-3xl md:text-4xl font-extrabold text-[color:var(--primary)]">
            {t("featuresTitle")}
          </h2>
          <p className="mt-3 text-lg text-[color:rgba(28,28,28,0.65)]">
            {t("featuresDesc")}
          </p>
        </div>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((f) => (
            <div key={f.title} className="rounded-3xl bg-white border border-[color:var(--border)] shadow-md p-8">
              <div className="flex items-start justify-between gap-4">
                <div className="h-14 w-14 rounded-2xl flex items-center justify-center text-2xl"
                  style={{ background: "rgba(31,42,68,0.10)", color: "var(--primary)" }}
                >
                  {f.icon}
                </div>
              </div>

              <h3 className="mt-6 text-2xl font-extrabold text-[color:var(--primary)]">{f.title}</h3>
              <p className="mt-3 text-base leading-relaxed text-[color:rgba(28,28,28,0.70)]">{f.desc}</p>

              <Link href={f.href} className="mt-6 inline-flex items-center gap-2 font-bold text-[color:var(--ai)]">
                {t("f1Link")} <span>→</span>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* TRUST STRIP */}
      <section className="py-10" style={{ background: "var(--primary)" }}>
        <div className="mx-auto max-w-6xl px-6">
          <div className="rounded-3xl px-6 py-8 flex flex-col md:flex-row items-center justify-center gap-8"
               style={{ background: "rgba(255,255,255,0.10)" }}>
            <div className="text-white/90 font-semibold flex items-center gap-3">🛡️ <span>{t("trust1")}</span></div>
            <div className="text-white/90 font-semibold flex items-center gap-3">🔒 <span>{t("trust2")}</span></div>
            <div className="text-white/90 font-semibold flex items-center gap-3">⚠️ <span>{t("trust3")}</span></div>
          </div>
        </div>
      </section>
    </main>
  );
}
