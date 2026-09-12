import { apiClient } from "./client";

const BASE_URL = "http://localhost:8000";

export type FilingStatus =
  | "single"
  | "married_filing_jointly"
  | "married_filing_separately"
  | "head_of_household";

export type ReturnStatus = "draft" | "computed" | "finalized";

export interface TaxReturn {
  id: string;
  user_id: string;
  tax_year: number;
  is_prior_year: boolean;
  filing_status: FilingStatus;
  status: ReturnStatus;
  created_at: string;
  updated_at: string;
}

export interface ComputedSummary {
  agi: string;
  deduction_amount: string;
  taxable_income: string;
  total_tax: string;
  refund_amount: string;
  amount_owed: string;
}

export const returnsApi = {
  list: () => apiClient.request<TaxReturn[]>("/api/returns"),
  create: (tax_year: number, filing_status: FilingStatus) =>
    apiClient.request<TaxReturn>("/api/returns", {
      method: "POST",
      body: JSON.stringify({ tax_year, filing_status }),
    }),
  get: (id: string) => apiClient.request<TaxReturn>(`/api/returns/${id}`),
  compute: (id: string) =>
    apiClient.request<ComputedSummary>(`/api/returns/${id}/compute`, { method: "POST" }),
  pdfUrl: (id: string) => `${BASE_URL}/api/returns/${id}/pdf`,
};
