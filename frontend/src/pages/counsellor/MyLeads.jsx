import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { getLeads, predictAllLeads } from "../../api/crmApi";
import LeadTable from "../../components/leads/LeadTable";
export default function MyLeads(){
  const[leads,setLeads]=useState([]),[q,setQ]=useState(""),[predicting,setPredicting]=useState(false),[message,setMessage]=useState("");
  async function load(){setLeads(await getLeads(q?{search:q}:{}));}
  useEffect(()=>{load();},[]);
  async function predictAll(){setPredicting(true);setMessage("");try{const r=await predictAllLeads();setMessage(`${r.predicted} of your active leads predicted.`);await load();}catch(e){setMessage(e.response?.data?.detail||"Prediction failed.");}finally{setPredicting(false);}}
  return <><div className="page-title page-title-actions"><div><span className="eyebrow">ASSIGNED TO ME</span><h1>My leads</h1><p>Contact students, add remarks and move each enquiry forward.</p></div><button className="btn soft" disabled={predicting} onClick={predictAll}><Sparkles size={17}/>{predicting?" Predicting...":" Predict My Leads"}</button></div>{message&&<div className="success-banner">{message}</div>}<section className="card"><div className="toolbar"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search my leads…"/><button className="btn primary" onClick={load}>Search</button></div><LeadTable leads={leads} basePath="/counsellor/leads"/></section></>;
}
