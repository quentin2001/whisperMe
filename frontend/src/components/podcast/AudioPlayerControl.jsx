import React from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX } from "lucide-react";
import { usePlayerStore } from "../../store/playerStore.js";
import { proxyImage } from "../../constants.js";
import { useTranslation } from "../../contexts/I18nContext";

export default function AudioPlayerControl({
  activeTask,
  isPlaying,
  togglePlay,
  currentTime,
  duration,
  playbackRate,
  handleProgressChange,
  handleStepBack,
  handleStepForward,
  handleSpeedToggle,
  isMuted,
  volume,
  handleVolumeInput,
  toggleMute,
  formatTime,
  isTriggeringRestore,
  handleRedownloadAudio
}) {
  const { t } = useTranslation();
  const displayTitle = activeTask?.title || "Untitled Session";

  return (
    <footer className="h-24 border-t border-[var(--border-primary)]/40 bg-[var(--bg-card)] px-8 flex items-center justify-between shrink-0 select-none">
      <div className="w-1/4 flex items-center gap-3">
        <div className="w-11 h-11 bg-[var(--accent-red)] rounded-lg overflow-hidden shadow-sm shrink-0 relative">
          {activeTask.image_url ? (
            <>
              <div className="w-full h-full flex flex-col justify-center items-center text-white font-bold tracking-tight absolute inset-0">
                <span className="text-[10px] uppercase font-mono tracking-wide leading-none">
                  {(activeTask.podcast_name || activeTask.title || "WM").charAt(0)}
                </span>
              </div>
              <img
                src={proxyImage(activeTask.image_url)}
                alt=""
                referrerPolicy="no-referrer"
                className="w-full h-full object-cover absolute inset-0"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </>
          ) : (
            <div className="w-full h-full flex flex-col justify-center items-center text-white font-bold tracking-tight">
              <span className="text-[10px] uppercase font-mono tracking-wide leading-none">
                {(activeTask.podcast_name || activeTask.title || "WM").charAt(0)}
              </span>
            </div>
          )}
        </div>
        <div className="hidden sm:block overflow-hidden">
          <h4 className="font-bold text-xs text-[var(--text-primary)] font-display max-w-[200px] truncate">{displayTitle}</h4>
          <p className="text-[10px] font-semibold text-[var(--accent-red)] uppercase tracking-wider mt-0.5 animate-pulse">
            {!activeTask.audio_url
              ? (activeTask.restoring ? t("音频重新下载中...", "Re-downloading Audio") : t("音频已被清理", "Audio Cleaned Up"))
              : (isPlaying ? t("解码播放中", "Active Playback Decoding") : t("播放空闲", "Playback Idle"))}
          </p>
        </div>
      </div>

      {!activeTask.audio_url ? (
        <div className="flex-1 max-w-2xl flex items-center justify-between bg-[var(--bg-primary)]/60 border border-[var(--border-primary)]/40 rounded-xl px-6 py-2.5 shadow-xs">
          <div className="flex items-center gap-3 flex-1 mr-4">
            <span className="text-lg">🗑️</span>
            <div className="text-left flex-1">
              <p className="text-xs font-bold text-[var(--text-primary)]">
                {activeTask.restoring 
                  ? t("正在从原始地址重新下载音频文件...", "Re-downloading audio file from source...") 
                  : t("音频文件已被自动清理以节省硬盘空间", "Audio file has been auto-cleaned to save disk space")}
              </p>
              {activeTask.restoring && (
                <div className="w-full max-w-md bg-[var(--bg-hover)] h-1.5 rounded-full overflow-hidden mt-1.5 relative">
                  <div 
                    className="bg-[var(--accent-red)] h-full transition-all duration-300" 
                    style={{ width: `${activeTask.restore_progress || 0}%` }}
                  />
                </div>
              )}
            </div>
          </div>
          
          <div>
            {activeTask.restoring ? (
              <span className="text-xs font-mono font-bold text-[var(--accent-red)] animate-pulse whitespace-nowrap">
                {typeof activeTask.restore_progress === 'number' ? Math.round(activeTask.restore_progress) : 0}%
              </span>
            ) : (
              <button
                onClick={handleRedownloadAudio}
                disabled={isTriggeringRestore}
                className="px-4 py-1.5 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] disabled:opacity-50 text-white font-bold rounded-lg text-xs shadow-xs hover:shadow-md cursor-pointer border-0 outline-none transition-all whitespace-nowrap"
              >
                {isTriggeringRestore ? t("启动中...", "Starting...") : t("重新下载音频", "Re-download Audio")}
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 max-w-2xl flex flex-col items-center gap-2">
          <div className="w-full flex items-center gap-3">
            <span className="text-xs font-mono font-bold text-[var(--accent-red)]">
              {formatTime(currentTime)}
            </span>
            <div className="flex-1 relative flex items-center">
              <input
                type="range"
                min={0}
                max={Math.max(1, duration || 0)}
                value={currentTime || 0}
                onChange={handleProgressChange}
                className="w-full accent-[#f62440] h-1.5 bg-[var(--bg-hover)] rounded-lg cursor-pointer appearance-none"
              />
            </div>
            <span className="text-xs font-mono font-bold text-[var(--text-muted)]">
              {formatTime(duration)}
            </span>
          </div>

          <div className="flex items-center gap-5">
            <button
              onClick={handleStepBack}
              className="p-1.5 hover:bg-[var(--bg-hover)] rounded text-[#926e6d] hover:text-[var(--text-primary)] transition-all cursor-pointer border-0 outline-none bg-transparent"
            >
              <SkipBack size={15} />
            </button>
            <button
              onClick={togglePlay}
              className="w-10 h-10 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white flex items-center justify-center rounded-full shadow-md active:scale-95 transition-all text-sm cursor-pointer border-0 outline-none"
            >
              {isPlaying ? <Pause size={16} fill="white" /> : <Play size={16} fill="white" className="ml-0.5" />}
            </button>
            <button
              onClick={handleStepForward}
              className="p-1.5 hover:bg-[var(--bg-hover)] rounded text-[#926e6d] hover:text-[var(--text-primary)] transition-all cursor-pointer border-0 outline-none bg-transparent"
            >
              <SkipForward size={15} />
            </button>
          </div>
        </div>
      )}

      <div className="w-1/4 flex items-center justify-end gap-3 font-semibold text-xs animate-fade-in">
        {activeTask.audio_url && (
          <>
            <button
              onClick={handleSpeedToggle}
              className="px-2.5 py-1 bg-[var(--bg-hover)] text-[var(--text-secondary)] rounded-md border border-[var(--border-primary)]/30 active:scale-98 transition-all cursor-pointer border-0 outline-none"
            >
              {t("语速", "Speed")} {playbackRate.toFixed(1)}x
            </button>

            <div className="flex items-center gap-1.5">
              <button
                onClick={toggleMute}
                className="p-1 text-[#926e6d] hover:text-[var(--text-primary)] cursor-pointer border-0 outline-none bg-transparent"
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
                className="w-20 accent-[#f62440] h-1 bg-[var(--bg-hover)] rounded-lg cursor-pointer"
              />
            </div>
          </>
        )}
      </div>
    </footer>
  );
}
