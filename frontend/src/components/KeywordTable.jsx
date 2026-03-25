import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap, Trash2, Pencil, Loader2, ChevronLeft, ChevronRight, FileText, Tag } from "lucide-react";
import StatusBadge from "./StatusBadge";
import Modal from "./Modal";
import { updateKeywordStatus } from "../api/keywords";
import { getPageByKeyword } from "../api/pages";

const INTENT_STYLE = {
  informational: "bg-blue-500/10 text-blue-400",
  transactional:  "bg-green-500/10 text-green-400",
  navigational:   "bg-purple-500/10 text-purple-400",
  commercial:     "bg-orange-500/10 text-orange-400",
};

const ALL_STATUSES = ["pending","queued","generating","draft","approved","published","error"];

function KdBadge({ kd }) {
  if (kd == null) return <span className="text-muted text-xs">—</span>;
  const cls =
    kd <= 30 ? "bg-green-500/10 text-green-400" :
    kd <= 60 ? "bg-yellow-500/10 text-yellow-400" :
               "bg-red-500/10 text-red-400";
  return <span className={`rounded-md px-1.5 py-0.5 text-[11px] font-medium ${cls}`}>{kd}</span>;
}

function VolDisplay({ vol }) {
  if (vol == null) return <span className="text-muted text-xs">—</span>;
  const fmt = vol >= 1000 ? `${(vol / 1000).toFixed(1)}K` : String(vol);
  return <span className="text-xs text-white">{fmt}</span>;
}

function IntentBadge({ intent }) {
  if (!intent) return <span className="text-muted text-xs">—</span>;
  const cls = INTENT_STYLE[intent] ?? "bg-gray-500/10 text-gray-400";
  return (
    <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${cls}`}>{intent}</span>
  );
}

export default function KeywordTable({
  keywords,
  total,
  page,
  limit,
  onPageChange,
  selectedIds,
  onSelectionChange,
  onGenerate,
  onDelete,
  onStatusChanged,
  generatingIds = new Set(),
}) {
  const navigate = useNavigate();
  const [editKw, setEditKw] = useState(null);
  const [viewingId, setViewingId] = useState(null);

  const handleViewPage = async (kwId) => {
    setViewingId(kwId);
    try {
      const res = await getPageByKeyword(kwId);
      const pageId = res.data?.data?.id;
      if (pageId) navigate(`/pages/${pageId}`);
    } catch {
      // no page yet
    } finally {
      setViewingId(null);
    }
  };
  const [editStatus, setEditStatus] = useState("");
  const [editLoading, setEditLoading] = useState(false);

  // Show volume/KD columns only when at least one keyword has data
  const hasVolume = keywords.some((k) => k.search_volume != null);
  const hasKD     = keywords.some((k) => k.keyword_difficulty != null);

  const totalPages = Math.max(1, Math.ceil(total / limit));
  const allChecked = keywords.length > 0 && keywords.every((k) => selectedIds.has(k.id));
  const someChecked = keywords.some((k) => selectedIds.has(k.id));

  const toggleAll = () => {
    if (allChecked) {
      const next = new Set(selectedIds);
      keywords.forEach((k) => next.delete(k.id));
      onSelectionChange(next);
    } else {
      const next = new Set(selectedIds);
      keywords.forEach((k) => next.add(k.id));
      onSelectionChange(next);
    }
  };

  const toggleOne = (id) => {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    onSelectionChange(next);
  };

  const openEdit = (kw) => {
    setEditKw(kw);
    setEditStatus(kw.status);
  };

  const saveEdit = async () => {
    if (!editKw) return;
    setEditLoading(true);
    try {
      await updateKeywordStatus(editKw.id, editStatus);
      onStatusChanged?.();
      setEditKw(null);
    } finally {
      setEditLoading(false);
    }
  };

  const SELECT_CLS = "w-full rounded border border-border bg-bg px-2 py-1.5 text-sm text-white outline-none focus:border-accent";

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-bg-card">
              <th className="w-10 px-4 py-3">
                <input
                  type="checkbox"
                  checked={allChecked}
                  ref={(el) => { if (el) el.indeterminate = someChecked && !allChecked; }}
                  onChange={toggleAll}
                  className="rounded border-border bg-bg accent-accent"
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted">Keyword</th>
              <th className="w-32 px-3 py-3 text-left text-xs font-medium text-muted">Intent</th>
              <th className="w-28 px-3 py-3 text-left text-xs font-medium text-muted">Tip</th>
              <th className="w-32 px-3 py-3 text-left text-xs font-medium text-muted">Status</th>
              {hasVolume && <th className="w-20 px-3 py-3 text-right text-xs font-medium text-muted">Volum</th>}
              {hasKD     && <th className="w-16 px-3 py-3 text-right text-xs font-medium text-muted">KD</th>}
              <th className="w-16 px-3 py-3 text-right text-xs font-medium text-muted">Cuvinte</th>
              <th className="w-20 px-3 py-3 text-right text-xs font-medium text-muted">Cost</th>
              <th className="w-28 px-3 py-3 text-right text-xs font-medium text-muted">Acțiuni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {keywords.length === 0 ? (
              <tr>
                <td colSpan={8 + (hasVolume ? 1 : 0) + (hasKD ? 1 : 0)} className="px-4 py-10 text-center text-sm text-muted">
                  Niciun cuvânt cheie
                </td>
              </tr>
            ) : (
              keywords.map((kw) => {
                const isGenerating = generatingIds.has(kw.id) || kw.status === "generating";
                const canGenerate = kw.status === "pending" || kw.status === "error";
                const canDelete  = kw.status === "pending" || kw.status === "error";
                const hasPage = ["draft", "approved", "published"].includes(kw.status);
                return (
                  <tr
                    key={kw.id}
                    className={`group transition hover:bg-bg-hover ${selectedIds.has(kw.id) ? "bg-accent/5" : ""} ${kw.cluster_role === "secondary" ? "opacity-80" : ""}`}
                  >
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(kw.id)}
                        onChange={() => toggleOne(kw.id)}
                        className="rounded border-border bg-bg accent-accent"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className={kw.cluster_role === "secondary" ? "pl-4" : ""}>
                        <div className="flex items-center gap-1.5">
                          {kw.cluster_role === "secondary" && (
                            <Tag className="h-3 w-3 text-muted flex-shrink-0" />
                          )}
                          <span className={`text-sm ${kw.cluster_role === "secondary" ? "text-white/70" : "text-white"}`}>
                            {kw.keyword}
                          </span>
                          {kw.cluster_role === "primary" && (
                            <span className="rounded bg-green-500/10 px-1.5 py-0.5 text-[10px] font-medium text-green-400">P</span>
                          )}
                        </div>
                        {kw.error_message && (
                          <p className="mt-0.5 text-[11px] text-red-400 truncate max-w-xs" title={kw.error_message}>
                            {kw.error_message}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-3"><IntentBadge intent={kw.search_intent} /></td>
                    <td className="px-3 py-3">
                      {kw.page_type
                        ? <span className="text-xs text-muted">{kw.page_type}</span>
                        : <span className="text-muted text-xs">—</span>}
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge status={kw.status} />
                    </td>
                    {hasVolume && (
                      <td className="px-3 py-3 text-right">
                        <VolDisplay vol={kw.search_volume} />
                      </td>
                    )}
                    {hasKD && (
                      <td className="px-3 py-3 text-right">
                        <KdBadge kd={kw.keyword_difficulty} />
                      </td>
                    )}
                    <td className="px-3 py-3 text-right text-xs text-muted">
                      {kw.word_count > 0 ? kw.word_count : "—"}
                    </td>
                    <td className="px-3 py-3 text-right text-xs text-muted">
                      {kw.cost_usd > 0 ? `$${Number(kw.cost_usd).toFixed(4)}` : "—"}
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {/* Generate */}
                        <button
                          disabled={!canGenerate || isGenerating}
                          onClick={() => canGenerate && onGenerate(kw.id)}
                          title="Generează"
                          className={`rounded-md p-1.5 transition ${
                            canGenerate
                              ? "text-accent hover:bg-accent/10"
                              : "cursor-not-allowed text-muted/30"
                          }`}
                        >
                          {isGenerating
                            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            : <Zap className="h-3.5 w-3.5" />}
                        </button>
                        {/* View page */}
                        {hasPage && (
                          <button
                            onClick={() => handleViewPage(kw.id)}
                            disabled={viewingId === kw.id}
                            title="Deschide pagina"
                            className="rounded-md p-1.5 text-accent transition hover:bg-accent/10 disabled:opacity-50"
                          >
                            {viewingId === kw.id
                              ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              : <FileText className="h-3.5 w-3.5" />}
                          </button>
                        )}
                        {/* Edit status */}
                        <button
                          onClick={() => openEdit(kw)}
                          title="Editează status"
                          className="rounded-md p-1.5 text-muted transition hover:bg-bg-hover hover:text-white"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        {/* Delete */}
                        <button
                          disabled={!canDelete}
                          onClick={() => canDelete && onDelete(kw.id)}
                          title="Șterge"
                          className={`rounded-md p-1.5 transition ${
                            canDelete
                              ? "text-red-400 hover:bg-red-500/10"
                              : "cursor-not-allowed text-muted/30"
                          }`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted">
          <span>{total} cuvinte cheie totale</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="rounded-lg border border-border p-1.5 hover:text-white disabled:opacity-40 transition"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-white">
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="rounded-lg border border-border p-1.5 hover:text-white disabled:opacity-40 transition"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Edit status modal */}
      <Modal
        open={!!editKw}
        onClose={() => setEditKw(null)}
        title="Editează status"
        size="sm"
        footer={
          <>
            <button onClick={() => setEditKw(null)} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
              Anulează
            </button>
            <button
              onClick={saveEdit}
              disabled={editLoading}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
            >
              {editLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Salvează
            </button>
          </>
        }
      >
        {editKw && (
          <div>
            <p className="mb-3 text-sm text-white font-medium truncate">{editKw.keyword}</p>
            <label className="mb-1.5 block text-xs text-muted">Status nou</label>
            <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)} className={SELECT_CLS}>
              {ALL_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        )}
      </Modal>
    </>
  );
}
