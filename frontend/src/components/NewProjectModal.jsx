import { useState } from "react";
import { Loader2 } from "lucide-react";
import Modal from "./Modal";

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";
const LABEL = "mb-1.5 block text-xs text-muted";

const CMS_TYPES = [
  { value: "wordpress", label: "WordPress" },
  { value: "php_custom", label: "PHP Custom" },
];

const EMPTY = {
  name: "",
  domain: "",
  description: "",
  monthly_budget_usd: "0",
  cms_type: "wordpress",
  wp_url: "",
  wp_username: "",
  wp_app_password: "",
  php_endpoint: "",
  php_secret: "",
};

export default function NewProjectModal({ open, onClose, onSave }) {
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      let cms_config = null;
      if (form.cms_type === "wordpress") {
        cms_config = {
          url: form.wp_url,
          username: form.wp_username,
          app_password: form.wp_app_password,
        };
      } else if (form.cms_type === "php_custom") {
        cms_config = {
          endpoint: form.php_endpoint,
          secret: form.php_secret,
        };
      }

      await onSave({
        name: form.name,
        domain: form.domain,
        description: form.description || null,
        monthly_budget_usd: Number(form.monthly_budget_usd) || 0,
        cms_type: form.cms_type,
        cms_config,
      });
      setForm(EMPTY);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Proiect nou"
      size="md"
      footer={
        <>
          <button onClick={onClose} className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-white transition">
            Anulează
          </button>
          <button
            form="new-project-form"
            type="submit"
            disabled={loading || !form.name || !form.domain}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent-hover disabled:opacity-50 transition"
          >
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Creează proiect
          </button>
        </>
      }
    >
      <form id="new-project-form" onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className={LABEL}>Nume *</label>
          <input value={form.name} onChange={set("name")} required className={FIELD} placeholder="Site-ul meu" />
        </div>

        <div>
          <label className={LABEL}>Domeniu *</label>
          <input value={form.domain} onChange={set("domain")} required className={FIELD} placeholder="example.com" />
        </div>

        <div>
          <label className={LABEL}>Descriere</label>
          <textarea value={form.description} onChange={set("description")} rows={2} className={`${FIELD} resize-none`} placeholder="Opțional..." />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={LABEL}>Budget lunar (USD)</label>
            <input type="number" min={0} step="0.01" value={form.monthly_budget_usd} onChange={set("monthly_budget_usd")} className={FIELD} />
          </div>
          <div>
            <label className={LABEL}>Tip CMS *</label>
            <select value={form.cms_type} onChange={set("cms_type")} className={FIELD}>
              {CMS_TYPES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
        </div>

        {form.cms_type === "wordpress" && (
          <div className="rounded-lg border border-border p-3 space-y-3">
            <p className="text-xs font-medium text-white">Configurare WordPress</p>
            <div>
              <label className={LABEL}>URL WordPress</label>
              <input value={form.wp_url} onChange={set("wp_url")} className={FIELD} placeholder="https://example.com" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={LABEL}>Username</label>
                <input value={form.wp_username} onChange={set("wp_username")} className={FIELD} placeholder="admin" />
              </div>
              <div>
                <label className={LABEL}>Application Password</label>
                <input type="password" value={form.wp_app_password} onChange={set("wp_app_password")} className={FIELD} placeholder="xxxx xxxx xxxx" />
              </div>
            </div>
          </div>
        )}

        {form.cms_type === "php_custom" && (
          <div className="rounded-lg border border-border p-3 space-y-3">
            <p className="text-xs font-medium text-white">Configurare PHP Custom</p>
            <div>
              <label className={LABEL}>Endpoint URL</label>
              <input value={form.php_endpoint} onChange={set("php_endpoint")} className={FIELD} placeholder="https://example.com/api/publish" />
            </div>
            <div>
              <label className={LABEL}>Secret</label>
              <input type="password" value={form.php_secret} onChange={set("php_secret")} className={FIELD} placeholder="secret-key" />
            </div>
          </div>
        )}
      </form>
    </Modal>
  );
}
