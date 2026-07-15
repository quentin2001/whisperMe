import React from 'react';
import { Play, Pause, Volume2, VolumeX } from "lucide-react";
import { usePlayerStore } from "../../store/playerStore.js";
import { proxyImage } from "../../constants.js";
import { useTranslation } from "../../contexts/I18nContext";

export function RotateCcwWithNumber({ number, size = 20, className = "" }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`lucide lucide-rotate-ccw ${className}`}
    >
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <text
        x="12"
        y="15.2"
        textAnchor="middle"
        fontSize="7.5"
        fontWeight="800"
        fill="currentColor"
        stroke="none"
        fontFamily="monospace"
      >
        {number}
      </text>
    </svg>
  );
}

export function RotateCwWithNumber({ number, size = 20, className = "" }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`lucide lucide-rotate-cw ${className}`}
    >
      <path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
      <text
        x="12"
        y="15.2"
        textAnchor="middle"
        fontSize="7.5"
        fontWeight="800"
        fill="currentColor"
        stroke="none"
        fontFamily="monospace"
      >
        {number}
      </text>
    </svg>
  );
}

export function SpeedDropdown({ playbackRate, handleSpeedChange }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef(null);
  const { t } = useTranslation();

  React.useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const speeds = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 3.0];

  const formatSpeed = (rate) => {
    const labels = {
      0.75: "0.75x",
      1.0: "1.0x",
      1.25: "1.25x",
      1.5: "1.5x",
      1.75: "1.75x",
      2.0: "2.0x",
      3.0: "3.0x"
    };
    return labels[rate] || `${rate.toFixed(1)}x`;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-2 py-1 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 hover:border-[var(--accent-red)]/30 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-semibold rounded-lg transition-all cursor-pointer flex items-center gap-1.5 outline-none select-none"
      >
        <span>{formatSpeed(playbackRate)}</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
        >
          <path d="m18 15-6-6-6 6" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute bottom-full right-0 mb-2 z-50 w-24 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg shadow-lg py-1 flex flex-col animate-fade-in">
          {speeds.map((speed) => (
            <button
              key={speed}
              onClick={() => {
                handleSpeedChange(speed);
                setIsOpen(false);
              }}
              className="w-full px-3 py-1.5 text-left text-xs font-semibold hover:bg-[var(--bg-hover)] transition-all cursor-pointer border-0 bg-transparent flex items-center justify-between gap-2"
              style={{
                color: speed === playbackRate ? "var(--accent-red)" : "var(--text-primary)"
              }}
            >
              <span>{formatSpeed(speed)}</span>
              {speed === playbackRate && (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}


export default function AudioPlayerControl({
  activeTask,
  isPlaying,
  togglePlay,
  currentTime,
  duration,
  playbackRate,
  handleProgressChange,
  handleJump,
  handleSpeedChange,
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
                className="w-full accent-[var(--accent-red)] h-1.5 bg-[var(--bg-hover)] rounded-lg cursor-pointer appearance-none"
                style={{
                  background: `linear-gradient(to right, var(--accent-red) ${(currentTime / Math.max(1, duration || 1)) * 100}%, var(--bg-hover) ${(currentTime / Math.max(1, duration || 1)) * 100}%)`
                }}
              />
            </div>
            <span className="text-xs font-mono font-bold text-[var(--text-muted)]">
              {formatTime(duration)}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => handleJump(-15)}
              className="w-8 h-8 flex items-center justify-center rounded-full border border-[var(--border-primary)]/30 text-[#926e6d] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all cursor-pointer bg-transparent outline-none"
              title="-15s"
            >
              <RotateCcwWithNumber number={15} size={16} />
              <span className="sr-only">-15s</span>
            </button>
            <button
              onClick={() => handleJump(-5)}
              className="w-8 h-8 flex items-center justify-center rounded-full border border-[var(--border-primary)]/30 text-[#926e6d] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all cursor-pointer bg-transparent outline-none"
              title="-5s"
            >
              <RotateCcwWithNumber number={5} size={16} />
              <span className="sr-only">-5s</span>
            </button>
            <button
              onClick={togglePlay}
              className="w-10 h-10 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white flex items-center justify-center rounded-full shadow-md active:scale-95 transition-all text-sm cursor-pointer border-0 outline-none shrink-0 mx-2"
            >
              {isPlaying ? <Pause size={16} fill="white" /> : <Play size={16} fill="white" className="ml-0.5" />}
            </button>
            <button
              onClick={() => handleJump(10)}
              className="w-8 h-8 flex items-center justify-center rounded-full border border-[var(--border-primary)]/30 text-[#926e6d] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all cursor-pointer bg-transparent outline-none"
              title="+10s"
            >
              <RotateCwWithNumber number={10} size={16} />
              <span className="sr-only">+10s</span>
            </button>
            <button
              onClick={() => handleJump(30)}
              className="w-8 h-8 flex items-center justify-center rounded-full border border-[var(--border-primary)]/30 text-[#926e6d] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-all cursor-pointer bg-transparent outline-none"
              title="+30s"
            >
              <RotateCwWithNumber number={30} size={16} />
              <span className="sr-only">+30s</span>
            </button>
          </div>
        </div>
      )}

      <div className="w-1/4 flex items-center justify-end gap-3 font-semibold text-xs animate-fade-in">
        {activeTask.audio_url && (
          <>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-secondary)] text-[10px] whitespace-nowrap font-mono select-none">
                {t("语速", "Speed")}
              </span>
              <SpeedDropdown playbackRate={playbackRate} handleSpeedChange={handleSpeedChange} />
            </div>

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
                className="w-20 accent-[var(--accent-red)] h-1 bg-[var(--bg-hover)] rounded-lg cursor-pointer"
              />
            </div>
          </>
        )}
      </div>
    </footer>
  );
}
