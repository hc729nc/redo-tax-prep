import { useEffect, useState } from "react";
import { authApi, type User } from "./api/authApi";
import { returnsApi } from "./api/returnsApi";
import { useReturnStore } from "./state/returnStore";
import { ChatPage } from "./pages/ChatPage";
import "./App.css";

const CURRENT_TAX_YEAR = 2025;

export default function App() {
  const { activeReturn, setActiveReturn } = useReturnStore();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        const me = await authApi.createSession();
        setUser(me);

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
        setError(e instanceof Error ? e.message : "Failed to connect to backend");
      }
    }
    bootstrap();
  }, [setActiveReturn]);

  if (error) {
    return (
      <div className="status-screen">
        <h1>Synthia</h1>
        <p className="error">Could not reach the backend: {error}</p>
        <p>Make sure `uvicorn app.main:app --reload` is running on port 8000.</p>
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

  return <ChatPage taxReturnId={activeReturn.id} />;
}
