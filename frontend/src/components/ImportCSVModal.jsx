import { useState, useRef } from "react";
import { Loader2, Upload, AlertCircle } from "lucide-react";
import Modal from "./Modal";
import { importCSV } from "../api/keywords";

// Source presets: field name → CSV column header
const SOURCE_PRESETS = {
  manual: { label: "Manual / Personalizat", mapping: {} },
  ahrefs: {
    label: "Ahrefs",
    mapping: { keyword: "Keyword", search_volume: "Volume", keyword_difficulty: "KD", cpc_usd: "CPC" },
  },
  semrush: {
    label: "SEMrush",
    mapping: { keyword: "Keyword", search_volume: "Search Volume", keyword_difficulty: "Keyword Difficulty", cpc_usd: "CPC" },
  },
  gsc: {
    label: "Google Search Console",
    mapping: { keyword: "query", search_volume: "impressions" },
  },
};

const MAPPING_FIELDS = [
  { field: "keyword",            label: "Keyword *",          required: true },
  { field: "search_intent",      label: "Intent (opțional)",  required: false },
  { field: "page_type",          label: "Tip pagină (opț.)",  required: false },
  { field: "search_volume",      label: "Search Volume (opț.)", required: false },
  { field: "keyword_difficulty", label: "KD (opțional)",      required: false },
  { field: "cpc_usd",            label: "CPC USD (opț.)",     required: false },
];

function parseCSVPreview(text) {
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (!lines.length) return { headers: [], rows: [] };
  const splitLine = (line) => {
    const out = [];
    let cur = "", inQ = false;
    for (const ch of line) {
      if (ch === '"') { inQ = !inQ; continue; }
      if (ch === "," && !inQ) { out.push(cur.trim()); cur = ""; continue; }
      cur += ch;
    }
    out.push(cur.trim());
    return out;
  };
  const headers = splitLine(lines[0]);
  const rows = lines.slice(1, 6).map((l) => {
    const vals = splitLine(l);
    return Object.fromEntries(headers.map((h, i) => [h, vals[i] ?? ""]));
  });
  return { headers, rows };
}

// Auto-detect column mapping from CSV headers
function autoDetect(headers) {
  const find = (...patterns) =>
    headers.find((h) => patterns.some((p) => new RegExp(p, "i").test(h))) || "";
  return {
    keyword:            find("^keyword$", "cuvant", "^kw$", "query"),
    search_intent:      find("intent"),
    page_type:          find("type", "tip"),
    search_volume:      find("volume", "impressions", "search.vol"),
    keyword_difficulty: find("^kd$", "difficulty", "dificultat"),
    cpc_usd:            find("^cpc"),
  };
}

export default function ImportCSVModal({ open, onClose, campaignId, onDone }) {
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [source, setSource] = useState("manual");
  const [mapping, setMapping] = useState(
    Object.fromEntries(MAPPING_FIELDS.map(({ field }) => [field, ""]))
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const applyPreset = (preset, headers) => {
    const presetMap = SOURCE_PRESETS[preset]?.mapping || {};
    const detected  = autoDetect(headers);
    const merged = { ...detected };
    // Preset overrides auto-detect only for fields it defines
    for (const [field, col] of Object.entries(presetMap)) {
      if (headers.includes(col)) merged[field] = col;
    }
    setMapping(merged);
  };

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError("");
    const reader = new FileReader();
    reader.onload = (ev) => {
      const { headers, rows } = parseCSVPreview(ev.target.result);
      setPreview({ headers, rows });
      applyPreset(source, headers);
    };
    reader.readAsText(f);
  };

  const handleSourceChange = (newSource) => {
    setSource(newSource);
    if (preview) applyPreset(newSource, preview.headers);
  };

  const handleImport = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      // Build column_mapping: only include fields that have a CSV column assigned
      const colMap = {};
      for (const [field, col] of Object.entries(mapping)) {
        if (col) colMap[field] = col;
      }
      const res = await importCSV(campaignId, file, { columnMapping: colMap, source });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Import eșuat.");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null); setPreview(null); setResult(null); setError("");
    setSource("manual");
    setMapping(Object.fromEntries(MAPPING_FIELDS.map(({ field }) => [field, ""])));
    onClose();
    if (result) onDone?.();
  };

  const SELECT = "w-full rounded border border-border bg-bg px-2 py-1.5 text-xs text-white outline-none focus:border-accent";

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Importă CSV"
      size="xl"
      footer={
        result ? (
          <button onClick={handleClose} className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover transition">
            Închide
          </button>
        ) : (
          <>
            <button onClick={handleClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
              Anulează
            </button>
            <button
              onClick={handleImport}
              disabled={!file || !mapping.keyword || loading}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
            >
              {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Importă
            </button>
          </>
        )
      }
    >
      <div className="space-y-4">

        {/* Result */}
        {result && (
          <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 space-y-1">
            <p className="text-sm font-medium text-white">Import finalizat</p>
            <p className="text-xs text-muted">
              <span className="text-accent font-medium">{result.imported}</span> importate ·{" "}
              <span className="text-yellow-400 font-medium">{result.duplicates}</span> duplicate ·{" "}
              <span className="text-muted">{result.skipped}</span> omise
            </p>
          </div>
        )}

        {!result && (
          <>
            {/* Source preset */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted">Sursă date</label>
              <div className="flex flex-wrap gap-2">
                {Object.entries(SOURCE_PRESETS).map(([key, { label }]) => (
                  <button
                    key={key}
                    onClick={() => handleSourceChange(key)}
                    className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                      source === key
                        ? "border-accent bg-accent/10 text-accent"
                        : "border-border text-muted hover:border-accent/40 hover:text-white"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Upload zone */}
            <div
              onClick={() => fileRef.current?.click()}
              className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border py-6 transition hover:border-accent/50"
            >
              <Upload className="mb-2 h-6 w-6 text-muted" />
              <p className="text-sm text-muted">
                {file
                  ? <span className="text-white">{file.name}</span>
                  : "Click pentru a selecta fișierul CSV"}
              </p>
              <input ref={fileRef} type="file" accept=".csv,text/csv" className="hidden" onChange={handleFile} />
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Column mapping */}
            {preview && (
              <>
                <div className="grid grid-cols-3 gap-2">
                  {MAPPING_FIELDS.map(({ field, label }) => (
                    <div key={field}>
                      <label className="mb-1 block text-[11px] text-muted">{label}</label>
                      <select
                        value={mapping[field] || ""}
                        onChange={(e) => setMapping((m) => ({ ...m, [field]: e.target.value }))}
                        className={SELECT}
                      >
                        <option value="">— ignoră —</option>
                        {preview.headers.map((h) => (
                          <option key={h} value={h}>{h}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>

                {/* Preview table */}
                <div>
                  <p className="mb-1.5 text-[11px] text-muted">Preview primele {preview.rows.length} rânduri</p>
                  <div className="overflow-x-auto rounded-lg border border-border">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border bg-bg">
                          {preview.headers.map((h) => {
                            const mapped = Object.entries(mapping).find(([, col]) => col === h)?.[0];
                            return (
                              <th key={h} className="px-3 py-2 text-left font-medium">
                                <span className="text-muted">{h}</span>
                                {mapped && (
                                  <span className="ml-1 rounded bg-accent/10 px-1 text-[10px] text-accent">
                                    → {mapped}
                                  </span>
                                )}
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.map((row, i) => (
                          <tr key={i} className="border-b border-border/50 last:border-0">
                            {preview.headers.map((h) => (
                              <td key={h} className="px-3 py-2 text-white/80 truncate max-w-[160px]">{row[h]}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}
