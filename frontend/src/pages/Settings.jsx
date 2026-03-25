import { useEffect, useState } from "react";
import {
  Key, Plus, Trash2, Copy, CheckCircle, Loader2, Eye, EyeOff, Shield
} from "lucide-react";
import { listAPIKeys, createAPIKey, revokeAPIKey } from "../api/apiKeys";

const SCOPES = [
  { value: "import_keywords", label: "Import Keywords", desc: "Permite importul de cuvinte cheie via webhook" },
  { value: "read_campaigns", label: "Read Campaigns", desc: "Permite citirea statusului campaniilor" },
  { value: "publish_pages", label: "Publish Pages", desc: "Permite aprobarea și publicarea paginilor" },
];

function ScopeBadge({ scope }) {
  const colors = {
    import_keywords: "bg-blue-500/10 text-blue-400",
    read_campaigns: "bg-purple-500/10 text-purple-400",
    publish_pages: "bg-green-500/10 text-green-400",
  };
  const labels = {
    import_keywords: "import",
    read_campaigns: "read",
    publish_pages: "publish",
  };
  return (
    <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-medium ${colors[scope] ?? "bg-gray-500/10 text-gray-400"}`}>
      {labels[scope] ?? scope}
    </span>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handle = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handle}
      className="rounded p-1 text-muted hover:text-white transition"
      title="Copiază"
    >
      {copied ? <CheckCircle className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
    </button>
  );
}

function NewKeyModal({ open, onClose, onCreate }) {
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const toggleScope = (s) =>
    setScopes((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);

  const handleSubmit = async () => {
    if (!name.trim()) { setError("Numele este obligatoriu"); return; }
    if (scopes.length === 0) { setError("Selectează cel puțin un scope"); return; }
    setLoading(true);
    setError("");
    try {
      const res = await createAPIKey({ name: name.trim(), scopes });
      onCreate(res.data);
      setName("");
      setScopes([]);
      onClose();
    } catch (e) {
      setError(e.response?.data?.detail || "Eroare la creare");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border bg-bg-card p-6 shadow-2xl">
        <h3 className="mb-4 text-lg font-semibold text-white">API Key nouă</h3>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs text-muted">Nume (ex: n8n Production)</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Numele cheii"
              className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="mb-2 block text-xs text-muted">Permisiuni (scopes)</label>
            <div className="space-y-2">
              {SCOPES.map((s) => (
                <label key={s.value} className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3 hover:border-accent/40 transition">
                  <input
                    type="checkbox"
                    checked={scopes.includes(s.value)}
                    onChange={() => toggleScope(s.value)}
                    className="mt-0.5 accent-accent"
                  />
                  <div>
                    <p className="text-sm font-medium text-white">{s.label}</p>
                    <p className="text-xs text-muted">{s.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {error && (
            <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition"
          >
            Anulează
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Creează
          </button>
        </div>
      </div>
    </div>
  );
}

function NewKeyDisplay({ keyData, onClose }) {
  const [visible, setVisible] = useState(false);
  if (!keyData) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-green-500/30 bg-bg-card p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-400" />
          <h3 className="text-lg font-semibold text-white">API Key creată cu succes</h3>
        </div>

        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 mb-4">
          <p className="text-sm text-yellow-300 font-medium">
            ⚠️ Copiază cheia acum — nu va mai fi afișată niciodată!
          </p>
        </div>

        <div className="rounded-lg border border-border bg-bg p-3 flex items-center gap-2">
          <code className={`flex-1 text-sm font-mono ${visible ? "text-white" : "text-muted select-none"}`}>
            {visible ? keyData.full_key : "sk-" + "•".repeat(40)}
          </code>
          <button
            onClick={() => setVisible((v) => !v)}
            className="rounded p-1 text-muted hover:text-white transition"
          >
            {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          <CopyButton text={keyData.full_key} />
        </div>

        <div className="mt-3 space-y-1 text-xs text-muted">
          <p>Nume: <span className="text-white">{keyData.name}</span></p>
          <p>Scopes: {keyData.scopes.map((s) => <ScopeBadge key={s} scope={s} />)}</p>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
          >
            Am copiat cheia
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Settings() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [revoking, setRevoking] = useState(null);

  const fetchKeys = async () => {
    try {
      const res = await listAPIKeys();
      setKeys(res.data || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchKeys(); }, []);

  const handleCreated = (data) => {
    setNewKey(data);
    fetchKeys();
  };

  const handleRevoke = async (id) => {
    if (!window.confirm("Revocare cheie API? Această acțiune nu poate fi anulată.")) return;
    setRevoking(id);
    try {
      await revokeAPIKey(id);
      setKeys((prev) => prev.map((k) => k.id === id ? { ...k, is_active: false } : k));
    } catch {
      // ignore
    } finally {
      setRevoking(null);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Setări</h1>
        <p className="mt-1 text-sm text-muted">Gestionează cheile API și integrările externe</p>
      </div>

      {/* API Keys section */}
      <div className="rounded-2xl border border-border bg-bg-card p-6">
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-semibold text-white">Chei API</h2>
          </div>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-black hover:bg-accent-hover transition"
          >
            <Plus className="h-4 w-4" />
            Cheie nouă
          </button>
        </div>

        {/* Info box */}
        <div className="mb-4 rounded-lg border border-border bg-bg p-3 text-xs text-muted space-y-1">
          <p>Folosește cheile API cu header <code className="text-white">X-API-Key: sk-...</code> pentru integrări n8n, Zapier sau alte servicii externe.</p>
          <p>Endpoint-uri disponibile: <code className="text-accent">/api/webhooks/import</code> · <code className="text-accent">/api/webhooks/import/sheets</code> · <code className="text-accent">/api/webhooks/campaign/&#123;id&#125;/status</code> · <code className="text-accent">/api/webhooks/approve-all/&#123;id&#125;</code></p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-muted" />
          </div>
        ) : keys.length === 0 ? (
          <div className="py-10 text-center">
            <Key className="mx-auto h-10 w-10 text-muted/30 mb-3" />
            <p className="text-sm text-muted">Nicio cheie API. Creează una pentru a conecta n8n sau alte servicii.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {keys.map((key) => (
              <div key={key.id} className={`flex items-center gap-3 py-3 ${!key.is_active ? "opacity-40" : ""}`}>
                <div className="rounded-lg bg-accent/10 p-2">
                  <Key className="h-4 w-4 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white truncate">{key.name}</p>
                    {!key.is_active && (
                      <span className="rounded bg-red-500/10 px-1.5 py-0.5 text-[10px] text-red-400">revocată</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <code className="text-xs text-muted">{key.key_masked}</code>
                    <span className="text-muted/40">·</span>
                    {key.scopes.map((s) => <ScopeBadge key={s} scope={s} />)}
                  </div>
                  {key.last_used_at && (
                    <p className="text-[11px] text-muted mt-0.5">
                      Ultima utilizare: {new Date(key.last_used_at).toLocaleString("ro-RO")}
                    </p>
                  )}
                </div>
                {key.is_active && (
                  <button
                    disabled={revoking === key.id}
                    onClick={() => handleRevoke(key.id)}
                    title="Revocă cheia"
                    className="rounded-lg p-2 text-red-400 hover:bg-red-500/10 transition disabled:opacity-50"
                  >
                    {revoking === key.id
                      ? <Loader2 className="h-4 w-4 animate-spin" />
                      : <Trash2 className="h-4 w-4" />}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Webhook reference */}
      <div className="rounded-2xl border border-border bg-bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">Exemplu n8n — HTTP Request</h2>
        <div className="rounded-lg bg-bg border border-border p-4 text-xs font-mono text-muted space-y-1">
          <p><span className="text-accent">Method:</span> POST</p>
          <p><span className="text-accent">URL:</span> https://seo.nrankai.com/api/webhooks/import</p>
          <p><span className="text-accent">Header:</span> X-API-Key: sk-...</p>
          <p className="pt-2"><span className="text-accent">Body (JSON):</span></p>
          <pre className="whitespace-pre-wrap text-white/70">{JSON.stringify({
            campaign_id: "uuid-campanie",
            keywords: [
              { keyword: "exemplu keyword", search_volume: 1200 },
              { keyword: "alt keyword" }
            ]
          }, null, 2)}</pre>
        </div>
      </div>

      {/* Modals */}
      <NewKeyModal
        open={showNew}
        onClose={() => setShowNew(false)}
        onCreate={handleCreated}
      />
      <NewKeyDisplay keyData={newKey} onClose={() => setNewKey(null)} />
    </div>
  );
}
