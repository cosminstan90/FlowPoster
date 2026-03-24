import { Globe, Settings, ArrowRight, AlertTriangle } from "lucide-react";
import BudgetBar from "./BudgetBar";

const CMS_BADGE = {
  wordpress: { label: "WordPress", cls: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  php_custom: { label: "PHP Custom", cls: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
};

export default function ProjectCard({ project, costData, onOpen, onSettings }) {
  const stats = project.stats || {};
  const badge = CMS_BADGE[project.cms_type] || CMS_BADGE.wordpress;
  const cost = costData?.total_usd ?? 0;
  const budget = Number(project.monthly_budget_usd) || 0;
  const alertLevel = project.budget_alert_level || "none";

  return (
    <div className="glass-panel flex h-full flex-col p-6 transition-all duration-300 hover:border-accent/40 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(16,185,129,0.1)] group">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div className="min-w-0 pr-4">
          <h3 className="truncate text-xl font-display font-semibold text-white/95 group-hover:text-white transition-colors">
            {project.name}
          </h3>
          <div className="mt-1.5 flex items-center gap-2 text-sm text-muted">
            <Globe className="h-4 w-4 text-accent/70" />
            <span className="truncate">{project.domain}</span>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {alertLevel !== "none" && (
            <span
              title={alertLevel === "critical" ? "Buget depășit!" : "Buget aproape epuizat"}
              className={`${alertLevel === "critical" ? "text-red-400 animate-pulse" : "text-yellow-400"}`}
            >
              <AlertTriangle className="h-5 w-5" />
            </span>
          )}
          <span className={`rounded-lg border px-2.5 py-1 text-xs font-semibold tracking-wide ${badge.cls}`}>
            {badge.label}
          </span>
        </div>
      </div>

      {/* Keyword stats */}
      <div className="mb-6 grid grid-cols-3 gap-4 rounded-xl bg-surface/50 p-4 border border-border/50">
        <div>
          <p className="text-2xl font-display font-bold text-white">{stats.total_keywords ?? 0}</p>
          <p className="text-xs font-medium text-muted mt-0.5">Total</p>
        </div>
        <div>
          <p className="text-2xl font-display font-bold text-accent">{stats.total_pages_published ?? 0}</p>
          <p className="text-xs font-medium text-muted mt-0.5">Publicate</p>
        </div>
        <div>
          <p className="text-2xl font-display font-bold text-yellow-400/90">
            {(stats.total_keywords ?? 0) - (stats.total_pages_published ?? 0)}
          </p>
          <p className="text-xs font-medium text-muted mt-0.5">Draft</p>
        </div>
      </div>

      {/* Budget */}
      <div className="mb-8 flex-1">
        <BudgetBar cost={cost} budget={budget} />
      </div>

      {/* Actions */}
      <div className="mt-auto flex gap-3">
        <button
          onClick={() => onOpen(project.id)}
          className="glass-button flex flex-1 items-center justify-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent-hover shadow-lg shadow-accent/20"
        >
          Deschide Proiect
          <ArrowRight className="h-4 w-4" />
        </button>
        <button
          onClick={() => onSettings(project.id)}
          className="glass-button flex items-center justify-center rounded-xl bg-surface border border-border px-4 py-2.5 text-muted transition hover:border-accent/40 hover:text-white"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
