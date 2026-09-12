// In production, the frontend is served by the same FastAPI process as the API
// (see backend/app/main.py), so requests can just be relative - no base URL needed.
// In local dev, the frontend runs on Vite's dev server (port 5173) while the API
// runs separately on 8000, so it needs an explicit absolute URL.
// Override either way by setting VITE_API_BASE_URL (see frontend/.env.example).
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "http://localhost:8000" : "");
