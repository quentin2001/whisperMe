import React, { useState, useRef, useEffect } from "react";
import { Sliders, Save, Database, ShieldAlert, Cpu, Terminal, Bell, ChevronDown, RotateCcw, Check, Loader2, AlertCircle, Trash2, Globe } from "lucide-react";

function SettingsDropdown({ value, options, onChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => opt.value === value) || options[0];

  return (
    <div className="relative w-full" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-[#fef9f2]/40 hover:bg-[#fef9f2]/80 border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] flex justify-between items-center transition-colors text-left"
      >
        <span>{selectedOption?.label}</span>
        <ChevronDown size={16} className={`text-[#5d3f3e]/60 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-1.5 bg-white border border-[#e7bcbb]/40 rounded-lg shadow-lg max-h-60 overflow-y-auto py-1 animate-fade-in">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 text-sm text-[#1d1c18] hover:bg-[#f2ede6] transition-colors flex items-center justify-between text-left font-semibold cursor-pointer border-0 bg-transparent"
            >
              <span>{option.label}</span>
              {option.value === value && <Check size={14} className="text-[#bf0029]" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SettingsView({
  versionInfo,
  configData,
  handleConfigChange,
  handleSaveConfig,
  onResetData,
  promptData,
  setPromptData,
  promptSaveStatus,
  handleSavePrompt,
  handleResetPrompt,
  onCheckVersion,
  checkingVersion
}) {
  const t = (zh, en) => (configData.language === "en" ? en : zh);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [isFlashing, setIsFlashing] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsFlashing(false);
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  const getHighlightClass = (val) => {
    return isFlashing && (!val || String(val).trim() === "") ? "highlight-flash" : "";
  };

  return (
    <div id="settings-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        <div className="mb-8">
          <h2 className="text-4xl font-extrabold tracking-tight text-[#1d1c18] font-display">{t("设置", "Settings")}</h2>
          <p className="text-sm text-[#5d5a55]/80 mt-1 font-medium">{t("精细化配置音频处理阈值及神经网络转录引擎大模型参数。", "Fine-tune acoustic processing thresholds and neural transcription engine models.")}</p>
        </div>

        {versionInfo?.has_update && (
          <div className="mb-6 p-4 bg-[#ffdad6]/40 border border-[#ffb4a8]/50 rounded-xl flex items-start gap-3 animate-fade-in">
            <ShieldAlert size={18} className="text-[#bf0029] mt-0.5 shrink-0" />
            <div className="flex-1">
              <h4 className="font-bold text-sm text-[#1d1c18] flex items-center gap-2">
                {t("发现新版本 whisperMe 可用！", "A new version of whisperMe is available!")}
                <span className="text-[10px] bg-[#f62440] text-white px-2 py-0.5 rounded-full font-mono uppercase font-extrabold tracking-wider animate-pulse">
                  v{versionInfo.latest_version}
                </span>
              </h4>
              <p className="text-xs text-[#5d5a55] mt-1 font-semibold leading-relaxed">
                {t("您当前正在使用", "You are running")} <span className="font-mono font-bold">v{versionInfo.current_version}</span>。
                {versionInfo.release_notes ? `${t("更新内容：", "What's new: ")} ${versionInfo.release_notes}` : t("推荐您立即升级以获得最新特性和 Bug 修复。", "We recommend upgrading to enjoy new features and bug fixes.")}
              </p>
              <a 
                href={versionInfo.release_url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="inline-flex items-center gap-1.5 mt-2.5 text-xs font-bold text-[#bf0029] hover:underline"
              >
                {t("前往 GitHub 下载与升级 ↗", "Upgrade on GitHub ↗")}
              </a>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Config Panels */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            
            {/* Card 1: ASR Settings */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Sliders size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">{t("ASR 引擎设置", "ASR Engine Settings")}</h3>
              </div>

              {/* Engine Mode */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("引擎工作模式", "Engine Mode")}</label>
                <SettingsDropdown
                  value={configData.asr_mode || "local"}
                  onChange={(val) => handleConfigChange("asr_mode", val)}
                  options={[
                    { value: "local", label: t("本地离线", "LOCAL OFFLINE") },
                    { value: "online", label: t("在线 API", "ONLINE API") }
                  ]}
                />
              </div>

              {/* Local Mode Subfields */}
              {configData.asr_mode === "local" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("本地 Whisper 模型路径", "Local Model Path")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.local_whisper_model_path || ""}
                      onChange={(e) => handleConfigChange("local_whisper_model_path", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.local_whisper_model_path)}`}
                      placeholder="/path/to/whisper/models/large-v3.bin"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("HF Token (人声分割分段)", "HF Token (Diarization)")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="password"
                      value={configData.hf_token || ""}
                      onChange={(e) => handleConfigChange("hf_token", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.hf_token)}`}
                      placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                  </div>
                </>
              )}

              {/* Online Mode Subfields */}
              {configData.asr_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("API 接口基础地址", "API Base URL")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.online_base_url || ""}
                      onChange={(e) => handleConfigChange("online_base_url", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.online_base_url)}`}
                      placeholder="https://token-plan-sgp.xiaomimimo.com/v1"
                    />
                    <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("样例：https://token-plan-sgp.xiaomimimo.com/v1 或 https://api.openai.com/v1", "Example: https://token-plan-sgp.xiaomimimo.com/v1 or https://api.openai.com/v1")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("模型标识符 (Model ID)", "Model ID")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.online_model || ""}
                      onChange={(e) => handleConfigChange("online_model", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.online_model)}`}
                      placeholder="mimo-v2.5-asr"
                    />
                    <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("样例：mimo-v2.5-asr 或 whisper-1", "Example: mimo-v2.5-asr or whisper-1")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("API 密钥 (API Key)", "API Key")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="password"
                      value={configData.online_api_key || ""}
                      onChange={(e) => handleConfigChange("online_api_key", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.online_api_key)}`}
                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                    <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("输入您在 ASR 服务商申请的 API 密钥", "Enter the API key you requested from your ASR service provider")}</span>
                  </div>
                </>
              )}
            </div>

            {/* Card 2: LLM Summary Settings */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Cpu size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">{t("LLM 总结大模型配置", "LLM Summary Settings")}</h3>
              </div>

              {/* LLM Mode */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("大模型工作模式", "LLM Mode")}</label>
                <SettingsDropdown
                  value={configData.summary_mode || "online"}
                  onChange={(val) => handleConfigChange("summary_mode", val)}
                  options={[
                    { value: "local", label: t("本地 OLLAMA", "LOCAL OLLAMA") },
                    { value: "online", label: t("在线 API", "ONLINE API") }
                  ]}
                />
              </div>

              {/* Local Ollama Subfields */}
              {configData.summary_mode === "local" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("本地 API 接口地址", "Local API URL")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.ollama_url || ""}
                      onChange={(e) => handleConfigChange("ollama_url", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.ollama_url)}`}
                      placeholder="http://localhost:11434"
                    />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("模型 ID", "Model ID")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.ollama_model || ""}
                      onChange={(e) => handleConfigChange("ollama_model", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.ollama_model)}`}
                      placeholder="qwen2.5:7b-instruct"
                    />
                  </div>
                </>
              )}

              {/* Online OpenAI Compatible Subfields */}
              {configData.summary_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("在线 API 基础地址", "Online API Base URL")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.online_summary_base_url || ""}
                      onChange={(e) => handleConfigChange("online_summary_base_url", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.online_summary_base_url)}`}
                      placeholder="https://api.openai.com/v1"
                    />
                    <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("样例：https://api.openai.com/v1 或第三方中转 API 地址", "Example: https://api.openai.com/v1 or a third-party OpenAI-compatible API base URL")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("在线大模型 ID", "Online Model ID")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="text"
                      value={configData.online_summary_model || ""}
                      onChange={(e) => handleConfigChange("online_summary_model", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.online_summary_model)}`}
                      placeholder="gpt-4o-mini"
                    />
                    <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("样例：gpt-4o-mini 或 qwen-plus", "Example: gpt-4o-mini or qwen-plus")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("API Key", "API Key")}<span className="text-[#f62440] ml-1">*</span></label>
                    <input
                      type="password"
                      value={configData.online_summary_api_key || ""}
                      onChange={(e) => handleConfigChange("online_summary_api_key", e.target.value)}
                      className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.online_summary_api_key)}`}
                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                    <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("输入您在大模型服务商申请的 API 密钥", "Enter the API key you requested from your LLM service provider")}</span>
                  </div>
                </>
              )}
            </div>

            {/* Card: LLM Prompt Template Settings */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center justify-between pb-4 border-b border-[#e7bcbb]/20">
                <div className="flex items-center gap-2">
                  <Terminal size={18} className="text-[#bf0029]" />
                  <h3 className="text-lg font-bold text-[#1d1c18]">{t("总结 Prompt 模板配置", "Summary Prompt Template")}</h3>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleResetPrompt}
                    className="px-3 py-1.5 bg-[#f2ede6] text-[#5d3f3e] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded-lg cursor-pointer transition-all border-0 outline-none flex items-center gap-1.5"
                  >
                    <RotateCcw size={13} />
                    <span>{t("恢复默认", "Reset to Default")}</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleSavePrompt}
                    disabled={promptSaveStatus === "saving"}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg cursor-pointer transition-all border-0 outline-none flex items-center gap-1.5 ${
                      promptSaveStatus === "saved"
                        ? "bg-[#d1e7dd] text-[#0f5132]"
                        : promptSaveStatus === "error"
                        ? "bg-[#f8d7da] text-[#842029]"
                        : "bg-[#f62440] hover:bg-[#bb0028] text-white"
                    }`}
                  >
                    {promptSaveStatus === "saving" && <Loader2 size={13} className="animate-spin" />}
                    {promptSaveStatus === "saved" && <Check size={13} />}
                    {promptSaveStatus === "error" && <AlertCircle size={13} />}
                    {promptSaveStatus !== "saving" && promptSaveStatus !== "saved" && promptSaveStatus !== "error" && <Save size={13} />}
                    <span>
                      {promptSaveStatus === "saving" 
                        ? t("保存中...", "Saving...") 
                        : promptSaveStatus === "saved" 
                        ? t("已保存", "Saved") 
                        : promptSaveStatus === "error" 
                        ? t("保存失败", "Failed") 
                        : t("保存 Prompt", "Save Prompt")}
                    </span>
                  </button>
                </div>
              </div>

              {/* Base Prompt */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">
                  {t("🔒 防幻觉守则 / 基础指令 (Base Prompt)", "🔒 Anti-Hallucination Rules / Base Prompt")}
                </label>
                <p className="text-xs text-[#5d5a55]/80 font-medium">
                  {t("注入给大模型的核心行为准则（防止脑补/幻觉）。数据块（转录文本、评论等）会自动注入在本段与 Action Prompt 之间。", "Core guidelines injected to the LLM to prevent hallucination. Data chunks (transcripts, comments, etc.) will be automatically injected between this block and Action Prompt.")}
                </p>
                <textarea
                  value={promptData?.base_prompt || ""}
                  onChange={(e) => setPromptData(prev => ({ ...prev, base_prompt: e.target.value }))}
                  rows={8}
                  className="w-full bg-white border border-[#e7bcbb]/40 rounded-lg p-3 text-sm font-mono text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] resize-y min-h-[160px]"
                  placeholder={t("输入基础 Prompt（角色定义、防幻觉规则等）...", "Enter base prompt (role definitions, anti-hallucination rules, etc.)...")}
                />
              </div>

              {/* Action Prompt */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">
                  {t("📋 输出格式指令 (Action Prompt)", "📋 Output Format Directive / Action Prompt")}
                </label>
                <p className="text-xs text-[#5d5a55]/80 font-medium">
                  {t("定义总结报告的具体输出章节与格式（章节结构、评级维度等）。这部分出现在数据块之后。", "Defines the specific sections and formatting of the summary report. Appended after data chunks.")}
                </p>
                <textarea
                  value={promptData?.action_prompt || ""}
                  onChange={(e) => setPromptData(prev => ({ ...prev, action_prompt: e.target.value }))}
                  rows={10}
                  className="w-full bg-white border border-[#e7bcbb]/40 rounded-lg p-3 text-sm font-mono text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] resize-y min-h-[220px]"
                  placeholder={t("输入输出格式 Prompt（要求的章节、格式、评级等）...", "Enter output formatting prompt (requested chapters, templates, ratings, etc.)...")}
                />
              </div>

              {/* Layout schema visual helper */}
              <div className="p-3.5 bg-[#f9f3ea]/50 border border-[#e7bcbb]/30 rounded-lg text-xs text-[#5d3f3e] leading-relaxed">
                {t("💡 最终 Prompt 拼接顺序：", "💡 Final prompt composition sequence:")}
                <code className="block mt-1 font-mono text-[11px] text-[#bf0029] select-all">
                  {t("[Base Prompt] → [播客元数据 + 评论 + 转录文本（自动注入）] → [Action Prompt]", "[Base Prompt] → [Metadata + Comments + Transcript (Auto Injected)] → [Action Prompt]")}
                </code>
              </div>
            </div>

            {/* Card 3: System Notifications */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5">
              <div className="flex items-center gap-2 pb-4 border-b border-[#e7bcbb]/20">
                <Bell size={18} className="text-[#bf0029]" />
                <h3 className="text-lg font-bold text-[#1d1c18]">{t("系统提醒设置", "System Notifications")}</h3>
              </div>

              {/* Windows Toast Notifications */}
              <div className="flex items-center justify-between p-4 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/30">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18]">{t("Windows 气泡通知", "Windows Toast Notifications")}</h4>
                  <p className="text-[#5d5a55] text-xs mt-0.5">{t("处理结束时在桌面推送通知提醒。", "Push notification on desktop when processing ends.")}</p>
                </div>
                <input
                  type="checkbox"
                  checked={configData.enable_win_notification !== false}
                  onChange={(e) => handleConfigChange("enable_win_notification", e.target.checked)}
                  className="w-4 h-4 rounded border-[#e7bcbb]/60 text-[#f62440] focus:ring-[#f62440] focus:ring-offset-0 bg-[#fef9f2]/40 transition-colors cursor-pointer"
                />
              </div>

              {/* Email Alerts */}
              <div className="flex items-center justify-between p-4 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/30">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18]">{t("邮件提醒 (Email Alerts)", "Email Alerts")}</h4>
                  <p className="text-[#5d5a55] text-xs mt-0.5">{t("任务结束时发送邮件通知（需要配置 SMTP）。", "Send mail alerts (SMTP) when task completes.")}</p>
                </div>
                <input
                  type="checkbox"
                  checked={configData.enable_email_notification === true}
                  onChange={(e) => handleConfigChange("enable_email_notification", e.target.checked)}
                  className="w-4 h-4 rounded border-[#e7bcbb]/60 text-[#f62440] focus:ring-[#f62440] focus:ring-offset-0 bg-[#fef9f2]/40 transition-colors cursor-pointer"
                />
              </div>

              {/* Email Subfields */}
              {configData.enable_email_notification === true && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-[#e7bcbb]/20 pt-4 animate-fade-in">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("SMTP 服务器", "SMTP Server")}</label>
                    <input
                      type="text"
                      value={configData.smtp_server || ""}
                      onChange={(e) => handleConfigChange("smtp_server", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="smtp.qq.com"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("端口", "Port")}</label>
                    <input
                      type="number"
                      value={configData.smtp_port || 465}
                      onChange={(e) => handleConfigChange("smtp_port", Number(e.target.value))}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="465"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("用户名", "Username")}</label>
                    <input
                      type="text"
                      value={configData.smtp_username || ""}
                      onChange={(e) => handleConfigChange("smtp_username", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="user@example.com"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("密码/授权码", "Password")}</label>
                    <input
                      type="password"
                      value={configData.smtp_password || ""}
                      onChange={(e) => handleConfigChange("smtp_password", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="••••••••••••••"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("发件邮箱", "Sender Email")}</label>
                    <input
                      type="text"
                      value={configData.smtp_sender || ""}
                      onChange={(e) => handleConfigChange("smtp_sender", e.target.value)}
                      className="bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440]"
                      placeholder="sender@example.com"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("收件人邮箱", "Receiver Email")}</label>
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
                <h3 className="text-lg font-bold text-[#1d1c18]">{t("核心运行时依赖路径", "Advanced Dependencies")}</h3>
              </div>

              {/* FFmpeg Executable Path */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("FFmpeg 执行文件路径", "FFmpeg Executable Path")}<span className="text-[#f62440] ml-1">*</span></label>
                <input
                  type="text"
                  value={configData.ffmpeg_path || ""}
                  onChange={(e) => handleConfigChange("ffmpeg_path", e.target.value)}
                  className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.ffmpeg_path)}`}
                  placeholder={t("C:\\ffmpeg\\bin\\ffmpeg.exe 或 /opt/homebrew/bin/ffmpeg", "C:\\ffmpeg\\bin\\ffmpeg.exe or /opt/homebrew/bin/ffmpeg")}
                />
                <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("Windows 示例：C:\\ffmpeg\\bin\\ffmpeg.exe，Mac 示例：/opt/homebrew/bin/ffmpeg", "Example for Windows: C:\\ffmpeg\\bin\\ffmpeg.exe, for Mac: /opt/homebrew/bin/ffmpeg")}</span>
              </div>

              {/* FFmpeg Bin Directory */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("FFmpeg Bin 目录", "FFmpeg Bin Directory")}<span className="text-[#f62440] ml-1">*</span></label>
                <input
                  type="text"
                  value={configData.ffmpeg_bin_dir || ""}
                  onChange={(e) => handleConfigChange("ffmpeg_bin_dir", e.target.value)}
                  className={`bg-white border border-[#e7bcbb]/40 rounded-lg p-2.5 text-sm font-semibold text-[#1d1c18] focus:outline-none focus:ring-1 focus:ring-[#f62440] ${getHighlightClass(configData.ffmpeg_bin_dir)}`}
                  placeholder={t("C:\\ffmpeg\\bin 或 /opt/homebrew/bin", "C:\\ffmpeg\\bin or /opt/homebrew/bin")}
                />
                <span className="text-xs text-[#5d3f3e]/60 font-medium">{t("Windows 示例：C:\\ffmpeg\\bin，Mac 示例：/opt/homebrew/bin", "Example for Windows: C:\\ffmpeg\\bin, for Mac: /opt/homebrew/bin")}</span>
              </div>

              {/* Auto Save Toggle */}
              <div className="flex items-center justify-between p-4 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/30 mt-2">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18]">{t("自动保存设置更改", "Auto-Save Changes")}</h4>
                  <p className="text-[#5d5a55] text-xs mt-0.5">{t("当配置输入参数发生变化时自动执行保存操作。", "Automatically trigger save commands when input parameters change.")}</p>
                </div>
                <input
                  type="checkbox"
                  checked={autoSaveEnabled}
                  onChange={(e) => setAutoSaveEnabled(e.target.checked)}
                  className="w-4 h-4 rounded border-[#e7bcbb]/60 text-[#f62440] focus:ring-[#f62440] focus:ring-offset-0 bg-[#fef9f2]/40 transition-colors cursor-pointer"
                />
              </div>
            </div>

            <button
              onClick={handleSaveConfig}
              className="w-full mt-2 bg-[#f62440] hover:bg-[#bb0028] text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all active:scale-98 shadow-xs border-0 outline-none cursor-pointer"
            >
              <Save size={16} />
              <span>{t("保存配置表", "Save Configuration")}</span>
            </button>
          </div>

          {/* Right Column: Database details */}
          <div className="flex flex-col gap-6">
            {/* Language Preference Card */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-4">
              <div className="flex items-center gap-2 pb-3 border-b border-[#e7bcbb]/10 text-[#bf0029]">
                <Globe size={16} />
                <h3 className="font-bold text-sm text-[#1d1c18]">{t("系统语言设置", "System Language Preference")}</h3>
              </div>
              
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[#5d5a55]">{t("语言选择", "Select Language")}</label>
                <SettingsDropdown
                  value={configData.language || "en"}
                  onChange={(val) => handleConfigChange("language", val)}
                  options={[
                    { value: "zh-CN", label: t("简体中文 (ZH-CN)", "CHINESE (ZH-CN)") },
                    { value: "en", label: t("ENGLISH (EN-US)", "ENGLISH (EN-US)") }
                  ]}
                />
              </div>
            </div>

            {/* Storage Cache Panel */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs">
              <div className="flex items-center gap-2 pb-3 border-b border-[#e7bcbb]/10 mb-4 text-[#bf0029]">
                <Database size={16} />
                <h3 className="font-bold text-sm text-[#1d1c18]">{t("工作区数据库缓存", "Workspace Database Cache")}</h3>
              </div>
              
              <p className="text-xs text-[#5d5a55] leading-relaxed mb-4 font-medium">
                {t("所有已录制的音频和生成的AI总结都会保存在浏览器的本地存储库中。", "Recorded tracks and parsed summaries are stored in your browser's persistent key-value namespace.")}
              </p>

              <button
                onClick={() => {
                  if (confirm(t("确定要重置当前工作区和数据库日志吗？所有用户录音及任务记录将被永久删除！", "Reset current sessions and database logs to initial reference state? All user custom recordings will be permanently removed."))) {
                    onResetData();
                  }
                }}
                className="w-full py-2.5 px-4 rounded-lg bg-[#ffdad6] text-[#b81a1a] hover:bg-[#ffdad6]/80 text-xs font-bold transition-all border border-[#ffb4a8]/50 flex items-center justify-center gap-2 border-0 outline-none cursor-pointer"
              >
                <ShieldAlert size={14} />
                <span>{t("重置工作区数据库", "Reset Workspace to Defaults")}</span>
              </button>
            </div>

            {/* Audio Auto-Cleanup Panel */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs flex flex-col gap-4 animate-fade-in">
              <div className="flex items-center gap-2 pb-3 border-b border-[#e7bcbb]/10 text-[#bf0029]">
                <Trash2 size={16} />
                <h3 className="font-bold text-sm text-[#1d1c18]">{t("自动清理音频", "Audio Auto-Cleanup")}</h3>
              </div>
              
              <p className="text-xs text-[#5d5a55] leading-relaxed font-medium">
                {t("自动删除本地缓存的播客音频源文件以节省硬盘空间。对应的文本转录和 AI 总结报告将完好保留。", "Automatically delete downloaded podcast audio files to free up disk space. Transcripts and AI summaries will be fully preserved.")}
              </p>

              {/* Toggle Switch */}
              <div className="flex items-center justify-between p-3.5 bg-[#f9f3ea]/30 rounded-lg border border-[#e7bcbb]/20">
                <div>
                  <h4 className="font-bold text-xs text-[#1d1c18]">{t("启用自动清理", "Enable Auto-Cleanup")}</h4>
                  <p className="text-[#5d5a55] text-[10px] mt-0.5">{t("开启后将定时清除过期音频。", "Regularly clean up expired audio files.")}</p>
                </div>
                <input
                  type="checkbox"
                  checked={configData.enable_auto_cleanup || false}
                  onChange={(e) => handleConfigChange("enable_auto_cleanup", e.target.checked)}
                  className="w-4 h-4 rounded border-[#e7bcbb]/60 text-[#f62440] focus:ring-[#f62440] focus:ring-offset-0 bg-[#fef9f2]/40 transition-colors cursor-pointer"
                />
              </div>

              {/* Threshold Dropdown */}
              {configData.enable_auto_cleanup && (
                <div className="flex flex-col gap-2 animate-fade-in">
                  <label className="text-[11px] font-bold uppercase tracking-wider text-[#5d5a55]">{t("清理时效周期", "Cleanup Threshold")}</label>
                  <SettingsDropdown
                    value={configData.cleanup_threshold_days || 30}
                    onChange={(val) => handleConfigChange("cleanup_threshold_days", Number(val))}
                    options={[
                      { value: 7, label: t("超过 7 天", "Older than 7 days") },
                      { value: 30, label: t("超过 30 天 (1个月)", "Older than 30 days (1 month)") }
                    ]}
                  />
                </div>
              )}
            </div>

            {/* API Secret panel guide instructions */}
            <div className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs">
              <div className="flex items-center gap-2 pb-3 border-b border-[#e7bcbb]/10 mb-4 text-[#bf0029]">
                <Cpu size={16} />
                <h3 className="font-bold text-sm text-[#1d1c18]">{t("AI 引擎机密凭据说明", "AI Secrets & Credentials")}</h3>
              </div>
              
              <p className="text-xs text-[#5d5a55] leading-relaxed font-semibold">
                {t("本应用调用服务器端的大模型进行语音处理与大模型自动总结。", "This application utilizes server-side AI Models for complete voice processing and transcript summarization.")}
              </p>
              <p className="text-xs text-[#5d5a55] leading-relaxed mt-2 font-medium">
                {t("您的 API 密钥在安全容器中受到严格保护。您可以通过配置大模型 API Key 来解锁实时的总结分析功能。", "Your API key is kept strictly confidential on the secure container. Configure your credentials under the settings to unlock live real-time analysis.")}
              </p>
            </div>

            {/* GitHub Repo & Version Info */}
            <a
              href={versionInfo?.has_update ? versionInfo.release_url : "https://github.com/quentin2001/whisperMe"}
              target="_blank"
              rel="noopener noreferrer"
              style={{ textDecoration: 'none' }}
              className="bg-white border border-[#e7bcbb]/40 rounded-xl p-6 shadow-xs hover:border-[#f62440]/55 hover:shadow-xs transition-all flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#f2ede6]/65 flex items-center justify-center text-[#1d1c18] group-hover:scale-105 transition-all">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
                </div>
                <div>
                  <h4 className="font-bold text-sm text-[#1d1c18] font-display group-hover:text-[#f62440] transition-all">{t("GitHub 仓库", "GitHub Repository")}</h4>
                  <p className="text-[11px] text-[#5d5a55] font-semibold mt-0.5">quentin2001/whisperMe</p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <span className={`text-[10px] font-extrabold tracking-wider uppercase px-2.5 py-1 rounded-full border font-mono ${
                  versionInfo?.has_update 
                    ? "bg-[#ffdad6] text-[#b81a1a] border-[#ffb4a8] animate-pulse" 
                    : "bg-[#f2ede6]/60 text-[#5d5a55] border-[#e7bcbb]/30"
                }`}>
                  {versionInfo?.has_update 
                    ? `${t("有新版本", "UPDATE")} v${versionInfo.latest_version}` 
                    : `v${versionInfo?.current_version || "1.0.0"}`
                  }
                </span>
                
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onCheckVersion(true); // 传入 true 代表强制跳过缓存，向 GitHub 重新请求
                  }}
                  className="text-[10px] text-[#bf0029] hover:underline bg-transparent border-0 cursor-pointer font-bold mt-1 flex items-center gap-1 select-none outline-none"
                  disabled={checkingVersion}
                >
                  {checkingVersion ? (
                    <>
                      <Loader2 size={10} className="animate-spin text-[#bf0029]" />
                      <span>{t("检查中...", "Checking...")}</span>
                    </>
                  ) : (
                    <span>{t("检查更新", "Check Updates")}</span>
                  )}
                </button>
              </div>
            </a>
          </div>

        </div>
      </div>
    </div>
  );
}
