"use client";

import { useTranslations } from "next-intl";
import { useMemo, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function UploadPage() {
  const t = useTranslations("Upload");

  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<number>(0);

  const inputRef = useRef<HTMLInputElement | null>(null);

  const fileLabel = useMemo(() => {
    if (!file) return t("noFile");
    return file.name;
  }, [file, t]);

  function openPicker() {
    inputRef.current?.click();
  }

  function onPick(f: File | null) {
    setMsg("");
    setProgress(0);
    setFile(f);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (!f) return;

    const name = f.name.toLowerCase();
    const ok = name.endsWith(".pdf") || name.endsWith(".docx") || name.endsWith(".doc");

    if (!ok) {
      setMsg("❌ " + t("invalidType"));
      return;
    }
    onPick(f);
  }

  function onDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
  }

  async function upload() {
    if (!file) return;

    setLoading(true);
    setMsg("");
    setProgress(5);

    try {
      const form = new FormData();
      form.append("file", file);

      const data = await new Promise<any>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API}/upload_contract`, true);

        xhr.upload.onprogress = (evt) => {
          if (!evt.lengthComputable) return;
          const p = Math.round((evt.loaded / evt.total) * 100);
          setProgress(Math.max(5, Math.min(95, p)));
        };

        xhr.onload = () => {
          try {
            const json = JSON.parse(xhr.responseText || "{}");
            if (xhr.status >= 200 && xhr.status < 300) resolve(json);
            else reject(json);
          } catch {
            reject({ error: "Invalid server response" });
          }
        };

        xhr.onerror = () => reject({ error: "Network error" });

        xhr.send(form);
      });

      setProgress(100);

      localStorage.setItem("contract_id", data.contract_id);
      localStorage.setItem("contract_lang", data.language);

      setMsg(
        `✅ ${t("success")}\n` +
          `${t("contractId")}: ${data.contract_id}\n` +
          `${t("language")}: ${data.language}\n` +
          `${t("clauses")}: ${data.num_clauses}`
      );
    } catch (e: any) {
      const errText = e?.error ? e.error : typeof e === "string" ? e : JSON.stringify(e);
      setMsg("❌ " + (errText || t("unknownError")));
      setProgress(0);
    } finally {
      setLoading(false);
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

        <div className="mx-auto max-w-6xl px-6 pt-10 pb-8 text-center relative">
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-[color:var(--primary)]">
            {t("title")}
          </h1>

          <p className="mt-3 text-base md:text-lg leading-relaxed text-[color:rgba(28,28,28,0.70)] max-w-3xl mx-auto">
            {t("subtitle")}
          </p>
        </div>
      </section>

      {/* CONTENT */}
      <section className="mx-auto max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* MAIN CARD */}
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
              >
                ⬆️
              </div>
            </div>

            {/* DROPZONE */}
            <div
              onDrop={onDrop}
              onDragOver={onDragOver}
              className="mt-6 rounded-3xl border border-dashed border-[color:var(--border)] bg-[rgba(255,255,255,0.7)] p-8 md:p-10 text-center"
            >
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[rgba(31,42,68,0.08)] text-2xl">
                📄
              </div>

              <p className="mt-4 font-extrabold text-[color:var(--primary)]">{t("dropTitle")}</p>

              <p className="mt-2 text-sm text-[color:rgba(28,28,28,0.65)]">{t("dropHint")}</p>

              {/* Selected */}
              <div className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-[color:var(--border)] bg-white px-4 py-2 text-sm shadow-sm">
                <span className="opacity-70">{t("selected")}</span>
                <span className="font-bold text-[color:var(--primary)]">{fileLabel}</span>
              </div>

              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                className="hidden"
                onChange={(e) => onPick(e.target.files?.[0] || null)}
              />

              {/* Buttons */}
              <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  type="button"
                  onClick={openPicker}
                  className="rounded-2xl px-6 py-3 font-bold border bg-white shadow-sm hover:bg-gray-50"
                  style={{ borderColor: "var(--border)", color: "var(--primary)" }}
                >
                  {t("chooseFile")}
                </button>

                <button
                  onClick={upload}
                  disabled={!file || loading}
                  className="rounded-2xl px-7 py-3 font-extrabold shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
                  style={{ background: "var(--primary)", color: "white" }}
                >
                  {loading ? t("uploading") : t("uploadBtn")}
                </button>
              </div>

              {/* Progress */}
              <div className="mt-6">
                <div className="h-2 w-full rounded-full bg-[rgba(31,42,68,0.10)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${progress}%`, background: "var(--ai)" }}
                  />
                </div>
                <div className="mt-2 text-xs text-[color:rgba(28,28,28,0.60)]">
                  {progress > 0 ? `${t("progress")}: ${progress}%` : t("progressHint")}
                </div>
              </div>

              {/* Formats */}
              <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
                <span className="rounded-full border border-[color:var(--border)] bg-white px-3 py-1 text-xs shadow-sm">
                  PDF
                </span>
                <span className="rounded-full border border-[color:var(--border)] bg-white px-3 py-1 text-xs shadow-sm">
                  DOCX
                </span>
                <span className="rounded-full border border-[color:var(--border)] bg-white px-3 py-1 text-xs shadow-sm">
                  {t("maxSize")}
                </span>
              </div>

              {/* Result */}
              {msg && (
                <pre className="mt-6 whitespace-pre-wrap rounded-2xl bg-[rgba(31,42,68,0.06)] p-4 text-sm text-start">
                  {msg}
                </pre>
              )}
            </div>

            {/* Steps */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { n: "1", title: t("step1Title"), desc: t("step1Desc") },
                { n: "2", title: t("step2Title"), desc: t("step2Desc") },
                { n: "3", title: t("step3Title"), desc: t("step3Desc") },
              ].map((s) => (
                <div
                  key={s.n}
                  className="rounded-3xl border border-[color:var(--border)] bg-white p-5 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="h-9 w-9 rounded-xl flex items-center justify-center font-extrabold"
                      style={{ background: "rgba(111,168,255,0.18)", color: "var(--primary)" }}
                    >
                      {s.n}
                    </div>
                    <div className="font-extrabold text-[color:var(--primary)]">{s.title}</div>
                  </div>
                  <p className="mt-2 text-sm text-[color:rgba(28,28,28,0.65)] leading-relaxed">
                    {s.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* SIDE INFO */}
          <aside className="rounded-3xl bg-white border border-[color:var(--border)] shadow-md p-6 md:p-8">
            <h3 className="text-lg font-extrabold text-[color:var(--primary)]">{t("sideTitle")}</h3>

            <ul className="mt-4 space-y-3 text-sm text-[color:rgba(28,28,28,0.70)]">
              <li className="flex gap-2">
                <span>🛡️</span>
                <span>{t("side1")}</span>
              </li>
              <li className="flex gap-2">
                <span>🔒</span>
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
