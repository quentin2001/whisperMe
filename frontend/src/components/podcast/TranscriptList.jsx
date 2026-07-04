import React, { memo } from 'react';
import { AlertCircle } from "lucide-react";

import { useTranslation } from "../../contexts/I18nContext";

const TranscriptList = memo(function TranscriptList({
  activeTask,
  paragraphs,
  searchWord,
  currentTime,
  activeBubbleRef,
  jumpToTimeSeconds
}) {
  const { t } = useTranslation();
  return (
    <>
      {/* Transcription progress indicator */}
      {(activeTask.status === "downloading" || activeTask.status === "transcribing") && (
        <div className="flex items-center gap-2 mb-4 px-3 py-2 bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-lg">
          <div className="w-3 h-3 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-[var(--accent-red)] font-semibold">
            {activeTask.status === "downloading"
              ? t("正在下载音频...", "Downloading audio...")
              : t("转录进行中...", "Transcribing...") + (paragraphs.length > 0 ? ` (${paragraphs.length} ${t("段", "paragraphs")})` : "")
            }
          </span>
        </div>
      )}

      {/* HF Token 缺失降级提示 */}
      {activeTask.hf_token_missing && (
        <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-xs font-semibold text-yellow-600">
          <AlertCircle size={14} />
          <span>{t("本次转录未启用说话人识别（HuggingFace Token 未配置）。", "Speaker identification was skipped — HuggingFace Token not configured.")}</span>
        </div>
      )}

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
                    ? "bg-[var(--bg-card)] border-[#f62440] ring-1 ring-[#f62440]/10 shadow-xs" 
                    : "border-transparent hover:bg-[var(--bg-card)]/40 hover:border-[var(--border-primary)]/20"
                }`}
              >
                <p className="font-mono text-xs text-[var(--accent-red)] font-bold mb-1.5 hover:underline">
                  {p.timeStart} — {p.timeEnd}
                </p>
                <div className="mb-2.5">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[var(--accent-red)]/8 text-[var(--accent-red)] font-bold text-[10px] tracking-wider uppercase select-none">
                    👤 {p.speaker}
                  </span>
                </div>
                <p className="text-[var(--text-primary)] text-[15px] leading-relaxed select-text font-medium">
                  {p.text}
                </p>
              </div>
            );
        })}
      </div>
    </>
  );
});

export default TranscriptList;
