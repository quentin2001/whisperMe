import React, { useState, useEffect, useRef } from "react";
import { 
  Play, Pause, ChevronLeft, Search, CheckCircle2, RotateCcw, 
  Volume2, VolumeX, SkipBack, SkipForward, Sparkles, Sliders, RefreshCw,
  MessageSquare, History, Calendar, FileText, Users
} from "lucide-react";

// ==================== 📝 Inline Markdown Parser ====================
function parseInlineMarkdown(text) {
  if (!text) return "";
  const parts = [];
  const boldRegex = /\*\*([^*]+)\*\*/g;
  let match;
  let lastIndex = 0;

  while ((match = boldRegex.exec(text)) !== null) {
    const textBefore = text.substring(lastIndex, match.index);
    if (textBefore) parts.push(textBefore);
    parts.push(
      <strong key={match.index} className="text-[#1d1c18] font-bold">
        {match[1]}
      </strong>
    );
    lastIndex = boldRegex.lastIndex;
  }
  
  const remaining = text.substring(lastIndex);
  if (remaining) parts.push(remaining);
  
  return parts.length > 0 ? parts : text;
}

// ==================== 📝 High-Performance Markdown Parser with Alerts ====================
function MarkdownRenderer({ text }) {
  if (!text) return <p className="text-[#5d3f3e]/60 text-xs">暂无总结内容</p>;
  
  const lines = text.replace(/\\n/g, "\n").split("\n");
  let inList = false;
  let listItems = [];
  let inBlockquote = false;
  let blockquoteLines = [];
  let blockquoteType = null; // "NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"
  const renderedElements = [];

  const flushList = (key) => {
    if (listItems.length > 0) {
      renderedElements.push(
        <ul key={`list-${key}`} className="list-disc pl-5 mb-4 space-y-1.5">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const flushBlockquote = (key) => {
    if (blockquoteLines.length > 0) {
      let bgClass = "bg-[#f2ede6]/40 border-[#926e6d]";
      let textClass = "text-[#5d3f3e]";
      let title = "NOTE";
      
      if (blockquoteType === "IMPORTANT") {
        bgClass = "bg-red-50 border-[#f62440]";
        textClass = "text-red-900";
        title = "IMPORTANT";
      } else if (blockquoteType === "WARNING") {
        bgClass = "bg-yellow-50 border-yellow-500";
        textClass = "text-yellow-900";
        title = "WARNING";
      } else if (blockquoteType === "CAUTION") {
        bgClass = "bg-red-100 border-red-600";
        textClass = "text-red-950";
        title = "CAUTION";
      } else if (blockquoteType === "TIP") {
        bgClass = "bg-green-50 border-green-500";
        textClass = "text-green-900";
        title = "TIP";
      }
      
      renderedElements.push(
        <div key={`bq-${key}`} className={`border-l-4 ${bgClass} p-4 rounded-r-lg my-4 text-xs`}>
          <div className="font-bold uppercase tracking-wider mb-1 text-[10px] opacity-75">{title}</div>
          <div className={`${textClass} space-y-1`}>
            {blockquoteLines.map((l, idx) => (
              <p key={idx}>{parseInlineMarkdown(l)}</p>
            ))}
          </div>
        </div>
      );
      blockquoteLines = [];
      blockquoteType = null;
      inBlockquote = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Parse blockquotes / alerts
    if (line.startsWith(">")) {
      inBlockquote = true;
      let content = line.substring(1).trim();
      const alertMatch = content.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i);
      if (alertMatch) {
        blockquoteType = alertMatch[1].toUpperCase();
        content = content.replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i, "").trim();
      }
      if (content || blockquoteLines.length > 0) {
        blockquoteLines.push(content);
      }
      continue;
    } else {
      if (inBlockquote) {
        flushBlockquote(i);
      }
    }

    // Parse list items
    if (line.startsWith("- ") || line.startsWith("* ")) {
      inList = true;
      const content = line.substring(2);
      listItems.push(
        <li key={`li-${i}`} className="text-[#1d1c18]/90 text-[13px] leading-relaxed">
          {parseInlineMarkdown(content)}
        </li>
      );
      continue;
    }
    
    // Flush list if non-list item
    if (inList && !line.startsWith("- ") && !line.startsWith("* ")) {
      flushList(i);
    }

    if (line === "") continue;

    // Header 2
    if (line.startsWith("## ")) {
      renderedElements.push(
        <h2 key={i} className="font-bold text-base text-[#1d1c18] mb-2 mt-6 pb-1 border-b border-[#e7bcbb]/20">
          {parseInlineMarkdown(line.substring(3))}
        </h2>
      );
    } 
    // Header 3
    else if (line.startsWith("### ")) {
      renderedElements.push(
        <h3 key={i} className="font-bold text-sm text-[#f62440] mb-2 mt-4">
          {parseInlineMarkdown(line.substring(4))}
        </h3>
      );
    } 
    // Header 1
    else if (line.startsWith("# ")) {
      renderedElements.push(
        <h1 key={i} className="font-bold text-lg text-[#1d1c18] mb-4 border-b border-[#e7bcbb]/40 pb-2">
          {parseInlineMarkdown(line.substring(2))}
        </h1>
      );
    }
    // Normal paragraph
    else {
      renderedElements.push(
        <p key={i} className="text-[13px] text-[#5d3f3e] leading-relaxed mb-3">
          {parseInlineMarkdown(line)}
        </p>
      );
    }
  }
  
  if (inBlockquote) {
    flushBlockquote(lines.length);
  }
  if (inList) {
    flushList(lines.length);
  }

  return <div className="markdown-body select-text">{renderedElements}</div>;
}

// ==================== 🎙️ Shownotes Parser & Timeline Renderer ====================
function parseTimestampToSeconds(timestampStr) {
  const cleanStr = timestampStr.replace(/[\[\]\(\)]/g, "").trim();
  const parts = cleanStr.split(":").map(Number);
  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    return parts[0] * 60 + parts[1];
  }
  return 0;
}

function parseShownotesToBlocks(text) {
  if (!text) return [];
  const rawLines = text.split(/\r?\n/);
  const tempItems = [];
  const timeRegex = /(?:\[|\()?\b(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\b(?:\]|\))?/;

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i].trim();
    if (!line) {
      tempItems.push({ type: "empty" });
      continue;
    }

    const timeMatch = line.match(timeRegex);
    if (timeMatch) {
      const fullMatch = timeMatch[0];
      const rawTime = fullMatch.replace(/[\[\]\(\)]/g, "").trim();
      const seconds = parseTimestampToSeconds(rawTime);
      let rest = line.replace(fullMatch, "").trim();
      rest = rest.replace(/^[:：\-—\s]+/, "").trim();

      if (rest === "" && i + 1 < rawLines.length) {
        const nextLine = rawLines[i + 1].trim();
        if (nextLine && !nextLine.match(timeRegex)) {
          rest = nextLine;
          i++;
        }
      }

      tempItems.push({
        type: "timestamp",
        timestamp: rawTime,
        seconds: seconds,
        text: rest
      });
    } else {
      tempItems.push({
        type: "text",
        text: line
      });
    }
  }

  const blocks = [];
  let currentTimeline = [];

  const flushTimeline = () => {
    if (currentTimeline.length > 0) {
      blocks.push({
        type: "timeline",
        items: [...currentTimeline]
      });
      currentTimeline = [];
    }
  };

  for (const item of tempItems) {
    if (item.type === "timestamp") {
      currentTimeline.push(item);
    } else if (item.type === "empty") {
      flushTimeline();
      blocks.push({ type: "space" });
    } else {
      flushTimeline();
      blocks.push({ type: "prose", text: item.text });
    }
  }
  flushTimeline();

  return blocks;
}

function ShownotesRenderer({ text, onTimeJump }) {
  if (!text) return <p className="text-xs text-[#5d3f3e]/60">本单集暂无节目简介所示时间轴。</p>;

  const blocks = parseShownotesToBlocks(text);
  const headerRegex = /^(?:#+\s+|[一二三四五六七八九十]+[、.]|[0-9]+\.|part\s*\d|【|🎙️|⏳|📅|💡|📌|「|『)/i;

  return (
    <div className="flex flex-col gap-2">
      {blocks.map((block, index) => {
        if (block.type === "space") {
          return <div key={index} className="h-2" />;
        }

        if (block.type === "timeline") {
          return (
            <div key={index} className="space-y-2.5 mt-2 mb-4">
              {block.items.map((item, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center gap-4 group cursor-pointer" 
                  onClick={() => onTimeJump(item.seconds)}
                >
                  <span className="font-mono text-xs w-12 text-[#bf0029] font-bold group-hover:underline">
                    [{item.timestamp}]
                  </span>
                  <div className="flex-1 h-9 bg-white border border-[#e7bcbb]/30 flex items-center px-4 rounded-lg group-hover:border-[#f62440] group-hover:bg-[#ffdad6]/10 transition-all">
                    <p className="text-xs font-semibold text-[#1d1c18] truncate">
                      {item.text ? parseInlineMarkdown(item.text) : "Timeline Event"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          );
        }

        const isHeader = headerRegex.test(block.text);
        if (isHeader) {
          return (
            <div key={index} className="font-bold text-xs text-[#bf0029] mb-2 mt-4 uppercase">
              {parseInlineMarkdown(block.text)}
            </div>
          );
        }

        return (
          <p key={index} className="text-xs text-[#5d3f3e] leading-relaxed mb-1">
            {parseInlineMarkdown(block.text)}
          </p>
        );
      })}
    </div>
  );
}

// ==================== 🎙️ Main View Component ====================
export default function PodcastDetailView({ 
  activeTask, 
  audioPlayerRef, 
  isPlaying, 
  togglePlay, 
  progress, 
  handleProgressChange,
  currentTime,
  duration,
  playbackRate,
  setPlaybackRate,
  volume,
  setVolume,
  onRefreshTask,
  onBack
}) {
  const [searchWord, setSearchWord] = useState("");
  const [isMuted, setIsMuted] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Layout resize state (proportion of left panel in %)
  const [leftWidth, setLeftWidth] = useState(60);
  const [isDragging, setIsDragging] = useState(false);
  const [detailSubTab, setDetailSubTab] = useState("summary"); // "summary" | "shownotes" | "comments"

  // Speaker Management State
  const [showSpeakerModal, setShowSpeakerModal] = useState(false);
  const [editingSpeakerId, setEditingSpeakerId] = useState(null);
  const [editingSpeakerName, setEditingSpeakerName] = useState("");
  const [isSavingSpeaker, setIsSavingSpeaker] = useState(false);

  const containerRef = useRef(null);
  const activeBubbleRef = useRef(null);

  const getUniqueSpeakers = () => {
    if (!activeTask || !activeTask.paragraphs) return [];
    const speakers = new Set();
    activeTask.paragraphs.forEach((p) => {
      if (p.speaker) {
        speakers.add(p.speaker);
      }
    });
    return Array.from(speakers).sort();
  };

  const handleRenameSpeaker = async (speakerId, newName) => {
    if (!newName.trim()) return;
    setIsSavingSpeaker(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/tasks/${activeTask.id}/speaker/rename`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          speaker_id: speakerId,
          new_name: newName.trim(),
        }),
      });
      if (res.ok) {
        setEditingSpeakerId(null);
        if (onRefreshTask) {
          onRefreshTask();
        }
      } else {
        alert("重命名发言人失败，请重试。");
      }
    } catch (err) {
      console.error(err);
      alert("通信出错：" + err.message);
    } finally {
      setIsSavingSpeaker(false);
    }
  };

  // Translate seconds to MM:SS string helper
  const formatTime = (secondsCount) => {
    if (isNaN(secondsCount) || secondsCount === null) return "00:00";
    const mins = Math.floor(secondsCount / 60);
    const secs = Math.floor(secondsCount % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Seeking handlers
  const jumpToTimeSeconds = (secs) => {
    if (!audioPlayerRef.current) return;
    audioPlayerRef.current.currentTime = secs;
    if (audioPlayerRef.current.paused) {
      audioPlayerRef.current.play().catch(err => console.log("播放被浏览器拦截:", err));
    }
  };

  const jumpToTimeMMSS = (mmss) => {
    const targetedSec = parseTimestampToSeconds(mmss);
    jumpToTimeSeconds(targetedSec);
  };

  const handleStepBack = () => {
    if (!audioPlayerRef.current) return;
    audioPlayerRef.current.currentTime = Math.max(0, audioPlayerRef.current.currentTime - 10);
  };

  const handleStepForward = () => {
    if (!audioPlayerRef.current) return;
    audioPlayerRef.current.currentTime = Math.min(duration, audioPlayerRef.current.currentTime + 10);
  };

  const handleSpeedToggle = () => {
    if (!audioPlayerRef.current) return;
    const nextRate = playbackRate === 1.0 ? 1.5 : playbackRate === 1.5 ? 2.0 : 1.0;
    audioPlayerRef.current.playbackRate = nextRate;
    setPlaybackRate(nextRate);
  };

  const handleVolumeInput = (e) => {
    const nextVol = parseFloat(e.target.value);
    setVolume(nextVol);
    if (audioPlayerRef.current) {
      audioPlayerRef.current.volume = nextVol;
    }
    if (nextVol > 0 && isMuted) {
      setIsMuted(false);
    }
  };

  const toggleMute = () => {
    if (!audioPlayerRef.current) return;
    const nextMute = !isMuted;
    setIsMuted(nextMute);
    audioPlayerRef.current.muted = nextMute;
  };

  // Trigger manual AI summary analysis regeneration
  const triggerAIAnalysis = async () => {
    setAnalyzing(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/tasks/${activeTask.id}/summarize`, {
        method: "POST"
      });
      if (res.ok) {
        alert("AI总结与深度分析已重新排队生成，请稍候！");
      } else {
        alert("无法联系服务器发起AI总结。");
      }
    } catch (err) {
      console.error(err);
      alert("通信错误：" + err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  // Handle Resizable Split Screen dragging
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const relativeX = e.clientX - rect.left;
      const percentage = (relativeX / rect.width) * 100;
      if (percentage > 25 && percentage < 75) {
        setLeftWidth(percentage);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  // Auto scroll transcript to active dialogue bubble
  useEffect(() => {
    if (activeBubbleRef.current) {
      activeBubbleRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center"
      });
    }
  }, [currentTime]);

  // Map backend paragraphs
  const paragraphs = (activeTask.paragraphs || []).map((p, idx) => {
    const rawSpeaker = p.speaker || `Speaker ${idx + 1}`;
    const displaySpeaker = activeTask.speaker_mappings?.[rawSpeaker] || rawSpeaker;
    return {
      id: p.id || `p-${idx}`,
      speaker: displaySpeaker,
      timeStart: formatTime(p.start_time),
      timeEnd: formatTime(p.end_time),
      text: p.content || "",
      start_time: p.start_time,
      end_time: p.end_time
    };
  });

  const displayTitle = activeTask.title || "Untitled Session";
  const displayStatus = activeTask.status === "completed" ? "Completed" : "In Progress";
  const commentsList = activeTask.metadata?.comments || [];

  return (
    <div id="session-detail-view" ref={containerRef} className="flex-1 flex flex-col h-screen font-sans bg-[#fef9f2] relative select-none">
      
      {/* Mouse dragging cover shield */}
      {isDragging && (
        <div className="fixed inset-0 cursor-col-resize z-[9999] bg-transparent" />
      )}

      {/* Detail bar Header */}
      <header className="px-10 py-5 border-b border-[#e7bcbb]/40 bg-[#fef9f2] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            id="btn-back-to-library"
            onClick={onBack}
            className="p-2 hover:bg-[#f2ede6] rounded-lg transition-all text-[#bf0029] cursor-pointer border-0 outline-none bg-transparent"
          >
            <ChevronLeft size={20} />
          </button>
          
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-extrabold tracking-tight text-[#1d1c18] font-display">
                {displayTitle}
              </h1>
              <span className="bg-[#f0e2b7] text-[#554428] text-[10px] font-extrabold tracking-widest px-2.5 py-0.5 rounded-sm uppercase">
                {displayStatus}
              </span>
            </div>
          </div>
        </div>

        {/* Search transcript & AI Analysis options */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#5d3f3e]/40 w-4 h-4" />
            <input
              type="text"
              placeholder="Search transcript..."
              value={searchWord}
              onChange={(e) => setSearchWord(e.target.value)}
              className="pl-9 pr-4 py-1.5 bg-white border border-[#e7bcbb]/40 rounded-lg text-xs w-56 focus:outline-none focus:ring-1 focus:ring-[#f62440]"
            />
          </div>

          <button
            onClick={triggerAIAnalysis}
            disabled={analyzing}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-[#f62440] hover:bg-[#bb0028] disabled:bg-neutral-300 text-white text-xs font-bold rounded-lg transition-all cursor-pointer border-0 outline-none"
          >
            {analyzing ? (
              <RefreshCw size={13} className="animate-spin" />
            ) : (
              <Sparkles size={13} fill="white" />
            )}
            <span>{analyzing ? "Regenerating..." : "AI Analysis"}</span>
          </button>

          <button
            onClick={() => setShowSpeakerModal(true)}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-white border border-[#e7bcbb]/40 hover:bg-[#f2ede6] text-[#5d3f3e] text-xs font-bold rounded-lg transition-all cursor-pointer border-0 outline-none animate-fade-in"
          >
            <Users size={13} className="text-[#bf0029]" />
            <span>发言人管理</span>
          </button>
        </div>
      </header>

      {/* Split section Workspace */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        
        {/* Left pane: Scrollable Full Transcript */}
        <div 
          className="overflow-y-auto px-10 py-8 border-r border-[#e7bcbb]/30 h-full shrink-0"
          style={{ width: `${leftWidth}%` }}
        >
          <h2 className="text-3xl font-extrabold tracking-tight text-[#1d1c18] font-display mb-6">Full Transcript</h2>
          
          <div className="flex flex-col gap-6">
            {paragraphs
              .filter(p => p.text.toLowerCase().includes(searchWord.toLowerCase()))
              .map((p) => {
                const isCurrentlyPlayingThis = currentTime >= p.start_time && currentTime <= p.end_time;

                return (
                  <div 
                    key={p.id}
                    onClick={() => jumpToTimeSeconds(p.start_time)}
                    ref={isCurrentlyPlayingThis ? activeBubbleRef : null}
                    className={`p-4 rounded-lg cursor-pointer transition-all border ${
                      isCurrentlyPlayingThis 
                        ? "bg-white border-[#f62440] ring-1 ring-[#f62440]/10 shadow-xs" 
                        : "border-transparent hover:bg-white/40 hover:border-[#e7bcbb]/20"
                    }`}
                  >
                    <p className="font-mono text-xs text-[#bf0029] font-bold mb-1.5 hover:underline">
                      {p.timeStart} — {p.timeEnd}
                    </p>
                    <h4 className="font-bold text-xs text-[#5d3f3e] uppercase mb-1">{p.speaker}</h4>
                    <p className="text-[#1d1c18] text-[15px] leading-relaxed select-text font-medium">
                      {p.text}
                    </p>
                  </div>
                );
            })}
          </div>
        </div>

        {/* Resizable Divider bar */}
        <div
          onMouseDown={handleMouseDown}
          className="w-1 cursor-col-resize flex justify-center items-center select-none shrink-0 bg-[#e7bcbb]/40 hover:bg-[#f62440] transition-colors z-20"
        />

        {/* Right pane: Analysis summaries, shownotes & timelines */}
        <div 
          className="bg-[#f9f3ea]/20 shrink-0 flex flex-col h-full overflow-hidden"
          style={{ width: `calc(${100 - leftWidth}% - 4px)` }}
        >
          {/* Sub-tabs header selectors */}
          <div className="flex border-b border-[#e7bcbb]/30 bg-[#fef9f2]/90 shrink-0 h-12">
            <button
              onClick={() => setDetailSubTab("summary")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "summary"
                  ? "border-[#f62440] text-[#f62440] bg-[#f9f3ea]/35"
                  : "border-transparent text-[#5d3f3e]/70 hover:text-[#f62440] hover:bg-[#ffdad6]/5 bg-transparent"
              }`}
            >
              AI总结
            </button>
            <button
              onClick={() => setDetailSubTab("shownotes")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "shownotes"
                  ? "border-[#f62440] text-[#f62440] bg-[#f9f3ea]/35"
                  : "border-transparent text-[#5d3f3e]/70 hover:text-[#f62440] hover:bg-[#ffdad6]/5 bg-transparent"
              }`}
            >
              节目简介
            </button>
            <button
              onClick={() => setDetailSubTab("comments")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "comments"
                  ? "border-[#f62440] text-[#f62440] bg-[#f9f3ea]/35"
                  : "border-transparent text-[#5d3f3e]/70 hover:text-[#f62440] hover:bg-[#ffdad6]/5 bg-transparent"
              }`}
            >
              听众热评
            </button>
          </div>

          {/* Sub-tab scrollable content */}
          <div className="flex-1 overflow-y-auto px-8 py-8 flex flex-col gap-6 custom-scrollbar">
            {detailSubTab === "summary" && (
              <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs select-text animate-fade-in">
                <div className="flex items-center gap-2 mb-4 text-[#bf0029] select-none">
                  <Sparkles size={16} fill="#bf0029" />
                  <h3 className="text-xs font-bold uppercase tracking-wider">AI VALUE ANALYSIS REPORT</h3>
                </div>
                
                {/* Custom Markdown renderer rendering entire summary including metrics */}
                <MarkdownRenderer text={activeTask.summary} />
              </div>
            )}

            {detailSubTab === "shownotes" && (
              <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs animate-fade-in">
                <h3 className="text-xs font-extrabold uppercase tracking-widest text-[#5d5a55] mb-4 pb-2 border-b border-[#e7bcbb]/20">Shownotes Timeline</h3>
                <ShownotesRenderer text={activeTask.metadata?.shownotes} onTimeJump={jumpToTimeSeconds} />
              </div>
            )}

            {detailSubTab === "comments" && (
              <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs animate-fade-in">
                <h3 className="text-xs font-extrabold uppercase tracking-widest text-[#5d5a55] mb-4 pb-2 border-b border-[#e7bcbb]/20">Hot Listener Comments</h3>
                
                <div className="flex flex-col gap-4">
                  {commentsList.length > 0 ? (
                    commentsList.map((comment, cIdx) => (
                      <div key={cIdx} className="border border-[#e7bcbb]/30 p-4 rounded-xl bg-[#fef9f2]/40 hover:border-[#f62440]/30 transition-all">
                        <div className="flex justify-between items-center mb-2 text-xs">
                          <span className="font-bold text-[#1d1c18] flex items-center gap-1.5 select-none">
                            👤 {comment.author || "Anonymous Listener"}
                          </span>
                          <span className="font-mono text-[#bf0029] font-bold flex items-center gap-1 select-none">
                            ❤️ {comment.likes ?? 0}
                          </span>
                        </div>
                        <div className="text-xs text-[#5d3f3e] leading-relaxed whitespace-pre-wrap">
                          <ShownotesRenderer text={comment.content || comment.text} onTimeJump={jumpToTimeSeconds} />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="border-2 border-dashed border-[#e7bcbb]/40 p-8 text-center rounded-xl select-none">
                      <span className="text-xs text-[#5d3f3e]/50 font-bold uppercase tracking-wider">No comments indexed</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Pinned Playback bottom bar panel */}
      <footer className="h-24 border-t border-[#e7bcbb]/40 bg-white px-8 flex items-center justify-between shrink-0 select-none">
        
        {/* Left: session audio details */}
        <div className="w-1/4 flex items-center gap-3">
          <div className="w-11 h-11 bg-[#f62440] rounded-lg flex flex-col justify-center items-center text-white font-bold tracking-tight shadow-sm shrink-0">
            <span className="text-[10px] uppercase font-mono tracking-wide leading-none">V3</span>
            <span className="text-xs uppercase font-sans tracking-tight leading-none mt-0.5">Noir</span>
          </div>
          <div className="hidden sm:block overflow-hidden">
            <h4 className="font-bold text-xs text-[#1d1c18] font-display max-w-[200px] truncate">{displayTitle}</h4>
            <p className="text-[10px] font-semibold text-[#f62440] uppercase tracking-wider mt-0.5 animate-pulse">
              {isPlaying ? "Active Playback Decoding" : "Playback Idle"}
            </p>
          </div>
        </div>

        {/* Center: Play controllers and timeline waveform scale */}
        <div className="flex-1 max-w-2xl flex flex-col items-center gap-2">
          {/* Timeline and timeline indicators */}
          <div className="w-full flex items-center gap-3">
            <span className="text-xs font-mono font-bold text-[#bf0029]">
              {formatTime(currentTime)}
            </span>
            
            {/* Range seeker bar */}
            <div className="flex-1 relative flex items-center">
              <input
                type="range"
                min={0}
                max={Math.max(1, duration || 0)}
                value={currentTime || 0}
                onChange={handleProgressChange}
                className="w-full accent-[#f62440] h-1.5 bg-[#f2ede6] rounded-lg cursor-pointer appearance-none"
              />
            </div>

            <span className="text-xs font-mono font-bold text-[#5d5a55]">
              {formatTime(duration)}
            </span>
          </div>

          {/* Playback action buttons */}
          <div className="flex items-center gap-5">
            <button
              onClick={handleStepBack}
              className="p-1.5 hover:bg-[#f2ede6] rounded text-[#926e6d] hover:text-[#1d1c18] transition-all cursor-pointer border-0 outline-none bg-transparent"
            >
              <SkipBack size={15} />
            </button>

            <button
              onClick={togglePlay}
              className="w-10 h-10 bg-[#f62440] hover:bg-[#bb0028] text-white flex items-center justify-center rounded-full shadow-md active:scale-95 transition-all text-sm cursor-pointer border-0 outline-none"
            >
              {isPlaying ? <Pause size={16} fill="white" /> : <Play size={16} fill="white" className="ml-0.5" />}
            </button>

            <button
              onClick={handleStepForward}
              className="p-1.5 hover:bg-[#f2ede6] rounded text-[#926e6d] hover:text-[#1d1c18] transition-all cursor-pointer border-0 outline-none bg-transparent"
            >
              <SkipForward size={15} />
            </button>
          </div>
        </div>

        {/* Right side controllers */}
        <div className="w-1/4 flex items-center justify-end gap-3 font-semibold text-xs">
          {/* Play speed selector rate */}
          <button
            onClick={handleSpeedToggle}
            className="px-2.5 py-1 bg-[#f2ede6] text-[#5d3f3e] rounded-md border border-[#e7bcbb]/30 active:scale-98 transition-all cursor-pointer border-0 outline-none"
          >
            Speed {playbackRate.toFixed(1)}x
          </button>

          {/* Volume bars and state */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={toggleMute}
              className="p-1 text-[#926e6d] hover:text-[#1d1c18] cursor-pointer border-0 outline-none bg-transparent"
            >
              {isMuted || volume === 0 ? <VolumeX size={15} /> : <Volume2 size={15} />}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeInput}
              className="w-20 accent-[#f62440] h-1 bg-[#f2ede6] rounded-lg cursor-pointer"
            />
          </div>
        </div>
      </footer>

      {/* Speaker Management Modal */}
      {showSpeakerModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[150] p-6 animate-fade-in select-none">
          <div className="bg-white border border-[#e7bcbb]/50 rounded-xl max-w-lg w-full relative flex flex-col shadow-2xl">
            <div className="p-6 border-b border-[#e7bcbb]/30 flex justify-between items-center bg-[#f9f3ea]/50 rounded-t-xl">
              <h3 className="text-xl font-bold font-display text-[#1d1c18] flex items-center gap-2">
                <Users size={20} className="text-[#bf0029]" />
                发言人管理
              </h3>
              <button 
                onClick={() => {
                  setShowSpeakerModal(false);
                  setEditingSpeakerId(null);
                }} 
                className="text-[#5d3f3e]/60 hover:text-[#f62440] transition-colors cursor-pointer border-0 bg-transparent text-lg"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto custom-scrollbar">
              <p className="text-sm text-[#5d5a55]/85">
                在此处修改发言人名称。修改后将自动更新整个文本的发言人标签。
              </p>

              <div className="flex flex-col gap-3">
                {getUniqueSpeakers().length === 0 ? (
                  <div className="border border-[#e7bcbb]/40 border-dashed p-8 text-center rounded-lg text-sm text-[#5d5a55]/60 font-semibold">
                    未检测到发言人
                  </div>
                ) : (
                  getUniqueSpeakers().map((spId) => {
                    const currentName = activeTask.speaker_mappings?.[spId] || spId;
                    const isEditing = editingSpeakerId === spId;

                    return (
                      <div key={spId} className="flex items-center justify-between p-3 border border-[#e7bcbb]/30 rounded-lg bg-[#fef9f2]/30">
                        {isEditing ? (
                          <div className="flex items-center gap-2 w-full">
                            <input
                              type="text"
                              value={editingSpeakerName}
                              onChange={(e) => setEditingSpeakerName(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") handleRenameSpeaker(spId, editingSpeakerName);
                                if (e.key === "Escape") setEditingSpeakerId(null);
                              }}
                              className="flex-1 bg-white border border-[#e7bcbb]/40 focus:border-[#f62440] focus:ring-1 focus:ring-[#f62440] rounded px-3 py-1.5 text-sm text-[#1d1c18] outline-none"
                              autoFocus
                              disabled={isSavingSpeaker}
                            />
                            <button
                              onClick={() => handleRenameSpeaker(spId, editingSpeakerName)}
                              disabled={isSavingSpeaker || !editingSpeakerName.trim()}
                              className="px-3 py-1.5 bg-[#f62440] hover:bg-[#bb0028] disabled:opacity-50 text-white text-xs font-bold rounded cursor-pointer border-0 outline-none"
                            >
                              保存
                            </button>
                            <button
                              onClick={() => setEditingSpeakerId(null)}
                              disabled={isSavingSpeaker}
                              className="px-3 py-1.5 bg-[#f2ede6] text-[#5d3f3e] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded cursor-pointer border-0 outline-none"
                            >
                              取消
                            </button>
                          </div>
                        ) : (
                          <>
                            <div className="flex flex-col">
                              <span className="text-sm font-bold text-[#1d1c18]">{currentName}</span>
                              {activeTask.speaker_mappings?.[spId] && (
                                <span className="text-[10px] text-[#5d5a55] font-semibold mt-0.5">原始 ID: {spId}</span>
                              )}
                            </div>
                            <button
                              onClick={() => {
                                setEditingSpeakerId(spId);
                                setEditingSpeakerName(currentName);
                              }}
                              className="text-xs text-[#bf0029] hover:underline font-bold bg-transparent border-0 outline-none cursor-pointer"
                            >
                              编辑
                            </button>
                          </>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
            
            <div className="p-6 border-t border-[#e7bcbb]/30 flex justify-end bg-[#f9f3ea]/20 rounded-b-xl">
              <button
                onClick={() => {
                  setShowSpeakerModal(false);
                  setEditingSpeakerId(null);
                }}
                className="px-4 py-2 bg-[#f2ede6] text-[#5d3f3e] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded-lg cursor-pointer border-0 outline-none"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
