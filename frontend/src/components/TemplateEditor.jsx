import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Plus, Trash2, Save, Zap } from "lucide-react";
import { createTemplate, updateTemplate } from "../api/templates";
import TemplateTestModal from "./TemplateTestModal";

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";
const LABEL = "mb-1.5 block text-xs font-medium text-muted";
const TEXTAREA = `${FIELD} font-mono text-xs resize-none`;

const TYPE_OPTIONS = [
  { value: "article", label: "Article" },
  { value: "faq", label: "FAQ Page" },
  { value: "product", label: "Product Page" },
  { value: "landing", label: "Landing Page" },
  { value: "comparison", label: "Comparison" },
];

// Highlight {variable} tokens in prompt text for the preview panel
function HighlightedPrompt({ text }) {
  const parts = text.split(/(\{[^}]+\})/g);
  return (
    <pre className="max-h-56 overflow-y-auto whitespace-pre-wrap break-words rounded-lg border border-border bg-bg p-3 text-xs leading-relaxed text-muted">
      {parts.map((part, i) =>
        /^\{[^}]+\}$/.test(part)
          ? <mark key={i} className="rounded bg-yellow-500/20 px-0.5 text-yellow-300 not-italic">{part}</mark>
          : part
      )}
    </pre>
  );
}

export default function TemplateEditor({ initialData = null }) {
  const navigate = useNavigate();
  const isNew = !initialData?.id;

  const [name, setName] = useState(initialData?.name || "");
  const [type, setType] = useState(initialData?.type || "article");
  const [systemPrompt, setSystemPrompt] = useState(initialData?.system_prompt || "");
  const [userPrompt, setUserPrompt] = useState(initialData?.user_prompt || "");
  const [variables, setVariables] = useState(initialData?.variables || ["keyword", "site_context", "outline"]);
  const [newVar, setNewVar] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveOk, setSaveOk] = useState(false);
  const [showTest, setShowTest] = useState(false);
  const [previewPane, setPreviewPane] = useState("system"); // "system" | "user"

  // Sync if initialData changes (e.g. after load)
  useEffect(() => {
    if (initialData) {
      setName(initialData.name || "");
      setType(initialData.type || "article");
      setSystemPrompt(initialData.system_prompt || "");
      setUserPrompt(initialData.user_prompt || "");
      setVariables(initialData.variables || []);
    }
  }, [initialData?.id]);

  const addVar = () => {
    const v = newVar.trim().replace(/[^a-z0-9_]/gi, "_");
    if (v && !variables.includes(v)) setVariables([...variables, v]);
    setNewVar("");
  };
  const removeVar = (v) => setVariables(variables.filter((x) => x !== v));

  const insertVar = (v) => {
    // Insert into whichever prompt was last focused — append to user prompt for simplicity
    setUserPrompt((p) => p + `{${v}}`);
  };

  const handleSave = async () => {
    if (!name.trim() || !systemPrompt.trim() || !userPrompt.trim()) return;
    setSaving(true);
    try {
      const payload = { name: name.trim(), type, system_prompt: systemPrompt, user_prompt: userPrompt, variables };
      if (isNew) {
        const res = await createTemplate(payload);
        const newId = res.data?.data?.id;
        setSaveOk(true);
        setTimeout(() => navigate(`/templates/${newId}`), 600);
      } else {
        await updateTemplate(initialData.id, payload);
        setSaveOk(true);
        setTimeout(() => setSaveOk(false), 2000);
      }
    } finally {
      setSaving(false);
    }
  };

  const templateForTest = initialData?.id
    ? { id: initialData.id, name }
    : null;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-white">
          {isNew ? "Template nou" : `Editare: ${initialData?.name}`}
        </h2>
        <div className="flex items-center gap-2">
          {!isNew && (
            <button
              onClick={() => setShowTest(true)}
              className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm text-muted hover:border-accent/40 hover:text-white transition"
            >
              <Zap className="h-4 w-4" />
              Test
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving || !name.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {saveOk ? "Salvat!" : "Salvează"}
          </button>
        </div>
      </div>

      {/* Two-panel layout */}
      <div className="grid gap-5 lg:grid-cols-2">

        {/* ---- LEFT: form ---- */}
        <div className="space-y-4">
          {/* Name + Type */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={LABEL}>Nume template *</label>
              <input value={name} onChange={(e) => setName(e.target.value)} className={FIELD} placeholder="Article RO" />
            </div>
            <div>
              <label className={LABEL}>Tip</label>
              <select value={type} onChange={(e) => setType(e.target.value)} className={FIELD}>
                {TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          {/* Variables */}
          <div className="rounded-lg border border-border bg-bg-card p-3">
            <p className="mb-2 text-xs font-medium text-muted">Variabile disponibile</p>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {variables.map((v) => (
                <span
                  key={v}
                  className="flex items-center gap-1 rounded-md bg-yellow-500/10 px-2 py-0.5 text-xs text-yellow-300 cursor-pointer hover:bg-yellow-500/20"
                  onClick={() => insertVar(v)}
                  title="Click to insert into User Prompt"
                >
                  {`{${v}}`}
                  <button
                    onClick={(e) => { e.stopPropagation(); removeVar(v); }}
                    className="text-yellow-400/60 hover:text-red-400 ml-0.5"
                  >
                    <Trash2 className="h-2.5 w-2.5" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={newVar}
                onChange={(e) => setNewVar(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addVar()}
                placeholder="nume_variabila"
                className="flex-1 rounded-lg border border-border bg-bg px-2 py-1 text-xs text-white outline-none focus:border-accent"
              />
              <button onClick={addVar} className="rounded-lg border border-border px-2 py-1 text-xs text-muted hover:text-white transition">
                <Plus className="h-3.5 w-3.5" />
              </button>
            </div>
            <p className="mt-1.5 text-[10px] text-muted/60">Click pe o variabilă pentru a o insera în User Prompt</p>
          </div>

          {/* System prompt */}
          <div>
            <label className={LABEL}>System Prompt</label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={8}
              className={TEXTAREA}
              placeholder="You are a senior SEO copywriter..."
            />
          </div>

          {/* User prompt */}
          <div>
            <label className={LABEL}>User Prompt</label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              rows={10}
              className={TEXTAREA}
              placeholder="Write an article for the keyword: {keyword}..."
            />
          </div>
        </div>

        {/* ---- RIGHT: preview ---- */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <div className="mb-3 flex items-center gap-2">
              <button
                onClick={() => setPreviewPane("system")}
                className={`rounded-md px-3 py-1 text-xs font-medium transition ${previewPane === "system" ? "bg-accent/10 text-accent" : "text-muted hover:text-white"}`}
              >
                System Prompt
              </button>
              <button
                onClick={() => setPreviewPane("user")}
                className={`rounded-md px-3 py-1 text-xs font-medium transition ${previewPane === "user" ? "bg-accent/10 text-accent" : "text-muted hover:text-white"}`}
              >
                User Prompt
              </button>
              <span className="ml-auto text-[10px] text-muted/60">
                <span className="rounded bg-yellow-500/20 px-1 text-yellow-300">{"{var}"}</span> = variabilă
              </span>
            </div>
            <HighlightedPrompt text={previewPane === "system" ? systemPrompt : userPrompt} />
          </div>

          {/* Variable reference table */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <p className="mb-3 text-xs font-medium text-white">Referință variabile</p>
            <div className="space-y-1.5 text-xs">
              {[
                ["keyword", "Keyword-ul țintă"],
                ["site_context", "Nișă, audiență, ton (din SiteContext)"],
                ["outline", "JSON cu secțiunile outline generate"],
                ["author_context", "Nume autor + credențiale"],
                ["internal_links_context", "Lista slug-urilor existente pentru link-uri interne"],
              ].map(([v, desc]) => (
                <div key={v} className="flex items-start gap-2">
                  <code className="shrink-0 rounded bg-yellow-500/10 px-1.5 py-0.5 text-yellow-300">{`{${v}}`}</code>
                  <span className="text-muted">{desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {showTest && templateForTest && (
        <TemplateTestModal
          open={showTest}
          onClose={() => setShowTest(false)}
          template={templateForTest}
        />
      )}
    </div>
  );
}
