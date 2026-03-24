import { Zap, CheckCircle, Globe, Trash2, X } from "lucide-react";

export default function BulkActionBar({ count, onGenerate, onApprove, onPublish, onDelete, onClear }) {
  if (count === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 z-40 -translate-x-1/2">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-bg-card px-4 py-3 shadow-2xl shadow-black/50">
        <span className="mr-2 text-sm font-medium text-white">{count} selectate</span>

        <button
          onClick={onGenerate}
          className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-black hover:bg-accent-hover transition"
        >
          <Zap className="h-3.5 w-3.5" />
          Generează
        </button>
        <button
          onClick={onApprove}
          className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition"
        >
          <CheckCircle className="h-3.5 w-3.5" />
          Aprobă
        </button>
        <button
          onClick={onPublish}
          className="flex items-center gap-1.5 rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-teal-700 transition"
        >
          <Globe className="h-3.5 w-3.5" />
          Publică
        </button>
        <button
          onClick={onDelete}
          className="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Șterge
        </button>

        <div className="mx-1 h-4 w-px bg-border" />

        <button onClick={onClear} className="rounded-md p-1 text-muted hover:text-white transition">
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
