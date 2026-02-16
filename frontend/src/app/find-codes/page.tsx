"use client";

import { useEffect, useMemo, useState } from "react";
import Papa from "papaparse";

type UseCaseKey = "text" | "batchJson" | "csv";

const DEFAULT_OPTIONS = { top_k: 50, min_retrieval_score: 0.005 };

// If NEXT_PUBLIC_API_BASE_URL is set (dev/local), use it.
// If empty/undefined (prod), use same-origin + CloudFront behavior (/api/* -> ALB).
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/+$/, "");

// All backend endpoints are rooted at /api/...
function apiUrl(path: string) {
  // Ensure we always have a leading slash
  const p = path.startsWith("/") ? path : `/${path}`;
  // In prod API_BASE == "" so this becomes "/api/..."
  return `${API_BASE}${p}`;
}

async function postJson(path: string, body: any) {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const text = await res.text();

  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { raw: text };
  }

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${JSON.stringify(data)}`);
  }

  return data;
}

function AccordionSection({
  open,
  onToggle,
  title,
  description,
  children,
}: {
  open: boolean;
  onToggle: () => void;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="pb-acc">
      <button type="button" onClick={onToggle} className="pb-acc-btn">
        <div>
          <div className="pb-acc-title">{title}</div>
          <div className="pb-acc-desc">{description}</div>
        </div>
        <div
          className="pb-acc-chevron"
          style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform .15s ease" }}
          aria-hidden
        >
          ▼
        </div>
      </button>

      {open ? <div className="pb-acc-body">{children}</div> : null}
    </div>
  );
}

export default function Page() {
  const [open, setOpen] = useState<UseCaseKey>("text");

  const [healthOk, setHealthOk] = useState(false);
  const [healthLabel, setHealthLabel] = useState("Checking...");

  // TEXT
  const [textId, setTextId] = useState("1");
  const [textName, setTextName] = useState("Test");
  const [textBody, setTextBody] = useState("Some policy text...");
  const [textLoading, setTextLoading] = useState(false);

  // BATCH JSON
  const [batchJson, setBatchJson] = useState(() =>
    JSON.stringify(
      {
        items: [
          { id: "1", name: "Policy A", text: "Some policy text for A..." },
          { id: "2", name: "Policy B", text: "Some policy text for B..." },
        ],
        options: DEFAULT_OPTIONS,
      },
      null,
      2
    )
  );
  const [batchLoading, setBatchLoading] = useState(false);

  // CSV
  const [csvFileName, setCsvFileName] = useState("");
  const [csvLoading, setCsvLoading] = useState(false);

  // Output
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  const prettyResult = useMemo(() => (result ? JSON.stringify(result, null, 2) : ""), [result]);

  // Health check:
  // - In dev: API_BASE can be http://localhost:5127 and /health works
  // - In prod: API_BASE is "" so we need CloudFront to route /health -> ALB
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(apiUrl("/health"), { cache: "no-store" });
        if (!res.ok) throw new Error();
        // Your backend /health might return plain text, so don't force JSON parse.
        await res.text();
        if (cancelled) return;
        setHealthOk(true);
        setHealthLabel("Backend: Online");
      } catch {
        if (cancelled) return;
        setHealthOk(false);
        setHealthLabel("Backend: Offline");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function runText() {
    setError("");
    setResult(null);
    setTextLoading(true);
    try {
      const body = { id: textId, name: textName, text: textBody, options: DEFAULT_OPTIONS };
      const data = await postJson("/api/v1/use-cases/json/find-codes", body);
      setResult(data);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setTextLoading(false);
    }
  }

  async function runBatch() {
    setError("");
    setResult(null);
    setBatchLoading(true);
    try {
      const parsed = JSON.parse(batchJson);
      const data = await postJson("/api/v1/use-cases/json/find-codes-batch-json", parsed);
      setResult(data);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setBatchLoading(false);
    }
  }

  async function onCsvSelected(file: File | null) {
    setError("");
    setResult(null);
    if (!file) return;

    setCsvFileName(file.name);
    setCsvLoading(true);

    try {
      const csvText = await file.text();
      const parsed = Papa.parse<Record<string, string>>(csvText, { header: true, skipEmptyLines: true });
      if (parsed.errors?.length) throw new Error(`CSV parse error: ${parsed.errors[0].message}`);

      const rows = parsed.data ?? [];
      const items = rows
        .map((r, idx) => ({
          id: (r["id"] ?? r["policy_id"] ?? `${idx + 1}`).toString(),
          name: (r["name"] ?? r["policy_name"] ?? "").toString(),
          text: (r["text"] ?? r["cleaned_policy_text"] ?? "").toString(),
        }))
        .filter((x) => x.text.trim().length > 0);

      if (items.length === 0) throw new Error("No valid rows found. Expected columns: id, name, text.");

      const body = { items, options: DEFAULT_OPTIONS };
      const data = await postJson("/api/v1/use-cases/json/find-codes-batch-json", body);
      setResult(data);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setCsvLoading(false);
    }
  }

  async function copyResult() {
    try {
      await navigator.clipboard.writeText(prettyResult || "");
    } catch {}
  }

  return (
    <div style={{ display: "grid", gap: 20 }}>
      {/* Use cases */}
      <div className="pb-panel">
        <div className="pb-panel-header">
          <div>
            <div className="pb-title">Use Cases</div>
            <div className="pb-subtitle">Only one section stays open at a time. Default is single-text.</div>
          </div>
          <div className={`pb-pill ${healthOk ? "pb-pill-ok" : "pb-pill-bad"}`}>{healthLabel}</div>
        </div>

        <div className="pb-panel-body" style={{ display: "grid", gap: 14 }}>
          <AccordionSection
            open={open === "text"}
            onToggle={() => setOpen("text")}
            title="Find Codes — Single Text"
            description="Send one text body (plus optional id/name) to the API."
          >
            <div style={{ display: "grid", gap: 14 }}>
              <div
                style={{
                  display: "grid",
                  gap: 14,
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                }}
              >
                <div>
                  <div className="pb-label">Id</div>
                  <input className="pb-input" value={textId} onChange={(e) => setTextId(e.target.value)} />
                </div>

                <div>
                  <div className="pb-label">Name</div>
                  <input className="pb-input" value={textName} onChange={(e) => setTextName(e.target.value)} />
                </div>
              </div>

              <div>
                <div className="pb-label">Text</div>
                <textarea className="pb-textarea" value={textBody} onChange={(e) => setTextBody(e.target.value)} />
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
                <button
                  type="button"
                  className="pb-btn pb-btn-primary"
                  onClick={runText}
                  disabled={textLoading}
                  style={textLoading ? { opacity: 0.7, cursor: "not-allowed" } : undefined}
                >
                  {textLoading ? "Running..." : "Run Find Codes"}
                </button>

                <div className="pb-muted">
                  POST{" "}
                  <span style={{ color: "var(--pb-ink)" }}>/api/v1/use-cases/json/find-codes</span>
                </div>
              </div>
            </div>
          </AccordionSection>

          <AccordionSection
            open={open === "batchJson"}
            onToggle={() => setOpen("batchJson")}
            title="Find Codes — Batch JSON"
            description="Paste raw JSON. We’ll build a nicer UI later."
          >
            <div>
              <div className="pb-label">Batch JSON</div>
              <textarea
                className="pb-textarea"
                value={batchJson}
                onChange={(e) => setBatchJson(e.target.value)}
                style={{
                  minHeight: 240,
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                  fontSize: 12,
                }}
              />

              <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", marginTop: 14 }}>
                <button
                  type="button"
                  className="pb-btn pb-btn-primary"
                  onClick={runBatch}
                  disabled={batchLoading}
                  style={batchLoading ? { opacity: 0.7, cursor: "not-allowed" } : undefined}
                >
                  {batchLoading ? "Running..." : "Run Batch"}
                </button>

                <div className="pb-muted">
                  POST{" "}
                  <span style={{ color: "var(--pb-ink)" }}>/api/v1/use-cases/json/find-codes-batch-json</span>
                </div>
              </div>
            </div>
          </AccordionSection>

          <AccordionSection
            open={open === "csv"}
            onToggle={() => setOpen("csv")}
            title="Find Codes — CSV Upload"
            description="Upload a CSV. We parse id/name/text and send as batch-json."
          >
            <div style={{ display: "grid", gap: 10 }}>
              <div className="pb-subtitle" style={{ marginTop: 0 }}>
                Expected columns (for now): <span style={{ fontWeight: 800 }}>id, name, text</span>
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
                <label
                  className="pb-btn"
                  style={{
                    background: "rgba(255,255,255,.60)",
                    border: "1px solid rgba(28,36,82,.25)",
                    color: "var(--pb-ink)",
                    cursor: "pointer",
                    padding: ".75rem 1.25rem",
                  }}
                >
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    style={{ display: "none" }}
                    onChange={(e) => onCsvSelected(e.target.files?.[0] ?? null)}
                  />
                  {csvLoading ? "Parsing..." : "Choose CSV"}
                </label>

                {csvFileName ? (
                  <div className="pb-muted">
                    Selected: <span style={{ color: "var(--pb-ink)" }}>{csvFileName}</span>
                  </div>
                ) : null}
              </div>

              <div className="pb-muted">
                Sends to{" "}
                <span style={{ color: "var(--pb-ink)" }}>/api/v1/use-cases/json/find-codes-batch-json</span>
              </div>
            </div>
          </AccordionSection>
        </div>
      </div>

      {/* Results */}
      <div className="pb-panel" id="results">
        <div className="pb-panel-header">
          <div>
            <div className="pb-title">Results</div>
            <div className="pb-subtitle">Raw API response</div>
          </div>

          <button
            type="button"
            className="pb-btn"
            onClick={copyResult}
            disabled={!prettyResult}
            style={{
              padding: ".5rem .9rem",
              fontSize: 12,
              background: "rgba(255,255,255,.60)",
              border: "1px solid rgba(28,36,82,.25)",
              color: "var(--pb-ink)",
              opacity: prettyResult ? 1 : 0.6,
              cursor: prettyResult ? "pointer" : "not-allowed",
            }}
          >
            Copy JSON
          </button>
        </div>

        <div className="pb-panel-body">
          {error ? <div className="pb-error">{error}</div> : null}
          <pre className="pb-pre">{prettyResult || "// Run a use case to see output here"}</pre>
        </div>
      </div>
    </div>
  );
}
