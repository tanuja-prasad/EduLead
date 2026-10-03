import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getCallTranscripts, getHistory, getLead, getMeetings } from "../../api/crmApi";
import StatusBadge from "../../components/common/StatusBadge";
import LeadTimeline from "../../components/leads/LeadTimeline";

export default function LeadDetails() {
  const { id } = useParams();
  const [lead,setLead]=useState(null),[history,setHistory]=useState([]),[calls,setCalls]=useState([]),[meetings,setMeetings]=useState([]);
  async function load(){setLead(await getLead(id));setHistory(await getHistory(id));setCalls(await getCallTranscripts(id));setMeetings(await getMeetings(id));}
  useEffect(()=>{load();},[id]);
  if(!lead)return <div>Loading...</div>;
  const prediction=lead.latest_prediction;
  return <><div className="page-title"><div><span className="eyebrow">LEAD #{lead.id}</span><h1>{lead.student_name}</h1><p>{lead.course||"Course not set"} · {lead.country||"Country not set"}</p></div><StatusBadge status={lead.status}/></div>
  <div className="grid-2 detail-grid"><section className="card"><h3>Lead Information</h3><div className="info-grid"><span>Phone<b>{lead.phone}</b></span><span>Email<b>{lead.email||"—"}</b></span><span>Source<b>{lead.source}</b></span><span>Office<b>{lead.office_name}</b></span><span>Counsellor<b>{lead.counsellor_name||"Unassigned"}</b></span><span>Expected Fee<b>₹{Number(lead.expected_fee).toLocaleString("en-IN")}</b></span></div><div className="prediction-box"><span className="eyebrow">LATEST ML PREDICTION</span>{prediction?<><h2>{prediction.admission_probability.toFixed(1)}%</h2><b>{prediction.priority} PRIORITY</b><p>Expected revenue: ₹{Number(prediction.expected_revenue).toLocaleString("en-IN")}</p></>:<p>No prediction yet. Run bulk predictions from Lead Management.</p>}</div></section><section className="card"><h3>Complete Lead History</h3><LeadTimeline items={history}/></section></div>
  <div className="grid-2 detail-grid manager-engagement"><section className="card"><h3>Call Transcripts</h3><p className="muted-copy">Counsellor call notes/transcripts are visible to the manager for quality and continuity.</p>{calls.length?calls.map(c=><article className="transcript-row" key={c.id}><div><b>{c.counsellor_name}</b><span>{new Date(c.created_at).toLocaleString()}</span></div><p>{c.transcript}</p></article>):<p>No transcripts saved yet.</p>}</section><section className="card"><h3>Scheduled Meetings</h3>{meetings.length?meetings.map(m=><article className="meeting-row" key={m.id}><b>{new Date(m.scheduled_at).toLocaleString()}</b><span>{m.status}</span><a href={m.meeting_url} target="_blank" rel="noreferrer">Join meeting</a></article>):<p>No meetings scheduled yet.</p>}</section></div></>;
}
