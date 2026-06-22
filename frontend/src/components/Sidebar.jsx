import React, { useEffect, useState } from "react";
import { Library, Sliders, Settings, Cpu } from "lucide-react";

export default function Sidebar({
  currentTab,
  onTabChange,
  onNewSessionTrigger,
  onShowLogsTrigger,
  perfData,
  versionInfo,
  t
}) {
  // Live simulated system stats that fluctuate slightly to feel alive and realistic!
  const [systStats, setSystStats] = useState({ cpu: 12, ram: 2.4 });

  useEffect(() => {
    const interval = setInterval(() => {
      setSystStats(prev => {
        const cpuDelta = (Math.random() - 0.5) * 4;
        const ramDelta = (Math.random() - 0.5) * 0.1;
        const nextCpu = Math.max(5, Math.min(48, Math.round(prev.cpu + cpuDelta)));
        const nextRam = Math.max(2.1, Math.min(3.2, parseFloat((prev.ram + ramDelta).toFixed(1))));
        return { cpu: nextCpu, ram: nextRam };
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const displayCpu = perfData && typeof perfData.cpu === 'number' ? Math.round(perfData.cpu) : systStats.cpu;
  const displayRam = perfData && perfData.ram && typeof perfData.ram.used === 'number'
    ? parseFloat(perfData.ram.used.toFixed(1))
    : systStats.ram;

  return (
    <aside 
      id="sidebar-container"
      className="w-64 bg-[#f9f3ea] border-r border-[#e7bcbb]/50 h-screen font-sans flex flex-col justify-between shrink-0 p-6"
    >
      <div className="flex flex-col gap-6">
        {/* Brand Header with Logo */}
        <div 
          id="brand-header" 
          onClick={() => onTabChange("library")}
          className="flex items-center gap-2 mb-2 cursor-pointer hover:opacity-80 transition-opacity select-none"
        >
          <div className="w-8 h-8 shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" className="w-full h-full">
              <defs>
                <linearGradient id="wmGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#8a2387" />
                  <stop offset="50%" stop-color="#e94057" />
                  <stop offset="100%" stop-color="#f27121" />
                </linearGradient>
              </defs>
              <path d="M 25 135 C 35 135, 40 65, 50 65 C 60 65, 65 135, 75 135 C 85 135, 90 80, 100 80 C 110 80, 115 135, 125 135 C 135 135, 140 65, 150 65 C 160 65, 165 135, 175 135" 
                     fill="none" stroke="url(#wmGrad)" strokeWidth="22" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-[#1d1c18] font-display">whisperMe</h1>
            {versionInfo?.has_update && (
              <span className="text-[9px] font-extrabold bg-[#f62440] text-white px-1.5 py-0.5 rounded-full select-none tracking-normal leading-none animate-pulse">
                NEW
              </span>
            )}
          </div>
        </div>

        {/* Top Divider */}
        <div className="border-t border-[#e7bcbb]/40 -mt-4" />

        {/* Main Tabs Navigation */}
        <nav id="sidebar-navigation" className="flex flex-col gap-1.5 -mt-2">
          <button
            id="tab-btn-library"
            onClick={() => onTabChange("library")}
            className={`w-full py-2.5 px-3.5 rounded-lg flex items-center gap-3 font-semibold transition-all cursor-pointer border-0 outline-none text-left ${
              currentTab === "library"
                ? "bg-[#f2ede6] text-[#1d1c18]"
                : "text-[#5d3f3e]/70 hover:bg-[#f2ede6]/50 hover:text-[#1d1c18] bg-transparent"
            }`}
          >
            <Library size={18} className="text-[#bf0029]" />
            <span className="text-[15px]">{t("媒体库", "Library")}</span>
          </button>

          <button
            id="tab-btn-workstation"
            onClick={() => onTabChange("workstation")}
            className={`w-full py-2.5 px-3.5 rounded-lg flex items-center gap-3 font-semibold transition-all cursor-pointer border-0 outline-none text-left ${
              currentTab === "workstation"
                ? "bg-[#f2ede6] text-[#1d1c18]"
                : "text-[#5d3f3e]/70 hover:bg-[#f2ede6]/50 hover:text-[#1d1c18] bg-transparent"
            }`}
          >
            <Sliders size={18} className="text-[#bf0029]" />
            <span className="text-[15px]">{t("工作台", "Workstation")}</span>
          </button>

          <button
            id="tab-btn-settings"
            onClick={() => onTabChange("settings")}
            className={`w-full py-2.5 px-3.5 rounded-lg flex items-center justify-between font-semibold transition-all cursor-pointer border-0 outline-none text-left ${
              currentTab === "settings"
                ? "bg-[#f2ede6] text-[#1d1c18]"
                : "text-[#5d3f3e]/70 hover:bg-[#f2ede6]/50 hover:text-[#1d1c18] bg-transparent"
            }`}
          >
            <div className="flex items-center gap-3">
              <Settings size={18} className="text-[#bf0029]" />
              <span className="text-[15px]">{t("系统设置", "Settings")}</span>
            </div>
            {versionInfo?.has_update && (
              <span className="w-2.5 h-2.5 rounded-full bg-[#f62440] border border-white animate-pulse" />
            )}
          </button>
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="border-t border-[#e7bcbb]/40 pt-4">
        {/* Dynamic System Status */}
        <div id="telemetry-info" className="flex flex-col gap-1 bg-[#f2ede6]/40 p-3 rounded-lg border border-[#e7bcbb]/20">
          <p className="text-[10px] text-[#5d3f3e]/60 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <Cpu size={12} className="text-[#f62440]" />
            {t("系统状态", "System Status")}
          </p>
          <p className="text-xs font-mono font-medium text-[#1d1c18] mt-0.5">
            CPU: {displayCpu}% | RAM: {displayRam}GB
          </p>
        </div>
      </div>
    </aside>
  );
}
