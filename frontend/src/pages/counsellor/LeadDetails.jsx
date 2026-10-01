import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  addFollowup,
  addHistory,
  getHistory,
  getLead,
  predictLead,
  updateLeadStatus,
} from "../../api/crmApi";
import StatusBadge from "../../components/common/StatusBadge";
import LeadTimeline from "../../components/leads/LeadTimeline";
import { STATUS_LABELS } from "../../utils/constants";

export default function LeadDetails() {
  const { id } = useParams();
  const [lead, setLead] = useState(null);
  const [history, setHistory] = useState([]);
  const [remark, setRemark] = useState("");

  async function load() {
    setLead(await getLead(id));
    setHistory(await getHistory(id));
  }

  useEffect(() => {
    load();
  }, [id]);

  async function saveRemark() {
    if (!remark.trim()) return;
    await addHistory(id, { activity_type: "REMARK", remark });
    setRemark("");
    await load();
  }

  async function changeStatus(event) {
    await updateLeadStatus(id, event.target.value);
    await load();
  }

  async function scheduleFollowup() {
    const followupAt = window.prompt("Follow-up date/time, example: 2026-10-02T17:00:00");
    const note = window.prompt("Follow-up note");

    if (followupAt) {
      await addFollowup({
        lead: Number(id),
        counsellor: lead.assigned_counsellor,
        followup_at: followupAt,
        note: note || "",
      });
      await load();
    }
  }

  async function runPrediction() {
    await predictLead(id);
    await load();
  }

  if (!lead) return <div>Loading...</div>;

  const prediction = lead.latest_prediction;

  return (
    <>
      <div className="page-title">
        <div>
          <span className="eyebrow">MY LEAD #{lead.id}</span>
          <h1>{lead.student_name}</h1>
          <p>{lead.phone} · {lead.source}</p>
        </div>
        <StatusBadge status={lead.status} />
      </div>

      <div className="detail-actions card">
        <label>
          Update Status
          <select value={lead.status} onChange={changeStatus}>
            {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <button className="btn soft" onClick={scheduleFollowup}>+ Schedule Follow-up</button>
        <button className="btn primary" onClick={runPrediction}>Run ML Prediction</button>
      </div>

      <div className="grid-2 detail-grid">
        <section className="card">
          <h3>Student Information</h3>
          <div className="info-grid">
            <span>Course<b>{lead.course || "—"}</b></span>
            <span>Country<b>{lead.country || "—"}</b></span>
            <span>Budget<b>₹{Number(lead.budget).toLocaleString("en-IN")}</b></span>
            <span>Expected Fee<b>₹{Number(lead.expected_fee).toLocaleString("en-IN")}</b></span>
          </div>

          <div className="prediction-box">
            <span className="eyebrow">ML ADMISSION PREDICTION</span>
            {prediction ? (
              <>
                <h2>{prediction.admission_probability.toFixed(1)}%</h2>
                <b>{prediction.priority} PRIORITY</b>
                <p>Expected revenue: ₹{Number(prediction.expected_revenue).toLocaleString("en-IN")}</p>
              </>
            ) : <p>No prediction generated yet.</p>}
          </div>

          <div className="remark-box">
            <h3>Add Remark</h3>
            <textarea value={remark} onChange={(event) => setRemark(event.target.value)} placeholder="Write what happened during the call..." />
            <button className="btn primary" onClick={saveRemark}>Save Remark</button>
          </div>
        </section>

        <section className="card">
          <h3>Lead History</h3>
          <LeadTimeline items={history} />
        </section>
      </div>
    </>
  );
}
