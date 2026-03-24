import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Loader2, ChevronLeft } from "lucide-react";
import { getTemplate } from "../api/templates";
import TemplateEditor from "../components/TemplateEditor";

export default function TemplateEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === "new";

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(!isNew);

  useEffect(() => {
    if (isNew) return;
    async function load() {
      try {
        const res = await getTemplate(id);
        setData(res.data?.data);
      } catch {
        navigate("/templates");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-10">
      <Link
        to="/templates"
        className="flex items-center gap-1 text-sm text-muted hover:text-white transition"
      >
        <ChevronLeft className="h-4 w-4" />
        Înapoi la template-uri
      </Link>
      <TemplateEditor initialData={isNew ? null : data} />
    </div>
  );
}
