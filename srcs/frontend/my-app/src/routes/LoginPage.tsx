import { useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface LocationState {
  from?: Location;
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | undefined;

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username || !password) {
      setError("Username and password are required");
      return;
    }

    try {
      setSubmitting(true);
      await login(username, password);
      const redirectTo =
        state?.from?.pathname && state.from.pathname !== "/login"
          ? state.from.pathname
          : "/";
      navigate(redirectTo, { replace: true });
    } catch (err: any) {
      setError(err?.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex justify-center items-center">
      <div className="w-full max-w-md bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm p-6">
        <h1 className="text-xl font-semibold mb-1">Login</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Sign in to upload documents or access analyst tools.
        </p>

        {error && (
          <div className="mb-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
              Username
            </label>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="px-3 py-2 rounded border text-sm bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
              Password
            </label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="px-3 py-2 rounded border text-sm bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 inline-flex justify-center items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-primary hover:bg-primary-dark disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {submitting ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="text-xs text-gray-600 dark:text-gray-400 mt-4">
          No account yet?{" "}
          <Link to="/register" className="text-primary hover:text-primary-dark">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
