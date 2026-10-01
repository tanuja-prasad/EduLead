import { ArrowRight, BarChart3, BrainCircuit, Building2, LineChart, Users } from "lucide-react";
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <main className="landing-page">
      <div className="landing-orb landing-orb-one" />
      <div className="landing-orb landing-orb-two" />
      <nav className="landing-nav">
        <div className="landing-brand"><span><Building2 size={22} /></span><div><b>EduLead</b><small>CRM & ANALYTICS</small></div></div>
        <div className="landing-actions"><Link className="landing-login" to="/login">Sign in</Link><Link className="landing-cta small" to="/signup">Get started <ArrowRight size={15} /></Link></div>
      </nav>

      <section className="landing-hero">
        <div className="landing-copy">
          <span className="landing-pill">Built for education consultancies</span>
          <h1>Every office. Every lead. <em>One intelligent CRM.</em></h1>
          <p>Manage employees, assign admission enquiries, track conversions and understand office-wise revenue with ML-powered admission and revenue projections.</p>
          <div className="landing-buttons"><Link className="landing-cta" to="/signup">Create account <ArrowRight size={17} /></Link><Link className="landing-secondary" to="/login">Employee sign in</Link></div>
          <div className="landing-trust"><span>Role-based access</span><span>Multi-office analytics</span><span>ML lead scoring</span></div>
        </div>

        <div className="hero-dashboard-wrap">
          <div className="hero-dashboard">
            <div className="hero-dash-head"><div><small>Leadership overview</small><b>Good morning 👋</b></div><span>This month</span></div>
            <div className="hero-stats"><article><small>Total Revenue</small><b>₹1.20 Cr</b><i>+12.4%</i></article><article><small>Expected Revenue</small><b>₹42.8 L</b><i>ML projection</i></article><article><small>Admissions</small><b>315</b><i>+8.1%</i></article></div>
            <div className="hero-chart"><div className="chart-title"><b>Revenue performance</b><small>Office-wise monthly trend</small></div><div className="chart-bars">{[42,58,49,72,63,86,78,96,82,100].map((h,i)=><i key={i} style={{height:`${h}%`}} />)}</div></div>
            <div className="hero-office-row"><span><b>Pune Branch</b><small>₹48L revenue</small></span><strong>14.7%</strong></div>
            <div className="hero-office-row"><span><b>Mumbai Branch</b><small>₹37L revenue</small></span><strong>13.2%</strong></div>
          </div>
          <div className="hero-float hero-float-one"><BrainCircuit size={20}/><span>Lead prediction</span><b>82% HIGH</b></div>
          <div className="hero-float hero-float-two"><Users size={20}/><span>Team conversion</span><b>18.4%</b></div>
        </div>
      </section>

      <section className="landing-features">
        <article><span><Building2 /></span><b>Multi-office CRM</b><p>Employees and leads stay connected to the correct branch.</p></article>
        <article><span><BarChart3 /></span><b>Revenue intelligence</b><p>Actual, expected and office-wise revenue in one leadership view.</p></article>
        <article><span><BrainCircuit /></span><b>ML lead scoring</b><p>Prioritize high, medium and low potential admission enquiries.</p></article>
        <article><span><LineChart /></span><b>Performance analytics</b><p>Measure manager and counsellor conversion performance.</p></article>
      </section>
    </main>
  );
}
