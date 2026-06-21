import React, { useState } from "react";
import { 
  Plus, Search, List, LayoutGrid, Calendar, SlidersHorizontal, Play, MoreVertical 
} from "lucide-react";

export default function WorkstationView({
  tasks,
  onOpenSession,
  onNewSessionTrigger
}) {
  const [selectedSpeaker, setSelectedSpeaker] = useState("All");
  const [dateFilter, setDateFilter] = useState("Last 30 Days");
  const [viewMode, setViewMode] = useState("grid");

  // Map backend tasks to UI sessions format
  const sessions = tasks.map((task, index) => {
    const defaultThumbs = [
      "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1516280440614-37939bbacd6a?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1507838153414-b4b713384a76?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop"
    ];

    return {
      id: task.id,
      title: task.title || `Session ${index + 1}`,
      date: task.date || "TODAY",
      time: task.time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      duration: task.duration || "00:00",
      status: task.status === "completed" ? "COMPLETED" : task.status === "failed" ? "FAILED" : "IN_PROGRESS",
      speaker: task.speaker || (index % 2 === 0 ? "V. Valerius" : "E. Black"),
      thumbnail: task.image_url || task.thumbnail || defaultThumbs[index % defaultThumbs.length],
      tags: Array.isArray(task.tags) && task.tags.length > 0 ? task.tags : ["Ambient", "Narrative"],
      rawTask: task
    };
  });

  // Filter logic
  const filtered = sessions.filter(session => {
    if (selectedSpeaker === "All") return true;
    return session.speaker === selectedSpeaker;
  });

  return (
    <div id="workstation-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        {/* Top Header controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-4xl font-extrabold tracking-tight text-[#1d1c18] font-display">Workstation</h2>
          <p className="text-sm text-[#5d5a55]/80 mt-1 font-medium">Select and parse any acoustic trace inside the advanced multi-track visualizer.</p>
        </div>

        {/* Action controllers */}
        <div className="flex items-center gap-3">
          <button
            id="btn-station-filters"
            onClick={() => alert("功能待上线")}
            className="flex items-center gap-1.5 px-4 py-2.5 bg-white border border-[#e7bcbb]/40 text-sm text-[#5d3f3e] font-semibold rounded-lg hover:bg-[#f9f3ea]/40 transition-all shadow-xs cursor-pointer border-0 outline-none"
          >
            <SlidersHorizontal size={14} />
            <span>Filters</span>
          </button>

          <button
            id="btn-new-recording-station"
            onClick={onNewSessionTrigger}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#f62440] hover:bg-[#bb0028] text-white text-sm font-semibold rounded-lg shadow-sm transition-all cursor-pointer border-0 outline-none"
          >
            <Plus size={16} />
            <span>Add New Link</span>
          </button>
        </div>
      </div>

      {/* Filter toolbar (Matches image mockup exactly) */}
      <div className="bg-[#f9f3ea]/50 border border-[#e7bcbb]/30 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        {/* Speaker Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-extrabold text-[#5d3f3e]/60 uppercase tracking-widest mr-2">Speaker:</span>
          {["All", "V. Valerius", "E. Black"].map((sp) => {
            const active = selectedSpeaker === sp;
            return (
              <button
                key={sp}
                onClick={() => setSelectedSpeaker(sp)}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer border-0 outline-none ${
                  active 
                    ? "bg-[#1d1c18] text-[#fef9f2]" 
                    : "bg-[#f2ede6] text-[#5d3f3e] hover:bg-[#e6e2db]"
                }`}
              >
                {sp}
              </button>
            );
          })}
        </div>

        {/* Date scope and grid controls */}
        <div className="flex items-center gap-3 self-end md:self-auto">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-extrabold text-[#5d3f3e]/60 uppercase tracking-widest">Date:</span>
            <select
              value={dateFilter}
              onChange={(e) => {
                setDateFilter(e.target.value);
                alert(`Query period set to: ${e.target.value}`);
              }}
              className="bg-[#f2ede6] border border-[#e7bcbb]/20 px-3 py-1.5 rounded-lg text-xs font-bold text-[#5d3f3e] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
            >
              <option value="Last 30 Days">Last 30 Days</option>
              <option value="Last 7 Days">Last 7 Days</option>
              <option value="All Time">All Time</option>
            </select>
          </div>

          <div className="h-4 w-[1px] bg-[#e7bcbb]/40 mx-1" />

          {/* Layout controls toggle */}
          <div className="flex items-center bg-[#f2ede6] p-0.5 rounded-lg border border-[#e7bcbb]/20">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-md transition-all cursor-pointer border-0 outline-none ${
                viewMode === "grid" ? "bg-white text-[#f62440]" : "text-[#5d3f3e]/60 bg-transparent"
              }`}
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-md transition-all cursor-pointer border-0 outline-none ${
                viewMode === "list" ? "bg-white text-[#f62440]" : "text-[#5d3f3e]/60 bg-transparent"
              }`}
            >
              <List size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Grid or List of Available sessions */}
      {viewMode === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((session) => (
            <div
              key={session.id}
              onClick={() => onOpenSession(session.rawTask)}
              className="bg-white border border-[#e7bcbb]/40 rounded-xl overflow-hidden hover:border-[#f62440]/50 hover:shadow-sm transition-all flex flex-col group cursor-pointer"
            >
              {/* Media Thumbnail Container */}
              <div className="aspect-[4/3] bg-neutral-900 relative overflow-hidden shrink-0">
                <img
                  src={session.thumbnail}
                  alt={session.title}
                  referrerPolicy="no-referrer"
                  className="w-full h-full object-cover transition-transform group-hover:scale-103 duration-500 opacity-90"
                />
                
                {/* Duration indicator tag */}
                <span className="absolute top-3 right-3 bg-black/75 backdrop-blur-xs text-white text-[11px] font-mono font-extrabold px-2.5 py-1 rounded-sm">
                  {session.duration}
                </span>

                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div 
                    className="w-12 h-12 bg-[#f62440] hover:bg-[#bb0028] text-white flex items-center justify-center rounded-full shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-all duration-300"
                  >
                    <Play size={18} fill="white" className="ml-0.5" />
                  </div>
                </div>
              </div>

              {/* Information body panel */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-base text-[#1d1c18] font-display leading-tight group-hover:text-[#f62440] transition-colors">
                      {session.title}
                    </h3>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        alert("Station Options: Open, Export, Rename, Delete Track.");
                      }}
                      className="p-1 hover:bg-[#f2ede6]/50 rounded text-neutral-400 hover:text-neutral-600 self-start cursor-pointer border-0 outline-none bg-transparent"
                    >
                      <MoreVertical size={14} />
                    </button>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-[#5d5a55] mt-2 font-semibold">
                    <Calendar size={12} className="text-[#bf0029]" />
                    <span>{session.date}</span>
                    <span>•</span>
                    <span className="text-[#1d1c18]">{session.speaker}</span>
                  </div>

                  {/* High rounded components tags */}
                  <div className="flex flex-wrap gap-1.5 mt-4">
                    {session.tags.map((tg, idx) => (
                      <span
                        key={idx}
                        className="bg-[#ffdad6]/40 text-[#b81a1a] text-[10px] font-extrabold tracking-wider uppercase px-2.5 py-1 rounded-full border border-[#ffb4a8]/30"
                      >
                        {tg}
                      </span>
                    ))}
                  </div>
                </div>


              </div>
            </div>
          ))}
        </div>
      ) : (
        /* List layout view alternative */
        <div className="flex flex-col gap-3">
          {filtered.map((session) => (
            <div
              key={session.id}
              onClick={() => onOpenSession(session.rawTask)}
              className="flex items-center justify-between p-4 bg-white border border-[#e7bcbb]/40 hover:border-[#f62440]/55 rounded-xl cursor-pointer hover:shadow-xs transition-all"
            >
              <div className="flex items-center gap-4">
                <img
                  src={session.thumbnail}
                  alt=""
                  referrerPolicy="no-referrer"
                  className="w-14 h-11 object-cover rounded-md border border-[#e7bcbb]/20 shrink-0"
                />
                <div>
                  <h3 className="font-bold text-sm text-[#1d1c18] font-display">{session.title}</h3>
                  <p className="text-xs text-[#5d5a55] mt-1 font-medium">
                    Duration: {session.duration} • Speaker: <b className="text-[#1d1c18]">{session.speaker}</b>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="hidden sm:flex gap-1">
                  {session.tags.map((tg, idx) => (
                    <span key={idx} className="bg-[#f2ede6] text-[#554428] px-2 py-0.5 rounded-sm text-[10px] uppercase font-bold">
                      {tg}
                    </span>
                  ))}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenSession(session.rawTask);
                  }}
                  className="bg-[#f62440] hover:bg-[#bb0028] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all cursor-pointer border-0 outline-none"
                >
                  Open
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      </div>
    </div>
  );
}
