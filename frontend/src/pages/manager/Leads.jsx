import { useEffect, useState } from "react";
import { Plus, Sparkles } from "lucide-react";

import { assignLead, getEmployees, getLeads, predictAllLeads } from "../../api/crmApi";
import AddLeadModal from "../../components/leads/AddLeadModal";
import LeadTable from "../../components/leads/LeadTable";

export default function Leads() {
  const [leads, setLeads] = useState([]);
  const [team, setTeam] = useState([]);
  const [query, setQuery] = useState("");
  const [showAddLead, setShowAddLead] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [predictionMessage, setPredictionMessage] = useState("");

  async function load() {
    const params = query ? { search: query } : {};
    setLeads(await getLeads(params));
  }

  useEffect(() => {
    load();
    getEmployees().then((employees) => {
      setTeam(employees.filter((employee) => employee.role === "COUNSELLOR"));
    });
  }, []);

  async function assign(lead) {
    const options = team.map((employee) => `${employee.id}: ${employee.name}`).join("\n");
    const counsellorId = window.prompt(`Assign ${lead.student_name} to counsellor ID:\n${options}`);
    if (counsellorId) {
      await assignLead(lead.id, Number(counsellorId));
      await load();
    }
  }

  async function runAllPredictions() {
    setPredicting(true); setPredictionMessage("");
    try {
      const result = await predictAllLeads();
      setPredictionMessage(`${result.predicted} active leads predicted${result.failed ? `, ${result.failed} failed` : ""}.`);
      await load();
    } catch (error) {
      setPredictionMessage(error.response?.data?.detail || "Bulk prediction failed.");
    } finally { setPredicting(false); }
  }

  return (
    <>
      <div className="page-title page-title-actions">
        <div>
          <span className="eyebrow">OFFICE LEADS</span>
          <h1>Lead Management</h1>
          <p>Create direct/walk-in enquiries and assign leads to counsellors in your office.</p>
        </div>
        <div className="inline-actions">
          <button className="btn soft" disabled={predicting} onClick={runAllPredictions}><Sparkles size={17}/>{predicting ? " Predicting..." : " Run ML Predictions"}</button>
          <button className="btn primary add-lead-button" onClick={() => setShowAddLead(true)}><Plus size={17} /> Add Lead</button>
        </div>
      </div>

      {predictionMessage && <div className="success-banner">{predictionMessage}</div>}
      <section className="card">
        <div className="toolbar">
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search student, course or country..." />
          <button className="btn primary" onClick={load}>Search</button>
        </div>
        <LeadTable leads={leads} basePath="/manager/leads" showAssign onAssign={assign} />
      </section>

      <AddLeadModal open={showAddLead} onClose={() => setShowAddLead(false)} onCreated={load} />
    </>
  );
}
