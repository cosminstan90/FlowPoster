export default function QualityScoreCircle({ score = 0 }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(100, Math.max(0, score));
  const offset = circumference - (pct / 100) * circumference;

  const color =
    pct >= 75 ? "#22c55e" :
    pct >= 50 ? "#eab308" :
    "#ef4444";

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle
          cx="50" cy="50" r={radius}
          fill="none" stroke="#2a2d3a" strokeWidth="10"
        />
        <circle
          cx="50" cy="50" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text
          x="50" y="50"
          textAnchor="middle" dominantBaseline="central"
          fill={color}
          fontSize="20"
          fontWeight="700"
        >
          {pct}
        </text>
      </svg>
      <span className="text-xs text-muted">Quality Score</span>
    </div>
  );
}
