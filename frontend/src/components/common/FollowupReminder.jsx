import { useEffect, useRef, useState } from "react";
import { BellRing, X } from "lucide-react";
import { getFollowups } from "../../api/crmApi";

export default function FollowupReminder() {
  const [alert, setAlert] = useState(null);
  const notified = useRef(new Set());

  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {});
    }
    async function check() {
      try {
        const rows = await getFollowups();
        const now = Date.now();
        rows.filter((f) => !f.completed).forEach((f) => {
          const due = new Date(f.followup_at).getTime();
          const mins = (due - now) / 60000;
          let key = null;
          let title = null;
          if (mins <= 0 && mins > -1.2) { key = `${f.id}-due`; title = "Follow-up due now"; }
          else if (mins <= 5 && mins > 0) { key = `${f.id}-5min`; title = "Follow-up in 5 minutes"; }
          if (key && !notified.current.has(key)) {
            notified.current.add(key);
            const message = `${f.student_name}${f.note ? ` — ${f.note}` : ""}`;
            setAlert({ title, message });
            if ("Notification" in window && Notification.permission === "granted") new Notification(title, { body: message });
          }
        });
      } catch (_) {}
    }
    check();
    const timer = setInterval(check, 30000);
    return () => clearInterval(timer);
  }, []);

  if (!alert) return null;
  return <div className="followup-toast"><BellRing size={20}/><div><b>{alert.title}</b><span>{alert.message}</span></div><button onClick={() => setAlert(null)}><X size={16}/></button></div>;
}
