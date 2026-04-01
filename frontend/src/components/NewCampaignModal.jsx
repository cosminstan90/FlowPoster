import { useState } from "react";
import { Loader2 } from "lucide-react";
import Modal from "./Modal";

const MODEL_GROUPS = [
  {
    label: "Anthropic Claude",
    models: [
      { value: "claude-sonnet-4-6",        label: "Claude Sonnet 4.6 — recomandat" },
      { value: "claude-opus-4-6",           label: "Claude Opus 4.6 — calitate maximă" },
      { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5 — rapid / ieftin" },
    ],
  },
  {
    label: "OpenAI",
    models: [
      { value: "gpt-4o",      label: "GPT-4o" },
      { value: "gpt-4o-mini", label: "GPT-4o mini — ieftin" },
      { value: "o3-mini",     label: "o3-mini" },
    ],
  },
];

const LANGUAGES = [
  { value: "ro", label: "Română" },
  { value: "en", label: "English" },
];

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";
const LABEL = "mb-1.5 block text-xs text-muted";

export default function NewCampaignModal({ open, onClose, onSave }) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    language: "ro",
    model: "claude-sonnet-4-6",
    pages_per_day: 5,
    time_of_day: "08:00",
  });
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave({
        name: form.name,
        description: form.description || null,
        language: form.language,
        model: form.model,
        publish_schedule:
          form.pages_per_day > 0
            ? { pages_per_day: Number(form.pages_per_day), time_of_day: form.time_of_day }
            : null,
      });
      setForm({ name: "", description: "", language: "ro", model: "claude-sonnet-4-6", pages_per_day: 5, time_of_day: "08:00" });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Campanie nouă"
      size="md"
      footer={
        <>
          <button onClick={onClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
            Anulează
          </button>
          <button
            form="new-campaign-form"
            type="submit"
            disabled={loading || !form.name}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Creează campanie
          </button>
        </>
      }
    >
      <form id="new-campaign-form" onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className={LABEL}>Nume *</label>
          <input value={form.name} onChange={set("name")} required className={FIELD} placeholder="Campania mea SEO" />
        </div>

        <div>
          <label className={LABEL}>Descriere</label>
          <textarea value={form.description} onChange={set("description")} rows={2} className={`${FIELD} resize-none`} placeholder="Opțional..." />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={LABEL}>Limbă</label>
            <select value={form.language} onChange={set("language")} className={FIELD}>
              {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
          <div>
            <label className={LABEL}>Model AI</label>
            <select value={form.model} onChange={set("model")} className={FIELD}>
              {MODEL_GROUPS.map((g) => (
                <optgroup key={g.label} label={g.label}>
                  {g.models.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        </div>

        <div className="rounded-lg border border-border p-3">
          <p className="mb-3 text-xs font-medium text-white">Program publicare</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={LABEL}>Pagini / zi</label>
              <input type="number" min={0} max={100} value={form.pages_per_day} onChange={set("pages_per_day")} className={FIELD} />
            </div>
            <div>
              <label className={LABEL}>Ora publicare</label>
              <input type="time" value={form.time_of_day} onChange={set("time_of_day")} className={FIELD} />
            </div>
          </div>
        </div>
      </form>
    </Modal>
  );
}
