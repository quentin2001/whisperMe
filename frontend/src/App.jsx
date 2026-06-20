import React, { useState, useEffect, useRef } from "react";
import Sidebar from "./components/Sidebar";
import LibraryView from "./views/LibraryView";
import WorkstationView from "./views/WorkstationView";
import PodcastDetailView from "./views/PodcastDetailView";
import SettingsView from "./views/SettingsView";
import { initialLogs } from "./data.js";

const BACKEND_URL = "http://127.0.0.1:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard"); // 'dashboard', 'workstation', 'detail', 'config'
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [newUrl, setNewUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);
  const [isAudioMissing, setIsAudioMissing] = useState(false);

  // Audio Playback states
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [volume, setVolume] = useState(0.8);

  const [perfData, setPerfData] = useState(null);

  const [configData, setConfigData] = useState({
    ffmpeg_path: "",
    ffmpeg_bin_dir: "",
    local_whisper_model_path: "",
    hf_token: "",
    ollama_url: "",
    ollama_model: "",
    smtp_server: "",
    smtp_port: 465,
    smtp_username: "",
    smtp_password: "",
    smtp_sender: "",
    notification_email: "",
    enable_win_notification: true,
    enable_email_notification: false,
    asr_mode: "local",
    online_api_key: "",
    online_base_url: "",
    online_model: "",
    summary_mode: "local",
    online_summary_api_key: "",
    online_summary_base_url: "",
    online_summary_model: "",
    enable_llm_semantic_sewing: false,
    webhook_url: "",
    custom_storage_dir: ""
  });
  const [asrMode, setAsrMode] = useState("online");

  // Local storage audit logs
  const [logs, setLogs] = useState(() => {
    const saved = localStorage.getItem("whisperme_logs");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return initialLogs;
      }
    }
    return initialLogs;
  });

  const fileInputRef = useRef(null);
  const audioPlayerRef = useRef(null);
  const activeTaskRef = useRef(null);

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setTasks(data);
        }
      }
    } catch (e) {
      console.error("无法获取任务列表:", e);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`);
      const data = await res.json();
      if (data) {
        setConfigData(data);
      }
    } catch (e) {
      console.error("无法加载系统配置:", e);
    }
  };

  const fetchPerformance = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/performance`);
      if (res.status === 200) {
        const data = await res.json();
        setPerfData(data);
      }
    } catch (e) {
      console.error("无法加载性能数据:", e);
    }
  };

  const fetchTaskDetail = async (id, isSilent = false) => {
    if (!isSilent) setDetailLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${id}`);
      if (res.status === 200) {
        const data = await res.json();
        setActiveTask(data);
      }
    } catch (e) {
      console.error("获取任务详情失败:", e);
    } finally {
      if (!isSilent) setDetailLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    fetchConfig();
    fetchPerformance();
    const interval = setInterval(fetchTasks, 4000);
    const perfInterval = setInterval(fetchPerformance, 5000);
    return () => {
      clearInterval(interval);
      clearInterval(perfInterval);
    };
  }, []);

  useEffect(() => {
    setIsAudioMissing(false);
    if (activeTaskId) {
      fetchTaskDetail(activeTaskId);
      const detailInterval = setInterval(() => {
        const tObj = activeTaskRef.current;
        if (tObj && (tObj.status === "downloading" || tObj.status === "transcribing" || tObj.status === "summarizing")) {
          fetchTaskDetail(activeTaskId, true);
        }
      }, 3000);
      return () => clearInterval(detailInterval);
    } else {
      setActiveTask(null);
    }
  }, [activeTaskId]);

  useEffect(() => {
    activeTaskRef.current = activeTask;
  }, [activeTask]);

  const handleCreateTask = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!newUrl.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: newUrl.trim(), asr_mode: asrMode })
      });
      if (res.status === 200) {
        setNewUrl("");
        setIsIngestModalOpen(false);
        fetchTasks();
      }
    } catch (e) {
      alert("发起任务失败，请检查后端服务是否启动！");
    } finally {
      setLoading(false);
    }
  };

  const handleLocalFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || uploading) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("asr_mode", asrMode);

      const res = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        setIsIngestModalOpen(false);
        fetchTasks();
        alert("音频文件导入成功！");
      } else {
        alert("文件上传失败。");
      }
    } catch (err) {
      console.error(err);
      alert("上传出错：" + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteTask = async (id) => {
    try {
      await fetch(`${BACKEND_URL}/api/tasks/${id}`, { method: "DELETE" });
      fetchTasks();
      if (activeTaskId === id) {
        setActiveTaskId(null);
        setActiveTab("dashboard");
      }
    } catch (e) {
      alert("删除失败");
    }
  };

  const handleSaveConfig = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configData)
      });
      if (res.status === 200) {
        alert("配置已成功更新！");
        fetchConfig();
      }
    } catch (e) {
      alert("保存配置失败");
    }
  };

  const handleConfigChange = (key, value) => {
    setConfigData(prev => ({ ...prev, [key]: value }));
  };

  const togglePlay = () => {
    if (!audioPlayerRef.current) return;
    if (isPlaying) {
      audioPlayerRef.current.pause();
    } else {
      audioPlayerRef.current.play().catch(err => console.log("播放被浏览器拦截:", err));
    }
  };

  const handleProgressChange = (e) => {
    if (!audioPlayerRef.current || !duration) return;
    const time = parseFloat(e.target.value);
    audioPlayerRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const handleAnalyzeAllLogs = () => {
    alert("Analyzing logs across all session records to find action items... Synthesis calculations loaded.");
    const newLog = {
      id: "9912-S",
      text: "Global action trace compiled. Synthesis confirms latency trends is stable and workspace frame rate of 60fps achieved.",
      tags: ["SYNTHESIS", "REPORTS"],
      timeAgo: "Just now",
      category: "PLANNING"
    };
    const updatedLogs = [newLog, ...logs];
    localStorage.setItem("whisperme_logs", JSON.stringify(updatedLogs));
    setLogs(updatedLogs);
  };

  const handleResetData = () => {
    localStorage.removeItem("whisperme_logs");
    setLogs(initialLogs);
    setActiveTaskId(null);
    setActiveTab("dashboard");
    alert("Local workspace memory wiped cleanly! Restored default recordings.");
  };

  return (
    <div id="application-layout-frame" className="flex h-screen w-screen overflow-hidden bg-[#fef9f2]">
      {/* Persistent Left Menu Sidebar */}
      <Sidebar
        currentTab={activeTab === "dashboard" ? "library" : activeTab === "workstation" ? "workstation" : "settings"}
        onTabChange={(tab) => {
          if (tab === "library") setActiveTab("dashboard");
          else if (tab === "workstation") setActiveTab("workstation");
          else if (tab === "settings") setActiveTab("config");
          setActiveTaskId(null); // Close detail view when switching top-level tabs
        }}
        onNewSessionTrigger={() => setIsIngestModalOpen(true)}
        onShowLogsTrigger={() => {
          if (activeTab !== "dashboard") {
            setActiveTab("dashboard");
          }
          setTimeout(() => {
            const logsSection = document.getElementById("btn-analyze-logs");
            if (logsSection) {
              logsSection.scrollIntoView({ behavior: "smooth" });
            }
          }, 200);
        }}
        perfData={perfData}
      />

      {/* Main split screens panel area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#fef9f2]" id="primary-content-workspace">
        {activeTab === "detail" && activeTask ? (
          /* Active full screen transcript parser */
          <PodcastDetailView
            activeTask={activeTask}
            audioPlayerRef={audioPlayerRef}
            isPlaying={isPlaying}
            togglePlay={togglePlay}
            progress={duration > 0 ? (currentTime / duration) * 100 : 0}
            handleProgressChange={handleProgressChange}
            currentTime={currentTime}
            duration={duration}
            playbackRate={playbackRate}
            setPlaybackRate={setPlaybackRate}
            volume={volume}
            setVolume={setVolume}
            onRefreshTask={() => fetchTaskDetail(activeTask.id, true)}
            onBack={() => {
              setActiveTaskId(null);
              setActiveTab("dashboard");
            }}
          />
        ) : (
          /* Tab contents switch */
          <>
            {activeTab === "dashboard" && (
              <LibraryView
                tasks={tasks}
                logs={logs}
                perfData={perfData}
                onOpenSession={(task) => {
                  setActiveTaskId(task.id);
                  setActiveTab("detail");
                }}
                onAddNewSession={(newTask) => {
                  fetchTasks();
                  const newLog = {
                    id: `${Math.floor(1000 + Math.random() * 9000)}-W`,
                    text: `Captured dynamic mic audio input. Saved trace successfully inside local warehouse registers.`,
                    tags: ["RAW WAVE", "MIC"],
                    timeAgo: "Just now",
                    category: "TECH"
                  };
                  const updatedLogs = [newLog, ...logs];
                  localStorage.setItem("whisperme_logs", JSON.stringify(updatedLogs));
                  setLogs(updatedLogs);
                }}
                onAnalyzeLogs={handleAnalyzeAllLogs}
                onDeleteTask={handleDeleteTask}
              />
            )}

            {activeTab === "workstation" && (
              <WorkstationView
                tasks={tasks}
                onOpenSession={(task) => {
                  setActiveTaskId(task.id);
                  setActiveTab("detail");
                }}
                onNewSessionTrigger={() => setIsIngestModalOpen(true)}
              />
            )}

            {activeTab === "config" && (
              <SettingsView 
                configData={configData}
                handleConfigChange={handleConfigChange}
                handleSaveConfig={handleSaveConfig}
                onResetData={handleResetData} 
              />
            )}
          </>
        )}
      </main>

      {/* Hidden Audio Player for Detail View */}
      {activeTab === "detail" && activeTask && activeTask.audio_url && (
         <audio 
            ref={audioPlayerRef}
            src={`${BACKEND_URL}${activeTask.audio_url}`}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
            onDurationChange={(e) => setDuration(e.target.duration)}
            onCanPlay={(e) => { e.target.playbackRate = playbackRate; }}
            onError={() => setIsAudioMissing(true)}
            className="hidden"
         />
      )}

      {/* Ingest Modal */}
      {isIngestModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[150] p-6 animate-fade-in">
          <div className="bg-white border border-[#e7bcbb]/50 rounded-xl max-w-lg w-full relative flex flex-col shadow-2xl">
            <div className="p-6 border-b border-[#e7bcbb]/30 flex justify-between items-center bg-[#f9f3ea]/50 rounded-t-xl">
              <h3 className="text-xl font-bold font-display text-[#1d1c18] flex items-center gap-2">
                New Transcription
              </h3>
              <button onClick={() => setIsIngestModalOpen(false)} className="text-[#5d3f3e]/60 hover:text-[#f62440] transition-colors cursor-pointer border-0 bg-transparent text-lg">
                ✕
              </button>
            </div>
            
            <div className="p-6 flex flex-col gap-4">
              <p className="text-sm text-[#5d5a55]/85">
                Enter an episode link or upload a local audio file to initiate processing.
              </p>

              <form onSubmit={handleCreateTask} className="flex flex-col gap-4">
                <input 
                  type="text" 
                  placeholder="Paste podcast URL..." 
                  value={newUrl} 
                  onChange={(e) => setNewUrl(e.target.value)} 
                  disabled={loading}
                  className="w-full bg-white border border-[#e7bcbb]/40 focus:border-[#f62440] focus:ring-1 focus:ring-[#f62440] rounded-lg px-4 py-3 text-sm text-[#1d1c18] placeholder-[#5d3f3e]/40 outline-none transition-colors"
                />
                
                <div className="flex gap-4 items-center">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#5d3f3e]/70">ASR MODE:</span>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1d1c18]">
                    <input type="radio" checked={asrMode === "online"} onChange={() => setAsrMode("online")} className="accent-[#f62440]" /> ONLINE API
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1d1c18]">
                    <input type="radio" checked={asrMode === "local"} onChange={() => setAsrMode("local")} className="accent-[#f62440]" /> LOCAL OFFLINE
                  </label>
                </div>

                <button 
                  type="submit" 
                  disabled={loading || !newUrl.trim()} 
                  className="w-full bg-[#f62440] hover:bg-[#bb0028] text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 cursor-pointer border-0 outline-none"
                >
                  {loading ? "INITIATING..." : "FETCH AUDIO"}
                </button>
              </form>

              <div className="flex items-center gap-4 text-[#e7bcbb] select-none my-2">
                <div className="flex-1 h-[1px] bg-current"></div>
                <span className="text-[10px] uppercase tracking-widest text-[#5d3f3e]/60 font-bold">OR UPLOAD LOCAL</span>
                <div className="flex-1 h-[1px] bg-current"></div>
              </div>

              <div>
                <button 
                  onClick={() => fileInputRef.current?.click()} 
                  disabled={uploading || loading} 
                  className="w-full border-2 border-dashed border-[#e7bcbb] hover:border-[#f62440] hover:bg-[#ffdad6]/10 text-[#5d3f3e]/70 hover:text-[#f62440] py-8 rounded-xl flex flex-col items-center justify-center gap-2 transition-colors disabled:opacity-50 cursor-pointer bg-transparent"
                >
                  <span className="text-3xl mb-1">☁️</span>
                  <span className="text-xs font-bold">{uploading ? "UPLOADING..." : "BROWSE FILES"}</span>
                </button>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleLocalFileUpload} 
                  accept=".mp3,.wav,.m4a,.aac,.flac,.ogg" 
                  className="hidden" 
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
