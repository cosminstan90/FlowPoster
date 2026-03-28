import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Loader2, ChevronLeft, Upload, ClipboardList, Plus,
  Zap, Globe, Download, Hash, AlertTriangle, Layers,
} from "lucide-react";
import { getCampaign, updateCampaign } from "../api/campaigns";
import { getKeywords, deleteKeyword, importPaste } from "../api/keywords";
import { generateSingle, generateBulk } from "../api/generate";
import { updateKeywordStatus } from "../api/keywords";
import KeywordTable from "../components/KeywordTable";
import BulkActionBar from "../components/BulkActionBar";
import ImportCSVModal from "../components/ImportCSVModal";
import PasteModal from "../components/PasteModal";
import CostEstimatorModal from "../components/CostEstimatorModal";
import ClusteringModal from "../components/ClusteringModal";
import Modal from "../components/Modal";
import { createKeyword } from "../api/keywords";

const STAT_CARD = [
  { key: "total",      label: "Total",       cls: "text-white" },
  { key: "generating", label: "Generare",    cls: "text-yellow-400" },
  { key: "draft",      label: "Draft",       cls: "text-orange-400" },
  { key: "approved",   label: "Aprobate",    cls: "text-green-400" },
  { key: "published",  label: "Publicate",   cls: "text-teal-400" },
  { key: "error",      label: "Erori",       cls: "text-red-400" },
];

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";
const LABEL = "mb-1.5 block text-xs text-muted";

export default function CampaignPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [campaign, setCampaign] = useState(null);
  const [keywords, setKeywords] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, limit: 50 });
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [generatingIds, setGeneratingIds] = useState(new Set());

  // Selection
  const [selectedIds, setSelectedIds] = useState(new Set());

  // Modals
  const [showCSV, setShowCSV] = useState(false);
  const [showPaste, setShowPaste] = useState(false);
  const [showCost, setShowCost] = useState(false);
  const [showManual, setShowManual] = useState(false);
  const [showCluster, setShowCluster] = useState(false);
  const [manualKw, setManualKw] = useState("");
  const [manualIntent, setManualIntent] = useState("");
  const [manualType, setManualType] = useState("");
  const [manualLoading, setManualLoading] = useState(false);

  // Scheduling
  const [schedEnabled, setSchedEnabled] = useState(false);
  const [schedPages, setSchedPages] = useState(1);
  const [schedTime, setSchedTime] = useState("10:00");
  const [schedSaving, setSchedSaving] = useState(false);
  const [schedSaved, setSchedSaved] = useState(false);

  // GEO/AEO
  const [geoEnabled, setGeoEnabled] = useState(false);
  const [geoMode, setGeoMode] = useState("balanced");
  const [geoSaving, setGeoSaving] = useState(false);
  const [geoSaved, setGeoSaved] = useState(false);

  // Auto-refresh
  const intervalRef = useRef(null);

  const fetchKeywords = useCallback(async (page = pagination.page) => {
    try {
      const res = await getKeywords(id, { page, limit: pagination.limit });
      setKeywords(res.data?.items || []);
      setPagination((p) => ({ ...p, total: res.data?.total || 0, page: res.data?.page || 1 }));
    } catch (err) {
      console.error(err);
    }
  }, [id, pagination.limit, pagination.page]);

  const fetchCampaign = useCallback(async () => {
    const res = await getCampaign(id);
    const c = res.data;
    setCampaign(c);
    setCounts(c?.keyword_counts || {});
    // Sync schedule state
    const sched = c?.publish_schedule || {};
    setSchedEnabled(sched.enabled || false);
    setSchedPages(sched.pages_per_day || 1);
    setSchedTime(sched.time_of_day || "10:00");
    // Sync GEO state
    setGeoEnabled(c?.geo_enabled || false);
    setGeoMode(c?.geo_mode || "balanced");
  }, [id]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([fetchCampaign(), fetchKeywords(1)]);
    } finally {
      setLoading(false);
    }
  }, [fetchCampaign, fetchKeywords]);

  useEffect(() => {
    load();
  }, [id]);

  // Auto-refresh: poll every 5s if any keyword is queued/generating
  useEffect(() => {
    const hasActive = keywords.some((k) => ["queued", "generating"].includes(k.status));
    if (hasActive) {
      if (!intervalRef.current) {
        intervalRef.current = setInterval(async () => {
          await fetchKeywords(pagination.page);
          await fetchCampaign();
        }, 5000);
      }
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {};
  }, [keywords, pagination.page]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // ---- Actions ----

  const handleGenerate = async (kwId) => {
    setGeneratingIds((s) => new Set(s).add(kwId));
    try {
      await generateSingle(kwId);
    } finally {
      setGeneratingIds((s) => { const n = new Set(s); n.delete(kwId); return n; });
      await fetchKeywords(pagination.page);
      await fetchCampaign();
    }
  };

  const handleDelete = async (kwId) => {
    await deleteKeyword(kwId);
    setSelectedIds((s) => { const n = new Set(s); n.delete(kwId); return n; });
    await fetchKeywords(pagination.page);
    await fetchCampaign();
  };

  const handleBulkApprove = async () => {
    await Promise.all([...selectedIds].map((kwId) => updateKeywordStatus(kwId, "approved").catch(() => {})));
    setSelectedIds(new Set());
    await fetchKeywords(pagination.page);
    await fetchCampaign();
  };

  const handleBulkPublish = async () => {
    await Promise.all([...selectedIds].map((kwId) => updateKeywordStatus(kwId, "published").catch(() => {})));
    setSelectedIds(new Set());
    await fetchKeywords(pagination.page);
    await fetchCampaign();
  };

  const handleBulkDelete = async () => {
    await Promise.all([...selectedIds].map((kwId) => deleteKeyword(kwId).catch(() => {})));
    setSelectedIds(new Set());
    await fetchKeywords(pagination.page);
    await fetchCampaign();
  };

  const handleConfirmGenerate = async () => {
    const kwIds = [...selectedIds];
    await generateBulk(id, kwIds, true);
    setSelectedIds(new Set());
    await fetchKeywords(pagination.page);
    await fetchCampaign();
  };

  const handleManualAdd = async (e) => {
    e.preventDefault();
    setManualLoading(true);
    try {
      await createKeyword({ campaign_id: id, keyword: manualKw, search_intent: manualIntent || null, page_type: manualType || null });
      setManualKw(""); setManualIntent(""); setManualType("");
      setShowManual(false);
      await fetchKeywords(pagination.page);
      await fetchCampaign();
    } finally {
      setManualLoading(false);
    }
  };

  const handlePasteImport = async (text) => {
    await importPaste(id, text);
    await fetchKeywords(1);
    await fetchCampaign();
  };

  const handleGeoToggle = async (enabled) => {
    setGeoEnabled(enabled);
    await updateCampaign(id, { geo_enabled: enabled, geo_mode: geoMode });
    await fetchCampaign();
  };

  const handleSaveGeo = async () => {
    setGeoSaving(true);
    try {
      await updateCampaign(id, { geo_enabled: geoEnabled, geo_mode: geoMode });
      setGeoSaved(true);
      setTimeout(() => setGeoSaved(false), 2000);
    } finally {
      setGeoSaving(false);
    }
  };

  const handleSaveSchedule = async () => {
    setSchedSaving(true);
    try {
      await updateCampaign(id, {
        publish_schedule: {
          enabled: schedEnabled,
          pages_per_day: Number(schedPages),
          time_of_day: schedTime,
        },
      });
      setSchedSaved(true);
      setTimeout(() => setSchedSaved(false), 2000);
    } finally {
      setSchedSaving(false);
    }
  };

  // Progress bar: queued + generating
  const activeCount = (counts.queued || 0) + (counts.generating || 0);
  const doneCount   = (counts.draft || 0) + (counts.approved || 0) + (counts.published || 0);
  const batchTotal  = activeCount + doneCount;
  const progressPct = batchTotal > 0 ? Math.round((doneCount / batchTotal) * 100) : 0;

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  if (!campaign) {
    return <div className="text-center text-muted py-12">Campanie negăsită</div>;
  }

  return (
    <div className="space-y-6 pb-20">
      {/* Back */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-1 text-sm text-muted hover:text-white transition"
        >
          <ChevronLeft className="h-4 w-4" />
          Înapoi la proiect
        </button>
        <h1 className="text-2xl font-semibold text-white">{campaign.name}</h1>
        {campaign.description && <p className="text-sm text-muted mt-1">{campaign.description}</p>}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
        {STAT_CARD.map(({ key, label, cls }) => (
          <div key={key} className="rounded-lg border border-border bg-bg-card px-4 py-3 text-center">
            <p className={`text-xl font-semibold ${cls}`}>{counts[key] ?? 0}</p>
            <p className="text-[11px] text-muted">{label}</p>
          </div>
        ))}
      </div>

      {/* Generation progress */}
      {activeCount > 0 && (
        <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/5 px-4 py-3">
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-yellow-400">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              {counts.generating || 0} în generare · {counts.queued || 0} în așteptare
            </span>
            <span className="text-muted">{progressPct}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-border overflow-hidden">
            <div
              className="h-full rounded-full bg-yellow-500 transition-all duration-1000"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setShowCSV(true)}
          className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm text-muted hover:border-accent/40 hover:text-white transition"
        >
          <Upload className="h-4 w-4" />
          Import CSV
        </button>
        <button
          onClick={() => setShowPaste(true)}
          className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm text-muted hover:border-accent/40 hover:text-white transition"
        >
          <ClipboardList className="h-4 w-4" />
          Paste Keywords
        </button>
        <button
          onClick={() => setShowManual(true)}
          className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm text-muted hover:border-accent/40 hover:text-white transition"
        >
          <Plus className="h-4 w-4" />
          Manual
        </button>

        <div className="ml-auto flex items-center gap-2">
          {(counts.pending || 0) >= 3 && (
            <button
              onClick={() => setShowCluster(true)}
              className="flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-500/10 px-3 py-2 text-sm font-medium text-purple-400 hover:bg-purple-500/20 transition"
            >
              <Layers className="h-4 w-4" />
              Analizează Clustere
            </button>
          )}
          {selectedIds.size > 0 && (
            <button
              onClick={() => setShowCost(true)}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
            >
              <Zap className="h-4 w-4" />
              Generează selectate ({selectedIds.size})
            </button>
          )}
        </div>
      </div>

      {/* GEO/AEO Mode */}
      <div className="rounded-xl border border-border bg-bg-card p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-medium text-white">Mod GEO/AEO</h3>
            <p className="text-xs text-muted mt-0.5">Optimizare pentru AI: ChatGPT, Perplexity, Gemini</p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              type="checkbox"
              checked={geoEnabled}
              onChange={(e) => handleGeoToggle(e.target.checked)}
              className="peer sr-only"
            />
            <div className="peer h-6 w-11 rounded-full bg-border after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-accent peer-checked:after:translate-x-full"></div>
          </label>
        </div>
        {geoEnabled && (
          <div className="space-y-3">
            <label className="block text-xs text-muted">Mod optimizare</label>
            <select
              value={geoMode}
              onChange={(e) => setGeoMode(e.target.value)}
              className={FIELD}
            >
              <option value="balanced">Echilibrat (SEO + GEO)</option>
              <option value="geo_first">GEO First — prioritate AI citability</option>
              <option value="seo_first">SEO First — structură tradițională</option>
            </select>
            <div className="rounded-lg bg-purple-500/10 border border-purple-500/20 px-3 py-2 text-xs text-purple-300">
              {geoMode === "geo_first" && "Conținut optimizat pentru a fi citat de ChatGPT, Perplexity și Gemini. Fiecare paragraf devine o afirmație citabilă."}
              {geoMode === "seo_first" && "Structură SEO tradițională cu îmbunătățiri GEO. Ideal pentru site-uri cu autoritate deja stabilită."}
              {geoMode === "balanced" && "Echilibru între SEO clasic și optimizare pentru AI. Recomandat pentru majoritatea site-urilor."}
            </div>
            <button
              onClick={handleSaveGeo}
              disabled={geoSaving}
              className="flex items-center gap-1.5 rounded-lg bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50 transition"
            >
              {geoSaving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {geoSaved ? "Salvat!" : "Salvează GEO"}
            </button>
          </div>
        )}
      </div>

      {/* Scheduling */}
      <div className="rounded-xl border border-border bg-bg-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-medium text-white">Publicare automată</h3>
          <label className="flex cursor-pointer items-center gap-2">
            <div
              onClick={() => setSchedEnabled((v) => !v)}
              className={`relative h-5 w-9 rounded-full transition ${schedEnabled ? "bg-accent" : "bg-border"}`}
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${schedEnabled ? "translate-x-4" : "translate-x-0.5"}`}
              />
            </div>
            <span className="text-xs text-muted">{schedEnabled ? "Activ" : "Inactiv"}</span>
          </label>
        </div>

        {schedEnabled && (
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className={LABEL}>Pagini per zi</label>
              <input
                type="number"
                min={1}
                max={50}
                value={schedPages}
                onChange={(e) => setSchedPages(e.target.value)}
                className={FIELD}
              />
            </div>
            <div>
              <label className={LABEL}>Ora publicare (UTC)</label>
              <input
                type="time"
                value={schedTime}
                onChange={(e) => setSchedTime(e.target.value)}
                className={FIELD}
              />
            </div>
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={handleSaveSchedule}
            disabled={schedSaving}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {schedSaving && <Loader2 className="h-3 w-3 animate-spin" />}
            {schedSaved ? "Salvat!" : "Salvează"}
          </button>
          {schedEnabled && (
            <p className="text-xs text-muted">
              Se publică {schedPages} pag./zi la ora {schedTime} UTC
            </p>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="space-y-3">
        <KeywordTable
          keywords={keywords}
          total={pagination.total}
          page={pagination.page}
          limit={pagination.limit}
          onPageChange={(p) => fetchKeywords(p)}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
          onGenerate={handleGenerate}
          onDelete={handleDelete}
          onStatusChanged={() => { fetchKeywords(pagination.page); fetchCampaign(); }}
          generatingIds={generatingIds}
        />
      </div>

      {/* Floating bulk bar */}
      <BulkActionBar
        count={selectedIds.size}
        onGenerate={() => setShowCost(true)}
        onApprove={handleBulkApprove}
        onPublish={handleBulkPublish}
        onDelete={handleBulkDelete}
        onClear={() => setSelectedIds(new Set())}
      />

      {/* Modals */}
      <ImportCSVModal
        open={showCSV}
        onClose={() => setShowCSV(false)}
        campaignId={id}
        onDone={() => { fetchKeywords(1); fetchCampaign(); }}
      />

      <PasteModal
        open={showPaste}
        onClose={() => setShowPaste(false)}
        onImport={handlePasteImport}
      />

      <CostEstimatorModal
        open={showCost}
        onClose={() => setShowCost(false)}
        onConfirm={handleConfirmGenerate}
        campaignId={id}
        keywordCount={selectedIds.size || counts.total}
      />

      <ClusteringModal
        open={showCluster}
        onClose={() => setShowCluster(false)}
        campaignId={id}
        pendingCount={counts.pending || 0}
        onDone={() => { fetchKeywords(pagination.page); fetchCampaign(); }}
      />

      {/* Manual add modal */}
      <Modal
        open={showManual}
        onClose={() => setShowManual(false)}
        title="Adaugă keyword manual"
        size="sm"
        footer={
          <>
            <button onClick={() => setShowManual(false)} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
              Anulează
            </button>
            <button
              form="manual-kw-form"
              type="submit"
              disabled={manualLoading || !manualKw.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
            >
              {manualLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Adaugă
            </button>
          </>
        }
      >
        <form id="manual-kw-form" onSubmit={handleManualAdd} className="space-y-3">
          <div>
            <label className={LABEL}>Keyword *</label>
            <input
              value={manualKw}
              onChange={(e) => setManualKw(e.target.value)}
              required
              autoFocus
              className={FIELD}
              placeholder="ex: cele mai bune laptopuri 2024"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={LABEL}>Intent (opțional)</label>
              <select value={manualIntent} onChange={(e) => setManualIntent(e.target.value)} className={FIELD}>
                <option value="">— selectează —</option>
                <option value="informational">Informational</option>
                <option value="navigational">Navigational</option>
                <option value="transactional">Transactional</option>
                <option value="commercial">Commercial</option>
              </select>
            </div>
            <div>
              <label className={LABEL}>Tip pagină (opțional)</label>
              <select value={manualType} onChange={(e) => setManualType(e.target.value)} className={FIELD}>
                <option value="">— selectează —</option>
                <option value="blog_post">Blog post</option>
                <option value="landing_page">Landing page</option>
                <option value="product_review">Product review</option>
                <option value="how_to">How-to</option>
                <option value="listicle">Listicle</option>
                <option value="comparison">Comparison</option>
              </select>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}
