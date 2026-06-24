import React, { useState, useRef, useEffect } from "react";
import { 
  List, LayoutGrid, Calendar, Play, MoreVertical, ChevronDown, Trash2 
} from "lucide-react";

const parseDurationToMinutes = (durationStr) => {
  if (!durationStr || typeof durationStr !== "string") return 0;
  const parts = durationStr.split(":").map(Number);
  if (parts.some(isNaN)) return 0;
  if (parts.length === 3) {
    return parts[0] * 60 + parts[1] + parts[2] / 60;
  } else if (parts.length === 2) {
    return parts[0] + parts[1] / 60;
  }
  return 0;
};

function CustomDropdown({ label, value, options, onChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => opt.value === value) || options[0];

  return (
    <div className="flex items-center gap-2" ref={dropdownRef}>
      <span className="text-[11px] font-extrabold text-[var(--text-secondary)]/60 uppercase tracking-widest">{label}</span>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`w-36 flex items-center justify-between bg-[var(--bg-hover)] border px-3 py-1.5 rounded-lg text-xs font-bold text-[var(--text-secondary)] transition-all text-left outline-none cursor-pointer ${
            isOpen 
              ? "border-[#f62440] ring-1 ring-[#f62440]" 
              : "border-[var(--border-primary)]/20 hover:border-[#f62440]/50"
          }`}
        >
          <span className="truncate">{selectedOption.label}</span>
          <ChevronDown size={14} className={`text-[var(--text-secondary)]/60 transition-transform duration-200 ${isOpen ? "rotate-180 text-[var(--accent-red)]" : ""}`} />
        </button>

        {isOpen && (
          <div className="absolute left-0 mt-1 w-36 bg-[var(--bg-hover)] border border-[var(--border-primary)]/40 rounded-lg shadow-lg z-50 py-0 overflow-hidden animate-fade-in">
            {options.map((opt) => {
              const active = opt.value === value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    onChange(opt.value);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-4 py-2.5 text-xs font-bold transition-all cursor-pointer border-0 outline-none block ${
                    active 
                      ? "bg-[var(--accent-red)] text-white" 
                      : "text-[var(--text-secondary)] bg-transparent hover:bg-[var(--accent-red-light)]/40 hover:text-[var(--accent-red)]"
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}



const formatDateToYYYYMMDD = (dateInput) => {
  if (!dateInput) return "";
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}/${month}/${day}`;
};

const isWithinDays = (dateInput, days) => {
  if (!dateInput) return false;
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return false;
  const now = new Date("2026-06-22T01:36:20+08:00");
  const diffTime = now.getTime() - d.getTime();
  const diffDays = diffTime / (1000 * 60 * 60 * 24);
  return diffDays <= days;
};

export default function WorkstationView({
  tasks,
  onOpenSession,
  onNewSessionTrigger,
  onDeleteTask,
  t
}) {
  const [selectedSpeaker, setSelectedSpeaker] = useState("All");
  const [importedDateFilter, setImportedDateFilter] = useState("All Time");
  const [publishedDateFilter, setPublishedDateFilter] = useState("All Time");
  const [durationFilter, setDurationFilter] = useState("All");
  const [viewMode, setViewMode] = useState("grid");

  // Map backend tasks to UI sessions format
  const sessions = tasks.map((task, index) => {
    const defaultThumbs = [
      "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1516280440614-37939bbacd6a?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1507838153414-b4b713384a76?q=80&w=600&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop"
    ];

    let parsedDate = "TODAY";
    let parsedTime = "";
    if (task.created_at) {
      try {
        const d = new Date(task.created_at);
        if (!isNaN(d.getTime())) {
          parsedDate = formatDateToYYYYMMDD(d);
          parsedTime = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
      } catch (e) {
        console.error("Failed to parse created_at:", e);
      }
    }
    if (!parsedTime) {
      parsedTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    return {
      id: task.id,
      title: task.title || `Session ${index + 1}`,
      date: task.date || parsedDate,
      time: task.time || parsedTime,
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
    if (selectedSpeaker !== "All" && session.speaker !== selectedSpeaker) return false;
    
    if (durationFilter !== "All") {
      const minutes = parseDurationToMinutes(session.duration);
      if (durationFilter === "< 30m" && minutes >= 30) {
        return false;
      }
      if (durationFilter === "> 30m" && minutes < 30) {
        return false;
      }
    }

    if (importedDateFilter !== "All Time") {
      const days = importedDateFilter === "Last 7 Days" ? 7 : 30;
      if (!isWithinDays(session.rawTask.created_at, days)) {
        return false;
      }
    }

    if (publishedDateFilter !== "All Time") {
      const days = publishedDateFilter === "Last 7 Days" ? 7 : 30;
      if (!session.rawTask.metadata || !session.rawTask.metadata.pub_date) return false;
      if (!isWithinDays(session.rawTask.metadata.pub_date, days)) {
        return false;
      }
    }

    return true;
  });

  return (
    <div id="workstation-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        {/* Top Header controls */}
      <div className="mb-8">
        <h2 className="text-4xl font-extrabold tracking-tight text-[var(--text-primary)] font-display">{t("工作台", "Workstation")}</h2>
        <p className="text-sm text-[var(--text-muted)]/80 mt-1 font-medium">{t("在多轨可视化工作台中选择并解析您的音频档案。", "Select and parse any acoustic trace inside the advanced multi-track visualizer.")}</p>
      </div>

      {/* Filter toolbar */}
      <div className="bg-[var(--bg-secondary)]/50 border border-[var(--border-primary)]/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        {/* Left: Filter select controls */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Imported Date Filter */}
          <CustomDropdown 
            label={t("导入日期：", "Imported:")} 
            value={importedDateFilter} 
            onChange={(val) => setImportedDateFilter(val)}
            options={[
              { value: "All Time", label: t("全部时间", "All Time") },
              { value: "Last 7 Days", label: t("最近7天", "Last 7 Days") },
              { value: "Last 30 Days", label: t("Last 30 Days", "Last 30 Days") }
            ]}
          />

          <div className="h-4 w-[1px] bg-[#e7bcbb]/30 hidden sm:block" />

          {/* Published Date Filter */}
          <CustomDropdown 
            label={t("发布日期：", "Published:")} 
            value={publishedDateFilter} 
            onChange={(val) => setPublishedDateFilter(val)}
            options={[
              { value: "All Time", label: t("全部时间", "All Time") },
              { value: "Last 7 Days", label: t("最近7天", "Last 7 Days") },
              { value: "Last 30 Days", label: t("Last 30 Days", "Last 30 Days") }
            ]}
          />

          <div className="h-4 w-[1px] bg-[#e7bcbb]/30 hidden sm:block" />

          {/* Duration Filter */}
          <CustomDropdown 
            label={t("时长：", "Duration:")} 
            value={durationFilter} 
            onChange={(val) => setDurationFilter(val)}
            options={[
              { value: "All", label: t("全部", "All") },
              { value: "< 30m", label: t("30分钟以内", "Under 30 mins") },
              { value: "> 30m", label: t("30分钟以上", "Over 30 mins") }
            ]}
          />
        </div>

        {/* Right: Layout Switcher */}
        <div className="flex items-center gap-3 self-end sm:self-auto">
          {/* Layout controls toggle */}
          <div className="flex items-center bg-[var(--bg-hover)] p-0.5 rounded-lg border border-[var(--border-primary)]/20">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-md transition-all cursor-pointer border-0 outline-none ${
                viewMode === "grid" ? "bg-[var(--bg-card)] text-[var(--accent-red)]" : "text-[var(--text-secondary)]/60 bg-transparent"
              }`}
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-md transition-all cursor-pointer border-0 outline-none ${
                viewMode === "list" ? "bg-[var(--bg-card)] text-[var(--accent-red)]" : "text-[var(--text-secondary)]/60 bg-transparent"
              }`}
            >
              <List size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Grid or List of Available sessions */}
      {viewMode === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {filtered.map((session) => (
            <div
              key={session.id}
              onClick={() => onOpenSession(session.rawTask)}
              className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl overflow-hidden hover:border-[#f62440]/50 hover:shadow-sm transition-all flex flex-col group cursor-pointer"
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

                {/* Delete button indicator tag */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (typeof onDeleteTask === "function") {
                      if (confirm(t(`确定要删除任务 "${session.title}" 并擦除音频缓存吗？`, `Determine to delete this task "${session.title}" and wipe audio cache?`))) {
                        onDeleteTask(session.id);
                      }
                    }
                  }}
                  className="absolute top-3 left-3 bg-black/75 hover:bg-[var(--accent-red)] hover:text-white backdrop-blur-xs text-white/80 p-1.5 rounded-full transition-all border-0 outline-none cursor-pointer z-10"
                  title={t("删除任务", "Delete Task")}
                >
                  <Trash2 size={13} />
                </button>

                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div 
                    className="w-12 h-12 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white flex items-center justify-center rounded-full shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-all duration-300"
                  >
                    <Play size={18} fill="white" className="ml-0.5" />
                  </div>
                </div>
              </div>

              {/* Information body panel */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-start">
                    <h3 className="font-bold text-base text-[var(--text-primary)] font-display leading-snug group-hover:text-[var(--accent-red)] transition-colors w-full">
                      {session.rawTask.podcast_name && (
                        <span className="text-[var(--accent-red)] font-extrabold mr-1.5">
                          {session.rawTask.podcast_name}
                          <span className="text-[#e7bcbb] font-normal ml-1.5">|</span>
                        </span>
                      )}
                      <span>{session.title}</span>
                    </h3>
                  </div>

                  <div className="flex flex-col gap-1 text-[11px] text-[var(--text-muted)] mt-2 font-semibold select-none">
                    <div className="flex items-center gap-1.5">
                      <Calendar size={12} className="text-[var(--accent-red)]" />
                      <span title="进入系统时间">{t("导入于: ", "Imported: ")}{session.date}</span>
                    </div>
                    {session.rawTask.metadata && session.rawTask.metadata.pub_date && (
                      <div className="flex items-center gap-1.5 text-[var(--accent-red)]" title="播客本身发布时间">
                        <Calendar size={12} className="text-[var(--accent-red)]" />
                        <span>{t("发布于: ", "Published: ")}{(() => {
                          try {
                            const pd = new Date(session.rawTask.metadata.pub_date);
                            if (!isNaN(pd.getTime())) {
                              return pd.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' });
                            }
                          } catch(e) {}
                          return session.rawTask.metadata.pub_date;
                        })()}</span>
                      </div>
                    )}
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
              className="flex items-center justify-between p-4 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 hover:border-[#f62440]/55 rounded-xl cursor-pointer hover:shadow-xs transition-all"
            >
              <div className="flex items-center gap-4">
                <img
                  src={session.thumbnail}
                  alt=""
                  referrerPolicy="no-referrer"
                  className="w-14 h-11 object-cover rounded-md border border-[var(--border-primary)]/20 shrink-0"
                />
                <div>
                  <h3 className="font-bold text-sm text-[var(--text-primary)] font-display leading-snug">
                    {session.rawTask.podcast_name && (
                      <span className="text-[var(--accent-red)] font-extrabold mr-1.5">
                        {session.rawTask.podcast_name}
                        <span className="text-[#e7bcbb] font-normal ml-1.5">|</span>
                      </span>
                    )}
                    <span>{session.title}</span>
                  </h3>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-[11px] font-semibold text-[var(--text-muted)] select-none">
                    <span>{t("时长：", "Duration: ")}{session.duration}</span>
                    <span className="text-[#e7bcbb]/40">•</span>
                    <div className="flex items-center gap-1">
                      <Calendar size={11} className="text-[var(--accent-red)]" />
                      <span>{t("导入于: ", "Imported: ")}{session.date}</span>
                    </div>
                    {session.rawTask.metadata && session.rawTask.metadata.pub_date && (
                      <>
                        <span className="text-[#e7bcbb]/40">•</span>
                        <div className="flex items-center gap-1 text-[var(--accent-red)]">
                          <Calendar size={11} className="text-[var(--accent-red)]" />
                          <span>{t("发布于: ", "Published: ")}{formatDateToYYYYMMDD(session.rawTask.metadata.pub_date)}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenSession(session.rawTask);
                  }}
                  className="bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all cursor-pointer border-0 outline-none"
                >
                  {t("打开", "Open")}
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (typeof onDeleteTask === "function") {
                      if (confirm(t(`确定要删除任务 "${session.title}" 并擦除音频缓存吗？`, `Determine to delete this task "${session.title}" and wipe audio cache?`))) {
                        onDeleteTask(session.id);
                      }
                    }
                  }}
                  className="p-1.5 hover:bg-[var(--accent-red-light)]/50 text-[var(--text-secondary)]/60 hover:text-[var(--accent-red)] rounded-full transition-all cursor-pointer border-0 outline-none bg-transparent"
                  title={t("删除任务", "Delete Task")}
                >
                  <Trash2 size={15} />
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
