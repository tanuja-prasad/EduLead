import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, BarChart3, Building2, Sparkles, Users } from "lucide-react";

import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../utils/constants";

function homeFor(role) {
  if (role === ROLES.ADMIN) return "/admin";
  if (role === ROLES.MANAGER) return "/manager";
  return "/counsellor";
}

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to={homeFor(user.role)} replace />;
  }

  function change(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const loggedUser = await login(form);
      navigate(homeFor(loggedUser.role), { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to sign in. Please check your email and password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-visual">
        <div className="motion-orb orb-one" />
        <div className="motion-orb orb-two" />
        <div className="motion-grid" />

        <Link className="auth-brand" to="/">
          <span className="auth-brand-mark"><Building2 size={23} /></span>
          <span><b>EduLead</b><small>CRM & ANALYTICS</small></span>
        </Link>

        <div className="auth-visual-copy">
          <span className="visual-pill"><Sparkles size={14} /> Smarter admission management</span>
          <h1>Turn every enquiry into a measurable opportunity.</h1>
          <p>One workspace for branches, employees, leads, admissions, revenue and ML-powered projections.</p>

          <div className="floating-dashboard">
            <div className="mini-chart-card">
              <span>Expected Revenue</span>
              <strong>₹42.8L</strong>
              <div className="mini-bars"><i /><i /><i /><i /><i /><i /></div>
            </div>
            <div className="float-card float-team"><Users size={18} /><span>Team conversion</span><b>18.4%</b></div>
            <div className="float-card float-office"><BarChart3 size={18} /><span>Active offices</span><b>04</b></div>
          </div>
        </div>
      </section>

      <section className="auth-form-side">
        <div className="auth-form-wrap">
          <span className="eyebrow">WELCOME BACK</span>
          <h2>Sign in to your workspace</h2>
          <p className="auth-intro">Use your registered employee email. Your office, role and dashboard are identified automatically.</p>

          <form onSubmit={submit}>
            <label className="auth-field">
              Email Address
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={change}
                placeholder="name@company.com"
                autoComplete="email"
                required
              />
            </label>

            <label className="auth-field">
              Password
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={change}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </label>

            {error && <div className="error auth-message">{error}</div>}

            <button className="primary auth-submit" disabled={submitting}>
              {submitting ? "Signing in..." : "Sign In"}
              <ArrowRight size={17} />
            </button>
          </form>

          <p className="auth-switch">New employee? <Link to="/signup">Create an account</Link></p>
          <p className="auth-note">Your access is automatically limited according to the role and office saved with your account.</p>
        </div>
      </section>
    </main>
  );
}
