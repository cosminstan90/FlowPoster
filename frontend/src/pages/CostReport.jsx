import { useState, useEffect } from "react";
import { Loader2, TrendingUp, FileText, DollarSign } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { getCostSummary, getProjectCost, getGeoReport } from "../api/costs";

const ALERT_BADGE = {
  none:     { label: "OK",       cls: "bg-green-500/10 text-green-400" },
  warning:  { label: "Atenție",  cls: "bg-yellow-500/10 text-yellow-400" },
  critical: { label: "Depășit",  cls: "bg-red-500/10 text-red-400" },
};

function monthOptions() {
  const opts = [];
  const now = new Date();
  for (let i = 0; i < 4; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const label = d.toLocaleString("ro-RO", { month: "long", year: "numeric" });
    opts.push({ val, label });
  }
  return opts;
}

export default function CostReport() {
  const [activeTab, setActiveTab] = useState("costuri");
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [month, setMonth] = useState(monthOptions()[0].val);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // GEO tab state
  const [geoData, setGeoData] = useState([]);
  const [geoLoading, setGeoLoading] = useState(false);

  const months = monthOptions();

  useEffect(() => {
    async function load() {
      try {
        const res = await getCostSummary();
        const rows = res.data || [];
        setSummary(rows);
        if (rows.length > 0 && !selectedId) setSelectedId(rows[0].project_id);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    async function loadDetail() {
      setDetailLoading(true);
      try {
        const res = await getProjectCost(selectedId, month);
        setDetail(res.data);
      } finally {
        setDetailLoading(false);
      }
    }
    loadDetail();
  }, [selectedId, month]);

  useEffect(() => {
    if (activeTab !== "geo") return;
    async function loadGeo() {
      setGeoLoading(true);
      try {
        const res = await getGeoReport();
        setGeoData(res.data || []);
      } finally {
        setGeoLoading(false);
      }
    }
    loadGeo();
  }, [activeTab]);

  const totalCost = summary.reduce((s, r) => s + Number(r.total_usd || 0), 0);
  const totalPages = summary.reduce((s, r) => s + (r.pages_count || 0), 0);
  const avgCost = totalPages > 0 ? totalCost / totalPages : 0;

  const chartData = (detail?.daily_breakdown || []).map((d) => ({
    date: d.date?.slice(5),      // MM-DD
    cost: Number(d.cost || 0),
    pages: d.pages,
  }));

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10">
      <div>
        <h1 className="text-2xl font-semibold text-white">Raport Costuri</h1>
        <p className="text-sm text-muted">Luna curentă · toate proiectele</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-border bg-bg-card p-1 w-fit">
        <button
          onClick={() => setActiveTab("costuri")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${activeTab === "costuri" ? "bg-accent text-black" : "text-muted hover:text-white"}`}
        >
          Costuri
        </button>
        <button
          onClick={() => setActiveTab("geo")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${activeTab === "geo" ? "bg-purple-600 text-white" : "text-muted hover:text-white"}`}
        >
          GEO Performance
        </button>
      </div>

      {activeTab === "geo" && (
        <GeoPerformanceTab data={geoData} loading={geoLoading} />
      )}

      {activeTab === "costuri" && (
        <>
      {/* Top 3 stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          icon={<DollarSign className="h-5 w-5 text-accent" />}
          label="Total cheltuit luna aceasta"
          value={`$${totalCost.toFixed(4)}`}
        />
        <StatCard
          icon={<FileText className="h-5 w-5 text-blue-400" />}
          label="Pagini generate luna aceasta"
          value={totalPages}
        />
        <StatCard
          icon={<TrendingUp className="h-5 w-5 text-purple-400" />}
          label="Cost mediu per pagină"
          value={`$${avgCost.toFixed(4)}`}
        />
      </div>

      {/* Projects table */}
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-card">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted">Proiect</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Pagini</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Tokens In</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Tokens Out</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Cost USD</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Buget</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Utilizat %</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-muted">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {summary.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-muted">
                  Nicio date disponibilă
                </td>
              </tr>
            ) : (
              summary.map((row) => {
                const alert = ALERT_BADGE[row.budget_alert_level] || ALERT_BADGE.none;
                const isSelected = selectedId === row.project_id;
                return (
                  <tr
                    key={row.project_id}
                    onClick={() => setSelectedId(row.project_id)}
                    className={`cursor-pointer transition hover:bg-bg-hover ${isSelected ? "bg-accent/5" : ""}`}
                  >
                    <td className="px-4 py-3 font-medium text-white">{row.project_name}</td>
                    <td className="px-3 py-3 text-right text-muted">{row.pages_count}</td>
                    <td className="px-3 py-3 text-right text-muted">{(row.tokens_input || 0).toLocaleString()}</td>
                    <td className="px-3 py-3 text-right text-muted">{(row.tokens_output || 0).toLocaleString()}</td>
                    <td className="px-3 py-3 text-right text-white">${Number(row.total_usd).toFixed(4)}</td>
                    <td className="px-3 py-3 text-right text-muted">
                      {Number(row.budget_usd) > 0 ? `$${Number(row.budget_usd).toFixed(2)}` : "—"}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <span className={Number(row.budget_percent_used) >= 80 ? "text-yellow-400" : "text-muted"}>
                        {Number(row.budget_percent_used).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${alert.cls}`}>
                        {alert.label}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Daily bar chart */}
      {selectedId && (
        <div className="rounded-xl border border-border bg-bg-card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-medium text-white">
              Consum zilnic —{" "}
              <span className="text-muted">
                {summary.find((r) => r.project_id === selectedId)?.project_name}
              </span>
            </h2>
            <select
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="rounded-lg border border-border bg-bg px-3 py-1.5 text-xs text-white outline-none focus:border-accent"
            >
              {months.map((m) => (
                <option key={m.val} value={m.val}>{m.label}</option>
              ))}
            </select>
          </div>

          {detailLoading ? (
            <div className="flex h-40 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-accent" />
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex h-40 items-center justify-center text-sm text-muted">
              Nicio activitate în această lună
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#6b7280", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#6b7280", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v.toFixed(3)}`}
                />
                <Tooltip
                  contentStyle={{
                    background: "#1a1d27",
                    border: "1px solid #2a2d3a",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#e2e8f0" }}
                  formatter={(v, name) =>
                    name === "cost" ? [`$${Number(v).toFixed(4)}`, "Cost"] : [v, "Pagini"]
                  }
                />
                <Bar dataKey="cost" fill="#22c55e" radius={[4, 4, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          )}

          {detail && (
            <div className="mt-3 grid grid-cols-3 gap-4 border-t border-border pt-3 text-xs">
              <div>
                <p className="text-muted">Total</p>
                <p className="font-medium text-white">${Number(detail.total_usd).toFixed(4)}</p>
              </div>
              <div>
                <p className="text-muted">Buget rămas</p>
                <p className="font-medium text-white">
                  {Number(detail.budget_usd) > 0 ? `$${Number(detail.budget_remaining).toFixed(2)}` : "—"}
                </p>
              </div>
              <div>
                <p className="text-muted">Utilizat</p>
                <p className={`font-medium ${Number(detail.budget_percent_used) >= 80 ? "text-yellow-400" : "text-white"}`}>
                  {Number(detail.budget_percent_used).toFixed(1)}%
                </p>
              </div>
            </div>
          )}
        </div>
      )}
      </>
      )}
    </div>
  );
}

const GEO_MODE_LABELS = {
  balanced: "Echilibrat",
  geo_first: "GEO First",
  seo_first: "SEO First",
};

const GEO_MODE_COLORS = {
  balanced: "bg-blue-500/10 text-blue-400",
  geo_first: "bg-purple-500/10 text-purple-400",
  seo_first: "bg-green-500/10 text-green-400",
};

const FACTOR_LABELS = {
  direct_answer: "Răspuns direct",
  speakable_sections: "Secțiuni speakable",
  qa_structure: "Structură Q&A",
  statistics: "Statistici cu surse",
  author_schema: "Schema autor",
  definition_intro: "Definiție în intro",
  comparison_table: "Tabel comparativ",
  sentence_length: "Fraze scurte",
};

function GeoPerformanceTab({ data, loading }) {
  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-bg-card p-8 text-center">
        <p className="text-muted text-sm">Nicio campanie GEO activată.</p>
        <p className="text-xs text-muted mt-1">Activează modul GEO/AEO în setările campaniei pentru a vedea statistici.</p>
      </div>
    );
  }

  // Find most failing factor across all campaigns
  const allFails = {};
  for (const row of data) {
    for (const [factor, count] of Object.entries(row.failing_factors || {})) {
      allFails[factor] = (allFails[factor] || 0) + Number(count);
    }
  }
  const topFailFactor = Object.entries(allFails).sort((a, b) => b[1] - a[1])[0];

  return (
    <div className="space-y-4">
      {topFailFactor && (
        <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 px-4 py-3">
          <p className="text-xs font-medium text-yellow-400 mb-0.5">Factor cu cele mai multe eșecuri</p>
          <p className="text-sm text-white">
            {FACTOR_LABELS[topFailFactor[0]] || topFailFactor[0]}
            <span className="ml-2 text-muted text-xs">({topFailFactor[1]} pagini)</span>
          </p>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-card">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted">Campanie</th>
              <th className="px-3 py-3 text-left text-xs font-medium text-muted">Mod</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Pagini GEO</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-muted">Scor mediu</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-muted">Distribuție</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {data.map((row) => {
              const scoreColor =
                row.avg_geo_score == null ? "text-muted" :
                row.avg_geo_score >= 70 ? "text-purple-400" :
                row.avg_geo_score >= 40 ? "text-yellow-400" :
                "text-red-400";
              return (
                <tr key={row.campaign_id} className="hover:bg-bg-hover transition">
                  <td className="px-4 py-3 font-medium text-white">{row.campaign_name}</td>
                  <td className="px-3 py-3">
                    <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${GEO_MODE_COLORS[row.geo_mode] || "bg-gray-500/10 text-gray-400"}`}>
                      {GEO_MODE_LABELS[row.geo_mode] || row.geo_mode}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-right text-muted">{row.pages_with_geo}</td>
                  <td className={`px-3 py-3 text-right font-semibold ${scoreColor}`}>
                    {row.avg_geo_score != null ? row.avg_geo_score : "—"}
                  </td>
                  <td className="px-3 py-3 text-center">
                    <div className="flex items-center justify-center gap-2 text-xs">
                      <span className="text-red-400">{row.score_distribution.low} ↓</span>
                      <span className="text-yellow-400">{row.score_distribution.mid} ~</span>
                      <span className="text-green-400">{row.score_distribution.high} ↑</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-border bg-bg-card px-5 py-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-bg">
        {icon}
      </div>
      <div>
        <p className="text-[11px] text-muted">{label}</p>
        <p className="text-xl font-semibold text-white">{value}</p>
      </div>
    </div>
  );
}
