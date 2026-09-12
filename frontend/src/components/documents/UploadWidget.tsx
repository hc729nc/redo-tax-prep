import { useRef, useState } from "react";
import { documentsApi, type UploadedDocument } from "../../api/documentsApi";
import { ApiError } from "../../api/client";

export function UploadWidget({
  taxReturnId,
  onUploaded,
}: {
  taxReturnId: string;
  onUploaded: (doc: UploadedDocument) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setStatus("uploading");
    try {
      const doc = await documentsApi.upload(taxReturnId, file);
      onUploaded(doc);
      setStatus("idle");
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Upload failed - try again.");
      setStatus("error");
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div style={{ padding: "0.6rem 0.75rem", borderTop: "1px solid #e5e5e5", display: "flex", alignItems: "center", gap: "0.6rem" }}>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={(e) => handleFiles(e.target.files)}
        style={{ display: "none" }}
        id="doc-upload-input"
      />
      <label
        htmlFor="doc-upload-input"
        style={{
          padding: "0.4rem 0.8rem",
          borderRadius: "6px",
          border: "1px solid #ccc",
          fontSize: "0.85rem",
          cursor: "pointer",
          background: "#fafafa",
        }}
      >
        Upload a document
      </label>
      {status === "uploading" && <span style={{ fontSize: "0.85rem", color: "#666" }}>Uploading and extracting...</span>}
      {status === "error" && (
        <span style={{ fontSize: "0.85rem", color: "#b00020" }}>{errorMessage}</span>
      )}
    </div>
  );
}
