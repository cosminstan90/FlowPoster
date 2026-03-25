import { useState } from "react";
import { Loader2, CheckCircle, Layers, Tag } from "lucide-react";
import Modal from "./Modal";
import { clusterKeywords } from "../api/keywords";

const REC_STYLE = {
  one_page_pillar:    { cls: "bg-blue-500/10 text-blue-400",   label: "Pagină Pillar" },
  separate_pages:     { cls: "bg-purple-500/10 text-purple-400", label: "Pagini Separate" },
  merge_with_primary: { cls: "bg-teal-500/10 text-teal-400",   label: "Merge cu Primary" },
};

function RecBadge({ rec }) {
  const s = REC_STYLE[rec] ?? { cls: "bg-gray-500/10 text-gray-400", label: rec };
  return (
    <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${s.cls}`}>
      {s.label}
    </span>
  );
}

export default function ClusteringModal({ open, onClose, campaignId, pendingCount, onDone }) {
  const [loading, setLoading]   = useState(false);
  const [clusters, setClusters] = useState(null);
  const [error, setError]       = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await clusterKeywords(campaignId, []);
      setClusters(res.data?.clusters || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Clustering eșuat. Încearcă din nou.");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setClusters(null);
    setError("");
    onClose();
    if (clusters) onDone?.();
  };

  const handleConfirmAll = () => {
    handleClose();
  };

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Analiză Clustere Keyword"
      size="xl"
      footer={
        clusters ? (
          <div className="flex gap-2">
            <button
              onClick={handleClose}
              className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition"
            >
              Selectează Manual
            </button>
            <button
              onClick={handleConfirmAll}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
            >
              <CheckCircle className="h-4 w-4" />
              Confirmă Toate
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <button onClick={handleClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
              Anulează
            </button>
            {!loading && !clusters && (
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
              >
                <Layers className="h-4 w-4" />
                Analizează {pendingCount} keywords
              </button>
            )}
          </div>
        )
      }
    >
      <div className="space-y-4 min-h-[200px]">

        {/* Initial state */}
        {!loading && !clusters && !error && (
          <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
            <div className="rounded-full bg-accent/10 p-4">
              <Layers className="h-8 w-8 text-accent" />
            </div>
            <div>
              <p className="text-white font-medium">Clustering semantic cu AI</p>
              <p className="text-sm text-muted mt-1">
                Claude Haiku va analiza cele {pendingCount} keywords pendinge și le va grupa
                semantic pentru o strategie SEO optimă.
              </p>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-sm text-muted">Analizăm keywords cu Claude Haiku…</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Results */}
        {clusters && clusters.length > 0 && (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
            <p className="text-xs text-muted">
              {clusters.length} clustere identificate · click pe un cluster pentru detalii
            </p>
            {clusters.map((c) => (
              <ClusterCard key={c.cluster_id} cluster={c} />
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

function ClusterCard({ cluster }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-border bg-bg-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-bg-hover transition text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Layers className="h-4 w-4 text-accent flex-shrink-0" />
          <span className="text-sm font-medium text-white truncate">{cluster.cluster_name}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          <RecBadge rec={cluster.recommendation} />
          <span className="text-[11px] text-muted">
            {1 + cluster.secondary_keywords.length} kw
          </span>
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
          {/* Primary keyword */}
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-green-500/10 px-2 py-0.5 text-[11px] font-medium text-green-400">
              PRIMARY
            </span>
            <span className="text-sm text-white">{cluster.primary_keyword}</span>
          </div>

          {/* Secondary keywords */}
          {cluster.secondary_keywords.length > 0 && (
            <div className="space-y-1">
              <p className="text-[11px] text-muted font-medium">Keywords secundare:</p>
              {cluster.secondary_keywords.map((kw) => (
                <div key={kw} className="flex items-center gap-2 pl-2">
                  <Tag className="h-3 w-3 text-muted flex-shrink-0" />
                  <span className="text-xs text-white/80">{kw}</span>
                </div>
              ))}
            </div>
          )}

          {/* Reasoning */}
          <p className="text-xs text-muted italic border-l-2 border-border pl-3">
            {cluster.reasoning}
          </p>
        </div>
      )}
    </div>
  );
}
