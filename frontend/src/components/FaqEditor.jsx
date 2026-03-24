import { Plus, Trash2 } from "lucide-react";

const FIELD = "w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-white outline-none transition focus:border-accent";

export default function FaqEditor({ items = [], onChange }) {
  const update = (index, key, value) => {
    const next = items.map((item, i) =>
      i === index ? { ...item, [key]: value } : item
    );
    onChange(next);
  };

  const add = () => {
    onChange([...items, { question: "", answer: "" }]);
  };

  const remove = (index) => {
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="rounded-lg border border-border bg-bg p-3 space-y-2">
          <div className="flex items-start gap-2">
            <div className="flex-1 space-y-2">
              <input
                value={item.question || ""}
                onChange={(e) => update(i, "question", e.target.value)}
                placeholder="Întrebare"
                className={FIELD}
              />
              <textarea
                value={item.answer || ""}
                onChange={(e) => update(i, "answer", e.target.value)}
                placeholder="Răspuns"
                rows={2}
                className={`${FIELD} resize-none`}
              />
            </div>
            <button
              onClick={() => remove(i)}
              className="mt-1 rounded-md p-1.5 text-red-400 hover:bg-red-500/10 transition"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ))}
      <button
        onClick={add}
        className="flex items-center gap-1.5 text-sm text-muted hover:text-white transition"
      >
        <Plus className="h-4 w-4" />
        Adaugă întrebare
      </button>
    </div>
  );
}
