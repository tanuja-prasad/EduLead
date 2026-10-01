export default function LeadTimeline({ items = [] }) {
  return (
    <div className="timeline">
      {items.map((item) => (
        <div className="timeline-item" key={item.id}>
          <span className="dot" />
          <div>
            <b>{item.activity_type.replace("_", " ")}</b>
            <p>{item.remark || `${item.old_status || ""} ${item.new_status ? `→ ${item.new_status}` : ""}`}</p>
            <small>{item.employee_name} · {new Date(item.created_at).toLocaleString()}</small>
          </div>
        </div>
      ))}
      {!items.length && <div className="empty">No activity yet.</div>}
    </div>
  );
}
