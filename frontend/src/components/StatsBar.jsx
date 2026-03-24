import { FileText, DollarSign, Hash, Megaphone } from "lucide-react";

function StatCard({ icon: Icon, label, value, sub, colorClass = "text-accent", bgClass = "bg-accent/10" }) {
  return (
    <div className="glass-panel flex items-center gap-4 rounded-2xl p-5 transition-transform hover:-translate-y-1 shadow-[0_8px_30px_rgba(0,0,0,0.12)]">
      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${bgClass} shadow-inner`}>
        <Icon className={`h-6 w-6 ${colorClass}`} />
      </div>
      <div>
        <p className="text-3xl font-display font-bold text-white tracking-tight">{value}</p>
        <p className="text-sm font-medium text-muted mt-0.5">{label}</p>
        {sub && <p className="text-xs text-muted/60 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export default function StatsBar({ totalPublished, totalCost, totalKeywords, activeCampaigns }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard 
        icon={FileText} 
        label="Pagini publicate" 
        value={totalPublished} 
        colorClass="text-accent"
        bgClass="bg-accent/10"
      />
      <StatCard
        icon={DollarSign}
        label="Cost luna aceasta"
        value={`$${Number(totalCost).toFixed(2)}`}
        colorClass="text-cyan-400"
        bgClass="bg-cyan-400/10"
      />
      <StatCard 
        icon={Hash} 
        label="Cuvinte cheie" 
        value={totalKeywords} 
        colorClass="text-purple-400"
        bgClass="bg-purple-400/10"
      />
      <StatCard 
        icon={Megaphone} 
        label="Campanii active" 
        value={activeCampaigns} 
        colorClass="text-blue-400"
        bgClass="bg-blue-400/10"
      />
    </div>
  );
}
