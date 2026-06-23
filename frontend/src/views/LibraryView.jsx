import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Search, SlidersHorizontal, Mic, Square, Cloud, Play,
  Trash2, BarChart3, Database, Plus, Calendar, FastForward, ExternalLink
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

export const AmenBreakWidget = () => {
  const [isHovered, setIsHovered] = useState(false);
  const [isPressing, setIsPressing] = useState(false);
  const [bpm, setBpm] = useState(103); // 一开始以 0.75 倍速展示 (137.14 * 0.75 ≈ 103)
  const [activeStep, setActiveStep] = useState(-1);
  
  // 音频引擎与 Buffer 引用
  const audioCtxRef = useRef(null);
  const masterGainRef = useRef(null);
  const audioBufferRef = useRef(null);
  const sourceNodeRef = useRef(null);
  
  const isPressingRef = useRef(false);
  const bpmRef = useRef(102.85); // 0.75倍速基准
  const nextNoteTimeRef = useRef(0);
  const currentStepRef = useRef(0);
  const timerIDRef = useRef(null);
  const pressStartTimeRef = useRef(0);

  // 页面加载时自动预加载并解码真实的 Amen Break 音频片断
  useEffect(() => {
    const loadAudio = async () => {
      try {
        const response = await fetch("/amen_break_sliced.wav");
        const arrayBuffer = await response.arrayBuffer();
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const tempCtx = new AudioContext();
        const decoded = await tempCtx.decodeAudioData(arrayBuffer);
        audioBufferRef.current = decoded;
        tempCtx.close();
      } catch (err) {
        console.error("Failed to load Amen Break audio file:", err);
      }
    };
    loadAudio();
    return () => {
      if (timerIDRef.current) clearTimeout(timerIDRef.current);
    };
  }, []);

  // 初始化或获取音频上下文
  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioContext();
      const masterGain = ctx.createGain();
      masterGain.gain.value = 0; // 默认静音
      masterGain.connect(ctx.destination);
      
      audioCtxRef.current = ctx;
      masterGainRef.current = masterGain;
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume();
    }
    return { ctx: audioCtxRef.current, masterGain: masterGainRef.current };
  }, []);

  // 启动真实的 Amen Break 循环播放
  const startLoop = useCallback(() => {
    const { ctx, masterGain } = getAudioContext();
    if (!ctx || !audioBufferRef.current) return;

    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop();
      } catch (e) {}
    }

    const source = ctx.createBufferSource();
    source.buffer = audioBufferRef.current;
    source.loop = true;
    source.loopStart = 0;
    source.loopEnd = 7.00; // 4个Bar的标准Amen Break循环点，约7.0秒

    // 设置初始播放速率，以 137.14 BPM 为基准
    source.playbackRate.value = bpmRef.current / 137.14;

    source.connect(masterGain);
    source.start(0);
    sourceNodeRef.current = source;
  }, [getAudioContext]);

  // 停止循环播放
  const stopLoop = useCallback(() => {
    if (sourceNodeRef.current) {
      const source = sourceNodeRef.current;
      setTimeout(() => {
        try {
          source.stop();
        } catch (e) {}
      }, 1000); // 在渐出结束后停止源节点
      sourceNodeRef.current = null;
    }
  }, []);

  // 音序器核心调度逻辑 (仅用于视觉上在正确的时间点点亮步骤，保持与音乐速率一致)
  const scheduleNote = useCallback(() => {
    const { ctx } = getAudioContext();
    if (!ctx) return;

    while (nextNoteTimeRef.current < ctx.currentTime + 0.1) {
      const step = currentStepRef.current;
      
      // 更新视觉状态
      setActiveStep(step);

      // 计算 16 分音符的时间步长 (60s / BPM / 4)
      const secondsPerBeat = 60.0 / bpmRef.current;
      nextNoteTimeRef.current += 0.25 * secondsPerBeat;
      currentStepRef.current = (step + 1) % 16;
    }
    
    timerIDRef.current = setTimeout(scheduleNote, 25);
  }, [getAudioContext]);

  // 处理物理交互 (按下/松开)
  const handlePointerDown = (e) => {
    e.preventDefault(); 
    setIsPressing(true);
    isPressingRef.current = true;
    pressStartTimeRef.current = Date.now();
    
    const { ctx, masterGain } = getAudioContext();
    if (!ctx) return;
    
    // 开启音频样本循环
    startLoop();
    
    // 平滑渐入
    masterGain.gain.cancelScheduledValues(ctx.currentTime);
    masterGain.gain.setValueAtTime(masterGain.gain.value, ctx.currentTime);
    masterGain.gain.linearRampToValueAtTime(1, ctx.currentTime + 0.15);

    // 重置音序器时钟并启动视觉扫描
    if (timerIDRef.current === null) {
      currentStepRef.current = 0;
      nextNoteTimeRef.current = ctx.currentTime;
      scheduleNote();
    }
  };

  const handlePointerUp = () => {
    setIsPressing(false);
    isPressingRef.current = false;
    
    if (audioCtxRef.current && masterGainRef.current) {
      const ctx = audioCtxRef.current;
      const gainNode = masterGainRef.current;
      
      // 平滑渐出
      gainNode.gain.cancelScheduledValues(ctx.currentTime);
      gainNode.gain.setValueAtTime(gainNode.gain.value, ctx.currentTime);
      gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 1);
    }

    // 渐出后停止音频源与音序器扫描
    stopLoop();
    setTimeout(() => {
      if (!isPressingRef.current) {
        clearTimeout(timerIDRef.current);
        timerIDRef.current = null;
        setActiveStep(-1);
      }
    }, 1000);
  };

  // 处理按压时的加速逻辑
  useEffect(() => {
    let animationFrameId;
    
    const updateLoop = () => {
      if (isPressingRef.current) {
        const pressDuration = Date.now() - pressStartTimeRef.current;
        
        if (pressDuration < 1200) {
          // 前 1.2 秒：保持 0.75 倍速 (约 103 BPM)
          bpmRef.current = 102.85;
        } else if (pressDuration >= 1200 && pressDuration < 2400) {
          // 1.2秒 到 2.4秒：非常平滑地过渡到 1.0 倍速 (137.14 BPM)
          const ratio = (pressDuration - 1200) / 1200; // 1.2秒的漫长过渡
          bpmRef.current = 102.85 + (137.14 - 102.85) * ratio;
        } else if (pressDuration >= 2400 && pressDuration < 3600) {
          // 2.4秒 到 3.6秒：稳稳停在原速 1.0 倍速 (137.14 BPM) 享受原声
          bpmRef.current = 137.14;
        } else {
          // 3.6秒之后：开始极其平缓地加速，最高至 220 BPM (经典 Jungle 速度)
          // 每次增量从 0.07 降低至 0.025，使提速感受极其顺滑温和
          bpmRef.current = Math.min(bpmRef.current + 0.025, 220);
        }
        
        setBpm(Math.round(bpmRef.current));
        if (sourceNodeRef.current) {
          sourceNodeRef.current.playbackRate.value = bpmRef.current / 137.14;
        }
      } else {
        // 松开时缓降回最初的 0.75 倍速 (102.85 BPM)
        bpmRef.current = Math.max(bpmRef.current - 1.2, 102.85);
        setBpm(Math.round(bpmRef.current));
        if (sourceNodeRef.current) {
          sourceNodeRef.current.playbackRate.value = bpmRef.current / 137.14;
        }
      }
      
      animationFrameId = requestAnimationFrame(updateLoop);
    };
    
    updateLoop();
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  return (
    <div 
      className={`
        relative overflow-hidden bg-transparent w-full
        transition-all duration-300 ease-out select-none cursor-pointer
        ${isPressing ? 'scale-[0.98]' : 'scale-100'}
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        if (isPressing) handlePointerUp();
      }}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onContextMenu={(e) => e.preventDefault()} // 防止移动端长按弹出菜单
    >
      {/* 内部 Padding 容器 */}
      <div className="py-2 px-0.5 relative z-10 flex flex-col h-full justify-center min-h-[40px]">
        {/* 16步进 音序器网格 */}
        <div className="flex justify-between items-center h-8 w-full gap-1">
          {(() => {
            const stepHeights = [
              'h-7', 'h-3', 'h-5', 'h-2',
              'h-6', 'h-4', 'h-3', 'h-2',
              'h-6', 'h-3', 'h-5', 'h-4',
              'h-7', 'h-4', 'h-6', 'h-3'
            ];
            return Array.from({ length: 16 }).map((_, index) => {
              const isActive = activeStep === index;
              return (
                <div 
                  key={index}
                  className={`
                    w-1.5 rounded-full transition-all duration-[70ms] origin-center
                    ${stepHeights[index]}
                    ${!isHovered && !isPressing ? 'bg-[#e4dfd5]' : ''} 
                    ${isHovered && !isPressing ? 'bg-[#c5b092]' : ''}
                    ${isPressing && isActive ? 'bg-[#f62440] shadow-[0_0_8px_rgba(246,36,64,0.6)] scale-y-110 z-10' : ''}
                    ${isPressing && !isActive ? 'bg-[#f1ded9] animate-audio-wave' : ''}
                  `}
                  style={isPressing && !isActive ? { animationDelay: `${(index % 6) * 0.12}s` } : {}}
                />
              );
            });
          })()}
        </div>
      </div>
      
      {/* 长按时的背景光晕特效 */}
      <div 
        className={`absolute inset-0 bg-[#f62440]/3 transition-opacity duration-500 pointer-events-none ${isPressing ? 'opacity-100' : 'opacity-0'}`} 
      />
    </div>
  );
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
    
    // FFmpeg is auto-detected by backend, no frontend validation needed
    
    // Check ASR
    if (configData.asr_mode === "online") {
      const provider = configData.online_asr_provider || "mimo";
      if (provider === "custom") {
        if (!configData.custom_asr_endpoint) return false;
      } else if (provider === "funasr") {
        if (!configData.online_base_url) return false;
      } else {
        if (!configData.online_base_url || !configData.online_model || !configData.online_api_key) return false;
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
      duration: task.duration || "--:--",
      status: uiStatus,
      speaker: task.speaker || "V. Valerius",
      thumbnail: task.image_url || task.thumbnail || defaultThumbs[index % defaultThumbs.length],
      tags: Array.isArray(task.tags) && task.tags.length > 0 ? task.tags : ["Acoustic", "AI Workstation"],
      progress: task.progress ?? 0,
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
            if (result.warning) {
              alert(result.warning);
            } else {
              alert(t("麦克风录音上传成功！", "Microphone recording uploaded successfully!"));
            }
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
          <div className="mt-4">
            <AmenBreakWidget />
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
                      onError={(e) => { e.target.style.display = 'none'; }}
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
                    <a
                      href={session.rawTask.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={t("打开原始播客链接", "Open original podcast link")}
                      className="p-1.5 hover:bg-[#f2ede6]/50 rounded-full transition-all text-[#8a8580] hover:text-[#1d1c18]"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink size={14} />
                    </a>
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
