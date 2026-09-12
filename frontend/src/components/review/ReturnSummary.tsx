import { useState } from "react";
import { returnsApi, type ComputedSummary } from "../../api/returnsApi";

function formatDollars(value: string) {
  const n = Number(value);
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export function ReturnSummary({ taxReturnId }: { taxReturnId: string }) {
  const [summary, setSummary] = useState<ComputedSummary | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleCompute() {
    setLoading(true);
    try {
      const result = await returnsApi.compute(taxReturnId);
      setSummary(result);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: "1rem", fontSize: "0.88rem" }}>
      <h3 style={{ marginTop: 0, fontSize: "1rem" }}>Return summary</h3>
      <button onClick={handleCompute} disabled={loading} style={{ marginBottom: "0.75rem" }}>
        {loading ? "Computing..." : "Compute return"}
      </button>

      {summary && (
        <div style={{ lineHeight: 1.7 }}>
          <div>AGI: {formatDollars(summary.agi)}</div>
          <div>Deduction: {formatDollars(summary.deduction_amount)}</div>
          <div>Taxable income: {formatDollars(summary.taxable_income)}</div>
          <div>Total tax: {formatDollars(summary.total_tax)}</div>
          {Number(summary.refund_amount) > 0 && (
            <div style={{ color: "#0a7d34", fontWeight: 600 }}>
              Refund: {formatDollars(summary.refund_amount)}
            </div>
          )}
          {Number(summary.amount_owed) > 0 && (
            <div style={{ color: "#b00020", fontWeight: 600 }}>
              Amount owed: {formatDollars(summary.amount_owed)}
            </div>
          )}
          <a
            href={returnsApi.pdfUrl(taxReturnId)}
            target="_blank"
            rel="noreferrer"
            style={{ display: "inline-block", marginTop: "0.75rem" }}
          >
            View filled 1040 PDF
          </a>
        </div>
      )}
    </div>
  );
}
