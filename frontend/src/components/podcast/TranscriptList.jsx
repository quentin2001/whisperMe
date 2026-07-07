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
      {/* Ingest Stepper Progress Header */}
      {(activeTask.status === "downloading" || activeTask.status === "diarizing" || activeTask.status === "transcribing") && (
        <div className="sticky top-0 z-30 -mt-2 mb-6 p-4 bg-[var(--bg-card)]/95 backdrop-blur-md border border-[var(--border-primary)]/50 rounded-xl shadow-md animate-fade-in">
          {/* Detailed Stats Header */}
          <div className="flex items-center justify-between text-xs font-bold text-[var(--text-primary)]">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-[var(--accent-red)] animate-pulse" />
              <span>
                {activeTask.status === "downloading" && t("⚡ 正在获取与下载音频文件...", "⚡ Downloading audio file...")}
                {activeTask.status === "diarizing" && t("⚡ 正在识别与分离说话人声...", "⚡ Distinguishing speaker voices...")}
                {activeTask.status === "transcribing" && t("⚡ 正在实时转写文字剧本...", "⚡ Transcribing spoken words...")}
              </span>
            </div>
            <span className="font-mono text-[var(--accent-red)]">{Math.round(activeTask.progress || 0)}%</span>
          </div>

          {/* Stepper Pipeline Indicators */}
          <div className="flex items-center justify-between gap-3 mt-1">
            {/* Step 1: Downloading */}
            <div className="flex-1 flex flex-col gap-1.5">
              <div className={`h-1.5 rounded-full transition-all duration-300 ${
                activeTask.status === "downloading" ? "bg-[var(--accent-red)] animate-pulse" : "bg-green-500"
              }`} />
              <span className="text-[10px] text-center font-extrabold tracking-wider uppercase text-[var(--text-tertiary)]">{t("1. 下载", "1. Download")}</span>
            </div>

            {/* Step 2: Diarizing (Conditional: Only show if enable_speaker_inference is true or not explicitly false) */}
            {activeTask.metadata?.enable_speaker_inference !== false && (
              <div className="flex-1 flex flex-col gap-1.5 animate-fade-in">
                <div className={`h-1.5 rounded-full transition-all duration-300 ${
                  activeTask.status === "downloading" ? "bg-[var(--border-primary)]/40"
                  : activeTask.status === "diarizing" ? "bg-[var(--accent-red)] animate-pulse"
                  : "bg-green-500"
                }`} />
                <span className="text-[10px] text-center font-extrabold tracking-wider uppercase text-[var(--text-tertiary)]">{t("2. 声纹", "2. Diarization")}</span>
              </div>
            )}

            {/* Step 3: Transcribing */}
            <div className="flex-1 flex flex-col gap-1.5">
              <div className={`h-1.5 rounded-full transition-all duration-300 ${
                activeTask.status === "transcribing" ? "bg-[var(--accent-red)] animate-pulse" : "bg-[var(--border-primary)]/40"
              }`} />
              <span className="text-[10px] text-center font-extrabold tracking-wider uppercase text-[var(--text-tertiary)]">{
                activeTask.metadata?.enable_speaker_inference !== false ? t("3. 转写", "3. ASR") : t("2. 转写", "2. ASR")
              }</span>
            </div>
          </div>

          {/* Real-time stats footer */}
          <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)] font-bold border-t border-[var(--border-primary)]/20 pt-2">
            <span>
              {activeTask.status === "transcribing" && paragraphs.length > 0 && (
                `${t("当前已转写", "Transcribed")}: ${paragraphs.length} ${t("段落", "paragraphs")}`
              )}
            </span>
            <span>
              {activeTask.status === "downloading" && activeTask.progress > 0 && (
                `${t("进度", "Progress")}: ${Math.round(activeTask.progress)}%`
              )}
            </span>
          </div>
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
