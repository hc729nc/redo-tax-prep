import { apiClient } from "./client";

export interface User {
  id: string;
  display_name: string;
  email: string | null;
}

export const authApi = {
  me: () => apiClient.request<User>("/api/auth/me"),
  signup: (email: string, password: string, display_name: string) =>
    apiClient.request<User>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),
  login: (email: string, password: string) =>
    apiClient.request<User>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => apiClient.request<{ status: string }>("/api/auth/logout", { method: "POST" }),
};
