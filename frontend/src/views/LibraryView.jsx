import React, { useState, useRef, useEffect } from "react";
import { 
  Search, SlidersHorizontal, Mic, Square, Sparkles, Cloud, Play, 
  Download, MoreVertical, LayoutGrid, List, BarChart3, Database, FileText
} from "lucide-react";

export default function LibraryView({
  tasks,
  logs,
  onOpenSession,
  onAddNewSession,
  onAnalyzeLogs,
  onDeleteTask,
  perfData
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordedTime, setRecordedTime] = useState("00:00");
  const [syncing, setSyncing] = useState(false);

  // Microphone recording refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const secondsRef = useRef(0);

  // Map backend tasks to UI sessions
  const sessions = tasks.map((task, index) => {
    const defaultThumbs = [
      "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1516280440614-37939bbacd6a?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1507838153414-b4b713384a76?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop"
    ];
    
    let uiStatus = "COMPLETED";
    if (task.status === "processing" || task.status === "downloading" || task.status === "transcribing" || task.status === "summarizing" || task.status === "pending") {
      uiStatus = "IN_PROGRESS";
    } else if (task.status === "failed") {
      uiStatus = "FAILED";
    }

    return {
      id: task.id,
      title: task.title || `Session ${index + 1}`,
      date: task.date || "TODAY",
      time: task.time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      duration: task.duration || "00:00",
      status: uiStatus,
      speaker: task.speaker || "V. Valerius",
      thumbnail: task.image_url || task.thumbnail || defaultThumbs[index % defaultThumbs.length],
      tags: Array.isArray(task.tags) && task.tags.length > 0 ? task.tags : ["Acoustic", "AI Workstation"],
      progress: task.progress || 82,
      rawTask: task
    };
  });

  // Handle Search Filtering
  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Dynamic status states
  const totalHours = (48.5 + (sessions.length - 6) * 0.25).toFixed(1);
  const totalStorage = perfData?.disk?.used
    ? perfData.disk.used.toFixed(2)
    : (12.8 + (sessions.length - 6) * 0.02).toFixed(2);

  // Microphone recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setSyncing(true);

        try {
          const formData = new FormData();
          formData.append("file", audioBlob, `mic_record_${Date.now()}.wav`);
          formData.append("asr_mode", "local");

          const response = await fetch("http://127.0.0.1:8000/api/upload", {
            method: "POST",
            body: formData
          });

          if (response.ok) {
            const result = await response.json();
            alert("Microphone recording uploaded successfully!");
            if (typeof onAddNewSession === "function") {
              onAddNewSession({
                id: result.task_id,
                title: `Voice capture - Session ${sessions.length + 1}`,
                status: "IN_PROGRESS",
                tags: ["Mic", "Direct"]
              });
            }
          } else {
            alert("Upload failed. Please ensure the backend is running.");
          }
        } catch (err) {
          console.error("Failed to upload captured audio:", err);
          alert("Connection error uploading captured audio to local server.");
        } finally {
          setSyncing(false);
          stream.getTracks().forEach(track => track.stop());
        }
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      secondsRef.current = 0;
      setRecordedTime("00:00");

      timerIntervalRef.current = setInterval(() => {
        secondsRef.current += 1;
        setRecordedTime(formatSecondsToMMSS(secondsRef.current));
      }, 1000);

    } catch (err) {
      console.error("Microphone permissions denied or error:", err);
      alert("Microphone connection failed. Please ensure you have allowed microphone permissions in your browser.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    }
  };

  const formatSecondsToMMSS = (totSeconds) => {
    const mins = Math.floor(totSeconds / 60);
    const secs = totSeconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleSyncClick = () => {
    setSyncing(true);
    setTimeout(() => {
      setSyncing(false);
      alert("Cloud Sync completed successfully! All acoustic archives are secured and encrypted.");
    }, 2000);
  };

  return (
    <div id="library-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        {/* Top Search bar/Header controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-4xl font-extrabold tracking-tight text-[#1d1c18] font-display">Library</h2>
          <p className="text-sm text-[#5d5a55]/80 mt-1 font-medium">Manage your acoustic archives and AI-powered transcriptions.</p>
        </div>

        {/* Search Input */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#5d3f3e]/40 w-4.5 h-4.5" />
            <input
              id="library-search-input"
              type="text"
              placeholder="Search sessions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onClick={() => alert("功能待上线")}
              readOnly
              className="pl-10 pr-4 py-2.5 bg-white border border-[#e7bcbb]/40 rounded-lg text-sm w-64 text-[#1d1c18] placeholder-[#5d3f3e]/40 focus:outline-none focus:ring-1 focus:ring-[#f62440] focus:border-[#f62440] cursor-pointer"
            />
          </div>

          <button
            id="btn-all-time-filter"
            className="flex items-center gap-1.5 px-3.5 py-2.5 bg-[#f2ede6] text-sm text-[#1d1c18] font-bold rounded-lg border border-[#e7bcbb]/30 hover:bg-[#e6e2db] transition-all cursor-pointer border-0 outline-none"
            onClick={() => alert("功能待上线")}
          >
            <span>All Time</span>
          </button>

          <button
            id="btn-all-speakers-filter"
            className="flex items-center gap-1.5 px-3.5 py-2.5 bg-[#f2ede6] text-sm text-[#1d1c18] font-bold rounded-lg border border-[#e7bcbb]/30 hover:bg-[#e6e2db] transition-all cursor-pointer border-0 outline-none"
            onClick={() => alert("功能待上线")}
          >
            <span>All Speakers</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Highlight Card & Pulse Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
        {/* Recording Launcher module */}
        <div 
          id="block-begin-session"
          className="lg:col-span-2 bg-[#ffffff] border border-[#e7bcbb]/45 rounded-xl p-6 shadow-xs flex flex-col justify-between relative overflow-hidden"
        >
          {/* Subtle background graphic */}
          <div className="absolute right-0 bottom-0 opacity-10 pointer-events-none translate-x-1/10 translate-y-1/10 select-none">
            <svg width="240" height="140" viewBox="0 0 240 140" fill="none">
              <path d="M0,70 Q40,30 80,70 T160,70 T240,70" stroke="#f62440" strokeWidth="6" fill="none" className="animate-pulse" />
              <path d="M0,90 Q40,50 80,90 T160,90 T240,90" stroke="#f62440" strokeWidth="2" fill="none" className="animate-wave-slow" />
            </svg>
          </div>

          <div>
            <div className="inline-flex items-center gap-1.5 bg-[#ffdad8] text-[#92001d] text-[11px] font-bold px-2.5 py-1 rounded-sm uppercase tracking-wider mb-4">
              <span className="w-1.5 h-1.5 bg-[#f62440] rounded-full animate-ping" />
              Active Engine: V3-Noir
            </div>
            <h3 className="text-3xl font-bold tracking-tight text-[#1d1c18] font-display">Begin a new session</h3>
            <p className="text-[#5d5a55] text-sm mt-2 max-w-lg leading-relaxed">
              Capture high-fidelity audio with real-time vampiric AI processing and instant transcription.
            </p>
          </div>

          <div className="mt-8 flex items-center gap-4 relative z-10">
            {!isRecording ? (
              <button
                id="btn-start-recording-inner"
                onClick={() => alert("功能待上线")}
                className="bg-[#f62440] hover:bg-[#bb0028] text-white font-semibold px-6 py-3 rounded-lg flex items-center gap-2.5 transition-all shadow-sm active:scale-98 cursor-pointer border-0 outline-none"
              >
                <Mic size={18} />
                <span>Start New Recording</span>
              </button>
            ) : (
              <div className="flex items-center gap-4 bg-[#ffdad6] border border-[#e7bcbb] p-2.5 rounded-lg">
                <span className="text-sm font-mono font-bold text-[#b81a1a] animate-pulse flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 bg-[#f62440] rounded-full animate-ping" />
                  Recording [{recordedTime}]
                </span>
                <button
                  id="btn-stop-recording-inner"
                  onClick={stopRecording}
                  className="bg-[#b81a1a] hover:bg-[#93000a] text-white font-semibold px-4 py-2 rounded-md flex items-center gap-1.5 transition-all text-xs cursor-pointer border-0 outline-none"
                >
                  <Square size={13} fill="white" />
                  <span>Stop Capture</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Pulse Stats Table column */}
        <div className="flex flex-col gap-5">
          {/* Library Pulse Card */}
          <div className="bg-[#ffffff] border border-[#e7bcbb]/45 rounded-xl p-6 shadow-xs">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#bf0029] mb-4 flex items-center gap-1.5">
              <BarChart3 size={15} />
              Library Pulse
            </h4>
            
            <div className="flex flex-col gap-3.5">
              <div className="flex items-center justify-between border-b border-[#e7bcbb]/20 pb-2">
                <span className="text-[13px] font-semibold text-[#5d5a55]">Total Sessions</span>
                <span className="text-lg font-extrabold text-[#1d1c18] font-mono">{sessions.length}</span>
              </div>
              <div className="flex items-center justify-between border-b border-[#e7bcbb]/20 pb-2">
                <span className="text-[13px] font-semibold text-[#5d5a55]">Hours Transcribed</span>
                <span className="text-lg font-extrabold text-[#1d1c18] font-mono">{totalHours}h</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-semibold text-[#5d5a55]">Storage Used</span>
                <span className="text-lg font-extrabold text-[#1d1c18] font-mono">{totalStorage} GB</span>
              </div>
            </div>
          </div>

          {/* Sync Status Card */}
          <div 
            onClick={() => alert("功能待上线")}
            className="bg-[#ffdad6]/20 hover:bg-[#ffdad6]/35 transition-all text-[#bf0029] border border-[#ffb4a8] rounded-xl p-4 flex items-center justify-between cursor-pointer"
          >
            <div className="flex flex-col">
              <span className="text-[11px] font-extrabold uppercase tracking-wide text-[#b81a1a]">Sync Status</span>
              <span className="text-xs text-[#5d3f3e] font-semibold mt-0.5">
                {syncing ? "Backing up files securely..." : "All files encrypted & backed up."}
              </span>
            </div>
            <Cloud size={20} className={`${syncing ? 'animate-bounce text-[#f62440]' : 'text-[#f62440]'}`} />
          </div>
        </div>
      </div>

      {/* Recent Recordings Category list */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-2xl font-bold tracking-tight text-[#1d1c18] font-display">Recent Recordings</h3>
          <div className="flex items-center gap-2">
            <button className="p-1.5 rounded-md hover:bg-[#e6e2db]/50 text-[#5d3f3e]/60 cursor-pointer border-0 outline-none bg-transparent" onClick={() => alert("Layout preset matches image mockups list layout")}>
              <LayoutGrid size={16} />
            </button>
            <button className="p-1.5 rounded-md bg-[#ffffff] border border-[#e7bcbb]/40 text-[#f62440] cursor-pointer outline-none">
              <List size={16} />
            </button>
          </div>
        </div>

        {/* List Layout with Row blocks */}
        <div className="flex flex-col gap-3">
          {filteredSessions.map((session) => {
            const isSelected = false; // can be customized
            return (
              <div
                key={session.id}
                id={`session-row-${session.id}`}
                onClick={() => onOpenSession(session.rawTask)}
                className={`flex flex-col md:flex-row md:items-center justify-between p-4 bg-white rounded-lg border cursor-pointer hover:border-[#f62440]/65 hover:shadow-xs transition-all ${
                  isSelected 
                    ? 'border-[#f62440] ring-1 ring-[#f62440]/20' 
                    : 'border-[#e7bcbb]/30'
                }`}
              >
                <div className="flex items-center gap-3.5">
                  {/* Square Program Cover Image */}
                  <div className="w-12 h-12 rounded-lg overflow-hidden shrink-0 border border-[#e7bcbb]/30 bg-[#f2ede6]/50 relative">
                    <img 
                      src={session.thumbnail} 
                      alt="" 
                      referrerPolicy="no-referrer"
                      className="w-full h-full object-cover"
                    />
                    {session.status === 'IN_PROGRESS' && (
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                        <span className="w-2 h-2 bg-[#f62440] rounded-full animate-ping" />
                      </div>
                    )}
                  </div>

                  {/* Title & Metadata tags */}
                  <div>
                    <h4 className="font-bold text-sm text-[#1d1c18] font-display">{session.title}</h4>
                    <div className="flex flex-wrap items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-[#5d3f3e]/70">
                      <span className="uppercase text-xs">{session.date}</span>
                      <span>•</span>
                      <span>{session.time}</span>
                      <span>•</span>
                      {session.status === 'IN_PROGRESS' ? (
                        <span className="bg-[#ffdad6] text-[#b81a1a] px-1.5 py-0.5 rounded-sm font-bold uppercase tracking-wider text-[10px]">
                          • {session.rawTask.status === 'pending' ? 'Queued' : `In Progress (${session.progress}%)`}
                        </span>
                      ) : (
                        <span className="bg-[#f0e2b7] text-[#554428] px-1.5 py-0.5 rounded-sm font-bold uppercase tracking-wider text-[10px]">
                          Completed
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right widgets Waveform or actions */}
                <div className="flex items-center gap-4 mt-3 md:mt-0 self-end md:self-auto">
                  {session.status === 'IN_PROGRESS' ? (
                    <span className="text-[12px] font-mono text-[#5d3f3e]/60 italic font-medium">
                      {session.rawTask.status === 'pending' ? 'Waiting in queue...' : 'AI generating tags...'}
                    </span>
                  ) : (
                    /* Brief simulated sound waves */
                    <div className="flex items-end gap-0.5 h-6 opacity-80">
                      <span className="w-1 bg-[#f62440] h-3 rounded-full" />
                      <span className="w-1 bg-[#f62440] h-5 rounded-full" />
                      <span className="w-1 bg-[#f62440] h-6 rounded-full animate-wave-slow" />
                      <span className="w-1 bg-[#f62440] h-2 rounded-full" />
                      <span className="w-1 bg-[#f61111]/30 h-4 rounded-full" />
                    </div>
                  )}

                  <div className="flex items-center gap-1 text-[#5d3f3e]/60">
                    <button
                      className="p-1.5 hover:bg-[#f2ede6]/50 rounded-md transition-all cursor-pointer border-0 outline-none bg-transparent"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenSession(session.rawTask);
                      }}
                    >
                      <Play size={14} />
                    </button>
                    <button
                      className="p-1.5 hover:bg-[#f2ede6]/50 rounded-md transition-all cursor-pointer border-0 outline-none bg-transparent"
                      onClick={(e) => {
                        e.stopPropagation();
                        alert(`Downloading complete acoustic wave file for: ${session.title}`);
                      }}
                    >
                      <Download size={14} />
                    </button>
                    <button
                      className="p-1.5 hover:bg-[#f2ede6]/50 rounded-md transition-all cursor-pointer border-0 outline-none bg-transparent"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (typeof onDeleteTask === "function") {
                          if (confirm(`Determine to delete this task "${session.title}" and wipe audio cache?`)) {
                            onDeleteTask(session.id);
                          }
                        } else {
                          alert("Session Options: Delete, Rename, Export XML, Sync to Drive.");
                        }
                      }}
                    >
                      <MoreVertical size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Load More Archives dotted button */}
        <button
          id="btn-load-more"
          onClick={() => alert("All matching recordings are fully displayed.")}
          className="w-full mt-4 py-3.5 bg-transparent border border-dashed border-[#e7bcbb] rounded-lg text-[#bf0029] hover:bg-[#ffdad6]/20 transition-all font-semibold text-center text-sm cursor-pointer outline-none"
        >
          Load More Archives
        </button>
      </section>

      {/* AI Analysis Log bento section */}
      <section>
        <h3 className="text-2xl font-bold tracking-tight text-[#1d1c18] font-display mb-4">AI Analysis Log</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {logs.map((log) => (
            <div
              key={log.id}
              className="bg-[#ffffff] border border-[#e7bcbb]/45 p-5 rounded-lg flex flex-col justify-between hover:shadow-xs hover:border-[#f62440]/40 transition-all text-xs"
            >
              <div>
                <div className="flex items-center justify-between text-[11px] font-mono text-[#5d5a55]/70 mb-3 select-none">
                  <span className="flex items-center gap-1 font-bold">
                    <FileText size={12} className="text-[#bf0029]" />
                    ID: {log.id}
                  </span>
                  <span>{log.timeAgo}</span>
                </div>
                <p className="text-[#1d1c18] italic font-medium leading-relaxed mb-4">
                  "{log.text}"
                </p>
              </div>

              {/* Tags matching layout */}
              <div className="flex flex-wrap items-center gap-1">
                {log.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="bg-[#f2ede6] text-[#554428] px-2.5 py-1 text-[10px] font-bold uppercase rounded-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}

          <div
            id="btn-analyze-logs"
            onClick={() => alert("功能待上线")}
            className="bg-[#f9f3ea] hover:bg-[#f2ede6] cursor-pointer border border-[#e7bcbb]/60 border-dashed rounded-lg p-5 flex flex-col items-center justify-center gap-3 text-center transition-all group"
          >
            <div className="w-10 h-10 bg-[#f62440]/10 text-[#f62440] group-hover:scale-105 transition-all rounded-full flex items-center justify-center">
              <Sparkles size={18} fill="#f62440" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-[#1d1c18] font-display">Analyze All Logs</h4>
              <p className="text-[#5d5a55] text-[11px] mt-1 pr-2">Regenerate structured summaries from recent session audio.</p>
            </div>
          </div>
        </div>
      </section>
      </div>
    </div>
  );
}
