import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Building2, CheckCircle2, Sparkles, UserPlus } from "lucide-react";

import { getPublicOffices, signupUser } from "../../api/authApi";
import { ROLES } from "../../utils/constants";

export default function Signup() {
  const navigate = useNavigate();
  const [offices, setOffices] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
    role: ROLES.COUNSELLOR,
    office: "",
    admin_signup_code: "",
  });

  useEffect(() => {
    async function loadOffices() {
      try {
        const data = await getPublicOffices();
        setOffices(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Unable to load offices", err);
        setOffices([]);
        setError("Office branches could not be loaded. Please make sure the backend is running.");
      }
    }

    loadOffices();
  }, []);

  function change(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (form.password !== form.confirm_password) {
      setError("Password and confirm password do not match.");
      return;
    }

    setSubmitting(true);

    try {
      const { confirm_password, ...signupData } = form;
      const payload = {
        ...signupData,
        office: form.role === ROLES.ADMIN ? null : form.office,
      };

      await signupUser(payload);
      setMessage("Account created successfully. Redirecting to sign in...");
      window.setTimeout(() => navigate("/login"), 900);
    } catch (err) {
      const data = err.response?.data;
      setError(data?.detail || data?.email?.[0] || JSON.stringify(data) || "Signup failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-visual signup-visual">
        <div className="motion-orb orb-one" />
        <div className="motion-orb orb-two" />
        <div className="motion-grid" />

        <Link className="auth-brand" to="/">
          <span className="auth-brand-mark"><Building2 size={23} /></span>
          <span><b>EduLead</b><small>CRM & ANALYTICS</small></span>
        </Link>

        <div className="auth-visual-copy signup-copy">
          <span className="visual-pill"><Sparkles size={14} /> One account, role-based access</span>
          <h1>Build your team around real office branches.</h1>
          <p>Managers and counsellors are linked to their branch during registration. Leadership accounts work across the organization.</p>
          <div className="signup-points">
            <span><CheckCircle2 size={17} /> Email-based secure sign in</span>
            <span><CheckCircle2 size={17} /> Automatic office identification</span>
            <span><CheckCircle2 size={17} /> Automatic role-based dashboard</span>
          </div>
        </div>
      </section>

      <section className="auth-form-side signup-form-side">
        <div className="auth-form-wrap signup-form-wrap">
          <span className="eyebrow">EMPLOYEE REGISTRATION</span>
          <h2>Create your EduLead account</h2>
          <p className="auth-intro">Register once. Your email will identify your role and office whenever you sign in.</p>

          <form className="modern-signup-grid" onSubmit={submit}>
            <label className="auth-field">First Name<input name="first_name" value={form.first_name} onChange={change} required /></label>
            <label className="auth-field">Last Name<input name="last_name" value={form.last_name} onChange={change} /></label>
            <label className="auth-field span-2">Email Address<input type="email" name="email" value={form.email} onChange={change} placeholder="name@company.com" autoComplete="email" required /></label>
            <label className="auth-field">Phone Number<input name="phone" value={form.phone} onChange={change} /></label>
            <label className="auth-field">Role
              <select name="role" value={form.role} onChange={change}>
                <option value={ROLES.ADMIN}>Admin / CEO / CMO</option>
                <option value={ROLES.MANAGER}>Manager</option>
                <option value={ROLES.COUNSELLOR}>Counsellor</option>
              </select>
            </label>

            {form.role !== ROLES.ADMIN ? (
              <label className="auth-field span-2">Office Branch
                <select name="office" value={form.office} onChange={change} required>
                  <option value="">{offices.length ? "Select your office branch" : "No office branches available"}</option>
                  {offices.map((office) => (
                    <option key={office.id} value={office.id}>{office.name} - {office.city}</option>
                  ))}
                </select>
              </label>
            ) : (
              <label className="auth-field span-2">Admin Signup Code
                <input type="password" name="admin_signup_code" value={form.admin_signup_code} onChange={change} required />
              </label>
            )}

            <label className="auth-field">Password<input type="password" name="password" value={form.password} onChange={change} minLength="8" autoComplete="new-password" required /></label>
            <label className="auth-field">Confirm Password<input type="password" name="confirm_password" value={form.confirm_password} onChange={change} minLength="8" autoComplete="new-password" required /></label>

            <div className="signup-submit-area span-2">
              {error && <div className="error auth-message">{error}</div>}
              {message && <div className="success auth-message">{message}</div>}
              <button className="primary auth-submit" disabled={submitting}>
                <UserPlus size={17} /> {submitting ? "Creating account..." : "Create Account"}
              </button>
              <p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p>
            </div>
          </form>
        </div>
      </section>
    </main>
  );
}
