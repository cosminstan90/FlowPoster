import { useState } from "react";
import { Loader2 } from "lucide-react";
import Modal from "./Modal";

export default function PasteModal({ open, onClose, onImport }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const handleImport = async () => {
    if (!lines.length) return;
    setLoading(true);
    try {
      await onImport(text);
      setText("");
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Importă cuvinte cheie (lipire)"
      size="md"
      footer={
        <>
          <button onClick={onClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
            Anulează
          </button>
          <button
            onClick={handleImport}
            disabled={loading || !lines.length}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Importă {lines.length > 0 ? `(${lines.length})` : ""}
          </button>
        </>
      }
    >
      <div className="space-y-3">
        <p className="text-xs text-muted">Un cuvânt cheie per linie.</p>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          placeholder={"cel mai bun laptop 2024\ncum sa faci pizza acasa\nreteta tort ciocolata\n..."}
          className="w-full rounded-lg border border-border bg-bg px-3 py-2 font-mono text-sm text-white outline-none transition focus:border-accent resize-none"
          autoFocus
        />
        {lines.length > 0 && (
          <p className="text-xs text-muted">
            <span className="text-accent font-medium">{lines.length}</span> cuvinte cheie detectate
          </p>
        )}
      </div>
    </Modal>
  );
}
