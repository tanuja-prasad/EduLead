import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getHistory, getLead, predictLead } from "../../api/crmApi";
import StatusBadge from "../../components/common/StatusBadge";
import LeadTimeline from "../../components/leads/LeadTimeline";

export default function LeadDetails() {
  const { id } = useParams();
  const [lead, setLead] = useState(null);
  const [history, setHistory] = useState([]);

  async function load() {
    setLead(await getLead(id));
    setHistory(await getHistory(id));
  }

  useEffect(() => { load(); }, [id]);

  async function runPrediction() {
    await predictLead(id);
    await load();
  }

  if (!lead) return <div>Loading...</div>;
  const prediction = lead.latest_prediction;

  return <><div className="page-title"><div><span className="eyebrow">LEAD #{lead.id}</span><h1>{lead.student_name}</h1><p>{lead.course || "Course not set"} · {lead.country || "Country not set"}</p></div><StatusBadge status={lead.status} /></div><div className="grid-2 detail-grid"><section className="card"><h3>Lead Information</h3><div className="info-grid"><span>Phone<b>{lead.phone}</b></span><span>Email<b>{lead.email || "—"}</b></span><span>Source<b>{lead.source}</b></span><span>Office<b>{lead.office_name}</b></span><span>Counsellor<b>{lead.counsellor_name || "Unassigned"}</b></span><span>Expected Fee<b>₹{Number(lead.expected_fee).toLocaleString("en-IN")}</b></span></div><div className="prediction-box"><span className="eyebrow">ML PREDICTION</span>{prediction ? <><h2>{prediction.admission_probability.toFixed(1)}%</h2><b>{prediction.priority} PRIORITY</b><p>Expected revenue: ₹{Number(prediction.expected_revenue).toLocaleString("en-IN")}</p></> : <p>No prediction yet.</p>}<button className="btn primary" onClick={runPrediction}>Calculate Prediction</button></div></section><section className="card"><h3>Complete Lead History</h3><LeadTimeline items={history} /></section></div></>;
}
