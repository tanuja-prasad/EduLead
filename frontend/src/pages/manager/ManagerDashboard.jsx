import { useEffect, useState } from "react";
import { CircleCheckBig, Clock3, IndianRupee, Plus, UserPlus } from "lucide-react";
import { Link } from "react-router-dom";

import { getDashboard, getLeads } from "../../api/crmApi";
import StatCard from "../../components/common/StatCard";
import LeadTable from "../../components/leads/LeadTable";

function currency(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value || 0);
}

export default function ManagerDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [leads, setLeads] = useState([]);

  useEffect(() => {
    getDashboard().then(setDashboard);
    getLeads().then((items) => setLeads(items.slice(0, 6)));
  }, []);

  return (
    <>
      <div className="page-title">
        <div>
          <span className="eyebrow">OFFICE WORKSPACE</span>
          <h1>Manager Overview</h1>
          <p>Assign leads and monitor the business pipeline for your branch.</p>
        </div>
        <Link className="btn primary add-lead-button" to="/manager/leads"><Plus size={17} /> Add Lead</Link>
      </div>

      <div className="stats-grid">
        <StatCard title="New Leads" value={dashboard?.new_leads ?? "—"} icon={UserPlus} subtitle="Waiting for assignment" />
        <StatCard title="Active Pipeline" value={dashboard?.active_pipeline ?? "—"} icon={Clock3} subtitle="Open opportunities" />
        <StatCard title="Admissions" value={dashboard?.admissions ?? "—"} icon={CircleCheckBig} subtitle="Converted leads" />
        <StatCard title="Revenue" value={currency(dashboard?.total_revenue)} icon={IndianRupee} subtitle="Office business" />
      </div>

      <section className="card">
        <div className="card-head"><div><h3>Recent Leads</h3><p>Open a lead to see its complete history.</p></div></div>
        <LeadTable leads={leads} basePath="/manager/leads" />
      </section>
    </>
  );
}
