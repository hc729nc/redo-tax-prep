import { useState } from "react";
import { documentsApi, type ExtractedField } from "../../api/documentsApi";

export function FieldConfirmationPanel({
  fields,
  onChanged,
}: {
  fields: ExtractedField[];
  onChanged: () => void;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const pending = fields.filter((f) => !f.confirmed_by_user);
  if (pending.length === 0) return null;

  async function confirm(id: string) {
    await documentsApi.confirmField(id);
    onChanged();
  }

  async function saveCorrection(id: string) {
    await documentsApi.correctField(id, editValue);
    setEditingId(null);
    onChanged();
  }

  return (
    <div style={{ padding: "0.75rem", borderTop: "1px solid #e5e5e5", background: "#fffbea" }}>
      <p style={{ margin: "0 0 0.5rem", fontSize: "0.85rem", fontWeight: 600 }}>
        Found {pending.length} value{pending.length > 1 ? "s" : ""} to confirm
      </p>
      {pending.map((f) => (
        <div
          key={f.id}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.4rem 0",
            fontSize: "0.85rem",
          }}
        >
          <span style={{ flex: 1 }}>
            <strong>{f.field_name}</strong>
            {editingId === f.id ? (
              <input
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                style={{ marginLeft: "0.5rem", width: "100px" }}
              />
            ) : (
              <> = ${f.value}</>
            )}
            {f.source_page != null && (
              <span style={{ color: "#888", marginLeft: "0.4rem" }}>(page {f.source_page})</span>
            )}
          </span>
          {editingId === f.id ? (
            <button onClick={() => saveCorrection(f.id)}>Save</button>
          ) : (
            <>
              <button onClick={() => confirm(f.id)}>Confirm</button>
              <button
                onClick={() => {
                  setEditingId(f.id);
                  setEditValue(f.value);
                }}
              >
                Edit
              </button>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
