"use client";

import Image from "next/image";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const TOPICS = [
  "Salary",
  "Probation",
  "Termination",
  "Working Hours",
  "Leave",
  "Benefits",
  "Non-Compete",
  "Penalties",
  "Duration",
] as const;

type Mode = "full" | "focused";

/** ===== Structured Summary Types (for json_schema output) ===== */
type SummarySource = { type: "contract" | "law"; id: string };

type SummaryBullet = { text: string; sources: SummarySource[] };

type SummarySection = {
  key: string;
  title: string;
  bullets: SummaryBullet[];
};

type SummaryStructured = {
  mode: "full" | "focused";
  language: string;
  overview: SummaryBullet[];
  sections: SummarySection[];
};

function isStructuredSummary(x: any): x is SummaryStructured {
  return (
    x &&
    typeof x === "object" &&
    (x.mode === "full" || x.mode === "focused") &&
    Array.isArray(x.overview) &&
    Array.isArray(x.sections)
  );
}

export default function SummaryPage() {
  const t = useTranslations("Summary");
  const locale = useLocale();

  const [mode, setMode] = useState<Mode>("full");
  const [topics, setTopics] = useState<string[]>([]);

  // ✅ Support both string fallback and structured JSON
  const [resultText, setResultText] = useState<string>("");
  const [resultData, setResultData] = useState<SummaryStructured | null>(null);

  const [loading, setLoading] = useState(false);

  const contractId = useMemo(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("contract_id");
  }, []);

  const outLang = locale; // output language follows current URL locale
  const hasContract = !!contractId;

  function toggleTopic(topic: string) {
    setTopics((prev) =>
      prev.includes(topic) ? prev.filter((x) => x !== topic) : [...prev, topic]
    );
  }

  async function generate() {
    const id = localStorage.getItem("contract_id");
    if (!id) return alert(t("needUpload"));

    const payload: any = { contract_id: id, mode, language: locale };
    if (mode === "focused") payload.topics = topics;

    setLoading(true);
    setResultText("");
    setResultData(null);

    try {
      const r = await fetch(`${API}/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await r.json();

      // ✅ Expect: { summary: <object|string>, contract_id, language }
      if (isStructuredSummary(data.summary)) {
        setResultData(data.summary);
        setResultText("");
      } else {
        setResultData(null);
        setResultText(
          typeof data.summary === "string" ? data.summary : JSON.stringify(data, null, 2)
        );
      }
    } catch (e: any) {
      setResultData(null);
      setResultText("❌ " + (e?.message || String(e)));
    } finally {
      setLoading(false);
    }
  }

  /** ===== Legacy string formatter (for plain-text summaries) ===== */
  function renderSummaryText(result: string, locale: string) {
    const lines = (result || "").split("\n").map((l) => l.trimEnd());
    const isRTL = ["ar", "ur"].includes(locale);

    return (
      <div
        className="whitespace-pre-wrap rounded-3xl border border-[color:var(--border)] bg-[rgba(31,42,68,0.04)] p-5 text-sm text-[color:rgba(28,28,28,0.90)]"
        style={{ direction: isRTL ? "rtl" : "ltr" }}
      >
        {lines.map((line, idx) => {
          const trimmed = line.trim();

          if (!trimmed) return <div key={idx} className="h-3" />;

          // headings like: ## ...
          if (trimmed.startsWith("##")) {
            const title = trimmed.replace(/^##\s*/, "");
            return (
              <div
                key={idx}
                className="mt-4 mb-2 font-extrabold text-[color:var(--primary)]"
              >
                {title}
              </div>
            );
          }

          // bullets like: - ...
          if (trimmed.startsWith("- ")) {
            let text = trimmed.replace(/^-+\s*/, "");
          
            // 🔧 FIX SOURCE LABELS
            text = text.replace(
              /\(Summary\.contractShort:\s*([A-Z0-9\-]+)\)/g,
              `(${t("contract")}: $1)`
            );
          
            text = text.replace(
              /\(Summary\.law:\s*([A-Za-z0-9\s]+)\)/g,
              `(${t("law")}: $1)`
            );
          
            return (
              <div key={idx} className="flex gap-2 leading-relaxed mb-2">
                <span className="mt-[2px]">•</span>
                <span>{text}</span>
              </div>
            );
          }
          
          return (
            <div key={idx} className="leading-relaxed">
              {trimmed}
            </div>
          );
        })}
      </div>
    );
  }

  /** ===== Structured summary renderer (for JSON schema output) ===== */
  function renderStructuredSummary(data: SummaryStructured, locale: string) {
    const isRTL = ["ar", "ur"].includes(locale);

    const contractLabel = t.has("contractShort")
    ? t("contractShort")
    : (isRTL ? "العقد" : "Contract");

    const lawLabel = t.has("lawShort")
      ? t("lawShort")
      : (isRTL ? "نظام العمل" : "Labor Law");

    const overviewTitle = t.has("overviewTitle")
      ? t("overviewTitle")
      : (isRTL ? "نظرة عامة" : "Overview");


    const sourceLabel = (s: SummarySource) =>
      s.type === "contract" ? contractLabel : lawLabel;

    return (
      <div
        className="rounded-3xl border border-[color:var(--border)] bg-[rgba(31,42,68,0.04)] p-5 text-sm text-[color:rgba(28,28,28,0.90)]"
        style={{ direction: isRTL ? "rtl" : "ltr" }}
      >
        {/* Overview */}
        {data.overview?.length > 0 && (
          <div className="mb-5">
            <div className="font-extrabold text-[color:var(--primary)] mb-2">
              {overviewTitle}
            </div>
            <ul className="list-disc pl-5 space-y-2">
              {data.overview.map((b, i) => (
                <li key={i} className="leading-relaxed">
                  {b.text}{" "}
                  <span className="text-xs opacity-70">
                    {b.sources?.map((s, j) => (
                      <span key={j}>
                        ({sourceLabel(s)}: {s.id})
                        {j < (b.sources?.length || 0) - 1 ? " " : ""}
                      </span>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Sections */}
        <div className="space-y-5">
          {data.sections?.map((sec, idx) => (
            <div key={idx}>
              <div className="font-extrabold text-[color:var(--primary)] mb-2">
                {sec.title}
              </div>
              <ul className="list-disc pl-5 space-y-2">
                {sec.bullets?.map((b, i) => (
                  <li key={i} className="leading-relaxed">
                    {b.text}{" "}
                    <span className="text-xs opacity-70">
                      {b.sources?.map((s, j) => (
                        <span key={j}>
                          ({sourceLabel(s)}: {s.id})
                          {j < (b.sources?.length || 0) - 1 ? " " : ""}
                        </span>
                      ))}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--bg)]">
      {/* HERO */}
      <section className="relative">
        <div className="pointer-events-none absolute inset-0">
          <div
            className="absolute -top-24 right-24 h-72 w-72 rounded-full blur-3xl opacity-20"
            style={{ background: "var(--ai)" }}
          />
          <div
            className="absolute top-24 left-24 h-72 w-72 rounded-full blur-3xl opacity-15"
            style={{ background: "var(--gold)" }}
          />
        </div>

        <div className="mx-auto max-w-6xl px-6 pt-10 pb-8 text-center relative">
          <div className="flex justify-center">
            <Image src="/daleel-logo.png" alt="Daleel" width={72} height={72} priority />
          </div>

          <h1 className="mt-5 text-3xl md:text-5xl font-extrabold tracking-tight text-[color:var(--primary)]">
            {t("title")}
          </h1>

          <p className="mt-3 text-base md:text-lg leading-relaxed text-[color:rgba(28,28,28,0.70)] max-w-3xl mx-auto">
            {t("subtitle")}
          </p>

          {/* Contract chip */}
          <div className="mt-5 flex items-center justify-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm shadow-sm">
              <span className="opacity-70">{t("contractId")}</span>
              <span className="font-bold text-[color:var(--primary)]">
                {hasContract ? contractId : t("notUploaded")}
              </span>
            </span>

            <Link
              href={`/${locale}/upload`}
              className="rounded-full bg-[rgba(31,42,68,0.06)] hover:bg-[rgba(31,42,68,0.10)] px-4 py-2 text-sm font-bold"
              style={{ color: "var(--primary)" }}
            >
              {t("goUpload")}
            </Link>
          </div>
        </div>
      </section>

      {/* CONTENT */}
      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* MAIN */}
          <div className="lg:col-span-2 rounded-3xl bg-white border border-[color:var(--border)] shadow-md p-6 md:p-8">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl md:text-2xl font-extrabold text-[color:var(--primary)]">
                  {t("cardTitle")}
                </h2>
                <p className="mt-2 text-sm md:text-base text-[color:rgba(28,28,28,0.65)]">
                  {t("cardDesc")}
                </p>
              </div>

              <div
                className="h-12 w-12 rounded-2xl flex items-center justify-center text-xl shrink-0"
                style={{ background: "rgba(31,42,68,0.10)", color: "var(--primary)" }}
                aria-hidden
              >
                📝
              </div>
            </div>

            {/* Mode toggle */}
            <div className="mt-6 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setMode("full")}
                className="rounded-2xl px-5 py-2.5 text-sm font-extrabold border transition"
                style={{
                  borderColor: "var(--border)",
                  background: mode === "full" ? "var(--primary)" : "white",
                  color: mode === "full" ? "white" : "var(--primary)",
                }}
              >
                {t("modeFull")}
              </button>

              <button
                type="button"
                onClick={() => setMode("focused")}
                className="rounded-2xl px-5 py-2.5 text-sm font-extrabold border transition"
                style={{
                  borderColor: "var(--border)",
                  background: mode === "focused" ? "var(--primary)" : "white",
                  color: mode === "focused" ? "white" : "var(--primary)",
                }}
              >
                {t("modeFocused")}
              </button>

              <span className="ml-auto inline-flex items-center gap-2 rounded-2xl border border-[color:var(--border)] bg-white px-4 py-2 text-sm text-[color:rgba(28,28,28,0.70)]">
                <span className="opacity-70">{t("outputLang")}</span>
                <b className="text-[color:var(--primary)]">{outLang.toUpperCase()}</b>
              </span>
            </div>

            {/* Focus topics */}
            {mode === "focused" && (
              <div className="mt-5 rounded-3xl border border-[color:var(--border)] bg-[rgba(31,42,68,0.04)] p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-extrabold text-[color:var(--primary)]">{t("topicsTitle")}</div>
                    <div className="mt-1 text-sm text-[color:rgba(28,28,28,0.65)]">{t("topicsDesc")}</div>
                  </div>

                  <div className="text-sm font-bold text-[color:rgba(28,28,28,0.70)]">
                    {t("selectedCount")}{" "}
                    <span className="text-[color:var(--primary)]">{topics.length}</span>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {TOPICS.map((topic) => {
                    const on = topics.includes(topic);
                    return (
                      <button
                        key={topic}
                        type="button"
                        onClick={() => toggleTopic(topic)}
                        className="rounded-full px-4 py-2 text-sm font-bold border transition"
                        style={{
                          borderColor: "var(--border)",
                          background: on ? "rgba(31,42,68,0.10)" : "white",
                          color: "var(--primary)",
                        }}
                      >
                        {t(`topic.${topic}`)}
                      </button>
                    );
                  })}
                </div>

                {topics.length === 0 && (
                  <div className="mt-3 text-xs text-[color:rgba(28,28,28,0.60)]">{t("topicsHint")}</div>
                )}
              </div>
            )}

            {/* Generate */}
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                onClick={generate}
                disabled={!hasContract || loading || (mode === "focused" && topics.length === 0)}
                className="rounded-2xl px-7 py-3 font-extrabold shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ background: "var(--primary)", color: "white" }}
              >
                {loading ? t("generating") : t("generateBtn")}
              </button>

              <button
                type="button"
                onClick={() => {
                  setResultText("");
                  setResultData(null);
                }}
                disabled={(!resultText && !resultData) || loading}
                className="rounded-2xl px-6 py-3 font-bold border bg-white shadow-sm hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ borderColor: "var(--border)", color: "var(--primary)" }}
              >
                {t("clearBtn")}
              </button>

              <Link
                href={`/${locale}/contract-qa`}
                className="rounded-2xl px-6 py-3 font-bold bg-[rgba(31,42,68,0.06)] hover:bg-[rgba(31,42,68,0.10)] text-center"
                style={{ color: "var(--primary)" }}
              >
                {t("goQA")}
              </Link>
            </div>

            {/* Result */}
            <div className="mt-6">
              {(!resultText && !resultData) ? (
                <div className="rounded-3xl border border-[color:var(--border)] bg-white p-8 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[rgba(31,42,68,0.08)] text-2xl">
                    ✨
                  </div>
                  <div className="mt-3 font-extrabold text-[color:var(--primary)]">{t("emptyTitle")}</div>
                  <div className="mt-2 text-sm text-[color:rgba(28,28,28,0.65)]">{t("emptyDesc")}</div>
                </div>
              ) : resultData ? (
                renderStructuredSummary(resultData, locale)
              ) : (
                renderSummaryText(resultText, locale)
              )}
            </div>
          </div>

          {/* SIDE INFO */}
          <aside className="rounded-3xl bg-white border border-[color:var(--border)] shadow-md p-6 md:p-8">
            <h3 className="text-lg font-extrabold text-[color:var(--primary)]">{t("sideTitle")}</h3>

            <ul className="mt-4 space-y-3 text-sm text-[color:rgba(28,28,28,0.70)]">
              <li className="flex gap-2">
                <span>✅</span>
                <span>{t("side1")}</span>
              </li>
              <li className="flex gap-2">
                <span>🧾</span>
                <span>{t("side2")}</span>
              </li>
              <li className="flex gap-2">
                <span>⚠️</span>
                <span>{t("side3")}</span>
              </li>
            </ul>

            <div className="mt-6 rounded-3xl p-5" style={{ background: "rgba(31,42,68,0.06)" }}>
              <p className="text-sm font-semibold text-[color:var(--primary)]">{t("tipTitle")}</p>
              <p className="mt-2 text-sm text-[color:rgba(28,28,28,0.70)] leading-relaxed">{t("tipDesc")}</p>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
