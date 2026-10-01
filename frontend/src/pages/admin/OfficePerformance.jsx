import { useEffect, useState } from "react";
import { getDashboard } from "../../api/crmApi";

const money = (value) => `₹${Number(value || 0).toLocaleString("en-IN")}`;

export default function OfficePerformance() {
  const [dashboard, setDashboard] = useState(null);
  useEffect(() => { getDashboard().then(setDashboard); }, []);

  return (
    <>
      <div className="page-title"><div><span className="eyebrow">BRANCHES</span><h1>Office Performance</h1><p>Compare leads, conversion, revenue and projected profit branch by branch.</p></div></div>
      <section className="card"><div className="table-wrap"><table>
        <thead><tr><th>Office</th><th>Leads</th><th>Admissions</th><th>Conversion</th><th>Revenue</th><th>Expected Additional Revenue</th><th>Projected Profit</th></tr></thead>
        <tbody>{(dashboard?.office_performance || []).map((row) => <tr key={row.office_id}><td><b>{row.office}</b><small>{row.city}</small></td><td>{row.leads}</td><td>{row.admissions}</td><td>{row.conversion}%</td><td>{money(row.revenue)}</td><td>{money(row.expected_revenue)}</td><td>{money(row.projected_profit)}</td></tr>)}</tbody>
      </table></div></section>
    </>
  );
}
