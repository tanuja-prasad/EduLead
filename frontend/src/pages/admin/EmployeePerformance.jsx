import { useEffect, useState } from "react";
import { getDashboard } from "../../api/crmApi";

const money = (value) => `₹${Number(value || 0).toLocaleString("en-IN")}`;

function TeamTable({ title, rows }) {
  return <section className="card"><div className="card-head"><h3>{title}</h3></div><div className="table-wrap"><table>
    <thead><tr><th>Name</th><th>Office</th><th>Assigned</th><th>Converted</th><th>Conversion</th><th>Revenue</th></tr></thead>
    <tbody>{rows.map((row) => <tr key={row.id}><td><b>{row.name}</b></td><td>{row.office}</td><td>{row.assigned}</td><td>{row.converted}</td><td>{row.conversion}%</td><td>{money(row.revenue)}</td></tr>)}</tbody>
  </table></div></section>;
}

export default function EmployeePerformance() {
  const [dashboard, setDashboard] = useState(null);
  useEffect(() => { getDashboard().then(setDashboard); }, []);
  return <><div className="page-title"><div><span className="eyebrow">EMPLOYEES</span><h1>Employee Performance</h1><p>Manager and counsellor results across all offices.</p></div></div><div className="grid-2"><TeamTable title="Managers" rows={dashboard?.manager_performance || []} /><TeamTable title="Counsellors" rows={dashboard?.counsellor_performance || []} /></div></>;
}
