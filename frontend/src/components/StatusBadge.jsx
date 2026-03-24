const STATUS = {
  pending:    { label: "Pending",    cls: "bg-slate-500/15 text-slate-400 border-slate-500/20" },
  queued:     { label: "Queued",     cls: "bg-blue-500/15 text-blue-400 border-blue-500/20" },
  generating: { label: "Generating", cls: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20 animate-pulse" },
  draft:      { label: "Draft",      cls: "bg-orange-500/15 text-orange-400 border-orange-500/20" },
  approved:   { label: "Aprobat",    cls: "bg-green-500/15 text-green-400 border-green-500/20" },
  published:  { label: "Publicat",   cls: "bg-teal-500/15 text-teal-400 border-teal-500/20" },
  error:      { label: "Eroare",     cls: "bg-red-500/15 text-red-400 border-red-500/20" },
};

export default function StatusBadge({ status, className = "" }) {
  const cfg = STATUS[status] ?? { label: status, cls: "bg-gray-500/15 text-gray-400" };
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${cfg.cls} ${className}`}
    >
      {cfg.label}
    </span>
  );
}

export { STATUS };
