import { useState, useEffect } from "react";
import { Loader2, Zap } from "lucide-react";
import Modal from "./Modal";
import { testTemplate } from "../api/templates";
import { getCampaigns } from "../api/campaigns";
import { getProjects } from "../api/projects";

export default function TemplateTestModal({ open, onClose, template }) {
  const [campaigns, setCampaigns] = useState([]);
  const [campaignId, setCampaignId] = useState("");
  const [keyword, setKeyword] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) { setResult(null); setError(""); return; }
    async function load() {
      try {
        const projRes = await getProjects();
        const projects = projRes.data || [];
        const all = [];
        for (const p of projects) {
          const campRes = await getCampaigns(p.id);
          for (const c of campRes.data || []) {
            all.push({ ...c, projectName: p.name });
          }
        }
        setCampaigns(all);
        if (all.length > 0) setCampaignId(all[0].id);
      } catch { /* ignore */ }
    }
    load();
  }, [open]);

  const handleRun = async () => {
    if (!keyword.trim() || !campaignId) return;
    setRunning(true);
    setResult(null);
    setError("");
    try {
      const res = await testTemplate(template.id, {
        test_keyword: keyword.trim(),
        campaign_id: campaignId,
      });
      setResult(res.data?.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Test failed");
    } finally {
      setRunning(false);
    }
  };

  const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Test: ${template?.name || ""}`}
      size="lg"
      footer={
        <>
          <button onClick={onClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
            Închide
          </button>
          <button
            onClick={handleRun}
            disabled={running || !keyword.trim() || !campaignId}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            {running ? "Se generează..." : "Rulează test"}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1.5 block text-xs text-muted">Keyword de test</label>
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRun()}
              className={FIELD}
              placeholder="ex: cele mai bune laptopuri 2024"
              autoFocus
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted">Campanie (pentru context)</label>
            <select
              value={campaignId}
              onChange={(e) => setCampaignId(e.target.value)}
              className={FIELD}
            >
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.projectName} › {c.name}
                </option>
              ))}
              {campaigns.length === 0 && <option value="">Nicio campanie</option>}
            </select>
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</div>
        )}

        {running && (
          <div className="flex flex-col items-center gap-2 py-6">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-sm text-muted">Generez outline + conținut cu template-ul...</p>
          </div>
        )}

        {result && !running && (
          <div className="space-y-3">
            {/* Cost bar */}
            <div className="grid grid-cols-3 gap-3">
              <MetaCard label="Tokeni folosiți" value={result.tokens_used?.toLocaleString()} />
              <MetaCard label="Cost USD" value={`$${result.cost_usd?.toFixed(4)}`} />
              <MetaCard label="Timp generare" value={`${result.time_seconds}s`} />
            </div>
            {/* Content preview */}
            <div>
              <p className="mb-1.5 text-xs font-medium text-muted">Preview conținut (text simplu)</p>
              <div className="max-h-64 overflow-y-auto rounded-lg border border-border bg-bg p-3 text-sm text-white leading-relaxed">
                {result.content_preview || "(nicio previzualizare)"}
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}

function MetaCard({ label, value }) {
  return (
    <div className="rounded-lg border border-border bg-bg px-3 py-2 text-center">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-sm font-semibold text-white">{value}</p>
    </div>
  );
}
