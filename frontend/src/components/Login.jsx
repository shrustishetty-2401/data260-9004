import { useState } from "react";
import { login } from "../api";

export default function Login({ onLogin }) {
 const [email, setEmail] = useState("");
 const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await login(email, password);
      onLogin(user);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Login failed. Check your email and password.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="card">
      <h1>Vulnerability Reports</h1>
      <h2>Login</h2>

      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </main>
  );
}