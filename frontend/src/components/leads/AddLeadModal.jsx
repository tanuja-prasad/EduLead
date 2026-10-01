import { useState } from "react";
import { X } from "lucide-react";

import { createLead } from "../../api/crmApi";

const INITIAL_FORM = {
  student_name: "",
  phone: "",
  email: "",
  source: "WALKIN",
  country: "",
  course: "",
  academic_score: 60,
  budget: "",
  expected_fee: "",
  status: "NEW",
};

export default function AddLeadModal({ open, onClose, onCreated }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  function change(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      await createLead({
        ...form,
        academic_score: Number(form.academic_score || 0),
        budget: Number(form.budget || 0),
        expected_fee: Number(form.expected_fee || 0),
      });
      setForm(INITIAL_FORM);
      await onCreated?.();
      onClose();
    } catch (err) {
      const data = err.response?.data;
      setError(data?.detail || (data ? JSON.stringify(data) : "Unable to create lead."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="lead-modal" onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <div>
            <span className="eyebrow">NEW ENQUIRY</span>
            <h2>Create Lead</h2>
            <p>Add a walk-in, phone enquiry, referral or digital lead.</p>
          </div>
          <button className="icon-button" type="button" onClick={onClose}><X size={18} /></button>
        </div>

        <form onSubmit={submit} className="lead-form-grid">
          <label>Student Name<input name="student_name" value={form.student_name} onChange={change} required /></label>
          <label>Phone<input name="phone" value={form.phone} onChange={change} required /></label>
          <label>Email<input type="email" name="email" value={form.email} onChange={change} /></label>
          <label>Lead Source
            <select name="source" value={form.source} onChange={change}>
              <option value="WALKIN">Walk-in</option><option value="INSTAGRAM">Instagram</option>
              <option value="FACEBOOK">Facebook</option><option value="GOOGLE">Google Ads</option>
              <option value="WEBSITE">Website</option><option value="REFERRAL">Referral</option>
              <option value="DIRECT">Direct Call</option><option value="OTHER">Other</option>
            </select>
          </label>
          <label>Preferred Country<input name="country" value={form.country} onChange={change} placeholder="UK, USA, Germany..." /></label>
          <label>Course<input name="course" value={form.course} onChange={change} placeholder="MSc Data Science" /></label>
          <label>Academic Score (%)<input type="number" min="0" max="100" name="academic_score" value={form.academic_score} onChange={change} /></label>
          <label>Student Budget (₹)<input type="number" min="0" name="budget" value={form.budget} onChange={change} /></label>
          <label>Expected Consultancy Fee (₹)<input type="number" min="0" name="expected_fee" value={form.expected_fee} onChange={change} /></label>
          <label>Status
            <select name="status" value={form.status} onChange={change}>
              <option value="NEW">New</option><option value="CONTACTED">Contacted</option>
              <option value="INTERESTED">Interested</option><option value="COUNSELLING">Counselling</option>
              <option value="APPLICATION">Application</option>
            </select>
          </label>
          {error && <div className="form-error span-2">{error}</div>}
          <div className="modal-actions span-2">
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn primary" disabled={saving}>{saving ? "Creating..." : "Create Lead"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
