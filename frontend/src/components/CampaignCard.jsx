import { ArrowRight, Cpu } from "lucide-react";

const MODEL_SHORT = {
  "claude-sonnet-4-20250514": { label: "Sonnet 4", cls: "bg-violet-500/10 text-violet-400 border-violet-500/20" },
  "claude-haiku-4-5-20251001": { label: "Haiku 4.5", cls: "bg-sky-500/10 text-sky-400 border-sky-500/20" },
};

const LANG_LABEL = { ro: "RO", en: "EN" };

const STAT_COUNTS = [
  { key: "pending",    cls: "bg-slate-500/15 text-slate-400" },
  { key: "generating", cls: "bg-yellow-500/15 text-yellow-400" },
  { key: "draft",      cls: "bg-orange-500/15 text-orange-400" },
  { key: "approved",   cls: "bg-green-500/15 text-green-400" },
  { key: "published",  cls: "bg-teal-500/15 text-teal-400" },
  { key: "error",      cls: "bg-red-500/15 text-red-400" },
];

export default function CampaignCard({ campaign, counts, onOpen }) {
  const model = MODEL_SHORT[campaign.model] ?? { label: campaign.model, cls: "bg-gray-500/10 text-gray-400" };
  const lang = LANG_LABEL[campaign.language] ?? campaign.language?.toUpperCase();

  return (
    <div className="flex flex-col rounded-xl border border-border bg-bg-card p-5 transition hover:border-accent/30">
      {/* Header */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-white">{campaign.name}</h3>
          {campaign.description && (
            <p className="mt-0.5 truncate text-xs text-muted">{campaign.description}</p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <span className="rounded border border-border px-1.5 py-0.5 text-[11px] text-muted">{lang}</span>
          <span className={`rounded border px-1.5 py-0.5 text-[11px] font-medium ${model.cls}`}>
            <span className="flex items-center gap-1">
              <Cpu className="h-3 w-3" />
              {model.label}
            </span>
          </span>
        </div>
      </div>

      {/* Status counts */}
      {counts && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          {STAT_COUNTS.map(({ key, cls }) =>
            counts[key] > 0 ? (
              <span key={key} className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${cls}`}>
                {counts[key]} {key}
              </span>
            ) : null,
          )}
          {counts.total === 0 && (
            <span className="text-xs text-muted">Niciun cuvânt cheie</span>
          )}
        </div>
      )}

      <button
        onClick={() => onOpen(campaign.id)}
        className="mt-auto flex w-full items-center justify-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-black transition hover:bg-accent-hover"
      >
        Deschide
        <ArrowRight className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
