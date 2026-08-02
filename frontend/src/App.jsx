import React, { useState, useEffect, useRef } from "react";
import Sidebar from "./components/Sidebar";
import LibraryView from "./views/LibraryView";
import WorkstationView from "./views/WorkstationView";
import PodcastDetailView from "./views/PodcastDetailView";
import SettingsView from "./views/SettingsView";
import DialogRenderer, { alert, confirm } from "./components/Dialog.jsx";
import { initialLogs } from "./data.js";
import { API_BASE } from "./constants.js";
import { usePlayerStore } from "./store/playerStore.js";
import { useConfigStore } from "./store/configStore.js";
import { useTaskStore } from "./store/taskStore.js";
import { useUIStore } from "./store/uiStore.js";
import { useTranslation } from "./contexts/I18nContext.jsx";
import { Loader2 } from "lucide-react";


const BACKEND_URL = API_BASE;

export default function App() {
  const activeTab = useUIStore(state => state.activeTab);
  const setActiveTab = useUIStore(state => state.setActiveTab); // 'dashboard', 'workstation', 'detail', 'config'
  const activeTaskId = useTaskStore(state => state.activeTaskId);
  const setActiveTaskId = useTaskStore(state => state.setActiveTaskId);
  const detailSourceTab = useUIStore(state => state.detailSourceTab);
  const setDetailSourceTab = useUIStore(state => state.setDetailSourceTab); // 'dashboard' or 'workstation'
  const activeTask = useTaskStore(state => state.activeTask);
  const setActiveTask = useTaskStore(state => state.setActiveTask);
  const tasks = useTaskStore(state => state.tasks);
  const setTasks = useTaskStore(state => state.setTasks);
  const newUrl = useTaskStore(state => state.newUrl);
  const setNewUrl = useTaskStore(state => state.setNewUrl);
  const loading = useUIStore(state => state.loading);
  const setLoading = useUIStore(state => state.setLoading);
  const setDetailLoading = useUIStore(state => state.setDetailLoading);
  const uploading = useUIStore(state => state.uploading);
  const setUploading = useUIStore(state => state.setUploading);

  const isIngestModalOpen = useUIStore(state => state.isIngestModalOpen);
  const setIsIngestModalOpen = useUIStore(state => state.setIsIngestModalOpen);
  const setIsAudioMissing = useUIStore(state => state.setIsAudioMissing);

  // Audio Playback states
  const isPlaying = usePlayerStore(state => state.isPlaying);
  const duration = usePlayerStore(state => state.duration);
  const setCurrentTime = usePlayerStore(state => state.setCurrentTime);
  const setIsPlaying = usePlayerStore(state => state.setIsPlaying);
  const setDuration = usePlayerStore(state => state.setDuration);
  const playbackRate = usePlayerStore(state => state.playbackRate);
  

  const perfData = useConfigStore(state => state.perfData);
  const setPerfData = useConfigStore(state => state.setPerfData);
  const versionInfo = useConfigStore(state => state.versionInfo);
  const setVersionInfo = useConfigStore(state => state.setVersionInfo);

  const configData = useConfigStore(state => state.configData);
  const setConfigData = useConfigStore(state => state.setConfigData);
  const { t } = useTranslation();
  const audioSource = useTaskStore(state => state.audioSource);
  const setAudioSource = useTaskStore(state => state.setAudioSource);

  // Prompt 编辑状态
  const promptData = useConfigStore(state => state.promptData);
  const setPromptData = useConfigStore(state => state.setPromptData);
  const promptSaveStatus = useConfigStore(state => state.promptSaveStatus);
  const setPromptSaveStatus = useConfigStore(state => state.setPromptSaveStatus);

  // Local storage audit logs
  const logs = useConfigStore(state => state.logs);
  const setLogs = useConfigStore(state => state.setLogs);

  const fileInputRef = useRef(null);
  const audioPlayerRef = useRef(null);
  const activeTaskRef = useRef(null);
  const playbackPositions = useRef({});

  const checkingVersion = useConfigStore(state => state.checkingVersion);
  const setCheckingVersion = useConfigStore(state => state.setCheckingVersion);
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
              await alert(t(
                `发现新版本 v${data.latest_version}！已为您在设置页面顶部载入更新日志。`,
                `New version v${data.latest_version} found! Changelog has been loaded at the top of Settings.`
              ), { variant: 'info', confirmText: t('好的', 'OK') });
            } else {
              await alert(t("当前已是最新版本！", "You are already on the latest version!"), { variant: 'success' });
            }
          }
        }
      }
    } catch (e) {
      console.error("无法获取软件版本信息:", e);
      if (force) {
        await alert(t(
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

  const handleResetPrompt = async () => {
    if (await confirm(t("确定要恢复默认 Prompt 模板吗？这会覆盖您当前的输入。", "Are you sure you want to restore the default Prompt templates? This will overwrite your current configuration."))) {
      // Reset to empty, then fetch default from backend
      fetch(`${BACKEND_URL}/api/prompt/template/standard`)
        .then(res => res.json())
        .then(data => {
          setPromptData({ 
            prompt: data.prompt || "",
            default_template_id: "standard"
          });
        })
        .catch(() => {
          setPromptData({ 
            prompt: "",
            default_template_id: "standard"
          });
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
    console.log("[DEBUG] fetchTaskDetail triggered for task ID:", id, "isSilent:", isSilent);
    if (!id) return;
    if (!isSilent) setDetailLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${id}`);
      console.log("[DEBUG] fetchTaskDetail response status:", res.status);
      if (res.status === 200) {
        const data = await res.json();
        console.log("[DEBUG] fetchTaskDetail success, task title:", data.title);
        setActiveTask(data);
      } else {
        console.error("[DEBUG] fetchTaskDetail failed with status:", res.status);
      }
    } catch (e) {
      console.error("[DEBUG] fetchTaskDetail exception:", e);
    } finally {
      if (!isSilent) setDetailLoading(false);
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem("whisperme_logs");
    if (saved) {
        try { setLogs(JSON.parse(saved)); } catch(e) {}
    }
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
    console.log("[DEBUG] useEffect [activeTaskId] triggered. activeTaskId is:", activeTaskId);
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
      console.log("[DEBUG] activeTaskId is null, setting activeTask to null");
      setActiveTask(null);
    }
  }, [activeTaskId]);

  useEffect(() => {
    activeTaskRef.current = activeTask;
  }, [activeTask]);

  const handleCreateTask = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const errorMsg = getConfigValidationMessage();
    if (errorMsg) {
      await alert(errorMsg);
      return;
    }
    const trimmedUrl = newUrl.trim();
    if (!trimmedUrl || loading) return;

    const exists = tasks.some(t => t.url === trimmedUrl);
    if (exists) {
      const proceed = await confirm(t("该链接似乎已经存在于播客库中，是否继续添加？", "This link already exists in the library. Continue?"));
      if (!proceed) return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmedUrl, asr_mode: configData.asr_mode || "online" })
      });
      if (res.status === 200) {
        const result = await res.json();
        setNewUrl("");
        setIsIngestModalOpen(false);
        fetchTasks();
        if (result.warning) {
          await alert(result.warning);
        }
      }
    } catch (e) {
      await alert(t("发起任务失败，请检查后端服务是否启动！", "Failed to start task. Please check if the backend service is running!"));
    } finally {
      setLoading(false);
    }
  };

  const handleLocalFileUpload = async (e) => {
    const errorMsg = getConfigValidationMessage();
    if (errorMsg) {
      await alert(errorMsg);
      if (e.target) e.target.value = "";
      return;
    }
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
          await alert(result.warning);
        } else {
          await alert(t("音频文件导入成功！", "Audio file imported successfully!"), { variant: 'success' });
        }
      } else {
        await alert(t("文件上传失败。", "File upload failed."));
      }
    } catch (err) {
      console.error(err);
      await alert(t("上传出错：", "Upload error: ") + err.message);
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
      await alert(t("删除失败", "Delete failed"));
    }
  };

  const handleSaveConfig = async (e, isSilent = false) => {
    if (e && e.preventDefault) e.preventDefault();
    if (configData.asr_mode === "local" && (!configData.local_whisper_model_path || configData.local_whisper_model_path.trim() === "")) {
      if (!isSilent) await alert(t("本地 ASR 模型文件夹路径不能为空！", "Local ASR model folder path cannot be empty!"));
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configData)
      });
      if (res.status === 200) {
        if (!isSilent) await alert(t("配置已成功更新！", "Configuration updated successfully!"), { variant: 'success' });
      }
    } catch (e) {
      if (!isSilent) await alert(t("保存配置失败", "Failed to save configuration"));
    }
  };

  const updateConfigData = useConfigStore(state => state.updateConfigData);

  const handleConfigChange = (key, value) => {
    updateConfigData({ [key]: value });
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

  const handleAnalyzeAllLogs = async () => {
    await alert(t("正在对所有单集记录进行日志分析以寻找行动项... 综合计算已加载。", "Analyzing logs across all session records to find action items... Synthesis calculations loaded."), { variant: 'info', confirmText: t('好的', 'OK') });
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

  const isPlaceholder = (val) => {
    if (!val || typeof val !== "string") return false;
    const cleanVal = val.trim().toLowerCase();
    return (
      cleanVal === "" ||
      cleanVal.includes("your_api_key") ||
      cleanVal.includes("your_base_url") ||
      cleanVal.includes("your_model") ||
      cleanVal.includes("placeholder")
    );
  };

  const getConfigValidationMessage = () => {
    if (!configData) return t("无法读取系统配置数据！", "Failed to load system config!");
    
    // ASR 校验
    if (configData.asr_mode === "local") {
      if (!configData.local_whisper_model_path || isPlaceholder(configData.local_whisper_model_path)) {
        return t("您启用了本地转录，但未在系统设置中配置正确的本地 Whisper 模型路径！", "Local ASR is active, but the Whisper model path is missing or invalid in settings!");
      }
    } else if (configData.asr_mode === "online") {
      const provider = configData.online_asr_provider || "mimo";
      if (provider === "custom") {
        if (!configData.custom_asr_endpoint || isPlaceholder(configData.custom_asr_endpoint)) {
          return t("您启用了自定义在线转录，但未配置自定义接口地址 (Endpoint)！", "Custom ASR is active, but the Endpoint URL is missing in settings!");
        }
      } else if (provider === "funasr") {
        if (!configData.online_base_url || isPlaceholder(configData.online_base_url)) {
          return t("您启用了在线 FunASR，但未在设置中配置 API 地址 (Base URL)！", "FunASR is active, but the ASR Base URL is missing in settings!");
        }
      } else {
        // mimo / openai 强校验这三个核心在线字段
        if (!configData.online_api_key) {
          return t("您启用了在线转录，但未在设置中配置 ASR API 密钥 (API Key)！", "Online ASR is active, but the ASR API Key is missing in settings!");
        }
        if (isPlaceholder(configData.online_api_key)) {
          return t("当前 ASR API 密钥为系统默认的测试 Key（已被拉黑），请替换为您申请的私有 Key！", "The ASR API Key is the default test key (blocked). Please replace it with your own private API Key!");
        }
        if (!configData.online_base_url || isPlaceholder(configData.online_base_url)) {
          return t("您启用了在线转录，但未在设置中配置 ASR 接口地址 (Base URL)！", "Online ASR is active, but the ASR Base URL is missing in settings!");
        }
        if (!configData.online_model || isPlaceholder(configData.online_model)) {
          return t("您启用了在线转录，但未在设置中配置 ASR 模型名称 (Model ID)！", "Online ASR is active, but the ASR Model ID is missing in settings!");
        }
      }
    }

    // Summary 校验
    if (configData.summary_mode === "local") {
      if (!configData.ollama_url || isPlaceholder(configData.ollama_url) || !configData.ollama_model || isPlaceholder(configData.ollama_model)) {
        return t("您启用了本地总结，但设置中 Ollama 服务地址或模型名称未正确配置！", "Local Summary is active, but the Ollama URL or model name is invalid in settings!");
      }
    } else if (configData.summary_mode === "online") {
      if (!configData.online_summary_api_key) {
        return t("您启用了在线总结，但设置中大模型总结的 API 密钥 (API Key) 未配置！", "Online Summary is active, but the LLM API Key is missing in settings!");
      }
      if (isPlaceholder(configData.online_summary_api_key)) {
        return t("当前大模型总结的 API 密钥为系统默认的测试 Key（已被拉黑），请替换为您申请的私有 Key！", "The LLM API Key is the default test key (blocked). Please replace it with your own private API Key!");
      }
      if (!configData.online_summary_base_url || isPlaceholder(configData.online_summary_base_url)) {
        return t("您启用了在线总结，但设置中大模型总结的接口地址 (Base URL) 未配置！", "Online Summary is active, but the LLM Base URL is missing in settings!");
      }
      if (!configData.online_summary_model || isPlaceholder(configData.online_summary_model)) {
        return t("您启用了在线总结，但设置中大模型总结的模型名称 (Model ID) 未配置！", "Online Summary is active, but the LLM Model ID is missing in settings!");
      }
    }

    return null;
  };

  const isConfigInvalid = () => {
    return getConfigValidationMessage() !== null;
  };


  const handleResetData = async () => {
    localStorage.removeItem("whisperme_logs");
    setLogs(initialLogs);
    setActiveTaskId(null);
    setActiveTab("dashboard");
    await alert(t("本地工作区内存已完全清除！已恢复默认录音。", "Local workspace memory wiped cleanly! Restored default recordings."), { variant: 'success' });
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
        
      />

      {/* Main split screens panel area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[var(--bg-primary)] transition-colors duration-300" id="primary-content-workspace">
        {(() => {
          console.log("[DEBUG] Render main panel. activeTab:", activeTab, "activeTask:", activeTask);
          return null;
        })()}
        {activeTab === "detail" && activeTask ? (
          /* Active full screen transcript parser */
          <PodcastDetailView
            
            audioPlayerRef={audioPlayerRef}
            
            togglePlay={togglePlay}
            
            handleProgressChange={handleProgressChange}
            
            
            
            
            
            
            onRefreshTask={() => fetchTaskDetail(activeTask.id, true)}
            onBack={() => {
              setActiveTaskId(null);
              setActiveTab(detailSourceTab === "workstation" ? "workstation" : "dashboard");
            }}
          />
        ) : activeTab === "detail" && !activeTask ? (
          <div className="flex-1 flex items-center justify-center bg-[var(--bg-primary)]">
            <Loader2 className="w-8 h-8 text-[var(--accent-red)] animate-spin" />
          </div>
        ) : (
          /* Tab contents switch */
          <>
            {activeTab === "dashboard" && (
              <LibraryView
                tasks={tasks}
                logs={logs}
                configData={configData}
                perfData={perfData}
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
              />
            )}

            {activeTab === "workstation" && (
              <WorkstationView
                
                onOpenSession={(task) => {
                  setDetailSourceTab("workstation");
                  setActiveTaskId(task.id);
                  setActiveTab("detail");
                }}
                onNewSessionTrigger={() => setIsIngestModalOpen(true)}
                onDeleteTask={handleDeleteTask}
              />
            )}

            {activeTab === "config" && (
              <SettingsView
                
                
                handleConfigChange={handleConfigChange}
                handleSaveConfig={handleSaveConfig}
                onResetData={handleResetData}
                
                
                
                handleSavePrompt={handleSavePrompt}
                handleResetPrompt={handleResetPrompt}
                onCheckVersion={fetchVersion}
                
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
                  <input type="radio" checked={audioSource === "link"} onChange={() => setAudioSource("link")} style={{ color: '#f62440', backgroundColor: audioSource === "link" ? '#f62440' : 'transparent' }} className="w-3.5 h-3.5 text-[#f62440] focus:ring-[var(--accent-red)] focus:ring-offset-0 cursor-pointer" /> {t("在线链接", "LINK")}
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[var(--text-primary)]">
                  <input type="radio" checked={audioSource === "file"} onChange={() => setAudioSource("file")} style={{ color: '#f62440', backgroundColor: audioSource === "file" ? '#f62440' : 'transparent' }} className="w-3.5 h-3.5 text-[#f62440] focus:ring-[var(--accent-red)] focus:ring-offset-0 cursor-pointer" /> {t("本地文件", "LOCAL FILE")}
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

      <DialogRenderer />
    </div>
  );
}
