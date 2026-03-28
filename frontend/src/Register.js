import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Register.css";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = "NAME_REQUIRED";
    if (!form.email.trim()) e.email = "EMAIL_REQUIRED";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "EMAIL_INVALID";
    if (!form.password) e.password = "PASSWORD_REQUIRED";
    else if (form.password.length < 6) e.password = "MIN_6_CHARS";
    if (form.password !== form.confirm) e.confirm = "PASSWORDS_MISMATCH";
    return e;
  };

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors(prev => ({ ...prev, [e.target.name]: null }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setLoading(true);
    // Simulate registration — replace with real API call
    await new Promise(r => setTimeout(r, 1200));
    setLoading(false);
    setSubmitted(true);
    setTimeout(() => navigate("/chat"), 1500);
  };

  return (
    <div className="reg-root">
      {/* pixel grid background */}
      <div className="reg-grid" aria-hidden="true" />

      <div className="reg-card">
        {/* corner decorations */}
        <span className="corner tl" />
        <span className="corner tr" />
        <span className="corner bl" />
        <span className="corner br" />

        <div className="reg-logo">
          <span className="logo-box">⚖</span>
        </div>

        <h1 className="reg-title">eFIR_SYSTEM</h1>
        <p className="reg-sub">CREATE_ACCOUNT // v2.0</p>

        {submitted ? (
          <div className="reg-success">
            <span className="success-icon">✓</span>
            <p>REGISTRATION_COMPLETE</p>
            <p className="success-sub">REDIRECTING…</p>
          </div>
        ) : (
          <form className="reg-form" onSubmit={handleSubmit} noValidate>

            <div className="field-group">
              <label className="field-label">FULL_NAME</label>
              <div className={`pixel-input-wrap ${errors.name ? "error" : ""}`}>
                <span className="input-prefix">›</span>
                <input
                  name="name"
                  type="text"
                  className="pixel-input"
                  placeholder="ENTER_NAME"
                  value={form.name}
                  onChange={handleChange}
                  autoComplete="name"
                />
              </div>
              {errors.name && <span className="field-error">// {errors.name}</span>}
            </div>

            <div className="field-group">
              <label className="field-label">EMAIL_ADDRESS</label>
              <div className={`pixel-input-wrap ${errors.email ? "error" : ""}`}>
                <span className="input-prefix">›</span>
                <input
                  name="email"
                  type="email"
                  className="pixel-input"
                  placeholder="USER@DOMAIN.COM"
                  value={form.email}
                  onChange={handleChange}
                  autoComplete="email"
                />
              </div>
              {errors.email && <span className="field-error">// {errors.email}</span>}
            </div>

            <div className="field-group">
              <label className="field-label">PASSWORD</label>
              <div className={`pixel-input-wrap ${errors.password ? "error" : ""}`}>
                <span className="input-prefix">›</span>
                <input
                  name="password"
                  type="password"
                  className="pixel-input"
                  placeholder="MIN_6_CHARS"
                  value={form.password}
                  onChange={handleChange}
                  autoComplete="new-password"
                />
              </div>
              {errors.password && <span className="field-error">// {errors.password}</span>}
            </div>

            <div className="field-group">
              <label className="field-label">CONFIRM_PASSWORD</label>
              <div className={`pixel-input-wrap ${errors.confirm ? "error" : ""}`}>
                <span className="input-prefix">›</span>
                <input
                  name="confirm"
                  type="password"
                  className="pixel-input"
                  placeholder="REPEAT_PASSWORD"
                  value={form.confirm}
                  onChange={handleChange}
                  autoComplete="new-password"
                />
              </div>
              {errors.confirm && <span className="field-error">// {errors.confirm}</span>}
            </div>

            <button type="submit" className="reg-btn" disabled={loading}>
              {loading ? (
                <span className="btn-loading"><span /><span /><span /></span>
              ) : (
                "[ REGISTER ]"
              )}
            </button>

            <p className="reg-login">
              HAVE_ACCOUNT?{" "}
              <span className="reg-link" onClick={() => navigate("/login")}>
                LOGIN →
              </span>
            </p>

          </form>
        )}
      </div>

      <p className="reg-footer">EFIR_SYSTEM © 2025 // ALL_RIGHTS_RESERVED</p>
    </div>
  );
}