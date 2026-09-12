import { apiClient } from "./client";

export interface User {
  id: string;
  display_name: string;
  email: string | null;
}

export const authApi = {
  createSession: () => apiClient.request<User>("/api/auth/session", { method: "POST" }),
  me: () => apiClient.request<User>("/api/auth/me"),
};
