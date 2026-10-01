import { useEffect, useState } from "react";
import { getDashboard } from "../../api/crmApi";

export default function BusinessAnalytics() {
  const [dashboard, setDashboard] = useState(null);
  useEffect(() => { getDashboard().then(setDashboard); }, []);

  return (
    <>
      <div className="page-title"><div><span className="eyebrow">MARKETING</span><h1>Source Analytics</h1><p>Identify which enquiry sources produce admissions.</p></div></div>
      <section className="card"><div className="table-wrap"><table>
        <thead><tr><th>Source</th><th>Leads</th><th>Admissions</th><th>Conversion</th></tr></thead>
        <tbody>{(dashboard?.source_performance || []).map((row) => {
          const conversion = row.total ? ((row.converted * 100) / row.total).toFixed(1) : 0;
          return <tr key={row.source}><td><b>{row.source}</b></td><td>{row.total}</td><td>{row.converted}</td><td>{conversion}%</td></tr>;
        })}</tbody>
      </table></div></section>
    </>
  );
}
