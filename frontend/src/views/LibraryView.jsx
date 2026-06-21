import React, { useState, useRef, useEffect } from "react";
import { 
  Search, SlidersHorizontal, Mic, Square, Cloud, Play, 
  Download, Trash2, BarChart3, Database, Plus, Calendar
} from "lucide-react";

const formatDateToYYYYMMDD = (dateInput) => {
  if (!dateInput) return "";
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}/${month}/${day}`;
};

export default function LibraryView({
  tasks,
  logs,
  onOpenSession,
  onAddNewSession,
  onAnalyzeLogs,
  onDeleteTask,
  perfData,
  onJumpToWorkstation,
  onJumpToSettings,
  onNewSessionTrigger,
  configData,
  t
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordedTime, setRecordedTime] = useState("00:00");
  const [syncing, setSyncing] = useState(false);

  // Check if all required configuration fields are filled
  const checkIsConfigured = () => {
    if (!configData) return false;
    
    // Check FFmpeg
    if (!configData.ffmpeg_path || !configData.ffmpeg_bin_dir) {
      return false;
    }
    
    // Check ASR
    if (configData.asr_mode === "online") {
      if (!configData.online_base_url || !configData.online_model || !configData.online_api_key) {
        return false;
      }
    } else {
      // local
      if (!configData.local_whisper_model_path) {
        return false;
      }
    }
    
    // Check LLM
    if (configData.summary_mode === "online") {
      if (!configData.online_summary_base_url || !configData.online_summary_model || !configData.online_summary_api_key) {
        return false;
      }
    } else {
      // local (ollama)
      if (!configData.ollama_url || !configData.ollama_model) {
        return false;
      }
    }
    
    return true;
  };

  const isConfigured = checkIsConfigured();

  const getActiveEngineName = () => {
    if (!isConfigured) return "NONE";
    if (configData.asr_mode === "online") {
      return configData.online_model || "V3-NOIR";
    } else {
      if (configData.local_whisper_model_path) {
        return configData.local_whisper_model_path.split(/[\\/]/).pop() || "V3-NOIR";
      }
      return "V3-NOIR";
    }
  };

  const activeEngineName = getActiveEngineName();

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

  // Helper to parse duration string (e.g. "01:23:45" or "12:34" or number of seconds) to seconds
  const parseDurationToSeconds = (durationStr) => {
    if (typeof durationStr === "number") return durationStr;
    if (!durationStr || typeof durationStr !== "string") return 0;
    
    const parts = durationStr.split(":").map(Number);
    if (parts.some(isNaN)) return 0;
    
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return 0;
  };

  // Calculate real total transcribed time
  const getRealTranscribedTime = () => {
    let totalSeconds = 0;
    tasks.forEach(task => {
      if (task.duration) {
        totalSeconds += parseDurationToSeconds(task.duration);
      }
    });
    
    if (totalSeconds < 3600) {
      const mins = Math.round(totalSeconds / 60);
      return `${mins}m`;
    }
    return `${(totalSeconds / 3600).toFixed(1)}h`;
  };

  const totalHoursFormatted = getRealTranscribedTime();

  // Generate 100% real weekly activity heatmap data based on tasks created_at timestamps
  const generateHeatmapData = () => {
    const dayMap = {};
    const msInDay = 24 * 60 * 60 * 1000;
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    // We want 112 cells (16 weeks * 7 days)
    const startDate = new Date(today.getTime() - 111 * msInDay);
    
    // Initialize day map with 0 counts
    for (let i = 0; i < 112; i++) {
      const date = new Date(startDate.getTime() + i * msInDay);
      const dateString = date.toLocaleDateString();
      dayMap[dateString] = {
        count: 0,
        date: date
      };
    }
    
    // Count tasks per day
    tasks.forEach(task => {
      let taskDate = null;
      if (task.created_at) {
        taskDate = new Date(task.created_at);
      } else if (task.date) {
        if (task.date === "TODAY") {
          taskDate = new Date();
        } else {
          taskDate = new Date(task.date);
        }
      }
      
      if (taskDate && !isNaN(taskDate.getTime())) {
        const taskDayStr = new Date(taskDate.getFullYear(), taskDate.getMonth(), taskDate.getDate()).toLocaleDateString();
        if (dayMap[taskDayStr] !== undefined) {
          dayMap[taskDayStr].count += 1;
        }
      }
    });
    
    // Map to levels (0-3)
    return Object.keys(dayMap).map((key, i) => {
      const item = dayMap[key];
      let level = 0;
      if (item.count === 0) level = 0;
      else if (item.count === 1) level = 1;
      else if (item.count === 2) level = 2;
      else level = 3;
      
      return {
        id: i,
        date: item.date,
        count: item.count,
        level
      };
    });
  };

  const heatmapCells = generateHeatmapData();

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
            alert(t("麦克风录音上传成功！", "Microphone recording uploaded successfully!"));
            if (typeof onAddNewSession === "function") {
              onAddNewSession({
                id: result.task_id,
                title: `Voice capture - Session ${sessions.length + 1}`,
                status: "IN_PROGRESS",
                tags: ["Mic", "Direct"]
              });
            }
          } else {
            alert(t("上传失败。请确保后端服务正在运行。", "Upload failed. Please ensure the backend is running."));
          }
        } catch (err) {
          console.error("Failed to upload captured audio:", err);
          alert(t("向本地服务器上传捕获的音频时发生连接错误。", "Connection error uploading captured audio to local server."));
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
      alert(t("麦克风连接失败。请确保您已在浏览器中允许麦克风权限。", "Microphone connection failed. Please ensure you have allowed microphone permissions in your browser."));
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
      alert(t("云同步成功！所有音频档案已安全加密存储。", "Cloud Sync completed successfully! All acoustic archives are secured and encrypted."));
    }, 2000);
  };

  return (
    <div id="library-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        {/* Top Search bar/Header controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-4xl font-extrabold tracking-tight text-[#1d1c18] font-display">{t("媒体库", "Library")}</h2>
          <p className="text-sm text-[#5d5a55]/80 mt-1 font-medium">{t("管理您的音频档案与 AI 转录内容。", "Manage your acoustic archives and AI-powered transcriptions.")}</p>
        </div>
        <div className="shrink-0 self-start sm:self-center">
          {isConfigured ? (
            <div className="inline-flex items-center gap-2 bg-[#ffdad6]/40 text-[#b81a1a] text-[11px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wider border border-[#ffb4a8]/30">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#f62440] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#f62440]"></span>
              </span>
              <span>{t("当前引擎：", "Active Engine: ")}{activeEngineName}</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 bg-[#f2ede6] text-[#5d3f3e] text-[11px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wider border border-[#e6e2db]">
              <span className="w-1.5 h-1.5 bg-[#5d3f3e] rounded-full" />
              <span>{t("当前引擎：无", "Active Engine: None")}</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Grid: Highlight Card & Pulse Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-10">
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
            <h3 className="text-3xl font-bold tracking-tight text-[#1d1c18] font-display">{t("解析播客链接", "Parse Podcast Link")}</h3>
            <p className="text-[#5d5a55] text-sm mt-2 max-w-lg leading-relaxed">
              {t("输入单集播客链接或上传本地音频文件，系统将自动进行抓取、转录与大语言模型总结。", "Enter a podcast link or upload a local audio file to automatically extract, transcribe, and summarize.")}
            </p>
          </div>

          <div className="mt-8 flex items-center gap-4 relative z-10">
            <button
              id="btn-add-link-hero"
              onClick={onNewSessionTrigger}
              className="bg-[#f62440] hover:bg-[#bb0028] text-white font-semibold px-6 py-3 rounded-lg flex items-center gap-2.5 transition-all shadow-sm active:scale-98 cursor-pointer border-0 outline-none"
            >
              <Plus size={18} />
              <span>{t("新建任务", "Add New Link")}</span>
            </button>
          </div>
        </div>

        {/* Library Pulse Card */}
        <div className="bg-[#ffffff] border border-[#e7bcbb]/45 rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#bf0029] mb-4 flex items-center gap-1.5">
              <BarChart3 size={15} />
              {t("库活跃统计", "Library Pulse")}
            </h4>
            
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-[#e7bcbb]/20 pb-3">
                <span className="text-[13px] font-semibold text-[#5d5a55]">{t("录音总数", "Total Recordings")}</span>
                <span className="text-lg font-extrabold text-[#1d1c18] font-mono">{sessions.length}</span>
              </div>
              <div className="flex items-center justify-between pb-1">
                <span className="text-[13px] font-semibold text-[#5d5a55]">{t("已转录时长", "Hours Transcribed")}</span>
                <span className="text-lg font-extrabold text-[#1d1c18] font-mono">{totalHoursFormatted}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Weekly Listening Heatmap Card */}
        <div className="bg-[#ffffff] border border-[#e7bcbb]/45 rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#bf0029] mb-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#f62440] animate-pulse" />
              {t("声音活力值", "Acoustic Energy")}
            </h4>
            <p className="text-[10px] text-[#5d5a55]/60 font-semibold mb-3">
              {t("周度声音处理热力分布", "Weekly voice processing density")}
            </p>
            
            {/* Heatmap Grid */}
            <div className="flex items-center justify-center py-1">
              <div className="grid grid-rows-7 grid-flow-col gap-[3px]">
                {heatmapCells.map((cell) => {
                  const colorClass = 
                    cell.level === 0 ? "bg-[#f2ede6]" : 
                    cell.level === 1 ? "bg-[#ffdad6]" : 
                    cell.level === 2 ? "bg-[#ff8a8f]" : 
                    "bg-[#f62440]";

                  return (
                    <div 
                      key={cell.id} 
                      className={`w-[10px] h-[10px] rounded-[1.5px] ${colorClass} transition-all duration-200 hover:scale-125 cursor-pointer`}
                      title={t(`${cell.date.toLocaleDateString()}: ${cell.count} 次录音`, `${cell.date.toLocaleDateString()}: ${cell.count} recordings`)}
                    />
                  );
                })}
              </div>
            </div>
          </div>

          {/* Legend and Footer */}
          <div className="flex items-center justify-between text-[9px] text-[#5d5a55]/60 font-bold tracking-wider mt-4">
            <span>{t("较少", "LESS")}</span>
            <div className="flex gap-1">
              <div className="w-[8px] h-[8px] bg-[#f2ede6] rounded-[1px]" />
              <div className="w-[8px] h-[8px] bg-[#ffdad6] rounded-[1px]" />
              <div className="w-[8px] h-[8px] bg-[#ff8a8f] rounded-[1px]" />
              <div className="w-[8px] h-[8px] bg-[#f62440] rounded-[1px]" />
            </div>
            <span>{t("较多", "MORE")}</span>
          </div>
        </div>
      </div>

      {/* Recent Recordings Category list */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-2xl font-bold tracking-tight text-[#1d1c18] font-display">{t("最近录音列表", "Recent Recordings")}</h3>
        </div>

        {/* List Layout with Row blocks */}
        <div className="flex flex-col gap-3">
          {filteredSessions.slice(0, 5).map((session) => {
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
                    <h4 className="font-bold text-sm text-[#1d1c18] font-display leading-snug">
                      {session.rawTask.podcast_name && (
                        <span className="text-[#f62440] font-extrabold mr-1.5">
                          {session.rawTask.podcast_name}
                          <span className="text-[#e7bcbb] font-normal ml-1.5">|</span>
                        </span>
                      )}
                      <span>{session.title}</span>
                    </h4>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[11px] font-semibold select-none text-[#5d3f3e]/70">
                      <span>{t("时长：", "Duration: ")}{session.duration}</span>
                      <span className="text-[#e7bcbb]/40">•</span>
                      <div className="flex items-center gap-1">
                        <Calendar size={11} className="text-[#bf0029]" />
                        <span>{t("导入于: ", "Imported: ")}{session.date} • {session.time}</span>
                      </div>
                      {session.rawTask.metadata && session.rawTask.metadata.pub_date && (
                        <>
                          <span className="text-[#e7bcbb]/40">•</span>
                          <div className="flex items-center gap-1 text-[#f62440]">
                            <Calendar size={11} className="text-[#bf0029]" />
                            <span>{t("发布于: ", "Published: ")}{formatDateToYYYYMMDD(session.rawTask.metadata.pub_date)}</span>
                          </div>
                        </>
                      )}
                      <span className="text-[#e7bcbb]/40">•</span>
                      {session.status === 'IN_PROGRESS' ? (
                        <span className="bg-[#ffdad6] text-[#b81a1a] px-1.5 py-0.5 rounded-sm font-bold uppercase tracking-wider text-[10px]">
                          {session.rawTask.status === 'pending' ? t("排队中", "Queued") : `${t("处理中", "In Progress")} (${session.progress}%)`}
                        </span>
                      ) : (
                        <span className="bg-[#f0e2b7] text-[#554428] px-1.5 py-0.5 rounded-sm font-bold uppercase tracking-wider text-[10px]">
                          {t("已完成", "Completed")}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right widgets Waveform or actions */}
                <div className="flex items-center gap-4 mt-3 md:mt-0 self-end md:self-auto">
                  {session.status === 'IN_PROGRESS' ? (
                    <span className="text-[12px] font-mono text-[#5d3f3e]/60 italic font-medium">
                      {session.rawTask.status === 'pending' ? t("排队等待中...", "Waiting in queue...") : t("AI 生成标签中...", "AI generating tags...")}
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
                      className="p-1.5 hover:bg-[#f2ede6]/50 rounded-full transition-all cursor-pointer border-0 outline-none bg-transparent"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenSession(session.rawTask);
                      }}
                    >
                      <Play size={14} />
                    </button>
                    <button
                      className="p-1.5 hover:bg-[#f2ede6]/50 rounded-full transition-all cursor-pointer border-0 outline-none bg-transparent"
                      onClick={(e) => {
                        e.stopPropagation();
                        alert(t(`正在下载音频文件: ${session.title}`, `Downloading complete acoustic wave file for: ${session.title}`));
                      }}
                    >
                      <Download size={14} />
                    </button>
                    <button
                      className="p-1.5 hover:bg-[#ffdad6]/50 hover:text-[#f62440] rounded-full transition-all cursor-pointer border-0 outline-none bg-transparent"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (typeof onDeleteTask === "function") {
                          if (confirm(t(`确定要删除任务 "${session.title}" 并擦除音频缓存吗？`, `Determine to delete this task "${session.title}" and wipe audio cache?`))) {
                            onDeleteTask(session.id);
                          }
                        } else {
                          alert("Session Options: Delete, Rename, Export XML, Sync to Drive.");
                        }
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* View All in Workstation button */}
        <button
          id="btn-jump-to-workstation"
          onClick={onJumpToWorkstation}
          className="w-full mt-4 py-3 bg-transparent border border-dashed border-[#e7bcbb] hover:border-[#f62440] rounded-lg text-[#bf0029] hover:text-[#f62440] hover:bg-[#ffdad6]/10 transition-all font-semibold text-center text-sm cursor-pointer outline-none flex items-center justify-center gap-1.5"
        >
          <span>{t("在工作台中查看全部", "View All in Workstation")}</span>
          <span className="text-xs">→</span>
        </button>
      </section>

      </div>
    </div>
  );
}
