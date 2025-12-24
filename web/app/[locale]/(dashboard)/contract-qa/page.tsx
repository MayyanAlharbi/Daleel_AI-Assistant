"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

/**
 * We keep the SAME UI design.
 * The only change: assistant messages can be either:
 *  - legacy string (text)
 *  - structured answer (direct_answer + bullets)
 */

type AssistantStructured = {
  direct_answer: string;
  from_contract: { text: string; clause_id: string }[];
  from_law: { text: string; article: string }[];
};

type Msg =
  | { role: "user"; text: string; at?: number }
  | { role: "assistant"; text?: string; data?: AssistantStructured; at?: number };

function isStructuredAnswer(x: any): x is AssistantStructured {
  return (
    x &&
    typeof x === "object" &&
    typeof x.direct_answer === "string" &&
    Array.isArray(x.from_contract) &&
    Array.isArray(x.from_law)
  );
}

export default function ContractQA() {
  const t = useTranslations("QA");
  const locale = useLocale();

  const [q, setQ] = useState("");
  const [chat, setChat] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const [contractId, setContractId] = useState<string | null>(null);

  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const id = localStorage.getItem("contract_id");
    setContractId(id);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, loading]);

  const quickPrompts = useMemo(
    () => [t("quick1"), t("quick2"), t("quick3"), t("quick4")],
    [t]
  );

  async function send() {
    const id = localStorage.getItem("contract_id");
    if (!id) {
      setChat((c) => [
        ...c,
        { role: "assistant", text: t("noContract"), at: Date.now() },
      ]);
      return;
    }

    if (!q.trim() || loading) return;

    const userText = q.trim();
    setQ("");
    setChat((c) => [...c, { role: "user", text: userText, at: Date.now() }]);
    setLoading(true);

    try {
      const r = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract_id: id, question: userText }),
      });

      const data = await r.json();

      if (!r.ok) {
        const err = data?.error ? data.error : JSON.stringify(data);
        setChat((c) => [
          ...c,
          { role: "assistant", text: "❌ " + err, at: Date.now() },
        ]);
        return;
      }

      // ✅ Prefer structured response if provided by backend
      // Expected:
      // { direct_answer, from_contract, from_law, language }
      if (isStructuredAnswer(data)) {
        setChat((c) => [
          ...c,
          { role: "assistant", data, at: Date.now() },
        ]);
      } else if (isStructuredAnswer(data?.answer)) {
        // In case you wrap it inside "answer"
        setChat((c) => [
          ...c,
          { role: "assistant", data: data.answer, at: Date.now() },
        ]);
      } else {
        // fallback to legacy behavior
        setChat((c) => [
          ...c,
          {
            role: "assistant",
            text: data?.answer ? data.answer : JSON.stringify(data),
            at: Date.now(),
          },
        ]);
      }
    } catch (e: any) {
      setChat((c) => [
        ...c,
        {
          role: "assistant",
          text: "❌ " + (e?.message || String(e)),
          at: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
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

        <div className="mx-auto max-w-6xl px-6 pt-10 pb-8 relative">
          <div className="text-center">
            <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-[color:var(--primary)]">
              {t("title")}
            </h1>
            <p className="mt-3 text-base md:text-lg leading-relaxed text-[color:rgba(28,28,28,0.70)] max-w-3xl mx-auto">
              {t("subtitle")}
            </p>

            {/* Contract Badge */}
            <div className="mt-5 flex justify-center">
              <div className="inline-flex items-center gap-2 rounded-2xl border border-[color:var(--border)] bg-white px-4 py-2 text-sm shadow-sm">
                <span className="opacity-70">{t("contractIdLabel")}</span>
                <span className="font-bold text-[color:var(--primary)]">
                  {contractId ? contractId : t("noId")}
                </span>
              </div>
            </div>

            {/* Quick prompts */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQ(p)}
                  className="rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm shadow-sm hover:bg-gray-50"
                  style={{ color: "rgba(28,28,28,0.85)" }}
                >
                  ✨ {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CONTENT */}
      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat */}
          <div className="lg:col-span-2 rounded-3xl bg-white border border-[color:var(--border)] shadow-md overflow-hidden">
            {/* Header strip */}
            <div className="flex items-center justify-between px-6 py-4 border-b bg-white/70">
              <div className="flex items-center gap-2">
                <div
                  className="h-10 w-10 rounded-2xl flex items-center justify-center text-lg"
                  style={{
                    background: "rgba(31,42,68,0.10)",
                    color: "var(--primary)",
                  }}
                >
                  ❓
                </div>
                <div>
                  <div className="font-extrabold text-[color:var(--primary)]">
                    {t("panelTitle")}
                  </div>
                  <div className="text-xs text-[color:rgba(28,28,28,0.60)]">
                    {t("panelHint")}
                  </div>
                </div>
              </div>

              <div className="text-xs text-[color:rgba(28,28,28,0.60)]">
                {t("enterHint")}
              </div>
            </div>

            {/* Messages */}
            <div className="h-[520px] overflow-y-auto px-5 py-5 space-y-3 bg-[rgba(31,42,68,0.03)]">
              {chat.length === 0 && (
                <div className="rounded-3xl border border-[color:var(--border)] bg-white p-5 text-sm text-[color:rgba(28,28,28,0.70)]">
                  <div className="font-bold text-[color:var(--primary)]">
                    {t("emptyTitle")}
                  </div>
                  <div className="mt-2 leading-relaxed">{t("emptyDesc")}</div>
                </div>
              )}

              {chat.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={[
                      "max-w-[92%] md:max-w-[78%] rounded-3xl px-5 py-4 shadow-sm",
                      m.role === "user"
                        ? "text-white"
                        : "bg-white border border-[color:var(--border)]",
                    ].join(" ")}
                    style={
                      m.role === "user"
                        ? { background: "var(--primary)" }
                        : undefined
                    }
                  >
                    {/* Keep SAME wrapper styles; only change content rendering */}
                    <div className="text-sm whitespace-pre-wrap leading-relaxed">
                      {/* USER */}
                      {m.role === "user" && m.text}

                      {/* ASSISTANT */}
                      {m.role === "assistant" && (
                        <>
                          {/* Structured */}
                          {m.data ? (
                            <div className="space-y-3">
                              {/* Direct Answer */}
                              <div className="font-semibold">
                                {m.data.direct_answer}
                              </div>

                              {/* Contract section */}
                              {m.data.from_contract?.length > 0 && (
                                <div className="space-y-2">
                                  <div className="font-bold">
                                    {t("fromContract")}
                                  </div>
                                  <ul className="list-disc pl-5 space-y-1">
                                    {m.data.from_contract.map((b, idx) => (
                                      <li key={idx}>
                                        {b.text}{" "}
                                        <span className="text-xs opacity-70">
                                          ({t("contract")}: {b.clause_id})
                                        </span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Law section (ONLY if exists) */}
                              {m.data.from_law?.length > 0 && (
                                <div className="space-y-2">
                                  <div className="font-bold">
                                    {t("saudiLaborLaw")}
                                  </div>
                                  <ul className="list-disc pl-5 space-y-1">
                                    {m.data.from_law.map((b, idx) => (
                                      <li key={idx}>
                                        {b.text}{" "}
                                        <span className="text-xs opacity-70">
                                          ({t("law")}: {b.article})
                                        </span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          ) : (
                            // Legacy string fallback
                            // Legacy string fallback (render headings without ##)
                            <div className="space-y-2">
                              {(m.text || "").split("\n").map((line, idx) => {
                                const trimmed = line.trim();

                                // markdown-like heading: ## ...
                                if (trimmed.startsWith("##")) {
                                  return (
                                    <div
                                      key={idx}
                                      className="font-bold text-[color:var(--primary)] mt-2"
                                    >
                                      {trimmed.replace(/^##\s*/, "")}
                                    </div>
                                  );
                                }

                                // normal line
                                return <div key={idx}>{line}</div>;
                              })}
                            </div>

                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-3xl bg-white border border-[color:var(--border)] px-5 py-4 text-sm text-[color:rgba(28,28,28,0.70)] shadow-sm">
                    {t("thinking")}
                  </div>
                </div>
              )}

              <div ref={endRef} />
            </div>

            {/* Composer */}
            <div className="p-5 border-t bg-white">
              <div className="flex gap-3 items-end">
                <textarea
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  onKeyDown={onKeyDown}
                  rows={2}
                  placeholder={t("placeholder")}
                  className="flex-1 resize-none rounded-2xl border border-[color:var(--border)] px-4 py-3 text-sm outline-none focus:ring-2"
                  style={{
                    boxShadow: "0 0 0 0 rgba(0,0,0,0)",
                    direction: ["ar", "ur"].includes(locale) ? "rtl" : "ltr",
                  }}
                />
                <button
                  onClick={send}
                  disabled={loading || !q.trim()}
                  className="rounded-2xl px-6 py-3 font-extrabold shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
                  style={{ background: "var(--primary)", color: "white" }}
                >
                  {loading ? t("sending") : t("send")}
                </button>
              </div>

              <div className="mt-3 flex flex-wrap gap-2 text-xs text-[color:rgba(28,28,28,0.60)]">
                <span className="rounded-full border border-[color:var(--border)] bg-white px-3 py-1 shadow-sm">
                  🛡️ {t("hint1")}
                </span>
                <span className="rounded-full border border-[color:var(--border)] bg-white px-3 py-1 shadow-sm">
                  📌 {t("hint2")}
                </span>
              </div>
            </div>
          </div>

          {/* Side panel */}
          <aside className="rounded-3xl bg-white border border-[color:var(--border)] shadow-md p-6 md:p-8">
            <h3 className="text-lg font-extrabold text-[color:var(--primary)]">
              {t("sideTitle")}
            </h3>

            <ul className="mt-4 space-y-3 text-sm text-[color:rgba(28,28,28,0.70)]">
              <li className="flex gap-2">
                <span>✅</span>
                <span>{t("side1")}</span>
              </li>
              <li className="flex gap-2">
                <span>📎</span>
                <span>{t("side2")}</span>
              </li>
              <li className="flex gap-2">
                <span>⚠️</span>
                <span>{t("side3")}</span>
              </li>
            </ul>

            <div
              className="mt-6 rounded-3xl p-5"
              style={{ background: "rgba(31,42,68,0.06)" }}
            >
              <p className="text-sm font-semibold text-[color:var(--primary)]">
                {t("tipTitle")}
              </p>
              <p className="mt-2 text-sm text-[color:rgba(28,28,28,0.70)] leading-relaxed">
                {t("tipDesc")}
              </p>
            </div>

            {/* (Optional) Sources placeholder for later */}
            <div className="mt-6 rounded-3xl border border-[color:var(--border)] p-5">
              <div className="text-sm font-extrabold text-[color:var(--primary)]">
                {t("sourcesTitle")}
              </div>
              <div className="mt-2 text-sm text-[color:rgba(28,28,28,0.65)] leading-relaxed">
                {t("sourcesDesc")}
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
