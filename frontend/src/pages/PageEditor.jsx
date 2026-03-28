import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  Loader2, ChevronRight, Save, Copy, Check,
  CheckCircle, Globe, Image as ImageIcon, ExternalLink,
} from "lucide-react";
import {
  getPage,
  updatePage,
  updatePageStatus,
  findPageImage,
  regenerateSection,
  publishPage,
} from "../api/pages";
import QualityScoreCircle from "../components/QualityScoreCircle";
import FaqEditor from "../components/FaqEditor";
import RegenerateButton from "../components/RegenerateButton";

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";
const LABEL = "mb-1.5 block text-xs font-medium text-muted";
const SECTION_HDR = "mb-3 flex items-center justify-between";

const META_COLOR = (len) =>
  len >= 120 && len <= 155 ? "text-green-400" :
  len > 155 ? "text-red-400" :
  "text-yellow-400";

export default function PageEditor() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveOk, setSaveOk] = useState(false);
  const [schemaOpen, setSchemaOpen] = useState(false);
  const [schemaCopied, setSchemaCopied] = useState(false);
  const [findingImg, setFindingImg] = useState(false);
  const [regenLoading, setRegenLoading] = useState({});
  const [statusLoading, setStatusLoading] = useState(false);

  // Local editable state
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [metaDesc, setMetaDesc] = useState("");
  const [content, setContent] = useState("");
  const [faqItems, setFaqItems] = useState([]);

  const loadPage = useCallback(async () => {
    try {
      const res = await getPage(id);
      const p = res.data?.data;
      setPage(p);
      setTitle(p?.title || "");
      setSlug(p?.slug || "");
      setMetaDesc(p?.meta_description || "");
      setContent(p?.content_html || "");
      setFaqItems(p?.faq_items || []);
    } catch {
      // 404 handled below
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadPage(); }, [loadPage]);

  // Auto-generate slug from title
  const handleTitleChange = (val) => {
    setTitle(val);
    if (!slug || slug === slugify(title)) {
      setSlug(slugify(val));
    }
  };

  const slugify = (str) =>
    str.toLowerCase().trim()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-");

  const handleSave = async () => {
    setSaving(true);
    try {
      await updatePage(id, {
        title,
        slug,
        meta_description: metaDesc,
        content_html: content,
        faq_items: faqItems,
      });
      setSaveOk(true);
      setTimeout(() => setSaveOk(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (status) => {
    setStatusLoading(true);
    try {
      const res = await updatePageStatus(id, status);
      setPage(res.data?.data);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleFindImage = async () => {
    setFindingImg(true);
    try {
      const res = await findPageImage(id);
      const result = res.data?.data;
      if (result?.url) {
        setPage((p) => ({ ...p, featured_image_url: result.url, featured_image_credit: result.credit }));
      }
    } finally {
      setFindingImg(false);
    }
  };

  const handleRegen = async (section) => {
    setRegenLoading((s) => ({ ...s, [section]: true }));
    try {
      const res = await regenerateSection(id, section);
      const updated = res.data?.data;
      if (section === "intro" || section === "body") {
        if (updated?.content_html) setContent(updated.content_html);
      } else if (section === "faq") {
        if (updated?.faq_items) setFaqItems(updated.faq_items);
      } else if (section === "meta") {
        if (updated?.title) setTitle(updated.title);
        if (updated?.meta_description) setMetaDesc(updated.meta_description);
        if (updated?.slug) setSlug(updated.slug);
      }
    } finally {
      setRegenLoading((s) => ({ ...s, [section]: false }));
    }
  };

  const copySchema = () => {
    if (page?.schema_markup) {
      navigator.clipboard.writeText(JSON.stringify(page.schema_markup, null, 2));
      setSchemaCopied(true);
      setTimeout(() => setSchemaCopied(false), 2000);
    }
  };

  // Score breakdown helpers
  const scoreBreakdown = page ? [
    { label: "Conținut minim (600 cuvinte)", ok: (page.word_count || 0) >= 600 },
    { label: "Lizibilitate bună", ok: (page.readability_score || 0) >= 40 },
    { label: "Intent validat", ok: page.intent_validation_passed === true },
    { label: "FAQ prezent", ok: faqItems.length >= 3 },
    { label: "Schema markup", ok: !!page.schema_markup },
    { label: "Meta description (120-155 ch)", ok: metaDesc.length >= 120 && metaDesc.length <= 155 },
    { label: "Titlu (≤60 ch)", ok: title.length > 0 && title.length <= 60 },
  ] : [];

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  if (!page) {
    return <div className="text-center text-muted py-12">Pagina nu a fost găsită.</div>;
  }

  const bc = page.breadcrumb;

  return (
    <div className="space-y-6 pb-24">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-xs text-muted flex-wrap">
        <Link to="/" className="hover:text-white transition">Dashboard</Link>
        {bc && (
          <>
            <ChevronRight className="h-3 w-3" />
            <Link to={`/projects/${bc.project_id}`} className="hover:text-white transition">
              {bc.project_name}
            </Link>
            <ChevronRight className="h-3 w-3" />
            <Link to={`/campaigns/${bc.campaign_id}`} className="hover:text-white transition">
              {bc.campaign_name}
            </Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-white truncate max-w-[200px]">{bc.keyword_text}</span>
          </>
        )}
      </div>

      {/* Page title row */}
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-white truncate">{title || "Pagină fără titlu"}</h1>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : saveOk ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
            {saveOk ? "Salvat!" : "Salvează"}
          </button>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_340px]">

        {/* ---- LEFT COLUMN ---- */}
        <div className="space-y-6">

          {/* Title */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <div className={SECTION_HDR}>
              <label className="text-sm font-medium text-white">Titlu</label>
              <div className="flex items-center gap-2">
                <span className={`text-xs ${title.length > 60 ? "text-red-400" : "text-muted"}`}>
                  {title.length}/60
                </span>
                <RegenerateButton
                  loading={regenLoading.meta}
                  onClick={() => handleRegen("meta")}
                  label="Regenerează meta"
                />
              </div>
            </div>
            <input
              value={title}
              onChange={(e) => handleTitleChange(e.target.value)}
              className={FIELD}
              placeholder="Titlul paginii"
            />
          </div>

          {/* Slug */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <label className={LABEL}>Slug URL</label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted">/</span>
              <input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className={FIELD}
                placeholder="slug-pagina"
              />
            </div>
          </div>

          {/* Meta description */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <div className={SECTION_HDR}>
              <label className="text-sm font-medium text-white">Meta Description</label>
              <span className={`text-xs font-medium ${META_COLOR(metaDesc.length)}`}>
                {metaDesc.length}/155
              </span>
            </div>
            <textarea
              value={metaDesc}
              onChange={(e) => setMetaDesc(e.target.value)}
              rows={3}
              className={`${FIELD} resize-none`}
              placeholder="Descrierea meta pentru motoarele de căutare"
            />
          </div>

          {/* SERP Preview */}
          <SerpPreview title={title} slug={slug} meta={metaDesc} page={page} />

          {/* Content */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <div className={SECTION_HDR}>
              <label className="text-sm font-medium text-white">Conținut HTML</label>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">{page.word_count} cuvinte</span>
                <RegenerateButton
                  loading={regenLoading.intro}
                  onClick={() => handleRegen("intro")}
                  label="Intro"
                />
                <RegenerateButton
                  loading={regenLoading.body}
                  onClick={() => handleRegen("body")}
                  label="Body"
                />
              </div>
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={18}
              className={`${FIELD} resize-y font-mono text-xs`}
              placeholder="<h2>...</h2><p>...</p>"
            />
          </div>

          {/* FAQ */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <div className={SECTION_HDR}>
              <label className="text-sm font-medium text-white">FAQ Items</label>
              <RegenerateButton
                loading={regenLoading.faq}
                onClick={() => handleRegen("faq")}
                label="Regenerează FAQ"
              />
            </div>
            <FaqEditor items={faqItems} onChange={setFaqItems} />
          </div>

          {/* Schema Markup */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <div className={SECTION_HDR}>
              <label className="text-sm font-medium text-white">Schema Markup</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSchemaOpen((v) => !v)}
                  className="text-xs text-muted hover:text-white transition"
                >
                  {schemaOpen ? "Ascunde" : "Afișează"}
                </button>
                <button
                  onClick={copySchema}
                  disabled={!page.schema_markup}
                  className="flex items-center gap-1 text-xs text-muted hover:text-white disabled:opacity-40 transition"
                >
                  {schemaCopied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  {schemaCopied ? "Copiat!" : "Copiază"}
                </button>
              </div>
            </div>
            {schemaOpen && page.schema_markup && (
              <pre className="overflow-x-auto rounded-lg bg-bg p-3 text-[11px] text-muted max-h-64">
                {JSON.stringify(page.schema_markup, null, 2)}
              </pre>
            )}
            {!page.schema_markup && (
              <p className="text-xs text-muted">Schema markup nu a fost generat.</p>
            )}
          </div>

        </div>

        {/* ---- RIGHT COLUMN ---- */}
        <div className="space-y-4">

          {/* Quality Score */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <h3 className="mb-3 text-sm font-medium text-white">Calitate</h3>
            <div className="flex flex-col items-center gap-4">
              <QualityScoreCircle score={page.quality_score} />
              <div className="w-full space-y-1.5">
                {scoreBreakdown.map(({ label, ok }) => (
                  <div key={label} className="flex items-center gap-2 text-xs">
                    <span className={ok ? "text-green-400" : "text-red-400"}>
                      {ok ? "✓" : "✗"}
                    </span>
                    <span className={ok ? "text-white" : "text-muted"}>{label}</span>
                  </div>
                ))}
              </div>
              {page.intent_validation_issues?.length > 0 && (
                <div className="w-full rounded-lg bg-yellow-500/10 p-3">
                  <p className="mb-1 text-xs font-medium text-yellow-400">Probleme intent:</p>
                  {page.intent_validation_issues.map((issue, i) => (
                    <p key={i} className="text-xs text-yellow-300">• {issue}</p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Featured Image */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <h3 className="mb-3 text-sm font-medium text-white">Imagine Featured</h3>
            {page.featured_image_url ? (
              <div className="space-y-2">
                <img
                  src={page.featured_image_url}
                  alt="Featured"
                  className="w-full rounded-lg object-cover"
                  style={{ maxHeight: 160 }}
                />
                {page.featured_image_credit && (
                  <p className="text-[11px] text-muted">{page.featured_image_credit}</p>
                )}
                <button
                  onClick={handleFindImage}
                  disabled={findingImg}
                  className="flex items-center gap-1.5 w-full justify-center rounded-lg border border-border px-3 py-2 text-xs text-muted hover:text-white hover:border-accent/40 transition disabled:opacity-50"
                >
                  {findingImg ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ImageIcon className="h-3.5 w-3.5" />}
                  Caută altă imagine
                </button>
              </div>
            ) : (
              <button
                onClick={handleFindImage}
                disabled={findingImg}
                className="flex items-center gap-1.5 w-full justify-center rounded-lg border border-dashed border-border px-3 py-6 text-sm text-muted hover:text-white hover:border-accent/40 transition disabled:opacity-50"
              >
                {findingImg ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImageIcon className="h-4 w-4" />}
                Caută Imagine
              </button>
            )}
          </div>

          {/* Internal Links */}
          {page.internal_links_suggested?.length > 0 && (
            <div className="rounded-xl border border-border bg-bg-card p-4">
              <h3 className="mb-3 text-sm font-medium text-white">Link-uri Interne</h3>
              <div className="space-y-1.5">
                {page.internal_links_suggested.map((link, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <ExternalLink className="h-3 w-3 text-muted flex-shrink-0" />
                    <span className="text-white truncate">{link.text || link.slug}</span>
                    <span className="text-muted">/{link.slug}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* GEO Score */}
          {page.geo_score != null && (
            <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-4">
              <h3 className="mb-3 text-sm font-medium text-white flex items-center gap-2">
                <span className="text-purple-400">⚡</span> GEO Score
              </h3>
              <div className="flex flex-col items-center gap-3 mb-4">
                <GeoScoreCircle score={page.geo_score} />
              </div>

              {/* Direct Answer Preview */}
              {page.has_direct_answer && (
                <div className="mb-3 rounded-lg border border-blue-500/20 bg-blue-500/10 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-blue-400 mb-1">
                    Răspuns direct pentru AI
                  </p>
                  <p className="text-xs text-white/80 leading-relaxed">
                    {page.content_html
                      ? (() => {
                          const m = page.content_html.match(/<p[^>]*>(.*?)<\/p>/is);
                          return m ? m[1].replace(/<[^>]+>/g, "").slice(0, 150) + "..." : "";
                        })()
                      : ""}
                  </p>
                </div>
              )}

              {/* Breakdown */}
              {page.geo_breakdown && (
                <div className="space-y-1.5">
                  {Object.entries(page.geo_breakdown).map(([key, val]) => {
                    const labels = {
                      direct_answer: "Răspuns direct",
                      speakable_sections: "Secțiuni speakable",
                      qa_structure: "Structură Q&A",
                      statistics: "Statistici cu surse",
                      author_schema: "Schema autor",
                      definition_intro: "Definiție în intro",
                      comparison_table: "Tabel comparativ",
                      sentence_length: "Fraze scurte",
                    };
                    return (
                      <div key={key} className="flex items-center gap-2 text-xs">
                        <span className={val.ok ? "text-green-400" : "text-red-400"}>
                          {val.ok ? "✓" : "✗"}
                        </span>
                        <span className={val.ok ? "text-white" : "text-muted"}>
                          {labels[key] || key}
                        </span>
                        <span className="ml-auto text-muted text-[10px]">
                          {val.points}/{val.max}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Speakable sections */}
              {page.speakable_sections?.length > 0 && (
                <div className="mt-3 border-t border-border pt-3">
                  <p className="text-[10px] uppercase tracking-wider text-muted mb-1.5">Secțiuni speakable</p>
                  {page.speakable_sections.map((s, i) => (
                    <p key={i} className="text-xs text-purple-300">• {s}</p>
                  ))}
                </div>
              )}

              {/* GEO Tips */}
              {page.geo_breakdown && <GeoTips breakdown={page.geo_breakdown} />}
            </div>
          )}

          {/* Publish */}
          <div className="rounded-xl border border-border bg-bg-card p-4">
            <h3 className="mb-3 text-sm font-medium text-white">Publicare</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted">Status curent</span>
                <PageStatusBadge status={page.status} />
              </div>
              {page.cost_usd > 0 && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Cost generare</span>
                  <span className="text-white">${Number(page.cost_usd).toFixed(4)}</span>
                </div>
              )}
              {page.model_used && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted">Model AI</span>
                  <span className="text-white">{page.model_used}</span>
                </div>
              )}
              {page.published_url && (
                <a
                  href={page.published_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-accent hover:underline"
                >
                  <Globe className="h-3 w-3" />
                  Vizualizează pe site
                </a>
              )}
            </div>

            <div className="mt-4 flex flex-col gap-2">
              {page.status === "draft" && (
                <button
                  onClick={() => handleStatusChange("approved")}
                  disabled={statusLoading}
                  className="flex items-center justify-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition"
                >
                  {statusLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                  Aprobă
                </button>
              )}
              {(page.status === "draft" || page.status === "approved") && (
                <button
                  onClick={async () => {
                    setStatusLoading(true);
                    try {
                      const res = await publishPage(id);
                      setPage((p) => ({ ...p, status: "published", published_url: res.data?.data?.published_url || p.published_url }));
                    } finally {
                      setStatusLoading(false);
                    }
                  }}
                  disabled={statusLoading}
                  className="flex items-center justify-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50 transition"
                >
                  {statusLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Globe className="h-4 w-4" />}
                  Publică pe site
                </button>
              )}
              {page.status !== "rejected" && page.status !== "draft" && (
                <button
                  onClick={() => handleStatusChange("draft")}
                  disabled={statusLoading}
                  className="text-xs text-muted hover:text-white transition"
                >
                  Resetează la Draft
                </button>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pixel-width estimator using an off-screen Canvas
// ---------------------------------------------------------------------------
let _canvas = null;
function estimatePx(text, font) {
  if (!text) return 0;
  if (typeof document === "undefined") return text.length * 7;
  _canvas = _canvas || document.createElement("canvas");
  const ctx = _canvas.getContext("2d");
  ctx.font = font;
  return Math.round(ctx.measureText(text).width);
}

// ---------------------------------------------------------------------------
// SERP Preview
// ---------------------------------------------------------------------------
function SerpPreview({ title, slug, meta, page }) {
  const domain = (() => {
    if (page?.published_url) {
      try { return new URL(page.published_url).hostname; } catch { /* */ }
    }
    return "yoursite.com";
  })();

  const titlePx  = estimatePx(title, "20px arial, sans-serif");
  const metaChars = meta?.length || 0;
  const metaPxEst = metaChars * 6;

  const titleColor =
    titlePx <= 580 ? "text-green-400" :
    titlePx <= 600 ? "text-yellow-400" :
                     "text-red-400";

  const RULER_MAX = 700;
  const markerPct = Math.min((titlePx / RULER_MAX) * 100, 100);
  const lineColor =
    titlePx <= 580 ? "bg-green-500" :
    titlePx <= 600 ? "bg-yellow-500" :
                     "bg-red-500";

  return (
    <div className="rounded-xl border border-border bg-bg-card p-4 space-y-3">
      <p className="text-sm font-medium text-white">Previzualizare SERP</p>

      {/* Google-style preview box */}
      <div className="rounded-lg border border-border bg-white/5 p-4 space-y-1" style={{ maxWidth: 652 }}>
        {/* Breadcrumb / URL */}
        <p className="text-xs text-green-400 font-mono truncate">
          {domain}{slug ? `/${slug}` : ""}
        </p>

        {/* Title */}
        <p
          className="text-[20px] leading-snug text-blue-400 cursor-pointer hover:underline"
          style={{ maxWidth: 600, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}
        >
          {title || <span className="text-muted italic">Titlu pagină…</span>}
        </p>

        {/* Meta description */}
        <p
          className="text-sm text-gray-400 leading-snug"
          style={{ maxHeight: "2.8em", overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}
        >
          {meta || <span className="italic text-muted">Meta description…</span>}
        </p>
      </div>

      {/* Title pixel ruler */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-mono text-muted">Titlu: ~{titlePx}px</span>
          <span className={`font-mono font-medium ${titleColor}`}>
            {titlePx <= 580 ? "✓ OK" : titlePx <= 600 ? "⚠ Limită" : "✗ Prea lung"}
          </span>
        </div>
        <div className="relative h-2 w-full rounded-full bg-border overflow-visible">
          {/* Zone markers */}
          <div className="absolute inset-y-0 left-0 rounded-l-full bg-green-500/20" style={{ width: `${(580/RULER_MAX)*100}%` }} />
          <div className="absolute inset-y-0 bg-yellow-500/20" style={{ left: `${(580/RULER_MAX)*100}%`, width: `${(20/RULER_MAX)*100}%` }} />
          <div className="absolute inset-y-0 rounded-r-full bg-red-500/20" style={{ left: `${(600/RULER_MAX)*100}%`, right: 0 }} />
          {/* Indicator */}
          <div
            className={`absolute top-1/2 -translate-y-1/2 h-3 w-1 rounded-full ${lineColor} transition-all duration-150`}
            style={{ left: `${markerPct}%` }}
          />
        </div>
        <div className="flex justify-between font-mono text-[10px] text-muted/60">
          <span>0</span><span>580</span><span>600</span><span>700px</span>
        </div>
      </div>

      {/* Meta pixel estimate */}
      <p className="text-[11px] font-mono text-muted">
        Meta: {metaChars} ch · ~{metaPxEst}px
        {metaChars >= 120 && metaChars <= 155
          ? <span className="ml-1 text-green-400">✓</span>
          : <span className="ml-1 text-yellow-400">⚠ ideal 120-155</span>}
      </p>
    </div>
  );
}

function PageStatusBadge({ status }) {
  const map = {
    draft: "bg-orange-500/10 text-orange-400",
    approved: "bg-green-500/10 text-green-400",
    published: "bg-teal-500/10 text-teal-400",
    rejected: "bg-red-500/10 text-red-400",
  };
  return (
    <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${map[status] || "bg-gray-500/10 text-gray-400"}`}>
      {status}
    </span>
  );
}

function GeoScoreCircle({ score }) {
  const r = 28, cx = 36, cy = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 70 ? "#a855f7" : score >= 40 ? "#f59e0b" : "#ef4444";
  return (
    <svg width="72" height="72" viewBox="0 0 72 72">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#2a2d3a" strokeWidth="6" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="6"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`} />
      <text x={cx} y={cy + 5} textAnchor="middle" fill={color} fontSize="14" fontWeight="bold">{score}</text>
    </svg>
  );
}

function GeoTips({ breakdown }) {
  const tips = [];
  if (!breakdown.direct_answer?.ok) tips.push("Adaugă un răspuns direct în primul paragraf (max 60 cuvinte, conține keyword-ul)");
  if (!breakdown.speakable_sections?.ok) tips.push("Marchează cel puțin 3 paragrafe cu <!-- speakable --> pentru AI assistants");
  if (!breakdown.qa_structure?.ok) tips.push("Adaugă minim 3 întrebări H3 cu răspunsuri scurte (sub 50 cuvinte)");
  if (!breakdown.statistics?.ok) tips.push("Include cel puțin 2 statistici cu surse explicite (ex: 'Conform Google, X%...')");
  if (!breakdown.definition_intro?.ok) tips.push("Definește conceptul principal în primele 100 cuvinte");
  if (!breakdown.comparison_table?.ok) tips.push("Adaugă un tabel comparativ pentru a fi citat în răspunsuri comparative");
  if (tips.length === 0) return null;
  return (
    <div className="mt-3 border-t border-border pt-3">
      <p className="text-[10px] uppercase tracking-wider text-purple-400 mb-2">Sfaturi GEO</p>
      {tips.map((t, i) => (
        <p key={i} className="text-[11px] text-muted mb-1">• {t}</p>
      ))}
    </div>
  );
}
