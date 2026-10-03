import { useEffect, useRef, useState } from "react";
import { CalendarPlus, Mic, MicOff, Phone, Video } from "lucide-react";
import { addFollowup, getCallTranscripts, getMeetings, saveCallTranscript, scheduleMeeting } from "../../api/crmApi";

export default function EngagementPanel({ lead, onChanged }) {
  const [transcript, setTranscript] = useState("");
  const [listening, setListening] = useState(false);
  const [calls, setCalls] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [followupAt, setFollowupAt] = useState("");
  const [followupNote, setFollowupNote] = useState("");
  const [meetingAt, setMeetingAt] = useState("");
  const [meetingNote, setMeetingNote] = useState("");
  const recognitionRef = useRef(null);

  async function loadEngagement() {
    setCalls(await getCallTranscripts(lead.id));
    setMeetings(await getMeetings(lead.id));
  }
  useEffect(() => { loadEngagement(); }, [lead.id]);

  function startTranscript() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Live browser transcription is supported in Chrome/Edge. You can still type/edit the transcript manually."); return; }
    const recognition = new SpeechRecognition();
    recognition.continuous = true; recognition.interimResults = true; recognition.lang = "en-IN";
    let finalText = transcript;
    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalText += `${event.results[i][0].transcript} `;
        else interim += event.results[i][0].transcript;
      }
      setTranscript((finalText + interim).trim());
    };
    recognition.onend = () => setListening(false);
    recognition.start(); recognitionRef.current = recognition; setListening(true);
  }
  function stopTranscript() { recognitionRef.current?.stop(); setListening(false); }
  async function saveTranscript() {
    if (!transcript.trim()) return;
    await saveCallTranscript({ lead: lead.id, transcript });
    setTranscript(""); await loadEngagement(); onChanged?.();
  }
  async function createFollowup() {
    if (!followupAt) return alert("Choose follow-up date and time.");
    await addFollowup({ lead: lead.id, counsellor: lead.assigned_counsellor, followup_at: new Date(followupAt).toISOString(), note: followupNote });
    setFollowupAt(""); setFollowupNote(""); alert("Follow-up scheduled. EduLead will remind you 5 minutes before and at the due time while the CRM is open.");
  }
  async function createMeeting() {
    if (!meetingAt) return alert("Choose meeting date and time.");
    const meeting = await scheduleMeeting({ lead: lead.id, scheduled_at: new Date(meetingAt).toISOString(), duration_minutes: 30, note: meetingNote });
    setMeetingAt(""); setMeetingNote(""); await loadEngagement();
    alert(meeting.invitation_sent ? "Meeting scheduled and calendar invitation emailed to the student." : "Meeting scheduled. Email was not sent; configure SMTP in backend .env for real delivery.");
  }

  return <section className="card engagement-card">
    <div className="card-head"><div></div></div>
    <div className="engagement-grid">
      <div className="engagement-box"><h4><Phone size={17}/> Call & Transcript</h4><a className="btn soft" href={`tel:${lead.phone}`}>Call {lead.student_name}</a><textarea value={transcript} onChange={(e)=>setTranscript(e.target.value)} placeholder="Live transcript appears here. Review it before saving..."/>
        <div className="inline-actions"><button className="btn soft" onClick={listening?stopTranscript:startTranscript}>{listening?<><MicOff size={15}/> Stop</>:<><Mic size={15}/> Start transcription</>}</button><button className="btn primary" onClick={saveTranscript}>Save Transcript</button></div>
        
      </div>
      <div className="engagement-box"><h4><Video size={17}/> Virtual Meeting</h4><label>Date & time<input type="datetime-local" value={meetingAt} onChange={(e)=>setMeetingAt(e.target.value)}/></label><label>Invitation note<input value={meetingNote} onChange={(e)=>setMeetingNote(e.target.value)} placeholder="Discuss course and application"/></label><button className="btn primary" onClick={createMeeting}>Schedule & Email Invite</button>
        {meetings.slice(0,2).map(m=><div className="mini-record" key={m.id}><b>{new Date(m.scheduled_at).toLocaleString()}</b><a href={m.meeting_url} target="_blank" rel="noreferrer">Join meeting</a><span>{m.invitation_sent?"Email sent":"Email pending"}</span></div>)}
      </div>
      <div className="engagement-box"><h4><CalendarPlus size={17}/> Follow-up</h4><label>Date & time<input type="datetime-local" value={followupAt} onChange={(e)=>setFollowupAt(e.target.value)}/></label><label>Reminder note<input value={followupNote} onChange={(e)=>setFollowupNote(e.target.value)} placeholder="Call regarding documents"/></label><button className="btn primary" onClick={createFollowup}>Schedule Follow-up</button><small className="feature-note"></small></div>
    </div>
    {calls.length>0 && <div className="transcript-history"><h4>Saved Call Transcripts</h4>{calls.map(c=><article key={c.id}><div><b>{c.counsellor_name}</b><span>{new Date(c.created_at).toLocaleString()}</span></div><p>{c.transcript}</p></article>)}</div>}
  </section>;
}
