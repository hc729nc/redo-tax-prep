import { apiClient } from "./client";

const BASE_URL = "http://localhost:8000";

export interface UploadedDocument {
  id: string;
  tax_return_id: string;
  original_filename: string;
  document_type: string;
  extraction_status: string;
}

export interface ExtractedField {
  id: string;
  field_name: string;
  value: string;
  confirmed_by_user: boolean;
  source_page: number | null;
  source_text_snippet: string | null;
}

export const documentsApi = {
  list: (taxReturnId: string) =>
    apiClient.request<UploadedDocument[]>(`/api/documents?tax_return_id=${taxReturnId}`),

  upload: async (taxReturnId: string, file: File): Promise<UploadedDocument> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/api/documents/upload?tax_return_id=${taxReturnId}`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  listFields: (taxReturnId: string) =>
    apiClient.request<ExtractedField[]>(`/api/documents/fields?tax_return_id=${taxReturnId}`),

  confirmField: (fieldId: string) =>
    apiClient.request<ExtractedField>(`/api/documents/fields/${fieldId}/confirm`, {
      method: "PATCH",
    }),

  correctField: (fieldId: string, newValue: string) =>
    apiClient.request<ExtractedField>(`/api/documents/fields/${fieldId}/correct`, {
      method: "PATCH",
      body: JSON.stringify({ new_value: newValue }),
    }),
};
