import { memo } from 'react';

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

  // Find the active paragraph ID using closest-previous-start logic:
  // Segment starts at or before currentTime (and ends before next segment starts).
  let activeParagraphId = null;
  for (let i = paragraphs.length - 1; i >= 0; i--) {
    if (paragraphs[i].start_time <= currentTime) {
      activeParagraphId = paragraphs[i].id;
      break;
    }
  }

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

      <div className="flex flex-col gap-6">
        {paragraphs
          .filter(p => p.text.toLowerCase().includes(searchWord.toLowerCase()))
          .map((p) => {
            const isActive = p.id === activeParagraphId;

            let activeSentenceIndex = -1;
            if (isActive && p.sentences && p.sentences.length > 0) {
              for (let sIdx = 0; sIdx < p.sentences.length; sIdx++) {
                if (currentTime >= p.sentences[sIdx].start) {
                  activeSentenceIndex = sIdx;
                } else {
                  break;
                }
              }
              if (activeSentenceIndex === -1) {
                activeSentenceIndex = 0;
              }
            }

            return (
              <div 
                key={p.id}
                onClick={() => jumpToTimeSeconds(p.start_time)}
                ref={isActive ? activeBubbleRef : null}
                className={`p-4 rounded-lg cursor-pointer transition-all border border-l-4 ${
                  isActive 
                    ? "bg-[var(--accent-red)]/[0.03] border-transparent border-l-[#f62440]" 
                    : "border-transparent border-l-transparent hover:bg-[var(--bg-card)]/40 hover:border-[var(--border-primary)]/20 hover:border-l-transparent"
                }`}
              >
                <p className="font-mono text-xs text-[var(--accent-red)] font-bold mb-1.5 hover:underline">
                  {p.timeStart} — {p.timeEnd}
                </p>
                {/* Speaker indicator hidden as requested */}
                <p className="text-[15px] leading-relaxed select-text transition-colors duration-200">
                  {p.sentences && p.sentences.length > 0 ? (
                    p.sentences.map((s, sIdx) => {
                      const isSentenceActive = isActive && sIdx === activeSentenceIndex;
                      return (
                        <span
                          key={sIdx}
                          onClick={(e) => {
                            e.stopPropagation();
                            jumpToTimeSeconds(s.start);
                          }}
                          className={`transition-all duration-150 cursor-pointer px-1 py-0.5 rounded mx-0.5 inline ${
                            isSentenceActive
                              ? "bg-[var(--accent-red)]/15 text-[var(--text-primary)] font-bold"
                              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-red)]/8 font-medium"
                          }`}
                        >
                          {s.text}
                        </span>
                      );
                    })
                  ) : (
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        jumpToTimeSeconds(p.start_time);
                      }}
                      className={`transition-all duration-150 cursor-pointer px-1 py-0.5 rounded mx-0.5 inline ${
                        isActive
                          ? "bg-[var(--accent-red)]/15 text-[var(--text-primary)] font-bold"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-red)]/8 font-medium"
                      }`}
                    >
                      {p.text}
                    </span>
                  )}
                </p>
              </div>
            );
        })}
      </div>
    </>
  );
});

export default TranscriptList;
