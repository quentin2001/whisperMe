import React, { useState, useEffect, useRef } from "react";
import {
  Play, Pause, ChevronLeft, Search, CheckCircle2, RotateCcw,
  Volume2, VolumeX, SkipBack, SkipForward, Sparkles, Sliders, RefreshCw,
  MessageSquare, History, Calendar, FileText, Users, Compass, Download,
  GitMerge, Trash2, AlertCircle
} from "lucide-react";
import { API_BASE, proxyImage } from "../constants.js";
import { alert, confirm } from "../components/Dialog.jsx";
import AudioPlayerControl from '../components/podcast/AudioPlayerControl.jsx';
import TranscriptList from '../components/podcast/TranscriptList.jsx';
import SpeakerManagerModal from '../components/podcast/SpeakerManagerModal.jsx';
import QAChatPanel from '../components/podcast/QAChatPanel.jsx';
import { usePlayerStore } from "../store/playerStore.js";
import { useTaskStore } from "../store/taskStore.js";

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
      <strong key={match.index} className="text-[var(--text-primary)] font-bold">
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
  const { t } = useTranslation();
  if (!text) return <p className="text-[var(--text-muted)] text-xs">{t("暂无总结内容", "No summary content available")}</p>;
  
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
      let bgClass = "bg-[var(--bg-hover)]/40 border-[#926e6d]";
      let textClass = "text-[var(--text-secondary)]";
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
        <li key={`li-${i}`} className="text-[var(--text-primary)] text-[13px] leading-relaxed">
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

    // Horizontal divider
    if (line === "---") {
      renderedElements.push(
        <hr key={i} className="border-t border-[var(--border-primary)]/45 my-6" />
      );
      continue;
    }

    // Timing stats metrics card collector
    if (line.includes("分析用时统计") || line.includes("Duration Statistics")) {
      let timingLines = [];
      let j = i + 1;
      while (j < lines.length) {
        const nextLine = lines[j].trim();
        if (nextLine.startsWith("#") || nextLine === "---") {
          break;
        }
        if (nextLine !== "") {
          timingLines.push(nextLine);
        }
        j++;
      }
      i = j - 1;
      
      renderedElements.push(
        <div key={`timing-${i}`} className="bg-[var(--bg-secondary)]/45 border border-[var(--border-primary)]/50 rounded-xl p-5 my-6 flex flex-col gap-3 shadow-2xs max-w-md animate-fade-in select-text">
          <div className="flex items-center gap-2 border-b border-[var(--border-primary)]/25 pb-2 text-[var(--accent-red)] font-bold text-xs tracking-wider">
            <span>⏱️</span>
            <span>{t("转录与分析耗时统计", "Processing Duration Statistics")}</span>
          </div>
          <div className="grid grid-cols-1 gap-2.5 text-xs font-semibold text-[var(--text-secondary)]">
            {timingLines.map((tLine, tIdx) => {
              let clean = tLine.replace(/^[:：\-—\*\s]+/, "").trim();
              if (clean.includes("总计耗时") || clean.includes("Total Time") || clean.includes("Total duration")) {
                const parts = clean.split(":");
                const label = parts[0].replace(/\*\*/g, "").trim();
                const durationVal = parts.slice(1).join(":").replace(/\*\*/g, "").trim();
                return (
                  <div key={tIdx} className="flex justify-between items-center border-t border-[var(--border-primary)]/30 pt-2.5 mt-1.5 font-bold text-[var(--accent-red)] text-[13px]">
                    <span>{label}</span>
                    <span>{durationVal}</span>
                  </div>
                );
              }
              const parts = clean.split(":");
              if (parts.length >= 2) {
                const key = parts[0].replace(/\*\*/g, "").trim();
                const val = parts.slice(1).join(":").replace(/\*\*/g, "").trim();
                return (
                  <div key={tIdx} className="flex justify-between items-center text-[11px]">
                    <span className="text-[var(--text-muted)]">{key}</span>
                    <span className="font-mono text-[var(--text-primary)] font-bold">{val}</span>
                  </div>
                );
              }
              return <div key={tIdx} className="text-[var(--text-primary)]">{clean}</div>;
            })}
          </div>
        </div>
      );
      continue;
    }

    // Header 2
    if (line.startsWith("## ")) {
      renderedElements.push(
        <h2 key={i} className="font-bold text-base text-[var(--text-primary)] mb-2 mt-6 pb-1 border-b border-[var(--border-primary)]/20">
          {parseInlineMarkdown(line.substring(3))}
        </h2>
      );
    } 
    // Header 3
    else if (line.startsWith("### ")) {
      renderedElements.push(
        <h3 key={i} className="font-bold text-sm text-[var(--accent-red)] mb-2 mt-4">
          {parseInlineMarkdown(line.substring(4))}
        </h3>
      );
    } 
    // Header 1
    else if (line.startsWith("# ")) {
      renderedElements.push(
        <h1 key={i} className="font-bold text-lg text-[var(--text-primary)] mb-4 border-b border-[var(--border-primary)]/40 pb-2">
          {parseInlineMarkdown(line.substring(2))}
        </h1>
      );
    }
    // Normal paragraph
    else {
      renderedElements.push(
        <p key={i} className="text-[13px] text-[var(--text-secondary)] leading-relaxed mb-3">
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
  const { t } = useTranslation();
  if (!text) return <p className="text-xs text-[var(--text-muted)]">{t("本单集暂无节目简介所示时间轴。", "No shownotes available for this episode.")}</p>;

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
                  <span className="font-mono text-xs w-12 text-[var(--accent-red)] font-bold group-hover:underline">
                    [{item.timestamp}]
                  </span>
                  <div className="flex-1 min-h-[2.25rem] py-2 bg-[var(--bg-card)] border border-[var(--border-primary)]/30 flex items-center px-4 rounded-lg group-hover:border-[#f62440] group-hover:bg-[var(--accent-red-light)]/10 transition-all">
                    <p className="text-xs font-semibold text-[var(--text-primary)] break-words whitespace-normal">
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
            <div key={index} className="font-bold text-xs text-[var(--accent-red)] mb-2 mt-4 uppercase">
              {parseInlineMarkdown(block.text)}
            </div>
          );
        }

        return (
          <p key={index} className="text-xs text-[var(--text-secondary)] leading-relaxed mb-1">
            {parseInlineMarkdown(block.text)}
          </p>
        );
      })}
    </div>
  );
}

// ==================== 🎙️ Comment Item Bubble Renderer ====================
function renderCommentText(text, onTimeJump) {
  if (!text) return "";
  
  // Match timestamps optionally surrounded by brackets or parentheses
  const regex = /(\[?\d{1,2}:\d{2}(?::\d{2})?\]?|\(?\d{1,2}:\d{2}(?::\d{2})?\)?)/g;
  const parts = text.split(regex);
  
  return parts.map((part, i) => {
    const cleanTime = part.replace(/[\[\]\(\)]/g, "");
    if (/^\d{1,2}:\d{2}(?::\d{2})?$/.test(cleanTime)) {
      return (
        <button
          key={i}
          onClick={() => onTimeJump(parseTimestampToSeconds(cleanTime))}
          className="px-1.5 py-0.5 mx-0.5 bg-[var(--accent-red-light)]/60 hover:bg-[var(--accent-red)] text-[var(--accent-red)] hover:text-white rounded-md text-[10px] font-mono font-bold transition-all border-0 outline-none cursor-pointer inline-flex items-center"
        >
          {cleanTime}
        </button>
      );
    }
    return parseInlineMarkdown(part);
  });
}

function CommentItemRenderer({ comment, onTimeJump }) {
  const { t } = useTranslation();
  const text = comment.content || comment.text || "";
  
  return (
    <div className="border border-[var(--border-primary)]/30 p-4 rounded-xl bg-[var(--bg-card)] hover:border-[#f62440]/30 shadow-2xs hover:shadow-xs transition-all select-text">
      {/* Top row: author avatar & likes */}
      <div className="flex justify-between items-center mb-3 text-xs">
        <span className="font-bold text-[var(--text-primary)] flex items-center gap-1.5 select-none">
          <span className="w-5 h-5 rounded-full bg-[var(--accent-red)]/10 flex items-center justify-center text-[10px] text-[var(--accent-red)] font-bold">👤</span>
          {comment.author || t("匿名听众", "Anonymous Listener")}
        </span>
        <span className="font-mono text-[var(--accent-red)] font-bold flex items-center gap-1 select-none">
          ❤️ {comment.likes ?? 0}
        </span>
      </div>
      
      {/* Content bubble */}
      <div className="flex items-start gap-3">
        <div className="flex-1 bg-[var(--bg-secondary)]/20 border border-[var(--border-primary)]/20 p-3 rounded-lg text-xs text-[var(--text-primary)] font-semibold leading-relaxed break-words whitespace-normal">
          {renderCommentText(text, onTimeJump)}
        </div>
      </div>
    </div>
  );
}

// ==================== 🎙️ Main View Component ====================
import { useTranslation } from "../contexts/I18nContext";

export default function PodcastDetailView({
  onBack,
  onRefreshTask,
  audioPlayerRef,
  togglePlay,
  handleProgressChange
}) {
  const { t } = useTranslation();
  const activeTask = useTaskStore(state => state.activeTask);
  const isPlaying = usePlayerStore(state => state.isPlaying);
  const currentTime = usePlayerStore(state => state.currentTime);
  const duration = usePlayerStore(state => state.duration);
  const playbackRate = usePlayerStore(state => state.playbackRate);
  const setPlaybackRate = usePlayerStore(state => state.setPlaybackRate);
  const volume = usePlayerStore(state => state.volume);
  const setVolume = usePlayerStore(state => state.setVolume);

  const [searchWord, setSearchWord] = useState("");
  const [isMuted, setIsMuted] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Layout resize state (proportion of left panel in %)
  const [leftWidth, setLeftWidth] = useState(60);
  const [isDragging, setIsDragging] = useState(false);
  const [detailSubTab, setDetailSubTab] = useState("shownotes"); // "shownotes" | "comments" | "summary" | "qa"
  // Speaker Management State
  const [showSpeakerModal, setShowSpeakerModal] = useState(false);
  const [isTriggeringRestore, setIsTriggeringRestore] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Scroll debounce state
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const scrollTimeoutRef = useRef(null);

  const handleUserScroll = () => {
    setIsUserScrolling(true);
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    scrollTimeoutRef.current = setTimeout(() => {
      setIsUserScrolling(false);
    }, 4000); // 4 seconds debounce
  };

  const containerRef = useRef(null);
  const activeBubbleRef = useRef(null);

  const handleRedownloadAudio = async () => {
    setIsTriggeringRestore(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${activeTask.id}/redownload`, {
        method: "POST"
      });
      if (res.ok) {
        if (onRefreshTask) {
          onRefreshTask();
        }
      } else {
        await alert(t("启动音频重新下载失败，请重试。", "Failed to trigger audio re-download. Please try again."));
      }
    } catch (err) {
      console.error("Error triggering redownload:", err);
      await alert(t("启动音频重新下载时发生网络错误。", "Network error triggering audio re-download."));
    } finally {
      setIsTriggeringRestore(false);
    }
  };

  // 网络错误检测与友好提示
  const getNetworkErrorHint = (errorMsg) => {
    if (!errorMsg) return null;
    const msg = errorMsg.toLowerCase();
    if (msg.includes("timeout") || msg.includes("超时")) {
      return { type: "timeout", tip: t("网络请求超时，请检查网络连接是否稳定。", "Network request timed out. Please check your internet connection.") };
    }
    if (msg.includes("dns") || msg.includes("resolve") || msg.includes("name resolution")) {
      return { type: "dns", tip: t("DNS 解析失败，请检查网络或尝试切换 DNS（如 8.8.8.8）。", "DNS resolution failed. Check your network or try switching DNS (e.g. 8.8.8.8).") };
    }
    if (msg.includes("connection refused") || msg.includes("connect") || msg.includes("网络")) {
      return { type: "network", tip: t("网络连接失败，请检查代理设置或网络状态。", "Connection failed. Please check your proxy settings or network status.") };
    }
    if (msg.includes("ssl") || msg.includes("certificate") || msg.includes("cert")) {
      return { type: "ssl", tip: t("SSL 证书错误，请检查系统时间或代理配置。", "SSL certificate error. Check system time or proxy configuration.") };
    }
    if (msg.includes("403") || msg.includes("forbidden") || msg.includes("access denied")) {
      return { type: "access", tip: t("访问被拒绝（403），该资源可能有地区限制，请尝试使用代理。", "Access denied (403). The resource may be region-restricted. Try using a proxy.") };
    }
    if (msg.includes("429") || msg.includes("rate limit")) {
      return { type: "rate", tip: t("请求过于频繁（429），请稍后再试。", "Too many requests (429). Please try again later.") };
    }
    return null;
  };

  // 重试失败/已取消的任务
  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${activeTask.id}/retry`, { method: "POST" });
      if (res.ok) {
        if (onRefreshTask) onRefreshTask();
      } else {
        const data = await res.json().catch(() => ({}));
        await alert(data.detail || t("重试失败，请刷新后重试。", "Retry failed. Please refresh and try again."));
      }
    } catch (err) {
      console.error("Error retrying task:", err);
      await alert(t("重试时发生网络错误。", "Network error while retrying."));
    } finally {
      setIsRetrying(false);
    }
  };

  // Translate seconds to MM:SS string helper
  const formatTime = (secondsCount) => {
    if (isNaN(secondsCount) || secondsCount === null) return "00:00";
    const mins = Math.floor(secondsCount / 60);
    const secs = Math.floor(secondsCount % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // SRT time format: HH:MM:SS,mmm
  const formatSrtTime = (seconds) => {
    if (isNaN(seconds) || seconds === null) return "00:00:00,000";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${h.toString().padStart(2,"0")}:${m.toString().padStart(2,"0")}:${s.toString().padStart(2,"0")},${ms.toString().padStart(3,"0")}`;
  };

  // VTT time format: HH:MM:SS.mmm
  const formatVttTime = (seconds) => {
    if (isNaN(seconds) || seconds === null) return "00:00:00.000";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${h.toString().padStart(2,"0")}:${m.toString().padStart(2,"0")}:${s.toString().padStart(2,"0")}.${ms.toString().padStart(3,"0")}`;
  };

  const handleExport = (format) => {
    if (!paragraphs || paragraphs.length === 0) return;
    const title = activeTask.title || "transcript";
    const safeName = title.replace(/[<>:"/\\|?*]/g, "_").slice(0, 60);
    let content = "";
    let ext = "";
    let mimeType = "text/plain";

    if (format === "srt") {
      ext = "srt";
      content = paragraphs.map((p, i) => {
        const speaker = p.speaker ? `${p.speaker}: ` : "";
        return `${i+1}\n${formatSrtTime(p.start_time)} --> ${formatSrtTime(p.end_time)}\n${speaker}${p.text}`;
      }).join("\n\n");
    } else {
      ext = "vtt";
      mimeType = "text/vtt";
      const body = paragraphs.map((p, i) => {
        const speaker = p.speaker ? `${p.speaker}: ` : "";
        return `${i+1}\n${formatVttTime(p.start_time)} --> ${formatVttTime(p.end_time)}\n${speaker}${p.text}`;
      }).join("\n\n");
      content = "WEBVTT\n\n" + body;
    }

    const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${safeName}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = () => {
    if (!activeTask) return;
    const title = activeTask.title || "transcript";
    const safeName = title.replace(/[<>:"/\\|?*]/g, "_").slice(0, 60);
    const metadata = activeTask.metadata || {};

    let frontmatter = "---\n";
    frontmatter += `title: "${title}"\n`;
    frontmatter += `podcast: "${activeTask.podcast_name || ""}"\n`;
    if (metadata.pub_date) frontmatter += `date: ${metadata.pub_date}\n`;
    if (metadata.duration) frontmatter += `duration: "${metadata.duration}"\n`;
    if (activeTask.url) frontmatter += `url: "${activeTask.url}"\n`;
    frontmatter += "---\n\n";

    let doc = frontmatter;
    doc += `# ${title}\n\n`;
    doc += `> ${activeTask.podcast_name || ""}`;
    if (metadata.pub_date) doc += ` · ${metadata.pub_date}`;
    if (metadata.duration) doc += ` · ${metadata.duration}`;
    doc += "\n\n";

    if (activeTask.summary) {
      doc += `## AI Summary\n\n${activeTask.summary}\n`;
    } else {
      doc += "*暂无 AI 总结*\n";
    }

    const blob = new Blob([doc], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${safeName}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
    if (!activeTask) return;
    setAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${activeTask.id}/summary/start`, {
        method: "POST"
      });
      if (res.ok) {
        await alert(t("AI总结与深度分析已排队生成，请稍候！", "AI summary and deep analysis have been queued for generation, please wait!"), { variant: 'info', confirmText: t('好的', 'OK') });
        if (onRefreshTask) onRefreshTask();
      } else {
        await alert(t("无法联系服务器发起AI总结。", "Could not connect to server to initiate AI summary."));
      }
    } catch (err) {
      console.error(err);
      await alert(t("通信出错：", "Communication error: ") + err.message);
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
    if (activeBubbleRef.current && !isUserScrolling) {
      activeBubbleRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center"
      });
    }
  }, [currentTime, isUserScrolling]);

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
  const statusMap = { completed: "Completed", failed: "Failed", cancelled: "Cancelled", pending: "Queued", downloading: "Downloading", transcribing: "Transcribing", summarizing: "Summarizing", transcribed: "Transcribed" };
  const displayStatus = statusMap[activeTask.status] || "In Progress";
  const commentsList = activeTask.metadata?.comments || [];

  return (
    <div id="session-detail-view" ref={containerRef} className="flex-1 flex flex-col h-screen font-sans bg-[var(--bg-primary)] relative">
      
      {/* Mouse dragging cover shield */}
      {isDragging && (
        <div className="fixed inset-0 cursor-col-resize z-[9999] bg-transparent" />
      )}

      {/* Detail bar Header */}
      <header className="px-10 py-5 border-b border-[var(--border-primary)]/40 bg-[var(--bg-primary)] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            id="btn-back-to-library"
            onClick={onBack}
            className="p-2 hover:bg-[var(--bg-hover)] rounded-lg transition-all text-[var(--accent-red)] cursor-pointer border-0 outline-none bg-transparent"
          >
            <ChevronLeft size={20} />
          </button>
          
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-extrabold tracking-tight text-[var(--text-primary)] font-display">
                {displayTitle}
              </h1>
              <span className={`${activeTask.status === "failed" ? "bg-red-500/20 text-red-400" : activeTask.status === "cancelled" ? "bg-gray-500/20 text-gray-400" : "bg-[var(--accent-gold)] text-[var(--text-secondary)]"} text-[10px] font-extrabold tracking-widest px-2.5 py-0.5 rounded-sm uppercase`}>
                {displayStatus}
              </span>
              {(activeTask.status === "failed" || activeTask.status === "cancelled") && (
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="flex items-center gap-1 text-xs text-[var(--accent-gold)] hover:text-[var(--text-primary)] transition-colors disabled:opacity-50"
                  title={t("重新执行此任务", "Retry this task")}
                >
                  <RefreshCw size={12} className={isRetrying ? "animate-spin" : ""} />
                  {isRetrying ? t("重试中...", "Retrying...") : t("重试", "Retry")}
                </button>
              )}
              {activeTask.status === "failed" && activeTask.error_message && (() => {
                const hint = getNetworkErrorHint(activeTask.error_message);
                return (
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <span className="text-xs text-red-400 truncate max-w-md" title={activeTask.error_message}>
                      {activeTask.error_message}
                    </span>
                    {hint && (
                      <span className="text-xs text-amber-400/80 flex items-center gap-1">
                        <span>💡</span> {hint.tip}
                      </span>
                    )}
                  </div>
                );
              })()}
              {activeTask.url && (
                <a
                  href={activeTask.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={t("打开原始播客链接", "Open original podcast link")}
                  className="p-1.5 hover:bg-[var(--bg-hover)] rounded-lg transition-all text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  <Compass size={15} />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Search transcript & AI Analysis options */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] w-4 h-4" />
            <input
              type="text"
              placeholder={t("搜索转录文本...", "Search transcript...")}
              value={searchWord}
              onChange={(e) => setSearchWord(e.target.value)}
              className="pl-9 pr-4 py-1.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg text-xs w-56 focus:outline-none focus:ring-1 focus:ring-[#f62440]"
            />
          </div>

          {(activeTask.status === "completed" || activeTask.status === "transcribed" || activeTask.status === "failed") && (
            <button
              onClick={triggerAIAnalysis}
              disabled={analyzing || activeTask.status === "summarizing"}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] disabled:bg-neutral-300 text-white text-xs font-bold rounded-lg transition-all cursor-pointer border-0 outline-none"
            >
              {analyzing || activeTask.status === "summarizing" ? (
                <RefreshCw size={13} className="animate-spin" />
              ) : (
                <Sparkles size={13} fill="white" />
              )}
              <span>{analyzing || activeTask.status === "summarizing" ? t("生成中...", "Generating...") : (activeTask.status === "completed" ? t("重新生成总结", "Regenerate Summary") : t("✨ 运行 AI 深度总结", "Run AI Summary"))}</span>
            </button>
          )}

          <button
            onClick={() => setShowSpeakerModal(true)}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] text-xs font-bold rounded-lg transition-all cursor-pointer border-0 outline-none animate-fade-in"
          >
            <Users size={13} className="text-[var(--accent-red)]" />
            <span>{t("发言人管理", "Speaker Management")}</span>
          </button>
        </div>
      </header>

      {/* Split section Workspace */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        
        {/* Left pane: Scrollable Full Transcript */}
        <div 
          className="overflow-y-auto px-10 py-8 border-r border-[var(--border-primary)]/30 h-full shrink-0 custom-scrollbar"
          style={{ width: `${leftWidth}%` }}
          onWheel={handleUserScroll}
          onTouchMove={handleUserScroll}
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-extrabold tracking-tight text-[var(--text-primary)] font-display">{t("完整转录文本", "Full Transcript")}</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleExport("srt")}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] text-xs font-bold rounded-lg transition-all cursor-pointer"
              >
                <Download size={13} className="text-[var(--accent-red)]" />
                <span>SRT</span>
              </button>
              <button
                onClick={() => handleExport("vtt")}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] text-xs font-bold rounded-lg transition-all cursor-pointer"
              >
                <Download size={13} className="text-[var(--accent-red)]" />
                <span>VTT</span>
              </button>
            </div>
          </div>
          
          {/* Transcription progress indicator */}
          <TranscriptList 
            activeTask={activeTask}
            paragraphs={paragraphs}
            searchWord={searchWord}
            currentTime={currentTime}
            activeBubbleRef={activeBubbleRef}
            jumpToTimeSeconds={jumpToTimeSeconds}
            
          />
        </div>

        {/* Resizable Divider bar */}
        <div
          onMouseDown={handleMouseDown}
          className="w-1 cursor-col-resize flex justify-center items-center select-none shrink-0 bg-[#e7bcbb]/40 hover:bg-[var(--accent-red)] transition-colors z-20"
        />

        {/* Right pane: Analysis summaries, shownotes & timelines */}
        <div 
          className="bg-[var(--bg-secondary)]/20 shrink-0 flex flex-col h-full overflow-hidden"
          style={{ width: `calc(${100 - leftWidth}% - 4px)` }}
        >
          {/* Sub-tabs header selectors */}
          <div className="flex border-b border-[var(--border-primary)]/30 bg-[var(--bg-primary)]/90 shrink-0 h-12">
            <button
              onClick={() => setDetailSubTab("shownotes")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "shownotes"
                  ? "border-[#f62440] text-[var(--accent-red)] bg-[var(--bg-secondary)]/35"
                  : "border-transparent text-[var(--text-tertiary)] hover:text-[var(--accent-red)] hover:bg-[var(--accent-red-light)]/5 bg-transparent"
              }`}
            >
              {t("节目简介", "Shownotes")}
            </button>
            <button
              onClick={() => setDetailSubTab("comments")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "comments"
                  ? "border-[#f62440] text-[var(--accent-red)] bg-[var(--bg-secondary)]/35"
                  : "border-transparent text-[var(--text-tertiary)] hover:text-[var(--accent-red)] hover:bg-[var(--accent-red-light)]/5 bg-transparent"
              }`}
            >
              {t("听众热评", "Listener Comments")}
            </button>
            <button
              onClick={() => setDetailSubTab("summary")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "summary"
                  ? "border-[#f62440] text-[var(--accent-red)] bg-[var(--bg-secondary)]/35"
                  : "border-transparent text-[var(--text-tertiary)] hover:text-[var(--accent-red)] hover:bg-[var(--accent-red-light)]/5 bg-transparent"
              }`}
            >
              {t("AI 总结", "AI Summary")}
            </button>
            <button
              onClick={() => setDetailSubTab("qa")}
              className={`flex-1 font-sans text-xs uppercase tracking-wider font-bold transition-all border-b-2 outline-none cursor-pointer ${
                detailSubTab === "qa"
                  ? "border-[#f62440] text-[var(--accent-red)] bg-[var(--bg-secondary)]/35"
                  : "border-transparent text-[var(--text-tertiary)] hover:text-[var(--accent-red)] hover:bg-[var(--accent-red-light)]/5 bg-transparent"
              }`}
            >
              {t("问答", "Q&A")}
            </button>
          </div>

          {/* Sub-tab scrollable content */}
          <div className="flex-1 overflow-y-auto px-8 py-8 flex flex-col gap-6 custom-scrollbar">
            {detailSubTab === "shownotes" && (
              <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs animate-fade-in select-text">
                <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-primary)]/30 mb-5 text-[var(--accent-red)] select-none">
                  <FileText size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-[13px] font-extrabold uppercase tracking-widest text-[var(--text-primary)] font-display">{t("节目大纲时间线", "Shownotes Timeline")}</h3>
                </div>
                <ShownotesRenderer text={activeTask.metadata?.shownotes} onTimeJump={jumpToTimeSeconds} />
              </div>
            )}

            {detailSubTab === "comments" && (
              <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs animate-fade-in select-text">
                <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-primary)]/30 mb-5 text-[var(--accent-red)] select-none">
                  <MessageSquare size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-[13px] font-extrabold uppercase tracking-widest text-[var(--text-primary)] font-display">{t("听众热门评论", "Hot Listener Comments")}</h3>
                </div>

                <div className="flex flex-col gap-4">
                  {commentsList.length > 0 ? (
                    commentsList.map((comment, cIdx) => (
                      <CommentItemRenderer key={cIdx} comment={comment} onTimeJump={jumpToTimeSeconds} />
                    ))
                  ) : (
                    <div className="border-2 border-dashed border-[var(--border-primary)]/40 p-8 text-center rounded-xl select-none">
                      <span className="text-xs text-[var(--text-muted)] font-bold uppercase tracking-wider">{t("暂无被索引的评论", "No comments indexed")}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {detailSubTab === "summary" && (
              <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs select-text animate-fade-in">
                <div className="flex items-center justify-between pb-4 border-b border-[var(--border-primary)]/30 mb-5 text-[var(--accent-red)] select-none">
                  <div className="flex items-center gap-2">
                    <Sparkles size={18} className="text-[var(--accent-red)]" />
                    <h3 className="text-[13px] font-extrabold uppercase tracking-widest text-[var(--text-primary)] font-display">{t("AI 价值分析报告", "AI VALUE ANALYSIS REPORT")}</h3>
                  </div>
                  {activeTask.summary && (
                    <button
                      onClick={handleExportMarkdown}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] text-xs font-bold rounded-lg transition-all cursor-pointer"
                    >
                      <Download size={13} className="text-[var(--accent-red)]" />
                      <span>MD</span>
                    </button>
                  )}
                </div>

                {activeTask.status === "summarizing" ? (
                  <div className="flex flex-col items-center justify-center py-12 gap-4">
                    <div className="w-10 h-10 border-3 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm text-[var(--text-muted)] font-semibold">
                      {t("AI 正在深度分析转录文本...", "AI is analyzing the transcript...")}
                    </p>
                  </div>
                ) : activeTask.summary ? (
                  <MarkdownRenderer text={activeTask.summary} />
                ) : (
                  <div className="border-2 border-dashed border-[var(--border-primary)]/40 p-8 text-center rounded-xl select-none">
                    <span className="text-xs text-[var(--text-muted)] font-bold uppercase tracking-wider">{t("暂无总结内容", "No summary available")}</span>
                  </div>
                )}
              </div>
            )}

            {detailSubTab === "qa" && (
              <QAChatPanel 
                activeTask={activeTask} 
                MarkdownRenderer={MarkdownRenderer} 
                 
              />
            )}
          </div>
        </div>

      </div>

      {/* Pinned Playback bottom bar panel */}
      <AudioPlayerControl 
        activeTask={activeTask}
        isPlaying={isPlaying}
        togglePlay={togglePlay}
        currentTime={currentTime}
        duration={duration}
        playbackRate={playbackRate}
        handleProgressChange={handleProgressChange}
        handleStepBack={handleStepBack}
        handleStepForward={handleStepForward}
        handleSpeedToggle={handleSpeedToggle}
        isMuted={isMuted}
        volume={volume}
        handleVolumeInput={handleVolumeInput}
        toggleMute={toggleMute}
        formatTime={formatTime}
        isTriggeringRestore={isTriggeringRestore}
        handleRedownloadAudio={handleRedownloadAudio}
        
      />

      {/* Speaker Management Modal */}
      <SpeakerManagerModal 
        activeTask={activeTask}
        showSpeakerModal={showSpeakerModal}
        setShowSpeakerModal={setShowSpeakerModal}
        onRefreshTask={onRefreshTask}
        
      />
    </div>
  );
}
