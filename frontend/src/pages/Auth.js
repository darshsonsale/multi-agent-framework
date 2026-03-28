import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Auth.css";

function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const submit = async () => {
    setError("");
    if (!form.email || !form.password) {
      setError("Please fill in all required fields.");
      return;
    }
    if (mode === "register" && !form.name) {
      setError("Please enter your name.");
      return;
    }
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/login" : "/register";
      const payload = mode === "login" 
        ? { email: form.email, password: form.password }
        : { name: form.name, email: form.email, password: form.password };

      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed");
      }

      if (mode === "register") {
        alert("Registration successful! Please check your email for confirmation.");
        setMode("login");
      } else {
        localStorage.setItem("user", JSON.stringify(data.user));
        navigate("/chat");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-left">
        <div className="auth-brand" onClick={() => navigate("/")}>⚖ eFIR</div>
        <div className="auth-left-text">
          <h2>File your FIR<br /><em>in minutes.</em></h2>
          <p>AI-guided. Secure. No office visit required.</p>
        </div>
        <div className="auth-left-tags">
          <span>⚡ Instant</span>
          <span>🔒 Encrypted</span>
          <span>🤖 AI-guided</span>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-toggle">
            <button
              className={mode === "login" ? "active" : ""}
              onClick={() => { setMode("login"); setError(""); }}
            >
              Login
            </button>
            <button
              className={mode === "register" ? "active" : ""}
              onClick={() => { setMode("register"); setError(""); }}
            >
              Register
            </button>
          </div>

          <h3 className="auth-title">
            {mode === "login" ? "Welcome back." : "Create account."}
          </h3>
          <p className="auth-sub">
            {mode === "login"
              ? "Sign in to continue filing."
              : "Get started — it's free."}
          </p>

          <div className="auth-fields">
            {mode === "register" && (
              <div className="field-group">
                <label>Full Name</label>
                <input
                  name="name"
                  value={form.name}
                  onChange={handle}
                  placeholder="Rahul Sharma"
                />
              </div>
            )}
            <div className="field-group">
              <label>Email Address</label>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handle}
                placeholder="you@example.com"
              />
            </div>
            <div className="field-group">
              <label>Password</label>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handle}
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button
            className="auth-submit"
            onClick={submit}
            disabled={loading}
          >
            {loading
              ? "Please wait…"
              : mode === "login"
              ? "Continue →"
              : "Create account →"}
          </button>

          <button className="auth-back" onClick={() => navigate("/")}>
            ← Back to home
          </button>
        </div>
      </div>
    </div>
  );
}

export default Auth;