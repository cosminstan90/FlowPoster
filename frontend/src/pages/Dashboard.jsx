import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Sparkles, FolderPlus } from "lucide-react";
import StatsBar from "../components/StatsBar";
import ProjectCard from "../components/ProjectCard";
import NewProjectModal from "../components/NewProjectModal";
import { getProjects, createProject } from "../api/projects";
import { getCostSummary } from "../api/costs";

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [costMap, setCostMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [showNewProject, setShowNewProject] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [projRes, costRes] = await Promise.all([getProjects(), getCostSummary()]);

        setProjects(projRes.data || []);

        const map = {};
        for (const row of costRes.data || []) {
          map[row.project_id] = row;
        }
        setCostMap(map);
      } catch (err) {
        console.error("Failed to load dashboard", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleCreateProject = async (payload) => {
    const res = await createProject(payload);
    navigate(`/projects/${res.data.id}`);
  };

  const totalPublished = projects.reduce((s, p) => s + (p.stats?.total_pages_published ?? 0), 0);
  const totalKeywords = projects.reduce((s, p) => s + (p.stats?.total_keywords ?? 0), 0);
  const totalCost = Object.values(costMap).reduce((s, c) => s + Number(c.total_usd || 0), 0);
  const activeCampaigns = projects.length;

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in relative z-10">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="h-5 w-5 text-accent animate-pulse-slow" />
            <h1 className="text-3xl font-display font-bold text-white tracking-tight">Privire de ansamblu</h1>
          </div>
          <p className="text-muted text-lg mt-1">Urmărește performanța proiectelor tale SEO și optimizările generate de AI.</p>
        </div>
        <button
          onClick={() => setShowNewProject(true)}
          className="glass-button flex items-center gap-2 rounded-xl bg-gradient-to-r from-accent to-cyan-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent/20 hover:shadow-accent/40"
        >
          <FolderPlus className="h-4 w-4" />
          Proiect Nou
        </button>
      </div>

      {/* Stats */}
      <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
        <StatsBar
          totalPublished={totalPublished}
          totalCost={totalCost}
          totalKeywords={totalKeywords}
          activeCampaigns={activeCampaigns}
        />
      </div>

      {/* Projects Grid */}
      <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
        <h2 className="text-xl font-display font-semibold text-white mb-6 flex items-center gap-3">
          Proiecte Active
          <span className="bg-surface border border-border/50 shadow-inner text-white text-xs py-0.5 px-3 rounded-full font-medium">{projects.length}</span>
        </h2>
        
        {projects.length === 0 ? (
          <div className="glass-panel flex flex-col items-center justify-center rounded-2xl py-24 text-center border-dashed border-border/60">
            <div className="h-16 w-16 rounded-full bg-accent/10 flex items-center justify-center mb-4 ring-4 ring-accent/5">
              <FolderPlus className="h-8 w-8 text-accent" />
            </div>
            <h3 className="text-xl font-display font-semibold text-white mb-2">Niciun proiect în desfășurare</h3>
            <p className="text-muted mb-6 max-w-sm text-sm">Nu ai creat încă niciun proiect. Începe automatizarea SEO adăugând primul tău website.</p>
            <button
              onClick={() => setShowNewProject(true)}
              className="glass-button rounded-xl bg-surface border border-border px-6 py-2.5 text-sm font-medium text-white hover:border-accent/50 hover:bg-white/5 transition-all"
            >
              Creează primul proiect
            </button>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {projects.map((p, i) => (
              <div key={p.id} className="animate-fade-in" style={{ animationFillMode: 'both', animationDelay: `${300 + i * 100}ms` }}>
                <ProjectCard
                  project={p}
                  costData={costMap[p.id]}
                  onOpen={(id) => navigate(`/projects/${id}`)}
                  onSettings={(id) => navigate(`/projects/${id}/settings`)}
                />
              </div>
            ))}
          </div>
        )}
      </div>
      <NewProjectModal
        open={showNewProject}
        onClose={() => setShowNewProject(false)}
        onSave={handleCreateProject}
      />
    </div>
  );
}
