import { useNavigate } from "react-router-dom";
import "./Home.css";

function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-wrapper">

      {/* NAVBAR */}
      <nav className="home-navbar">
        <div className="logo">⚖ eFIR</div>
        <div className="nav-links">
          <a href="#features">How it works</a>
          <a href="#features">Features</a>
          <a href="#cta">Contact</a>
        </div>
        <button className="nav-btn" onClick={() => navigate("/auth")}>
          Login <span>↗</span>
        </button>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-tag">✦ AI-Powered Legal Filing</div>

          <h1 className="hero-heading">
            File your FIR<br />
            <em>without the chaos.</em>
          </h1>

          <p className="hero-sub">
            eFIR guides you through the entire First Information Report process —
            intelligently, step by step. No forms. No confusion. Just answers.
          </p>

          <div className="hero-actions">
            <button className="btn-primary" onClick={() => navigate("/auth")}>
              Get started <span className="arrow-circle">↗</span>
            </button>
            <button className="btn-ghost" onClick={() => navigate("/auth")}>
              See how it works ▶
            </button>
          </div>

          <div className="hero-stat-bar">
            <div className="stat">
              <strong>10,000+</strong>
              <span>FIRs Filed</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <strong>3 min</strong>
              <span>Average filing time</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <strong>100%</strong>
              <span>Guided process</span>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="chat-mockup">
            <div className="mockup-bar">
              <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
              <span className="mockup-title">eFIR Assistant</span>
            </div>
            <div className="mockup-body">
              <div className="mock-msg bot">When did the incident occur?</div>
              <div className="mock-msg user">Yesterday around 9pm near MG Road</div>
              <div className="mock-msg bot">Got it. Was any property stolen or damaged?</div>
              <div className="mock-msg user">Yes, my motorcycle was taken</div>
              <div className="mock-msg bot typing">
                <span /><span /><span />
              </div>
            </div>
            <div className="mockup-badge">● Live Preview updating…</div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="features" id="features">
        <div className="section-label">✦ Why eFIR</div>
        <h2 className="section-heading">
          Everything you need,<br />nothing you don't.
        </h2>

        <div className="feature-grid">
          <div className="feature-card large">
            <div className="feature-icon">⚡</div>
            <h3>Instant Filing</h3>
            <p>Submit a complete, structured FIR in under 5 minutes using guided conversation — no legal knowledge required.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI Assistant</h3>
            <p>Asks the right questions, fills the right fields. Automatically.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔒</div>
            <h3>Secure & Private</h3>
            <p>End-to-end encrypted. Your data stays yours.</p>
          </div>

          <div className="feature-card wide">
            <div className="feature-icon">📄</div>
            <h3>Live Document Preview</h3>
            <p>Watch your FIR get structured in real-time on screen as you describe the incident.</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta" id="cta">
        <div className="cta-inner">
          <div className="section-label light">✦ Ready?</div>
          <h2>File your FIR<br /><em>right now.</em></h2>
          <p>It takes three minutes. No office visit. No paperwork.</p>
          <button onClick={() => navigate("/auth")}>
            Start filing <span className="arrow-circle dark">↗</span>
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="home-footer">
        <span>⚖ eFIR — Electronic First Information Report System</span>
        <span>Built for citizens. Powered by AI.</span>
      </footer>

    </div>
  );
}

export default Home;