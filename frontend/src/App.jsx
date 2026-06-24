import React, { useState, useEffect, useRef } from "react";
import Sidebar from "./components/Sidebar";
import LibraryView from "./views/LibraryView";
import WorkstationView from "./views/WorkstationView";
import PodcastDetailView from "./views/PodcastDetailView";
import SettingsView from "./views/SettingsView";
import { initialLogs } from "./data.js";
import { API_BASE } from "./constants.js";

const BACKEND_URL = API_BASE;

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard"); // 'dashboard', 'workstation', 'detail', 'config'
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [detailSourceTab, setDetailSourceTab] = useState("dashboard"); // 'dashboard' or 'workstation'
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
  const [versionInfo, setVersionInfo] = useState({
    current_version: "1.0.0",
    latest_version: "1.0.0",
    has_update: false,
    release_url: "https://github.com/quentin2001/whisperMe/releases",
    release_notes: ""
  });

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
    asr_mode: "online",
    online_asr_provider: "mimo",
    online_api_key: "",
    online_base_url: "",
    online_model: "",
    custom_asr_endpoint: "",
    custom_asr_method: "POST",
    custom_asr_headers: "{}",
    custom_asr_body_template: "",
    custom_asr_response_jsonpath: "$.data.text",
    custom_asr_timestamp_jsonpath: "",
    custom_asr_audio_format: "mp3",
    custom_asr_chunk_duration: 60,
    summary_mode: "online",
    online_summary_api_key: "",
    online_summary_base_url: "",
    online_summary_model: "",
    enable_llm_semantic_sewing: false,
    webhook_url: "",
    custom_storage_dir: "",
    language: "en"
  });
  const t = (zh, en) => (configData.language === "en" ? en : zh);
  const [audioSource, setAudioSource] = useState("link");

  // Prompt 编辑状态
  const [promptData, setPromptData] = useState({
    prompt: ""
  });
  const [promptSaveStatus, setPromptSaveStatus] = useState("idle"); // 'idle' | 'saving' | 'saved' | 'error'

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
  const playbackPositions = useRef({});

  const [checkingVersion, setCheckingVersion] = useState(false);
  const fetchVersion = async (force = false) => {
    setCheckingVersion(true);
    try {
      const url = `${BACKEND_URL}/api/version/check` + (force ? "?force=true" : "");
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data.current_version) {
          setVersionInfo(data);
          if (force) {
            if (data.has_update) {
              alert(t(
                `发现新版本 v${data.latest_version}！已为您在设置页面顶部载入更新日志。`,
                `New version v${data.latest_version} found! Changelog has been loaded at the top of Settings.`
              ));
            } else {
              alert(t("当前已是最新版本！", "You are already on the latest version!"));
            }
          }
        }
      }
    } catch (e) {
      console.error("无法获取软件版本信息:", e);
      if (force) {
        alert(t(
          "检测更新失败，请稍后重试（可能触发了 GitHub API 速率限制）。",
          "Failed to check updates, please try again later (GitHub API rate limit might be exceeded)."
        ));
      }
    } finally {
      setCheckingVersion(false);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setTasks(data.filter(t => t && t.id));
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

  const fetchPrompt = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/prompt`);
      if (res.ok) {
        const data = await res.json();
        setPromptData(data);
      }
    } catch (e) {
      console.error("无法加载 Prompt 配置:", e);
    }
  };

  const handleSavePrompt = async () => {
    setPromptSaveStatus("saving");
    try {
      const res = await fetch(`${BACKEND_URL}/api/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(promptData)
      });
      if (res.ok) {
        setPromptSaveStatus("saved");
        setTimeout(() => setPromptSaveStatus("idle"), 3000);
      } else {
        setPromptSaveStatus("error");
      }
    } catch (e) {
      setPromptSaveStatus("error");
    }
  };

  const handleResetPrompt = () => {
    if (window.confirm(t("确定要恢复默认 Prompt 模板吗？这会覆盖您当前的输入。", "Are you sure you want to restore the default Prompt templates? This will overwrite your current configuration."))) {
      // Reset to empty, then fetch default from backend
      fetch(`${BACKEND_URL}/api/prompt/template/standard`)
        .then(res => res.json())
        .then(data => {
          setPromptData({ prompt: data.prompt || "" });
        })
        .catch(() => {
          setPromptData({ prompt: "" });
        });
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
    fetchVersion();
    fetchPrompt();
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
    setCurrentTime(0);
    setDuration(0);
    setIsPlaying(false);
    if (activeTaskId) {
      fetchTaskDetail(activeTaskId);
      const detailInterval = setInterval(() => {
        const tObj = activeTaskRef.current;
        if (tObj && (tObj.status === "downloading" || tObj.status === "transcribing" || tObj.status === "summarizing" || tObj.restoring)) {
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
        body: JSON.stringify({ url: newUrl.trim(), asr_mode: configData.asr_mode || "online" })
      });
      if (res.status === 200) {
        const result = await res.json();
        setNewUrl("");
        setIsIngestModalOpen(false);
        fetchTasks();
        if (result.warning) {
          alert(result.warning);
        }
      }
    } catch (e) {
      alert(t("发起任务失败，请检查后端服务是否启动！", "Failed to start task. Please check if the backend service is running!"));
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
      formData.append("asr_mode", configData.asr_mode || "online");

      const res = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const result = await res.json();
        setIsIngestModalOpen(false);
        fetchTasks();
        if (result.warning) {
          alert(result.warning);
        } else {
          alert(t("音频文件导入成功！", "Audio file imported successfully!"));
        }
      } else {
        alert(t("文件上传失败。", "File upload failed."));
      }
    } catch (err) {
      console.error(err);
      alert(t("上传出错：", "Upload error: ") + err.message);
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
      alert(t("删除失败", "Delete failed"));
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
        alert(t("配置已成功更新！", "Configuration updated successfully!"));
        fetchConfig();
      }
    } catch (e) {
      alert(t("保存配置失败", "Failed to save configuration"));
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
    alert(t("正在对所有单集记录进行日志分析以寻找行动项... 综合计算已加载。", "Analyzing logs across all session records to find action items... Synthesis calculations loaded."));
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

  const isConfigInvalid = () => {
    if (!configData) return true;
    // FFmpeg is auto-detected, no need to validate on frontend

    if (configData.asr_mode === "local") {
      if (!configData.local_whisper_model_path || !configData.hf_token) return true;
    } else if (configData.asr_mode === "online") {
      const provider = configData.online_asr_provider || "mimo";
      if (provider === "custom") {
        if (!configData.custom_asr_endpoint) return true;
      } else if (provider === "funasr") {
        if (!configData.online_base_url) return true;
      } else {
        // mimo / openai
        if (!configData.online_base_url || !configData.online_model || !configData.online_api_key) return true;
      }
    }
    
    if (configData.summary_mode === "local") {
      if (!configData.ollama_url || !configData.ollama_model) return true;
    } else if (configData.summary_mode === "online") {
      if (!configData.online_summary_base_url || !configData.online_summary_model || !configData.online_summary_api_key) return true;
    }
    return false;
  };

  const handleResetData = () => {
    localStorage.removeItem("whisperme_logs");
    setLogs(initialLogs);
    setActiveTaskId(null);
    setActiveTab("dashboard");
    alert(t("本地工作区内存已完全清除！已恢复默认录音。", "Local workspace memory wiped cleanly! Restored default recordings."));
  };

  return (
    <div id="application-layout-frame" className="flex h-screen w-screen overflow-hidden bg-[var(--bg-primary)] transition-colors duration-300">
      {/* Persistent Left Menu Sidebar */}
      <Sidebar
        versionInfo={versionInfo}
        isConfigInvalid={isConfigInvalid()}
        currentTab={
          activeTab === "dashboard"
            ? "library"
            : activeTab === "workstation"
            ? "workstation"
            : activeTab === "detail"
            ? (detailSourceTab === "workstation" ? "workstation" : "library")
            : "settings"
        }
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
        t={t}
      />

      {/* Main split screens panel area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[var(--bg-primary)] transition-colors duration-300" id="primary-content-workspace">
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
              setActiveTab(detailSourceTab === "workstation" ? "workstation" : "dashboard");
            }}
            t={t}
          />
        ) : (
          /* Tab contents switch */
          <>
            {activeTab === "dashboard" && (
              <LibraryView
                tasks={tasks}
                logs={logs}
                perfData={perfData}
                configData={configData}
                onJumpToWorkstation={() => setActiveTab("workstation")}
                onJumpToSettings={() => setActiveTab("config")}
                onNewSessionTrigger={() => setIsIngestModalOpen(true)}
                onOpenSession={(task) => {
                  setDetailSourceTab("dashboard");
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
                t={t}
              />
            )}

            {activeTab === "workstation" && (
              <WorkstationView
                tasks={tasks}
                onOpenSession={(task) => {
                  setDetailSourceTab("workstation");
                  setActiveTaskId(task.id);
                  setActiveTab("detail");
                }}
                onNewSessionTrigger={() => setIsIngestModalOpen(true)}
                onDeleteTask={handleDeleteTask}
                t={t}
              />
            )}

            {activeTab === "config" && (
              <SettingsView
                versionInfo={versionInfo}
                configData={configData}
                handleConfigChange={handleConfigChange}
                handleSaveConfig={handleSaveConfig}
                onResetData={handleResetData}
                promptData={promptData}
                setPromptData={setPromptData}
                promptSaveStatus={promptSaveStatus}
                handleSavePrompt={handleSavePrompt}
                handleResetPrompt={handleResetPrompt}
                onCheckVersion={fetchVersion}
                checkingVersion={checkingVersion}
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
            onTimeUpdate={(e) => {
                setCurrentTime(e.target.currentTime);
                if (activeTaskId) {
                    playbackPositions.current[activeTaskId] = e.target.currentTime;
                }
            }}
            onDurationChange={(e) => setDuration(e.target.duration)}
            onLoadedMetadata={(e) => {
                const savedPos = activeTaskId ? playbackPositions.current[activeTaskId] : 0;
                if (savedPos && savedPos > 0) {
                    e.target.currentTime = savedPos;
                    setCurrentTime(savedPos);
                }
            }}
            onCanPlay={(e) => { e.target.playbackRate = playbackRate; }}
            onError={() => setIsAudioMissing(true)}
            className="hidden"
         />
      )}

      {/* Ingest Modal */}
      {isIngestModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[150] p-6 animate-fade-in">
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/50 rounded-xl max-w-lg w-full relative flex flex-col shadow-2xl transition-colors duration-300">
            <div className="p-6 border-b border-[var(--border-primary)]/30 flex justify-between items-center bg-[var(--bg-secondary)]/50 rounded-t-xl">
              <h3 className="text-xl font-bold font-display text-[var(--text-primary)] flex items-center gap-2">
                {t("新建转录任务", "New Transcription")}
              </h3>
              <button onClick={() => setIsIngestModalOpen(false)} className="text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors cursor-pointer border-0 bg-transparent text-lg">
                ✕
              </button>
            </div>

            <div className="p-6 flex flex-col gap-4">
              <p className="text-sm text-[var(--text-muted)]">
                {t("选择音频来源：粘贴在线链接或上传本地文件。", "Choose audio source: paste a link or upload a local file.")}
              </p>

              <div className="flex gap-4 items-center">
                <span className="text-xs font-bold uppercase tracking-widest text-[var(--text-tertiary)]">{t("音频来源：", "AUDIO SOURCE:")}</span>
                <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[var(--text-primary)]">
                  <input type="radio" checked={audioSource === "link"} onChange={() => setAudioSource("link")} className="w-3.5 h-3.5 text-[var(--accent-red)] focus:ring-[var(--accent-red)] focus:ring-offset-0 cursor-pointer" /> {t("在线链接", "LINK")}
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[var(--text-primary)]">
                  <input type="radio" checked={audioSource === "file"} onChange={() => setAudioSource("file")} className="w-3.5 h-3.5 text-[var(--accent-red)] focus:ring-[var(--accent-red)] focus:ring-offset-0 cursor-pointer" /> {t("本地文件", "LOCAL FILE")}
                </label>
              </div>

              {audioSource === "link" ? (
                <form onSubmit={handleCreateTask} className="flex flex-col gap-4">
                  <input
                    type="text"
                    placeholder={t("粘贴播客 URL...", "Paste podcast URL...")}
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    disabled={loading}
                    className="w-full bg-[var(--bg-card)] border border-[var(--border-primary)]/40 focus:border-[var(--accent-red)] focus:ring-1 focus:ring-[var(--accent-red)] rounded-lg px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none transition-colors"
                  />

                  <button
                    type="submit"
                    disabled={loading || !newUrl.trim()}
                    className="w-full bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 cursor-pointer border-0 outline-none"
                  >
                    {loading ? t("正在初始化...", "INITIATING...") : t("获取音频", "FETCH AUDIO")}
                  </button>
                </form>
              ) : (
                <div className="flex flex-col gap-4">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading || loading}
                    className="w-full border-2 border-dashed border-[var(--border-primary)] hover:border-[var(--accent-red)] hover:bg-[var(--accent-red-light)]/10 text-[var(--text-tertiary)] hover:text-[var(--accent-red)] py-8 rounded-xl flex flex-col items-center justify-center gap-2 transition-colors disabled:opacity-50 cursor-pointer bg-transparent"
                  >
                    <span className="text-3xl mb-1">☁️</span>
                    <span className="text-xs font-bold">{uploading ? t("正在上传...", "UPLOADING...") : t("浏览本地文件", "BROWSE FILES")}</span>
                  </button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleLocalFileUpload}
                    accept=".mp3,.wav,.m4a,.aac,.flac,.ogg"
                    className="hidden"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
