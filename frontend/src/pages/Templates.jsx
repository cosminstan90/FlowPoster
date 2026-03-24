import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Plus, Pencil, Zap, Copy, Trash2, FileCode2 } from "lucide-react";
import { getTemplates, deleteTemplate, createTemplate } from "../api/templates";
import TemplateTestModal from "../components/TemplateTestModal";

const TYPE_BADGE = {
  article:    "bg-blue-500/10 text-blue-400",
  faq:        "bg-purple-500/10 text-purple-400",
  product:    "bg-green-500/10 text-green-400",
  landing:    "bg-orange-500/10 text-orange-400",
  comparison: "bg-teal-500/10 text-teal-400",
};

function timeAgo(isoStr) {
  if (!isoStr) return "—";
  const diff = Math.floor((Date.now() - new Date(isoStr)) / 1000);
  if (diff < 60) return "acum";
  if (diff < 3600) return `${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ore`;
  return `${Math.floor(diff / 86400)} zile`;
}

export default function Templates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testTarget, setTestTarget] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const load = async () => {
    try {
      const res = await getTemplates();
      setTemplates(res.data?.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDuplicate = async (tpl) => {
    await createTemplate({
      name: `${tpl.name} (copie)`,
      type: tpl.type,
      system_prompt: tpl.system_prompt,
      user_prompt: tpl.user_prompt,
      variables: tpl.variables,
    });
    await load();
  };

  const handleDelete = async (id) => {
    setDeleting(id);
    try {
      await deleteTemplate(id);
      setTemplates((ts) => ts.filter((t) => t.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || "Delete failed");
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Template-uri Prompt</h1>
          <p className="text-sm text-muted">{templates.length} template-uri disponibile</p>
        </div>
        <button
          onClick={() => navigate("/templates/new")}
          className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
        >
          <Plus className="h-4 w-4" />
          Template nou
        </button>
      </div>

      {templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-bg-card py-16">
          <FileCode2 className="mb-3 h-8 w-8 text-muted/40" />
          <p className="text-muted">Niciun template</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {templates.map((tpl) => {
            const typeCls = TYPE_BADGE[tpl.type] || "bg-gray-500/10 text-gray-400";
            return (
              <div
                key={tpl.id}
                className="flex flex-col rounded-xl border border-border bg-bg-card p-5 transition hover:border-accent/30"
              >
                {/* Header */}
                <div className="mb-3 flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-white">{tpl.name}</h3>
                    <p className="mt-0.5 text-xs text-muted">
                      {tpl.campaigns_count} campanie{tpl.campaigns_count !== 1 ? "" : ""}
                      {" · "}acum {timeAgo(tpl.created_at)}
                    </p>
                  </div>
                  <span className={`shrink-0 rounded-md px-2 py-0.5 text-[11px] font-medium ${typeCls}`}>
                    {tpl.type}
                  </span>
                </div>

                {/* Variables preview */}
                {tpl.variables?.length > 0 && (
                  <div className="mb-4 flex flex-wrap gap-1">
                    {tpl.variables.slice(0, 4).map((v) => (
                      <span key={v} className="rounded bg-yellow-500/10 px-1.5 py-0.5 text-[10px] text-yellow-300">
                        {`{${v}}`}
                      </span>
                    ))}
                    {tpl.variables.length > 4 && (
                      <span className="text-[10px] text-muted">+{tpl.variables.length - 4}</span>
                    )}
                  </div>
                )}

                {/* System prompt preview */}
                <p className="mb-4 line-clamp-2 text-xs text-muted leading-relaxed">
                  {tpl.system_prompt?.slice(0, 120)}…
                </p>

                {/* Actions */}
                <div className="mt-auto flex items-center gap-1.5">
                  <button
                    onClick={() => navigate(`/templates/${tpl.id}`)}
                    className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs text-muted hover:border-accent/40 hover:text-white transition"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                    Edit
                  </button>
                  <button
                    onClick={() => setTestTarget(tpl)}
                    className="flex items-center gap-1 rounded-lg border border-border px-2 py-2 text-xs text-muted hover:border-accent/40 hover:text-white transition"
                    title="Test"
                  >
                    <Zap className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => handleDuplicate(tpl)}
                    className="flex items-center gap-1 rounded-lg border border-border px-2 py-2 text-xs text-muted hover:border-accent/40 hover:text-white transition"
                    title="Duplică"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(tpl.id)}
                    disabled={deleting === tpl.id || tpl.campaigns_count > 0}
                    title={tpl.campaigns_count > 0 ? "Folosit de campanii — nu poate fi șters" : "Șterge"}
                    className="flex items-center gap-1 rounded-lg border border-border px-2 py-2 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-30 disabled:cursor-not-allowed transition"
                  >
                    {deleting === tpl.id
                      ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      : <Trash2 className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <TemplateTestModal
        open={!!testTarget}
        onClose={() => setTestTarget(null)}
        template={testTarget}
      />
    </div>
  );
}
