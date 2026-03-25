import { NavLink } from "react-router-dom";
import { LayoutDashboard, PlusCircle, BarChart2, FileCode2, Sparkles, Settings } from "lucide-react";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/costs", icon: BarChart2, label: "Costuri" },
  { to: "/templates", icon: FileCode2, label: "Template-uri" },
  { to: "/settings", icon: Settings, label: "Setări" },
  { to: "/projects/new", icon: PlusCircle, label: "Proiect nou", highlight: true },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-64 flex-col border-r border-border bg-bg-card/80 backdrop-blur-xl transition-all duration-300">
      <div className="flex h-20 items-center gap-3 border-b border-border/50 px-6 mt-1">
        <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-cyan-500 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <span className="text-lg font-display font-bold text-white tracking-wide">
          SEO Publisher
        </span>
      </div>

      <nav className="flex-1 space-y-2 px-4 py-6">
        <div className="px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-muted/60">
          Meniu Principal
        </div>
        {NAV.map(({ to, icon: Icon, label, highlight }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-300 ${
                isActive
                  ? "bg-accent/10 text-accent shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] border border-accent/20"
                  : highlight
                  ? "text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300 mt-6 border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.1)]"
                  : "text-muted hover:bg-white/5 hover:text-white"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`h-5 w-5 transition-transform duration-300 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                {label}
                {isActive && (
                  <div className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-md bg-accent" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border/50 p-6">
        <div className="rounded-xl bg-surface/50 p-4 border border-border/50">
          <p className="text-[11px] uppercase tracking-wider text-muted mb-1">Versiune</p>
          <p className="text-sm font-medium text-white/80">v0.1.0 Beta</p>
        </div>
      </div>
    </aside>
  );
}
