import { useState } from "react";
import type { FormEvent } from "react";
import { authApi, type User } from "../api/authApi";
import { ApiError } from "../api/client";

export function AuthPage({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user =
        mode === "login"
          ? await authApi.login(email, password)
          : await authApi.signup(email, password, displayName);
      onAuthenticated(user);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: "360px", margin: "4rem auto", padding: "0 1.5rem", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: "0.25rem" }}>Synthia</h1>
      <p style={{ color: "#666", marginTop: 0, fontSize: "0.9rem" }}>
        {mode === "login" ? "Log in to your return." : "Create an account to get started."}
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {mode === "signup" && (
          <input
            placeholder="Your name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            style={{ padding: "0.5rem 0.7rem", borderRadius: "6px", border: "1px solid #ccc" }}
          />
        )}
        <input
          type="email"
          placeholder="Email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ padding: "0.5rem 0.7rem", borderRadius: "6px", border: "1px solid #ccc" }}
        />
        <input
          type="password"
          placeholder="Password"
          required
          minLength={mode === "signup" ? 8 : undefined}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ padding: "0.5rem 0.7rem", borderRadius: "6px", border: "1px solid #ccc" }}
        />

        {error && <p style={{ color: "#b00020", fontSize: "0.85rem", margin: 0 }}>{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          style={{
            padding: "0.6rem",
            borderRadius: "6px",
            border: "none",
            background: "#2563eb",
            color: "#fff",
            cursor: submitting ? "default" : "pointer",
          }}
        >
          {submitting ? "Please wait..." : mode === "login" ? "Log in" : "Sign up"}
        </button>
      </form>

      <p style={{ fontSize: "0.85rem", marginTop: "1rem" }}>
        {mode === "login" ? "Don't have an account? " : "Already have an account? "}
        <button
          onClick={() => {
            setMode(mode === "login" ? "signup" : "login");
            setError(null);
          }}
          style={{ background: "none", border: "none", color: "#2563eb", cursor: "pointer", padding: 0 }}
        >
          {mode === "login" ? "Sign up" : "Log in"}
        </button>
      </p>

      <p style={{ fontSize: "0.78rem", color: "#999", marginTop: "2rem" }}>
        This is a demo tax-prep assistant. Please don't enter real Social Security numbers or
        other sensitive identifiers.
      </p>
    </div>
  );
}
