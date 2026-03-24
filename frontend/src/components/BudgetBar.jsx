export default function BudgetBar({ cost, budget }) {
  if (!budget || budget === 0) {
    return (
      <div className="text-xs text-muted">
        <span className="text-white font-medium">${Number(cost).toFixed(2)}</span>
        {" "}/ fara buget
      </div>
    );
  }

  const pct = Math.min(100, (cost / budget) * 100);
  let barColor = "bg-accent";
  let textColor = "text-accent";
  if (pct >= 95) {
    barColor = "bg-red-500";
    textColor = "text-red-400";
  } else if (pct >= 80) {
    barColor = "bg-yellow-500";
    textColor = "text-yellow-400";
  }

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted">
          <span className="text-white font-medium">${Number(cost).toFixed(2)}</span>
          {" "}/ ${Number(budget).toFixed(0)}
        </span>
        <span className={textColor}>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-border overflow-hidden">
        <div className={`h-full rounded-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
