
import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Building2,
  IndianRupee,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getDashboard } from "../../api/crmApi";
import StatCard from "../../components/common/StatCard";

// Cache dashboard data for the current browser tab/session.
const CACHE_PREFIX = "edulead_admin_dashboard_";
const CACHE_DURATION = 60 * 1000;

// Prevent duplicate simultaneous dashboard requests.
const pendingRequests = new Map();

function currency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value) || 0);
}

function getCacheKey() {
  // Use an authenticated user ID here if your app exposes one.
  // Do not cache different users' dashboard data under the same key.
  const userId = getCurrentUserId();
  return userId ? `${CACHE_PREFIX}${userId}` : null;
}

function getCurrentUserId() {
  // Adapt this to your application's actual authentication storage.
  try {
    const stored = sessionStorage.getItem("user");
    if (!stored) return null;

    const user = JSON.parse(stored);
    return user?.id || null;
  } catch {
    return null;
  }
}

function readCache(key) {
  if (!key) return null;

  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;

    const cached = JSON.parse(raw);

    if (
      !cached ||
      !cached.data ||
      !cached.timestamp ||
      Date.now() - cached.timestamp > CACHE_DURATION
    ) {
      sessionStorage.removeItem(key);
      return null;
    }

    return cached;
  } catch {
    return null;
  }
}

function writeCache(key, data) {
  if (!key) return;

  try {
    sessionStorage.setItem(
      key,
      JSON.stringify({
        data,
        timestamp: Date.now(),
      })
    );
  } catch {
    // Storage may be unavailable; the dashboard still works.
  }
}

function fetchDashboardOnce(key) {
  const requestKey = key || "current-admin";

  if (!pendingRequests.has(requestKey)) {
    const request = Promise.resolve()
      .then(() => getDashboard())
      .finally(() => {
        pendingRequests.delete(requestKey);
      });

    pendingRequests.set(requestKey, request);
  }

  return pendingRequests.get(requestKey);
}

function LoadingDashboard() {
  return (
    <div className="page">
      <div className="page-title">
        <div>
          <span className="eyebrow">LEADERSHIP DASHBOARD</span>
          <h1>Business Overview</h1>
          <p>Loading your business statistics...</p>
        </div>
      </div>

      <div className="stats-grid">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="card"
            style={{
              minHeight: 125,
              padding: 24,
              opacity: 0.65,
            }}
          >
            <div
              style={{
                height: 14,
                width: "60%",
                background: "#e2e8f0",
                borderRadius: 6,
                marginBottom: 20,
              }}
            />
            <div
              style={{
                height: 30,
                width: "75%",
                background: "#e2e8f0",
                borderRadius: 6,
              }}
            />
          </div>
        ))}
      </div>

      <div className="grid-2">
        {[1, 2].map((item) => (
          <section
            key={item}
            className="card"
            style={{ minHeight: 320, padding: 24 }}
          >
            <div
              style={{
                width: "45%",
                height: 20,
                background: "#e2e8f0",
                borderRadius: 6,
                marginBottom: 24,
              }}
            />
            <div
              style={{
                width: "100%",
                height: 220,
                background: "#f1f5f9",
                borderRadius: 8,
              }}
            />
          </section>
        ))}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [cacheKey] = useState(getCacheKey);

  const [data, setData] = useState(
    () => readCache(cacheKey)?.data || null
  );

  const [loading, setLoading] = useState(
    () => !readCache(cacheKey)?.data
  );

  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(
    () => readCache(cacheKey)?.timestamp || null
  );

  const loadDashboard = useCallback(
    async (background = false) => {
      if (background) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      try {
        const result = await fetchDashboardOnce(cacheKey);

        if (!result || typeof result !== "object") {
          throw new Error("Invalid dashboard response");
        }

        setData(result);

        const now = Date.now();
        setLastUpdated(now);
        writeCache(cacheKey, result);
      } catch (err) {
        console.error("Admin dashboard error:", err);

        const message =
          err?.code === "ECONNABORTED" ||
          err?.code === "ETIMEDOUT"
            ? "The server is taking too long to respond. Please try again."
            : err?.response?.status === 401
            ? "Your session has expired. Please log in again."
            : "Unable to load the dashboard. Please try again.";

        setError(message);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [cacheKey]
  );

  useEffect(() => {
    // Fresh cached data is displayed immediately.
    // Request new data only when the cache is absent or expired.
    if (!readCache(cacheKey)) {
      loadDashboard(false);
    }
  }, [cacheKey, loadDashboard]);

  if (loading && !data) {
    return <LoadingDashboard />;
  }

  if (!data) {
    return (
      <div className="page">
        <div className="card" style={{ padding: 30 }}>
          <AlertCircle size={30} color="#dc2626" />
          <h2>Unable to load dashboard</h2>
          <p>{error || "Dashboard data is currently unavailable."}</p>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => loadDashboard(false)}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-title">
        <div>
          <span className="eyebrow">LEADERSHIP DASHBOARD</span>
          <h1>Business Overview</h1>
          <p>
            All-office revenue, conversion, projections and
            employee performance.
          </p>

          {lastUpdated && (
            <small style={{ color: "#64748b" }}>
              Last updated:{" "}
              {new Date(lastUpdated).toLocaleTimeString("en-IN")}
            </small>
          )}
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <RefreshCw
            size={16}
            className={refreshing ? "animate-spin" : ""}
          />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            padding: "12px 16px",
            marginBottom: 16,
            borderRadius: 8,
            background: "#fef2f2",
            color: "#991b1b",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="stats-grid">
        <StatCard
          title="Total Revenue"
          value={currency(data.total_revenue)}
          icon={IndianRupee}
          subtitle="Confirmed admissions"
        />

        <StatCard
          title="Expected Additional Revenue"
          value={currency(data.expected_revenue)}
          icon={Sparkles}
          subtitle="ML probability weighted active leads"
        />

        <StatCard
          title="Expected Admissions"
          value={Math.round(
            Number(data.expected_admissions || 0)
          )}
          icon={TrendingUp}
          subtitle="ML estimated admission count"
        />

        <StatCard
          title="Projected Profit"
          value={currency(data.projected_profit)}
          icon={Building2}
          subtitle="Confirmed + expected revenue - branch expenses"
        />
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-head">
            <div>
              <h3>Office-wise Performance</h3>
              <p>Revenue and conversion by branch</p>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Office</th>
                  <th>Leads</th>
                  <th>Admissions</th>
                  <th>Conversion</th>
                  <th>Revenue</th>
                  <th>Expected Additional</th>
                </tr>
              </thead>

              <tbody>
                {(data.office_performance || []).map((row) => (
                  <tr key={row.office_id}>
                    <td>
                      <b>{row.office}</b>
                      <small>{row.city}</small>
                    </td>
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
          <div className="card-head">
            <div>
              <h3>Monthly Revenue</h3>
              <p>Actual revenue vs ML projected revenue</p>
            </div>
          </div>

          <div style={{ width: "100%", height: 310 }}>
            <ResponsiveContainer>
              <BarChart data={data.monthly_revenue || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => currency(value)} />
                <Legend />

                <Bar
                  dataKey="actual_revenue"
                  name="Actual Revenue"
                  fill="#3563e9"
                />

                <Bar
                  dataKey="expected_revenue"
                  name="Projected Revenue"
                  fill="#9bb1ff"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid-2 dashboard-section">
        <PerformanceTable
          title="Manager Performance"
          rows={data.manager_performance || []}
        />

        <PerformanceTable
          title="Counsellor Performance"
          rows={data.counsellor_performance || []}
        />
      </div>
    </div>
  );
}

function PerformanceTable({ title, rows = [] }) {
  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h3>{title}</h3>
          <p>Assigned leads, conversions and revenue</p>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Office</th>
              <th>Assigned</th>
              <th>Converted</th>
              <th>Revenue</th>
            </tr>
          </thead>

          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center" }}>
                  No performance data available
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id}>
                  <td><b>{row.name}</b></td>
                  <td>{row.office}</td>
                  <td>{row.assigned}</td>
                  <td>
                    {row.converted} ({row.conversion}%)
                  </td>
                  <td>{currency(row.revenue)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
