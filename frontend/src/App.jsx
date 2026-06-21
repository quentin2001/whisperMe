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

  // Prompt 编辑状态
  const [promptData, setPromptData] = useState({
    base_prompt: "",
    action_prompt: ""
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
    if (window.confirm("确定要恢复默认 Prompt 模板吗？这会覆盖您当前的输入。")) {
      const defaultPrompt = {
        base_prompt: `请根据下面提供的【播客单集 Shownotes】、【听众热门评论】和【播客对话转录文本】，生成一份详尽、结构清晰的【播客价值总结分析报告】。

核心防伪守则（必须严格遵守，否则视为失败）：
1. 严禁臆测发散：所有分析结论、嘉宾立场、议题提炼及评级，必须100%基于下方提供的事实源数据。严禁使用你自身固有知识库中的外部信息去扩展或脑补播客中未提及的事情或技术细节。
2. 拒绝幻觉，空值如实报告：如果播客转录本中完全没有提及某人、某事或某个观点，哪怕该词出现在了 Shownotes 简介里，也绝对不得在总结中编造其对话内容，必须如实标注转录文本中未讨论或未提及。
3. 精准引用：提炼核心观点和发言人立场时，必须直接引用（或高度提炼）转录文本中的原话、金句或提及的具体事例，并指明是谁说的。
4. 客观呈现听众反馈：舆情分析部分必须完全基于热门听众评论列表中的实际留言，不得凭空编造听众情感走向。`,
        action_prompt: `请以 Markdown 格式输出以下结构的内容（严禁输出结构外的发散废话，直接输出报告正文）：

## 1. 播客概要与含金量评级
- **核心主旨**：用2-3句话精准总结这期播客实际讨论的核心主题（拒绝大话空话，紧扣转录事实）。
- **目标受众**：根据播客讨论内容的专业深度，说明适合哪些细分人群收听。
- **含金量评级与判定理由**：请给出评级（A+ / A / B / C / D 之一），并从内容信息密度、观点的独特性和知识实用度三个维度，基于转录中的干货多寡简述判定理由。
- **推荐等级**：是否值得花时间复听（值得去听 / 仅看总结即可 / 建议避坑）。

## 2. 核心观点与议题提炼
请梳理出播客实际讨论的3-5个核心议题。对每个议题：
- **议题名称**
- **核心论点**：结合不同人的发言总结其达成的共识或分歧。
- **关键论据/金句**：必须包含转录中发言人提到过的原话、金句或他们讲到的具体案例。

## 3. 发言人画像与立场分析
- **角色定位**：说明都有谁参与了说话，谁是主持人（Host），谁是嘉宾（Guest）。
- **立场与风格**：简述各位发言人的核心立场、讨论风格以及观点倾向，切忌根据发言人的名气脑补其背景，只分析其在此单集中的言论表现。
- **互动氛围**：他们之间的互动如何（比如是和谐互补，还是存在观点的交锋摩擦）。

## 4. 听众口碑与评论区舆情分析
- **听众主要反馈**：评论区大家最赞同的观点是什么？有没有提出不同的质疑？（必须从提供的评论列表中提取，无评论则写暂无评论数据）。
- **评论情感极性**：正向期待为主 / 中立探讨 / 存在争议偏见。
- **社会共鸣点**：这期播客勾起了听众什么共鸣或情绪。

## 5. 事实一致性与局限性声明
请在此处特别说明：本报告有哪些内容是简介（Shownotes）中提到但转录对话中实际并未展开讨论的？（若有，请逐一列出；若无，写 Shownotes 提及内容与实际转录文本一致）。`
      };
      setPromptData(defaultPrompt);
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
                onJumpToWorkstation={() => setActiveTab("workstation")}
                onNewSessionTrigger={() => setIsIngestModalOpen(true)}
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
                promptData={promptData}
                setPromptData={setPromptData}
                promptSaveStatus={promptSaveStatus}
                handleSavePrompt={handleSavePrompt}
                handleResetPrompt={handleResetPrompt}
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
