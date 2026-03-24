import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Loader2, Globe, Plus, ChevronLeft } from "lucide-react";
import { getProject } from "../api/projects";
import { getCampaigns, getCampaign, createCampaign } from "../api/campaigns";
import CampaignCard from "../components/CampaignCard";
import NewCampaignModal from "../components/NewCampaignModal";

const TAB_CLS = (active) =>
  `px-4 py-2 text-sm font-medium border-b-2 transition ${
    active
      ? "border-accent text-accent"
      : "border-transparent text-muted hover:text-white"
  }`;

export default function ProjectPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [campaignDetails, setCampaignDetails] = useState({});
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("campaigns");
  const [showNew, setShowNew] = useState(false);

  useEffect(() => {
    load();
  }, [id]);

  async function load() {
    setLoading(true);
    try {
      const [projRes, campRes] = await Promise.all([getProject(id), getCampaigns(id)]);
      setProject(projRes.data);
      const camps = campRes.data || [];
      setCampaigns(camps);

      // Fetch keyword counts for each campaign in parallel
      const details = await Promise.all(camps.map((c) => getCampaign(c.id).catch(() => null)));
      const map = {};
      details.forEach((res, i) => {
        if (res) map[camps[i].id] = res.data?.keyword_counts;
      });
      setCampaignDetails(map);
    } finally {
      setLoading(false);
    }
  }

  const handleCreateCampaign = async (payload) => {
    await createCampaign({ ...payload, project_id: id });
    await load();
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  if (!project) {
    return <div className="text-center text-muted py-12">Proiect negăsit</div>;
  }

  return (
    <div className="space-y-6">
      {/* Back + title */}
      <div>
        <button
          onClick={() => navigate("/")}
          className="mb-4 flex items-center gap-1 text-sm text-muted hover:text-white transition"
        >
          <ChevronLeft className="h-4 w-4" />
          Dashboard
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">{project.name}</h1>
            <div className="mt-1 flex items-center gap-1.5 text-sm text-muted">
              <Globe className="h-4 w-4" />
              {project.domain}
            </div>
          </div>
          {tab === "campaigns" && (
            <button
              onClick={() => setShowNew(true)}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
            >
              <Plus className="h-4 w-4" />
              Campanie nouă
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex gap-0">
          <button className={TAB_CLS(tab === "campaigns")} onClick={() => setTab("campaigns")}>
            Campanii
            <span className="ml-1.5 rounded-full bg-border px-1.5 py-0.5 text-[11px]">
              {campaigns.length}
            </span>
          </button>
          <button className={TAB_CLS(tab === "settings")} onClick={() => setTab("settings")}>
            Setări Site
          </button>
        </div>
      </div>

      {/* Campanii tab */}
      {tab === "campaigns" && (
        <>
          {campaigns.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-bg-card py-16">
              <p className="mb-3 text-muted">Nicio campanie încă</p>
              <button
                onClick={() => setShowNew(true)}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
              >
                Creează prima campanie
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {campaigns.map((c) => (
                <CampaignCard
                  key={c.id}
                  campaign={c}
                  counts={campaignDetails[c.id]}
                  onOpen={(cid) => navigate(`/campaigns/${cid}`)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Setări Site tab */}
      {tab === "settings" && (
        <div className="rounded-xl border border-border bg-bg-card p-6">
          <h2 className="mb-4 text-base font-semibold text-white">Setări Site Context</h2>
          {project.site_context ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              {[
                ["Nișă", project.site_context.niche],
                ["Audiență", project.site_context.target_audience],
                ["Ton", project.site_context.tone],
                ["Autor", project.site_context.author_name || "—"],
                ["Credențiale", project.site_context.author_credentials || "—"],
                ["An fondare", project.site_context.site_founded_year || "—"],
              ].map(([k, v]) => (
                <div key={k}>
                  <p className="text-xs text-muted">{k}</p>
                  <p className="text-white">{v}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted text-sm">Site context neconfigurat.</p>
          )}
        </div>
      )}

      <NewCampaignModal
        open={showNew}
        onClose={() => setShowNew(false)}
        onSave={handleCreateCampaign}
      />
    </div>
  );
}
