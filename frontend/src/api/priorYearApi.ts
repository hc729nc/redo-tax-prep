import type { UploadedDocument } from "./documentsApi";
import { API_BASE_URL as BASE_URL } from "./config";

export interface ComparisonLine {
  current: string;
  prior: string | null;
  change: string | null;
}

export interface ComparisonResult {
  has_prior_year: boolean;
  prior_tax_year?: number;
  prior_year_has_data?: boolean;
  comparisons?: Record<string, ComparisonLine>;
}

export const priorYearApi = {
  upload: async (currentReturnId: string, file: File): Promise<UploadedDocument> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/api/prior-year/upload?current_return_id=${currentReturnId}`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  compare: async (currentReturnId: string): Promise<ComparisonResult> => {
    const res = await fetch(`${BASE_URL}/api/prior-year/compare?current_return_id=${currentReturnId}`, {
      credentials: "include",
    });
    if (!res.ok) throw new Error(`Compare failed: ${res.status}`);
    return res.json();
  },
};
