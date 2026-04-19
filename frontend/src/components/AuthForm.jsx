import { useState } from "react";
import { login, register } from "../api";

export default function AuthForm({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let data;
      if (isLogin) {
        data = await login(username, password);
      } else {
        data = await register(username, password);
      }
      
      if (data.ok) {
        onAuthSuccess(data.token, data.username);
      } else {
        setError(data.reason || "Authentication failed");
      }
    } catch (err) {
      if (err.response && err.response.data && err.response.data.reason) {
        setError(err.response.data.reason);
      } else {
        setError("An error occurred during authentication");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-8 rounded-xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900 mb-4">
        {isLogin ? "Log in to checkout" : "Create an account to checkout"}
      </h2>
      
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Username</label>
          <input
            type="text"
            required
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-slate-700">Password</label>
          <input
            type="password"
            required
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? "Please wait..." : (isLogin ? "Log In" : "Register")}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-600">
        {isLogin ? "Don't have an account? " : "Already have an account? "}
        <button
          type="button"
          onClick={() => setIsLogin(!isLogin)}
          className="font-medium text-blue-600 hover:underline"
        >
          {isLogin ? "Sign up" : "Log in"}
        </button>
      </p>
    </div>
  );
}
