import { useRef, useState } from "react";
import { documentsApi, type ExtractedField } from "../../api/documentsApi";
import { priorYearApi, type ComparisonResult } from "../../api/priorYearApi";
import { FieldConfirmationPanel } from "../documents/FieldConfirmationPanel";

const LABELS: Record<string, string> = {
  wages: "Wages",
  agi: "AGI",
  total_tax: "Total tax",
};

function formatDelta(value: string) {
  const n = Number(value);
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })}`;
}

export function PriorYearPanel({ taxReturnId }: { taxReturnId: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [priorReturnId, setPriorReturnId] = useState<string | null>(null);
  const [priorFields, setPriorFields] = useState<ExtractedField[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");

  async function refreshPriorFields(returnId: string) {
    const fields = await documentsApi.listFields(returnId);
    setPriorFields(fields);
  }

  async function handleUpload(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setStatus("uploading");
    try {
      const doc = await priorYearApi.upload(taxReturnId, file);
      setPriorReturnId(doc.tax_return_id);
      await refreshPriorFields(doc.tax_return_id);
      setStatus("idle");
    } catch {
      setStatus("error");
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function handleCompare() {
    const result = await priorYearApi.compare(taxReturnId);
    setComparison(result);
  }

  return (
    <div style={{ borderTop: "1px solid #e5e5e5", padding: "1rem", fontSize: "0.88rem" }}>
      <h3 style={{ marginTop: 0, fontSize: "1rem" }}>Last year's return</h3>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={(e) => handleUpload(e.target.files)}
        style={{ display: "none" }}
        id="prior-year-upload-input"
      />
      <label
        htmlFor="prior-year-upload-input"
        style={{
          display: "inline-block",
          padding: "0.35rem 0.7rem",
          borderRadius: "6px",
          border: "1px solid #ccc",
          fontSize: "0.82rem",
          cursor: "pointer",
          background: "#fafafa",
        }}
      >
        Upload prior-year 1040
      </label>
      {status === "uploading" && <p style={{ color: "#666" }}>Uploading and extracting...</p>}
      {status === "error" && <p style={{ color: "#b00020" }}>Upload failed - try again.</p>}

      {priorReturnId && (
        <div style={{ marginTop: "0.5rem" }}>
          <FieldConfirmationPanel fields={priorFields} onChanged={() => refreshPriorFields(priorReturnId)} />
        </div>
      )}

      <button onClick={handleCompare} style={{ marginTop: "0.75rem" }}>
        Compare to last year
      </button>

      {comparison && !comparison.has_prior_year && (
        <p style={{ color: "#666", marginTop: "0.5rem" }}>No prior-year return uploaded yet.</p>
      )}
      {comparison?.has_prior_year && !comparison.prior_year_has_data && (
        <p style={{ color: "#666", marginTop: "0.5rem" }}>
          Prior-year return uploaded, but no fields confirmed yet - confirm the values above first.
        </p>
      )}
      {comparison?.comparisons && (
        <div style={{ marginTop: "0.5rem", lineHeight: 1.7 }}>
          {Object.entries(comparison.comparisons).map(([key, line]) => (
            <div key={key}>
              <strong>{LABELS[key] ?? key}:</strong> {line.change ? formatDelta(line.change) : "n/a"} vs{" "}
              {comparison.prior_tax_year}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
