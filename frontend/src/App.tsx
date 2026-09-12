import { useEffect, useState } from "react";
import { authApi, type User } from "./api/authApi";
import { ApiError } from "./api/client";
import { returnsApi } from "./api/returnsApi";
import { useReturnStore } from "./state/returnStore";
import { ChatPage } from "./pages/ChatPage";
import { AuthPage } from "./pages/AuthPage";
import "./App.css";

const CURRENT_TAX_YEAR = 2025;

type AuthState = "checking" | "anonymous" | "authenticated";

export default function App() {
  const { activeReturn, setActiveReturn } = useReturnStore();
  const [user, setUser] = useState<User | null>(null);
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authApi
      .me()
      .then((me) => {
        setUser(me);
        setAuthState("authenticated");
      })
      .catch(() => setAuthState("anonymous"));
  }, []);

  useEffect(() => {
    if (authState !== "authenticated") return;

    async function bootstrapReturn() {
      try {
        const existing = await returnsApi.list();
        const currentYearReturn = existing.find(
          (r) => r.tax_year === CURRENT_TAX_YEAR && !r.is_prior_year
        );
        if (currentYearReturn) {
          setActiveReturn(currentYearReturn);
        } else {
          const created = await returnsApi.create(CURRENT_TAX_YEAR, "single");
          setActiveReturn(created);
        }
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "Failed to connect to backend");
      }
    }
    bootstrapReturn();
  }, [authState, setActiveReturn]);

  function handleAuthenticated(authedUser: User) {
    setUser(authedUser);
    setAuthState("authenticated");
  }

  async function handleLogout() {
    await authApi.logout();
    setUser(null);
    setActiveReturn(null);
    setAuthState("anonymous");
  }

  if (authState === "checking") {
    return (
      <div className="status-screen">
        <h1>Synthia</h1>
        <p>Loading...</p>
      </div>
    );
  }

  if (authState === "anonymous") {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  if (error) {
    return (
      <div className="status-screen">
        <h1>Synthia</h1>
        <p className="error">Could not reach the backend: {error}</p>
      </div>
    );
  }

  if (!user || !activeReturn) {
    return (
      <div className="status-screen">
        <h1>Synthia</h1>
        <p>Loading...</p>
      </div>
    );
  }

  return <ChatPage taxReturnId={activeReturn.id} user={user} onLogout={handleLogout} />;
}
