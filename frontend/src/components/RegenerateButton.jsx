import { RefreshCw } from "lucide-react";

export default function RegenerateButton({ onClick, loading = false, label = "Regenerează" }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      title={label}
      className="flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted hover:border-accent/40 hover:text-white disabled:opacity-50 transition"
    >
      <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
      {label}
    </button>
  );
}
