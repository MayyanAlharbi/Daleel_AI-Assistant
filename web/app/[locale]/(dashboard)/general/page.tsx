"use client";

import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Msg = { role: "user" | "assistant"; text: string };

export default function GeneralPage() {
  const t = useTranslations("General");
  const locale = useLocale();

  const [q, setQ] = useState("");
  const [chat, setChat] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);

  const listRef = useRef<HTMLDivElement | null>(null);

  const dir = useMemo(() => (["ar", "ur"].includes(locale) ? "rtl" : "ltr"), [locale]);

  useEffect(() => {
    // auto scroll to bottom
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [chat, loading]);

  const quickQuestions = useMemo(
    () => [t("quick1"), t("quick2"), t("quick3"), t("quick4")],
    [t]
  );

  async function send(text?: string) {
    const userText = (text ?? q).trim();
    if (!userText) return;

    setQ("");
    setChat((c) => [...c, { role: "user", text: userText }]);
    setLoading(true);

    try {
      const r = await fetch(`${API}/ask_general`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userText,
          language: locale, // ✅ important
        }),
      });

      const data = await r.json();
      const answer = data?.answer ? String(data.answer) : JSON.stringify(data, null, 2);

      setChat((c) => [...c, { role: "assistant", text: answer }]);
    } catch (e: any) {
      setChat((c) => [
        ...c,
        { role: "assistant", text: "❌ " + (e?.message || String(e)) },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter new line
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function clearChat() {
    setChat([]);
    setQ("");
  }

  return (
    <main className="min-h-screen bg-[var(--bg)]" dir={dir}>
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

          {/* Quick questions */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            {quickQuestions.map((qq, i) => (
              <button
                key={i}
                type="button"
                onClick={() => send(qq)}
                className="rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-bold shadow-sm hover:bg-gray-50"
                style={{ color: "var(--primary)" }}
                title={qq}
              >
                ✨ {qq}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* CONTENT */}
      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* CHAT CARD */}
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
                💬
              </div>
            </div>

            {/* Chat window */}
            <div
              ref={listRef}
              className="mt-6 h-[440px] overflow-auto rounded-3xl border border-[color:var(--border)] bg-[rgba(31,42,68,0.03)] p-4"
            >
              {!chat.length ? (
                <div className="h-full flex items-center justify-center text-center">
                  <div>
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[rgba(31,42,68,0.08)] text-2xl">
                      ✨
                    </div>
                    <div className="mt-3 font-extrabold text-[color:var(--primary)]">
                      {t("emptyTitle")}
                    </div>
                    <div className="mt-2 text-sm text-[color:rgba(28,28,28,0.65)]">
                      {t("emptyDesc")}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {chat.map((m, i) => {
                    const isUser = m.role === "user";
                    return (
                      <div key={i} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                        <div
                          className="max-w-[85%] rounded-3xl px-4 py-3 text-sm whitespace-pre-wrap"
                          style={{
                            background: isUser ? "var(--primary)" : "white",
                            color: isUser ? "white" : "rgba(28,28,28,0.90)",
                            border: isUser ? "none" : "1px solid var(--border)",
                            boxShadow: isUser ? "0 10px 25px rgba(31,42,68,0.12)" : "none",
                          }}
                        >
                          {m.text}
                        </div>
                      </div>
                    );
                  })}

                  {loading && (
                    <div className="text-xs text-[color:rgba(28,28,28,0.55)]">
                      {t("thinking")}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Composer */}
            <div className="mt-4 rounded-3xl border border-[color:var(--border)] bg-white p-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1">
                  <div className="text-xs text-[color:rgba(28,28,28,0.55)]">{t("hintKeys")}</div>
                  <textarea
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    onKeyDown={onKeyDown}
                    rows={2}
                    placeholder={t("placeholder")}
                    className="mt-2 w-full resize-none rounded-2xl border border-[color:var(--border)] px-4 py-3 text-sm outline-none"
                  />
                </div>

                <div className="flex flex-col sm:w-44 gap-2">
                  <button
                    type="button"
                    onClick={() => send()}
                    disabled={!q.trim() || loading}
                    className="rounded-2xl px-6 py-3 font-extrabold shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
                    style={{ background: "var(--primary)", color: "white" }}
                  >
                    {t("sendBtn")}
                  </button>

                  <button
                    type="button"
                    onClick={clearChat}
                    disabled={!chat.length || loading}
                    className="rounded-2xl px-6 py-3 font-bold border bg-white shadow-sm hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
                    style={{ borderColor: "var(--border)", color: "var(--primary)" }}
                  >
                    {t("clearBtn")}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* SIDE INFO */}
          <aside className="rounded-3xl bg-white border border-[color:var(--border)] shadow-md p-6 md:p-8">
            <h3 className="text-lg font-extrabold text-[color:var(--primary)]">{t("sideTitle")}</h3>

            <ul className="mt-4 space-y-3 text-sm text-[color:rgba(28,28,28,0.70)]">
              <li className="flex gap-2">
                <span>📚</span>
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
              <p className="mt-2 text-sm text-[color:rgba(28,28,28,0.70)] leading-relaxed">
                {t("tipDesc")}
              </p>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
