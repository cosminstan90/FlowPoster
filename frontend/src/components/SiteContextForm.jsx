import { useState, useEffect } from "react";
import { Loader2, Sparkles, Save, AlertCircle, CheckCircle2 } from "lucide-react";
import { getSiteContext, upsertSiteContext, analyzeSite } from "../api/projects";

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";
const LABEL = "mb-1.5 block text-xs text-muted";

const TONES = [
  { value: "professional", label: "Professional" },
  { value: "friendly",     label: "Prietenos" },
  { value: "expert",       label: "Expert" },
  { value: "educational",  label: "Educativ" },
  { value: "conversational", label: "Conversațional" },
  { value: "casual",       label: "Casual" },
];

const EMPTY = {
  niche: "",
  target_audience: "",
  tone: "professional",
  topics_to_avoid: "",
  author_name: "",
  author_bio: "",
  author_credentials: "",
  site_founded_year: "",
  editorial_policy_url: "",
  competitor_urls: "",
  sitemap_urls: "",
};

function fromContext(ctx) {
  if (!ctx) return EMPTY;
  return {
    niche: ctx.niche || "",
    target_audience: ctx.target_audience || "",
    tone: ctx.tone || "professional",
    topics_to_avoid: ctx.topics_to_avoid || "",
    author_name: ctx.author_name || "",
    author_bio: ctx.author_bio || "",
    author_credentials: ctx.author_credentials || "",
    site_founded_year: ctx.site_founded_year ? String(ctx.site_founded_year) : "",
    editorial_policy_url: ctx.editorial_policy_url || "",
    competitor_urls: (ctx.competitor_urls || []).join("\n"),
    sitemap_urls: (ctx.sitemap_urls || []).join("\n"),
  };
}

function toPayload(form) {
  return {
    niche: form.niche,
    target_audience: form.target_audience,
    tone: form.tone,
    topics_to_avoid: form.topics_to_avoid || null,
    author_name: form.author_name || null,
    author_bio: form.author_bio || null,
    author_credentials: form.author_credentials || null,
    site_founded_year: form.site_founded_year ? Number(form.site_founded_year) : null,
    editorial_policy_url: form.editorial_policy_url || null,
    competitor_urls: form.competitor_urls.split("\n").map(s => s.trim()).filter(Boolean),
    sitemap_urls: form.sitemap_urls.split("\n").map(s => s.trim()).filter(Boolean),
  };
}

export default function SiteContextForm({ projectId, domain }) {
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    getSiteContext(projectId)
      .then((res) => setForm(fromContext(res.data)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError("");
    setSuccess("");
    try {
      const res = await analyzeSite(projectId);
      const s = res.data;
      setForm((f) => ({
        ...f,
        niche: s.niche || f.niche,
        target_audience: s.target_audience || f.target_audience,
        tone: s.tone || f.tone,
        topics_to_avoid: s.topics_to_avoid || f.topics_to_avoid,
      }));
      setSuccess("Câmpurile au fost completate de AI. Verifică și salvează.");
    } catch (err) {
      setError(err.response?.data?.detail || "Nu am putut analiza site-ul.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await upsertSiteContext(projectId, toPayload(form));
      setSuccess("Context salvat cu succes.");
    } catch (err) {
      setError(err.response?.data?.detail || "Eroare la salvare.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {/* AI Analyze button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Site Context</h2>
          <p className="text-xs text-muted mt-0.5">
            Informațiile sunt folosite de AI la generarea articolelor.
          </p>
        </div>
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={analyzing}
          className="flex items-center gap-1.5 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-sm font-medium text-accent hover:bg-accent/20 disabled:opacity-50 transition"
        >
          {analyzing
            ? <Loader2 className="h-4 w-4 animate-spin" />
            : <Sparkles className="h-4 w-4" />}
          {analyzing ? "Analizez..." : "Analizează cu AI"}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 rounded-lg bg-green-500/10 border border-green-500/20 px-3 py-2 text-sm text-green-400">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {success}
        </div>
      )}

      {/* Core fields */}
      <div className="rounded-lg border border-border p-4 space-y-4">
        <p className="text-xs font-medium text-white">Informații principale</p>

        <div>
          <label className={LABEL}>Nișă *</label>
          <input
            value={form.niche}
            onChange={set("niche")}
            required
            className={FIELD}
            placeholder="ex: sănătate naturistă, finanțe personale"
          />
        </div>

        <div>
          <label className={LABEL}>Audiență țintă *</label>
          <textarea
            value={form.target_audience}
            onChange={set("target_audience")}
            required
            rows={2}
            className={`${FIELD} resize-none`}
            placeholder="ex: adulți 25-45 ani interesați de sănătate preventivă"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={LABEL}>Ton *</label>
            <select value={form.tone} onChange={set("tone")} className={FIELD}>
              {TONES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={LABEL}>An fondare</label>
            <input
              type="number"
              min={1990}
              max={2030}
              value={form.site_founded_year}
              onChange={set("site_founded_year")}
              className={FIELD}
              placeholder="2020"
            />
          </div>
        </div>

        <div>
          <label className={LABEL}>Subiecte de evitat</label>
          <textarea
            value={form.topics_to_avoid}
            onChange={set("topics_to_avoid")}
            rows={2}
            className={`${FIELD} resize-none`}
            placeholder="ex: politică, religie, conținut controversat"
          />
        </div>
      </div>

      {/* Author */}
      <div className="rounded-lg border border-border p-4 space-y-4">
        <p className="text-xs font-medium text-white">Autor (E-E-A-T)</p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={LABEL}>Nume autor</label>
            <input value={form.author_name} onChange={set("author_name")} className={FIELD} placeholder="Dr. Ion Popescu" />
          </div>
          <div>
            <label className={LABEL}>Credențiale</label>
            <input value={form.author_credentials} onChange={set("author_credentials")} className={FIELD} placeholder="Medic, 10 ani experiență" />
          </div>
        </div>
        <div>
          <label className={LABEL}>Bio autor</label>
          <textarea value={form.author_bio} onChange={set("author_bio")} rows={2} className={`${FIELD} resize-none`} placeholder="Scurtă descriere..." />
        </div>
        <div>
          <label className={LABEL}>URL politică editorială</label>
          <input value={form.editorial_policy_url} onChange={set("editorial_policy_url")} className={FIELD} placeholder="https://site.ro/editorial" />
        </div>
      </div>

      {/* URLs */}
      <div className="rounded-lg border border-border p-4 space-y-4">
        <p className="text-xs font-medium text-white">URL-uri (câte unul pe linie)</p>
        <div>
          <label className={LABEL}>Competitori</label>
          <textarea value={form.competitor_urls} onChange={set("competitor_urls")} rows={3} className={`${FIELD} resize-none font-mono text-xs`} placeholder={"https://competitor1.ro\nhttps://competitor2.ro"} />
        </div>
        <div>
          <label className={LABEL}>Sitemap-uri</label>
          <textarea value={form.sitemap_urls} onChange={set("sitemap_urls")} rows={2} className={`${FIELD} resize-none font-mono text-xs`} placeholder={"https://site.ro/sitemap.xml"} />
        </div>
      </div>

      {/* Save */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-1.5 rounded-lg bg-accent px-5 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
        >
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          {saving ? "Salvez..." : "Salvează"}
        </button>
      </div>
    </form>
  );
}
