"use client";

import { useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const fileLabel = useMemo(() => {
    if (!file) return "Choose PDF or DOCX";
    return file.name;
  }, [file]);

  async function upload() {
    if (!file) return;

    setLoading(true);
    setMsg("");

    try {
      const form = new FormData();
      form.append("file", file);

      const r = await fetch(`${API}/upload_contract`, {
        method: "POST",
        body: form,
      });

      const data = await r.json();

      if (!r.ok) {
        setMsg("❌ " + (data?.error ? data.error : JSON.stringify(data)));
        return;
      }

      localStorage.setItem("contract_id", data.contract_id);
      localStorage.setItem("contract_lang", data.language);

      setMsg(
        `✅ Uploaded successfully!
Contract ID: ${data.contract_id}
Language: ${data.language}
Clauses: ${data.num_clauses}`
      );
    } catch (e: any) {
      setMsg("❌ Error: " + (e?.message || String(e)));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-0px)] bg-gray-50">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-3xl font-semibold tracking-tight">
          Upload Employment Contract
        </h1>
        <p className="mt-2 text-gray-600">
          Upload a <b>PDF</b> or <b>DOCX</b>. We will split it into clauses and prepare it
          for Q&A and summaries.
        </p>

        <div className="mt-8 rounded-2xl border bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <label className="w-full cursor-pointer rounded-xl border border-dashed p-4 hover:bg-gray-50">
              <input
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <div className="text-sm text-gray-500">File</div>
              <div className="mt-1 font-medium">{fileLabel}</div>
            </label>

            <button
              onClick={upload}
              disabled={!file || loading}
              className="h-12 w-full rounded-xl bg-black px-5 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60 sm:w-48"
            >
              {loading ? "Uploading..." : "Upload"}
            </button>
          </div>

          {msg && (
            <pre className="mt-5 whitespace-pre-wrap rounded-xl bg-gray-50 p-4 text-sm text-gray-800">
              {msg}
            </pre>
          )}

          <div className="mt-4 text-xs text-gray-500">
            Tip: After upload, the Contract ID is stored automatically in your browser.
          </div>
        </div>
      </div>
    </div>
  );
}
