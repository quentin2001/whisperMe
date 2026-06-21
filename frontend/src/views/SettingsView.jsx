import React, { useState } from "react";
import { Sliders, Save, Database, ShieldAlert, Cpu, Terminal, Bell } from "lucide-react";

export default function SettingsView({
  configData,
  handleConfigChange,
  handleSaveConfig,
  onResetData,
  promptData,
  setPromptData,
  promptSaveStatus,
  handleSavePrompt,
  handleResetPrompt
}) {
  const [language, setLanguage] = useState("zh-CN");
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);

  return (
    <div id="settings-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        <div className="mb-8">
          <h2 className="text-4xl font-extrabold tracking-tight text-[#1d1c18] font-display">Settings</h2>
          <p className="text-sm text-[#5d5a55]/80 mt-1 font-medium">Fine-tune acoustic processing thresholds and neural transcription engine models.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Config Panels */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            
            {/* Card 1: ASR Settings */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Sliders size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">ASR Engine Settings</h3>
              </div>

              {/* Engine Mode */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Engine Mode</label>
                <select
                  value={configData.asr_mode || "local"}
                  onChange={(e) => handleConfigChange("asr_mode", e.target.value)}
                  className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                >
                  <option value="local">LOCAL OFFLINE (FASTER-WHISPER)</option>
                  <option value="online">ONLINE API</option>
                </select>
              </div>

              {/* Local Mode Subfields */}
              {configData.asr_mode === "local" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Local Model Path</label>
                    <input
                      type="text"
                      value={configData.local_whisper_model_path || ""}
                      onChange={(e) => handleConfigChange("local_whisper_model_path", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="/path/to/whisper/models/large-v3.bin"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">HF Token (Diarization)</label>
                    <input
                      type="password"
                      value={configData.hf_token || ""}
                      onChange={(e) => handleConfigChange("hf_token", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                  </div>
                </>
              )}

              {/* Online Mode Subfields */}
              {configData.asr_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">API Base URL</label>
                    <input
                      type="text"
                      value={configData.online_base_url || ""}
                      onChange={(e) => handleConfigChange("online_base_url", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="https://api.openai.com/v1"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Model ID</label>
                    <input
                      type="text"
                      value={configData.online_model || ""}
                      onChange={(e) => handleConfigChange("online_model", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="whisper-1"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">API Key</label>
                    <input
                      type="password"
                      value={configData.online_api_key || ""}
                      onChange={(e) => handleConfigChange("online_api_key", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                  </div>
                </>
              )}
            </div>

            {/* Card 2: LLM Summary Settings */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Cpu size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">LLM Summary Settings</h3>
              </div>

              {/* LLM Mode */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">LLM Mode</label>
                <select
                  value={configData.summary_mode || "online"}
                  onChange={(e) => handleConfigChange("summary_mode", e.target.value)}
                  className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                >
                  <option value="local">LOCAL (OLLAMA)</option>
                  <option value="online">ONLINE API (OPENAI COMPATIBLE)</option>
                </select>
              </div>

              {/* Local Ollama Subfields */}
              {configData.summary_mode === "local" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Local API URL</label>
                    <input
                      type="text"
                      value={configData.ollama_url || ""}
                      onChange={(e) => handleConfigChange("ollama_url", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="http://localhost:11434"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Model ID</label>
                    <input
                      type="text"
                      value={configData.ollama_model || ""}
                      onChange={(e) => handleConfigChange("ollama_model", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="qwen2.5:7b-instruct"
                    />
                  </div>
                </>
              )}

              {/* Online OpenAI Compatible Subfields */}
              {configData.summary_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Online API Base URL</label>
                    <input
                      type="text"
                      value={configData.online_summary_base_url || ""}
                      onChange={(e) => handleConfigChange("online_summary_base_url", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="https://api.openai.com/v1"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Online Model ID</label>
                    <input
                      type="text"
                      value={configData.online_summary_model || ""}
                      onChange={(e) => handleConfigChange("online_summary_model", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="gpt-4o-mini"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">API Key</label>
                    <input
                      type="password"
                      value={configData.online_summary_api_key || ""}
                      onChange={(e) => handleConfigChange("online_summary_api_key", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                  </div>
                </>
              )}
            </div>

            {/* Card: LLM Prompt Template Settings */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center justify-between pb-4 border-b border-[#e7bcbb]/20">
                <div className="flex items-center gap-2">
                  <Terminal size={18} className="text-[#bf0029]" />
                  <h3 className="text-lg font-bold text-[#1d1c18]">总结 Prompt 模板</h3>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleResetPrompt}
                    className="px-3 py-1.5 bg-[#f2ede6] text-[#5d3f3e] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded-lg cursor-pointer transition-all border-0 outline-none"
                  >
                    ↩️ 恢复默认
                  </button>
                  <button
                    type="button"
                    onClick={handleSavePrompt}
                    disabled={promptSaveStatus === "saving"}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg cursor-pointer transition-all border-0 outline-none ${
                      promptSaveStatus === "saved"
                        ? "bg-[#d1e7dd] text-[#0f5132]"
                        : promptSaveStatus === "error"
                        ? "bg-[#f8d7da] text-[#842029]"
                        : "bg-[#f62440] hover:bg-[#bb0028] text-white"
                    }`}
                  >
                    {promptSaveStatus === "saving" ? "⏳ 保存中..." : promptSaveStatus === "saved" ? "✅ 已保存" : promptSaveStatus === "error" ? "❌ 保存失败" : "💾 保存 Prompt"}
                  </button>
                </div>
              </div>

              {/* Base Prompt */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">
                  🔒 防幻觉守则 / 基础指令 (Base Prompt)
                </label>
                <p className="text-xs text-[#5d5a55]/80 font-medium">
                  注入给大模型的核心行为准则（防止脑补/幻觉）。数据块（转录文本、评论等）会自动注入在本段与 Action Prompt 之间。
                </p>
                <textarea
                  value={promptData?.base_prompt || ""}
                  onChange={(e) => setPromptData(prev => ({ ...prev, base_prompt: e.target.value }))}
                  rows={8}
                  className="w-full bg-white border border-[#e7bcbb]/40 rounded-lg p-3 text-sm font-mono text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] resize-y min-h-[160px]"
                  placeholder="输入基础 Prompt（角色定义、防幻觉规则等）..."
                />
              </div>

              {/* Action Prompt */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">
                  📋 输出格式指令 (Action Prompt)
                </label>
                <p className="text-xs text-[#5d5a55]/80 font-medium">
                  定义总结报告的具体输出章节与格式（章节结构、评级维度等）。这部分出现在数据块之后。
                </p>
                <textarea
                  value={promptData?.action_prompt || ""}
                  onChange={(e) => setPromptData(prev => ({ ...prev, action_prompt: e.target.value }))}
                  rows={10}
                  className="w-full bg-white border border-[#e7bcbb]/40 rounded-lg p-3 text-sm font-mono text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] resize-y min-h-[220px]"
                  placeholder="输入输出格式 Prompt（要求的章节、格式、评级等）..."
                />
              </div>

              {/* Layout schema visual helper */}
              <div className="p-3.5 bg-[#f9f3ea]/50 border border-[#e7bcbb]/30 rounded-lg text-xs text-[#5d3f3e] leading-relaxed">
                💡 <b>最终 Prompt 拼接顺序：</b>
                <code className="block mt-1 font-mono text-[11px] text-[#bf0029] select-all">
                  [Base Prompt] → [播客元数据 + 评论 + 转录文本（自动注入）] → [Action Prompt]
                </code>
              </div>
            </div>

            {/* Card 3: System Notifications */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Bell size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">System Notifications</h3>
              </div>

              {/* Windows Toast Notifications */}
              <div className="flex items-center justify-between p-4 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/30">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18]">Windows Toast Notifications</h4>
                  <p className="text-[#5d5a55] text-xs mt-0.5">Push notification on desktop when processing ends.</p>
                </div>
                <input
                  type="checkbox"
                  checked={configData.enable_win_notification !== false}
                  onChange={(e) => handleConfigChange("enable_win_notification", e.target.checked)}
                  className="w-4 h-4 accent-[#f62440] cursor-pointer"
                />
              </div>

              {/* Email Alerts */}
              <div className="flex items-center justify-between p-4 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/30">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18]">Email Alerts</h4>
                  <p className="text-[#5d5a55] text-xs mt-0.5">Send mail alerts (SMTP) when task completes.</p>
                </div>
                <input
                  type="checkbox"
                  checked={configData.enable_email_notification === true}
                  onChange={(e) => handleConfigChange("enable_email_notification", e.target.checked)}
                  className="w-4 h-4 accent-[#f62440] cursor-pointer"
                />
              </div>

              {/* Email Subfields */}
              {configData.enable_email_notification === true && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-[#e7bcbb]/20 pt-4 animate-fade-in">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">SMTP Server</label>
                    <input
                      type="text"
                      value={configData.smtp_server || ""}
                      onChange={(e) => handleConfigChange("smtp_server", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="smtp.qq.com"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Port</label>
                    <input
                      type="number"
                      value={configData.smtp_port || 465}
                      onChange={(e) => handleConfigChange("smtp_port", Number(e.target.value))}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="465"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Username</label>
                    <input
                      type="text"
                      value={configData.smtp_username || ""}
                      onChange={(e) => handleConfigChange("smtp_username", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="user@example.com"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Password</label>
                    <input
                      type="password"
                      value={configData.smtp_password || ""}
                      onChange={(e) => handleConfigChange("smtp_password", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="••••••••••••••"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Sender Email</label>
                    <input
                      type="text"
                      value={configData.smtp_sender || ""}
                      onChange={(e) => handleConfigChange("smtp_sender", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="sender@example.com"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Receiver Email</label>
                    <input
                      type="text"
                      value={configData.notification_email || ""}
                      onChange={(e) => handleConfigChange("notification_email", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="receiver@example.com"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Card 4: Advanced Dependencies */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Terminal size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">Advanced Dependencies</h3>
              </div>

              {/* FFmpeg Executable Path */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">FFmpeg Executable Path</label>
                <input
                  type="text"
                  value={configData.ffmpeg_path || ""}
                  onChange={(e) => handleConfigChange("ffmpeg_path", e.target.value)}
                  className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                  placeholder="/usr/local/bin/ffmpeg"
                />
              </div>

              {/* FFmpeg Bin Directory */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">FFmpeg Bin Directory</label>
                <input
                  type="text"
                  value={configData.ffmpeg_bin_dir || ""}
                  onChange={(e) => handleConfigChange("ffmpeg_bin_dir", e.target.value)}
                  className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                  placeholder="/usr/local/bin"
                />
              </div>

              {/* Language Preference */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">Language Preference</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                >
                  <option value="zh-CN">简体中文 (ZH-CN)</option>
                  <option value="en">ENGLISH (EN-US)</option>
                </select>
              </div>

              {/* Auto Save Toggle */}
              <div className="flex items-center justify-between p-4 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/30 mt-2">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18]">Auto-Save Changes</h4>
                  <p className="text-[#5d5a55] text-xs mt-0.5">Automatically trigger save commands when input parameters change.</p>
                </div>
                <input
                  type="checkbox"
                  checked={autoSaveEnabled}
                  onChange={(e) => setAutoSaveEnabled(e.target.checked)}
                  className="w-4 h-4 accent-[#f62440] cursor-pointer"
                />
              </div>
            </div>

            <button
              onClick={handleSaveConfig}
              className="w-full mt-2 bg-[#f62440] hover:bg-[#bb0028] text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all active:scale-98 shadow-xs border-0 outline-none cursor-pointer"
            >
              <Save size={16} />
              <span>Save Configuration</span>
            </button>
          </div>

          {/* Right Column: Database details */}
          <div className="flex flex-col gap-6">
            {/* Storage Cache Panel */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs">
              <div className="flex items-center gap-2 pb-3 border-b border-[#e7bcbb]/10 mb-4 text-[#bf0029]">
                <Database size={16} />
                <h3 className="font-bold text-sm text-[#1d1c18]">Workspace Database Cache</h3>
              </div>
              
              <p className="text-xs text-[#5d5a55] leading-relaxed mb-4 font-medium">
                Recorded tracks and parsed summaries are stored in your browser's persistent key-value namespace.
              </p>

              <button
                onClick={() => {
                  if (confirm("Reset current sessions and database logs to initial reference state? All user custom recordings will be permanently removed.")) {
                    onResetData();
                  }
                }}
                className="w-full py-2.5 px-4 rounded-lg bg-[#ffdad6] text-[#b81a1a] hover:bg-[#ffdad6]/80 text-xs font-bold transition-all border border-[#ffb4a8]/50 flex items-center justify-center gap-2 border-0 outline-none cursor-pointer"
              >
                <ShieldAlert size={14} />
                <span>Reset Workspace to Defaults</span>
              </button>
            </div>

            {/* API Secret panel guide instructions */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs">
              <div className="flex items-center gap-2 pb-3 border-b border-[#e7bcbb]/10 mb-4 text-[#bf0029]">
                <Cpu size={16} />
                <h3 className="font-bold text-sm text-[#1d1c18]">AI Secrets & Credentials</h3>
              </div>
              
              <p className="text-xs text-[#5d5a55] leading-relaxed font-semibold">
                This application utilizes server-side **Gemini 3.5 Models** for complete voice processing and transcript summarization.
              </p>
              <p className="text-xs text-[#5d5a55] leading-relaxed mt-2 font-medium">
                Your API key is kept strictly confidential on the secure container. Configure your credentials under the <b>Settings &gt; Secrets</b> panel in Google AI Studio to unlock live real-time analysis.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
