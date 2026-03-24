import { useEffect, useState } from "react";
import { Loader2, DollarSign, Zap, AlertCircle } from "lucide-react";
import Modal from "./Modal";
import { estimateCost } from "../api/costs";

const MODEL_LABELS = {
  "claude-sonnet-4-20250514": "Claude Sonnet 4",
  "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
};

export default function CostEstimatorModal({ open, onClose, onConfirm, campaignId, keywordCount }) {
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!open || !campaignId || !keywordCount) return;
    setEstimate(null);
    setError("");
    setLoading(true);
    estimateCost(campaignId, keywordCount)
      .then((res) => setEstimate(res.data))
      .catch(() => setError("Nu s-a putut calcula estimarea."))
      .finally(() => setLoading(false));
  }, [open, campaignId, keywordCount]);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await onConfirm();
      onClose();
    } finally {
      setConfirming(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Estimare cost generare"
      size="sm"
      footer={
        <>
          <button onClick={onClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
            Anulează
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || !!error || confirming}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {confirming && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Confirmă și Generează
          </button>
        </>
      }
    >
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-accent" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      ) : estimate ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-bg p-4 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">Cuvinte cheie</span>
              <span className="font-medium text-white">{estimate.keyword_count}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">Model</span>
              <span className="font-medium text-white">{MODEL_LABELS[estimate.model] ?? estimate.model}</span>
            </div>
            <div className="h-px bg-border" />
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1 text-muted">
                <Zap className="h-3.5 w-3.5" />
                Tokeni estimați
              </span>
              <span className="font-medium text-white">
                {(estimate.estimated_tokens / 1000).toFixed(0)}k
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1 text-sm text-muted">
                <DollarSign className="h-3.5 w-3.5" />
                Cost estimat
              </span>
              <span className="text-base font-semibold text-white">
                ${Number(estimate.min_usd).toFixed(3)}
                <span className="text-muted"> – </span>
                ${Number(estimate.max_usd).toFixed(3)}
              </span>
            </div>
          </div>
          <p className="text-xs text-muted">
            Costul real poate varia în funcție de lungimea conținutului generat.
          </p>
        </div>
      ) : null}
    </Modal>
  );
}
