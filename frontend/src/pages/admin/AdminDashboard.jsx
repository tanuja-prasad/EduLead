import { useEffect, useState } from "react";
import { Building2, IndianRupee, Sparkles, TrendingUp } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getDashboard } from "../../api/crmApi";
import StatCard from "../../components/common/StatCard";

function currency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export default function AdminDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getDashboard().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return <div className="page">Loading dashboard...</div>;
  }

  return (
    <div className="page">
      <div className="page-title">
        <div>
          <span className="eyebrow">LEADERSHIP DASHBOARD</span>
          <h1>Business Overview</h1>
          <p>All-office revenue, conversion, projections and employee performance.</p>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard title="Total Revenue" value={currency(data.total_revenue)} icon={IndianRupee} subtitle="Confirmed admissions" />
        <StatCard title="Expected Additional Revenue" value={currency(data.expected_revenue)} icon={Sparkles} subtitle="ML probability weighted active leads" />
        <StatCard title="Expected Admissions" value={Math.round(Number(data.expected_admissions || 0))} icon={TrendingUp} subtitle="ML estimated admission count" />
        <StatCard title="Projected Profit" value={currency(data.projected_profit)} icon={Building2} subtitle="Confirmed + expected revenue - branch expenses" />
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-head">
            <div><h3>Office-wise Performance</h3><p>Revenue and conversion by branch</p></div>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Office</th><th>Leads</th><th>Admissions</th><th>Conversion</th><th>Revenue</th><th>Expected Additional</th></tr></thead>
              <tbody>
                {data.office_performance?.map((row) => (
                  <tr key={row.office_id}>
                    <td><b>{row.office}</b><small>{row.city}</small></td>
                    <td>{row.leads}</td>
                    <td>{row.admissions}</td>
                    <td>{row.conversion}%</td>
                    <td>{currency(row.revenue)}</td>
                    <td>{currency(row.expected_revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card">
          <div className="card-head"><div><h3>Monthly Revenue</h3><p>Actual revenue vs ML projected revenue</p></div></div>
          <div style={{ width: "100%", height: 310 }}>
            <ResponsiveContainer>
              <BarChart data={data.monthly_revenue}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => currency(value)} />
                <Legend />
                <Bar dataKey="actual_revenue" name="Actual Revenue" fill="#3563e9" />
                <Bar dataKey="expected_revenue" name="Projected Revenue" fill="#9bb1ff" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid-2 dashboard-section">
        <PerformanceTable title="Manager Performance" rows={data.manager_performance} />
        <PerformanceTable title="Counsellor Performance" rows={data.counsellor_performance} />
      </div>
    </div>
  );
}

function PerformanceTable({ title, rows = [] }) {
  return (
    <section className="card">
      <div className="card-head"><div><h3>{title}</h3><p>Assigned leads, conversions and revenue</p></div></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Employee</th><th>Office</th><th>Assigned</th><th>Converted</th><th>Revenue</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td><b>{row.name}</b></td>
                <td>{row.office}</td>
                <td>{row.assigned}</td>
                <td>{row.converted} ({row.conversion}%)</td>
                <td>{currency(row.revenue)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
