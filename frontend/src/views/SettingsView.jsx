import React, { useState, useRef, useEffect } from "react";
import { Sliders, Save, ShieldAlert, Cpu, Terminal, Bell, ChevronDown, RotateCcw, Check, Loader2, AlertCircle, Trash2, Globe, RefreshCw, FileText, Power, Activity, Sparkles } from "lucide-react";
import { API_BASE } from "../constants.js";
import { useConfigStore } from "../store/configStore.js";
import { useTranslation } from "../contexts/I18nContext";

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
        className="w-full bg-[var(--bg-input)]/40 hover:bg-[var(--bg-input)]/80 border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] flex justify-between items-center transition-colors text-left"
      >
        <span>{selectedOption?.label}</span>
        <ChevronDown size={16} className={`text-[var(--text-muted)] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg shadow-lg max-h-60 overflow-y-auto py-1 animate-fade-in">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors flex items-center justify-between text-left font-semibold cursor-pointer border-0 bg-transparent"
            >
              <span>{option.label}</span>
              {option.value === value && <Check size={14} className="text-[var(--accent-red)]" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SettingsView({
  handleConfigChange,
  handleSaveConfig,
  onResetData,
  handleSavePrompt,
  handleResetPrompt,
  onCheckVersion}) {
  const { t } = useTranslation();
  const versionInfo = useConfigStore(state => state.versionInfo);
  const configData = useConfigStore(state => state.configData);
  const promptData = useConfigStore(state => state.promptData);
  const setPromptData = useConfigStore(state => state.setPromptData);
  const promptSaveStatus = useConfigStore(state => state.promptSaveStatus);
  const checkingVersion = useConfigStore(state => state.checkingVersion);

  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [isFlashing, setIsFlashing] = useState(true);
  const [ffmpegStatus, setFfmpegStatus] = useState(null);
  const [dependencies, setDependencies] = useState(null);
  const [hfTokenStatus, setHfTokenStatus] = useState(null);
  const [hfChecking, setHfChecking] = useState(false);
  const [testingAsr, setTestingAsr] = useState(false);
  const [testingLlm, setTestingLlm] = useState(false);

  const testConnection = async (type) => {
    const isAsr = type === "asr";
    const apiKey = isAsr ? configData.online_api_key : configData.online_summary_api_key;
    const baseUrl = isAsr ? configData.online_base_url : configData.online_summary_base_url;
    const model = isAsr ? configData.online_model : configData.online_summary_model;

    if (!baseUrl) {
      alert("请输入 API Base URL");
      return;
    }

    if (isAsr) setTestingAsr(true);
    else setTestingLlm(true);

    try {
      const res = await fetch(`${API_BASE}/api/config/test/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey || "", base_url: baseUrl, model: model || "" })
      });
      const data = await res.json();
      if (data.success) {
        await import("../components/Dialog.jsx").then(m => m.alert(`✅ 测试成功：${data.message}`, { variant: 'info' }));
      } else {
        await import("../components/Dialog.jsx").then(m => m.alert(`❌ 测试失败：${data.message}`, { variant: 'danger' }));
      }
    } catch (e) {
      await import("../components/Dialog.jsx").then(m => m.alert(`❌ 网络请求异常：${e.message}`, { variant: 'danger' }));
    } finally {
      if (isAsr) setTestingAsr(false);
      else setTestingLlm(false);
    }
  };

  const handleVerifyHF = async () => {
    setHfChecking(true);
    setHfTokenStatus(null);
    try {
      const res = await fetch(`${API_BASE}/api/settings/hf-token-status`);
      const data = await res.json();
      setHfTokenStatus(data);
    } catch (e) {
      setHfTokenStatus({ status: "unknown", message: "网络错误" });
    } finally {
      setHfChecking(false);
    }
  };

  // Prompt template system
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [loadingTemplate, setLoadingTemplate] = useState(false);


  useEffect(() => {
    fetch(`${API_BASE}/api/prompt/templates`)
      .then(r => r.json())
      .then(data => {
        if (data && typeof data === "object") {
          const list = Object.entries(data).map(([id, info]) => ({ id, ...info }));
          setTemplates(list);
        }
      })
      .catch(() => {});
  }, []);

  const handleTemplateSelect = (templateId) => {
    if (!templateId) return;
    setSelectedTemplate(templateId);
    setLoadingTemplate(true);
    fetch(`${API_BASE}/api/prompt/template/${templateId}`)
      .then(r => r.json())
      .then(data => {
        if (data.prompt) {
          setPromptData({ prompt: data.prompt });
        }
      })
      .catch(() => {})
      .finally(() => setLoadingTemplate(false));
  };

  const handleVerifyFfmpeg = async (p = "") => {
    setFfmpegStatus({ status: "checking" });
    const url = p ? `${API_BASE}/api/dependencies?ffmpeg_path=${encodeURIComponent(p)}` : `${API_BASE}/api/dependencies`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      setFfmpegStatus(data);
    } catch (e) {
      setFfmpegStatus({ status: "unknown", message: "网络错误" });
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsFlashing(false);
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const p = configData.ffmpeg_path || "";
    const url = p ? `${API_BASE}/api/dependencies?ffmpeg_path=${encodeURIComponent(p)}` : `${API_BASE}/api/dependencies`;
    fetch(url)
      .then(r => r.json())
      .then(d => {
        setDependencies(d);
        setFfmpegStatus(d.ffmpeg || { available: false });
      })
      .catch(() => setFfmpegStatus({ available: false }));
  }, [configData?.ffmpeg_path]);

  const getHighlightClass = (val) => {
    return isFlashing && (!val || String(val).trim() === "") ? "highlight-flash" : "";
  };

  return (
    <div id="settings-view-section" className="flex-1 overflow-y-auto w-full">
      <div className="max-w-[1280px] mx-auto p-10 font-sans w-full">
        <div className="mb-8">
          <h2 className="text-4xl font-extrabold tracking-tight text-[var(--text-primary)] font-display">{t("设置", "Settings")}</h2>
          <p className="text-sm text-[var(--text-muted)] mt-1 font-medium">{t("精细化配置音频处理阈值及神经网络转录引擎大模型参数。", "Fine-tune acoustic processing thresholds and neural transcription engine models.")}</p>
        </div>

        {versionInfo?.has_update && (
          <div className="mb-6 p-4 bg-[var(--accent-red-light)]/40 border border-[var(--accent-red-light)]/50 rounded-xl flex items-start gap-3 animate-fade-in">
            <ShieldAlert size={18} className="text-[var(--accent-red)] mt-0.5 shrink-0" />
            <div className="flex-1">
              <h4 className="font-bold text-sm text-[var(--text-primary)] flex items-center gap-2">
                {t("发现新版本 whisperMe 可用！", "A new version of whisperMe is available!")}
                <span className="text-[10px] bg-[var(--accent-red)] text-white px-2 py-0.5 rounded-full font-mono uppercase font-extrabold tracking-wider animate-pulse">
                  v{versionInfo.latest_version}
                </span>
              </h4>
              <p className="text-xs text-[var(--text-muted)] mt-1 font-semibold leading-relaxed">
                {t("您当前正在使用", "You are running")} <span className="font-mono font-bold">v{versionInfo.current_version}</span>。
                {versionInfo.release_notes ? `${t("更新内容：", "What's new: ")} ${versionInfo.release_notes}` : t("推荐您立即升级以获得最新特性和 Bug 修复。", "We recommend upgrading to enjoy new features and bug fixes.")}
              </p>
              <a
                href={versionInfo.release_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 mt-2.5 text-xs font-bold text-[var(--accent-red)] hover:underline"
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
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center justify-between pb-4 border-b border-[var(--border-primary)]/20">
                <div className="flex items-center gap-2">
                  <Sliders size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("ASR 引擎设置", "ASR Engine Settings")}</h3>
                </div>
                {configData.asr_mode === "online" && (
                  <button onClick={() => testConnection("asr")} disabled={testingAsr} className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] border border-[var(--border-primary)]/40 transition-all cursor-pointer disabled:opacity-50 whitespace-nowrap shrink-0">
                    {testingAsr ? <Loader2 size={12} className="animate-spin" /> : <Activity size={12} className="text-[var(--accent-red)]" />}
                    <span>{testingAsr ? t("测试中...", "Testing...") : t("连通性测试", "Test Connection")}</span>
                  </button>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("引擎工作模式", "Engine Mode")}</label>
                <SettingsDropdown
                  value={configData.asr_mode || "online"}
                  onChange={(val) => handleConfigChange("asr_mode", val)}
                  options={[
                    { value: "local", label: t("本地模型", "LOCAL MODEL") },
                    { value: "online", label: t("在线 API", "ONLINE API") }
                  ]}
                />
              </div>

              {configData.asr_mode === "local" && (
                <div className="flex flex-col gap-2 animate-fade-in">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("本地 Whisper 模型路径", "Local Model Path")}</label>
                  <input
                    type="text"
                    value={configData.local_whisper_model_path || ""}
                    onChange={(e) => handleConfigChange("local_whisper_model_path", e.target.value)}
                    className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.local_whisper_model_path)}`}
                    placeholder="/path/to/whisper/models/large-v3.bin"
                  />
                </div>
              )}


              {configData.asr_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("API Base URL", "API Base URL")}</label>
                    <input type="text" value={configData.online_base_url || ""} onChange={(e) => handleConfigChange("online_base_url", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_base_url)}`}
                      placeholder="https://api.openai.com/v1" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">
                      {t("样例：https://api.openai.com/v1 或第三方中转地址", "Example: https://api.openai.com/v1 or a third-party API base URL")}
                    </span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("Model ID", "Model ID")}</label>
                    <input type="text" value={configData.online_model || ""} onChange={(e) => handleConfigChange("online_model", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_model)}`}
                      placeholder="whisper-1" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">
                      {t("样例：whisper-1 / mimo-v2.5-asr", "Example: whisper-1 / mimo-v2.5-asr")}
                    </span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("API Key", "API Key")}</label>
                    <input type="password" value={configData.online_api_key || ""} onChange={(e) => handleConfigChange("online_api_key", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_api_key)}`}
                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">{t("输入您在 ASR 服务商申请的 API 密钥", "Enter the API key from your ASR service provider")}</span>
                  </div>

                </>
              )}
            </div>


            {/* Card 2: LLM Summary Settings */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center justify-between pb-4 border-b border-[var(--border-primary)]/20">
                <div className="flex items-center gap-2">
                  <Cpu size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("LLM 总结大模型配置", "LLM Summary Settings")}</h3>
                </div>
                {configData.summary_mode === "online" && (
                  <button onClick={() => testConnection("llm")} disabled={testingLlm} className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] border border-[var(--border-primary)]/40 transition-all cursor-pointer disabled:opacity-50 whitespace-nowrap shrink-0">
                    {testingLlm ? <Loader2 size={12} className="animate-spin" /> : <Activity size={12} className="text-[var(--accent-red)]" />}
                    <span>{testingLlm ? t("测试中...", "Testing...") : t("连通性测试", "Test Connection")}</span>
                  </button>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("大模型工作模式", "LLM Mode")}</label>
                <SettingsDropdown
                  value={configData.summary_mode || "online"}
                  onChange={(val) => handleConfigChange("summary_mode", val)}
                  options={[
                    { value: "local", label: t("本地模型", "LOCAL MODEL") },
                    { value: "online", label: t("在线 API", "ONLINE API") }
                  ]}
                />
              </div>

              {configData.summary_mode === "local" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("本地 API 接口地址", "Local API URL")}</label>
                    <input type="text" value={configData.ollama_url || ""} onChange={(e) => handleConfigChange("ollama_url", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.ollama_url)}`}
                      placeholder="http://localhost:11434" />
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("模型 ID", "Model ID")}</label>
                    <input type="text" value={configData.ollama_model || ""} onChange={(e) => handleConfigChange("ollama_model", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.ollama_model)}`}
                      placeholder="qwen2.5:7b-instruct" />
                  </div>
                </>
              )}

              {configData.summary_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("在线 API 基础地址", "Online API Base URL")}</label>
                    <input type="text" value={configData.online_summary_base_url || ""} onChange={(e) => handleConfigChange("online_summary_base_url", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_summary_base_url)}`}
                      placeholder="https://api.openai.com/v1" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">{t("样例：https://api.openai.com/v1 或第三方中转 API 地址", "Example: https://api.openai.com/v1 or a third-party OpenAI-compatible API base URL")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("在线大模型 ID", "Online Model ID")}</label>
                    <input type="text" value={configData.online_summary_model || ""} onChange={(e) => handleConfigChange("online_summary_model", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_summary_model)}`}
                      placeholder="gpt-4o-mini" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">{t("样例：gpt-4o-mini 或 qwen-plus", "Example: gpt-4o-mini or qwen-plus")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("API Key", "API Key")}</label>
                    <input type="password" value={configData.online_summary_api_key || ""} onChange={(e) => handleConfigChange("online_summary_api_key", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_summary_api_key)}`}
                      placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">{t("输入您在大模型服务商申请的 API 密钥", "Enter the API key you requested from your LLM service provider")}</span>
                  </div>

                </>
              )}
            </div>

            {/* Card: LLM Prompt Template Settings */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center justify-between pb-4 border-b border-[var(--border-primary)]/20">
                <div className="flex items-center gap-2">
                  <Terminal size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("总结 Prompt 模板配置", "Summary Prompt Template")}</h3>
                </div>

                <div className="flex items-center gap-2">
                  <button type="button" onClick={handleResetPrompt}
                    className="px-3 py-1.5 bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:bg-[var(--border-primary)]/30 text-xs font-bold rounded-lg cursor-pointer transition-all border-0 outline-none flex items-center gap-1.5">
                    <RotateCcw size={13} />
                    <span>{t("恢复默认", "Reset to Default")}</span>
                  </button>
                  <button type="button" onClick={handleSavePrompt} disabled={promptSaveStatus === "saving"}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg cursor-pointer transition-all border-0 outline-none flex items-center gap-1.5 ${
                      promptSaveStatus === "saved" ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                      : promptSaveStatus === "error" ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300"
                      : "bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white"
                    }`}>
                    {promptSaveStatus === "saving" && <Loader2 size={13} className="animate-spin" />}
                    {promptSaveStatus === "saved" && <Check size={13} />}
                    {promptSaveStatus === "error" && <AlertCircle size={13} />}
                    {promptSaveStatus !== "saving" && promptSaveStatus !== "saved" && promptSaveStatus !== "error" && <Save size={13} />}
                    <span>
                      {promptSaveStatus === "saving" ? t("保存中...", "Saving...")
                        : promptSaveStatus === "saved" ? t("已保存", "Saved")
                        : promptSaveStatus === "error" ? t("保存失败", "Failed")
                        : t("保存 Prompt", "Save Prompt")}
                    </span>
                  </button>
                </div>
              </div>

              {/* Template Preset Selector */}
              {templates.length > 0 && (
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                    <FileText size={13} className="inline mr-1 -mt-0.5" />
                    {t("快速选用预设模板", "Quick Preset Templates")}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {templates.map((tpl) => (
                      <button
                        key={tpl.id}
                        type="button"
                        onClick={() => handleTemplateSelect(tpl.id)}
                        disabled={loadingTemplate}
                        className={`px-3 py-1.5 text-xs font-bold rounded-lg cursor-pointer transition-all border outline-none flex items-center gap-1.5 ${
                          selectedTemplate === tpl.id
                            ? "bg-[var(--accent-red)] text-white border-[var(--accent-red)]"
                            : "bg-[var(--bg-hover)] text-[var(--text-secondary)] border-[var(--border-primary)]/40 hover:border-[var(--accent-red)]/50 hover:text-[var(--text-primary)]"
                        }`}
                      >
                        {loadingTemplate && selectedTemplate === tpl.id && <Loader2 size={12} className="animate-spin" />}
                        <span>{configData.language === "en" ? (tpl.name_en || tpl.name) : tpl.name}</span>
                      </button>
                    ))}
                  </div>
                  {selectedTemplate && templates.find(t => t.id === selectedTemplate)?.description && (
                    <p className="text-xs text-[var(--text-muted)] font-medium mt-0.5">
                      {configData.language === "en"
                        ? (templates.find(t => t.id === selectedTemplate).description_en || templates.find(t => t.id === selectedTemplate).description)
                        : templates.find(t => t.id === selectedTemplate).description}
                    </p>
                  )}
                </div>
              )}

              {/* Single Prompt Editor */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  {t("📝 总结 Prompt（完整指令）", "📝 Summary Prompt (Full Instructions)")}
                </label>
                <textarea
                  value={promptData?.prompt || ""}
                  onChange={(e) => setPromptData(prev => ({ ...prev, prompt: e.target.value }))}
                  rows={18}
                  className="w-full bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-3 text-sm font-mono text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] resize-y min-h-[360px]"
                  placeholder={t(
                    "输入完整的总结 Prompt... 使用 {{PODCAST_DATA}} 标记数据注入位置。",
                    "Enter full summary prompt... Use {{PODCAST_DATA}} to mark data injection point."
                  )}
                />
              </div>

            </div>

            <div className="flex items-center gap-3 mt-2">
              <button onClick={handleSaveConfig}
                className="flex-1 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all active:scale-98 shadow-xs border-0 outline-none cursor-pointer">
                <Save size={16} />
                <span>{t("保存配置表", "Save Configuration")}</span>
              </button>
              <button type="button" role="switch" aria-checked={autoSaveEnabled} onClick={() => setAutoSaveEnabled(!autoSaveEnabled)}
                className={`group flex items-center gap-2.5 px-4 py-3 rounded-lg transition-all cursor-pointer border-0 outline-none select-none shadow-xs ${
                  autoSaveEnabled ? "bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white" : "bg-[var(--border-primary)] hover:bg-[var(--border-primary)] text-[var(--text-muted)]"
                }`}>
                <RefreshCw size={16} />
                <span className="font-bold whitespace-nowrap">{t("自动保存", "Auto-Save")}</span>
                <div className={`relative w-8 h-[18px] rounded-full transition-colors duration-200 ${autoSaveEnabled ? "bg-white/30" : "bg-[var(--bg-hover)]"}`}>
                  <span className={`absolute top-[2px] w-[14px] h-[14px] rounded-full bg-white shadow-sm transition-transform duration-200 ${autoSaveEnabled ? "left-[16px]" : "left-[2px]"}`} />
                </div>
              </button>
            </div>
          </div>

          {/* Right Column */}
          <div className="flex flex-col gap-6">
            {/* Language Preference Card */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-4 transition-colors duration-300">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-primary)]/10 text-[var(--accent-red)]">
                <Globe size={16} />
                <h3 className="font-bold text-sm text-[var(--text-primary)]">{t("系统语言设置", "System Language Preference")}</h3>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("语言选择", "Select Language")}</label>
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

            {/* Windows Autostart Card */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-4 transition-colors duration-300">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-primary)]/10 text-[var(--accent-red)]">
                <Power size={16} />
                <h3 className="font-bold text-sm text-[var(--text-primary)]">{t("开机自启动", "Auto Start on Boot")}</h3>
              </div>
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={configData.enable_autostart_windows || false}
                      onChange={(e) => handleConfigChange("enable_autostart_windows", e.target.checked)}
                    />
                    <div className={`block w-10 h-6 rounded-full transition-colors ${configData.enable_autostart_windows ? 'bg-[var(--accent-red)]' : 'bg-[var(--border-primary)]'}`}></div>
                    <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${configData.enable_autostart_windows ? 'transform translate-x-4' : ''}`}></div>
                  </div>
                  <span className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-red)] transition-colors">
                    {t("随系统开机自动后台运行", "Start automatically in background on system boot")}
                  </span>
                </label>
              </div>
            </div>

            {/* AI Lab Beta Features Card */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-primary)]/20">
                <Sparkles size={18} className="text-[var(--accent-red)]" />
                <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("实验室选项 (Beta)", "Lab Options (Beta)")}</h3>
              </div>
              <div className="flex flex-col p-4 bg-[var(--bg-secondary)]/30 rounded-lg border border-[var(--border-primary)]/30 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-[var(--text-primary)]">{t("智能声纹推理与说话人分离", "Speaker Diarization & Smart Inference")}</h4>
                    <p className="text-[var(--text-muted)] text-xs mt-0.5">{t("关闭后转录速度极快，但无法区分不同说话人（适合单人播客）。", "Turn off for blazing fast transcription without speaker separation (ideal for solo podcasts).")}</p>
                  </div>
                  <input type="checkbox" checked={configData.enable_speaker_inference !== false} onChange={(e) => handleConfigChange("enable_speaker_inference", e.target.checked)} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[var(--accent-red)] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
                </div>
                {configData.enable_speaker_inference !== false && (
                  <div className="mt-4 pt-4 border-t border-[var(--border-primary)]/20 flex flex-col gap-3 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5 flex-1">
                        <ShieldAlert size={14} className="text-[var(--accent-red)] shrink-0" />
                        {t("Hugging Face Token", "Hugging Face Token")}
                        <span className="text-[var(--accent-red)]">*</span>
                      </label>
                      <button type="button" onClick={handleVerifyHF} disabled={hfChecking} className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] text-[11px] font-bold rounded-md transition-all disabled:opacity-50 cursor-pointer border border-[var(--border-primary)]/40 outline-none whitespace-nowrap shrink-0">
                        {hfChecking ? <Loader2 size={12} className="animate-spin" /> : <ShieldAlert size={12} />}
                        <span>{t("验证 Token", "Verify Token")}</span>
                      </button>
                    </div>
                    <input type="password" value={configData.hf_token || ""} onChange={(e) => handleConfigChange("hf_token", e.target.value)} className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.hf_token)}`} placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
                    <div className="flex items-center gap-2">
                      {hfTokenStatus && (
                        hfTokenStatus.status === "valid" ? (
                          <span className="text-[var(--success-color,green)] text-xs font-bold flex items-center gap-1.5"><Check size={14} /> {t("Token 验证通过", "Token is valid")}</span>
                        ) : (
                          <span className="text-[var(--accent-red)] text-xs font-bold flex items-center gap-1.5"><AlertCircle size={14} /> {hfTokenStatus.message}</span>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Notifications Card */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-primary)]/20">
                <Bell size={18} className="text-[var(--accent-red)]" />
                <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("通知设置", "Notifications")}</h3>
              </div>
              <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)]/30 rounded-lg border border-[var(--border-primary)]/30">
                <div>
                  <h4 className="font-bold text-sm text-[var(--text-primary)]">{t("桌面通知", "Desktop Notifications")}</h4>
                  <p className="text-[var(--text-muted)] text-xs mt-0.5">{t("处理结束时在桌面推送通知提醒。", "Push notification on desktop when processing ends.")}</p>
                </div>
                <input type="checkbox" checked={configData.enable_win_notification !== false} onChange={(e) => handleConfigChange("enable_win_notification", e.target.checked)} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[var(--accent-red)] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
              </div>
              <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)]/30 rounded-lg border border-[var(--border-primary)]/30">
                <div>
                  <h4 className="font-bold text-sm text-[var(--text-primary)]">{t("邮件提醒", "Email Alerts")}</h4>
                  <p className="text-[var(--text-muted)] text-xs mt-0.5">{t("任务结束时发送邮件通知（需要配置 SMTP）。", "Send mail alerts (SMTP) when task completes.")}</p>
                </div>
                <input type="checkbox" checked={configData.enable_email_notification === true} onChange={(e) => handleConfigChange("enable_email_notification", e.target.checked)} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[var(--accent-red)] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
              </div>
              {configData.enable_email_notification === true && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-[var(--border-primary)]/20 pt-4 animate-fade-in">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">SMTP Server</label>
                    <input type="text" value={configData.smtp_server || ""} onChange={(e) => handleConfigChange("smtp_server", e.target.value)} className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]" placeholder="smtp.qq.com" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Port</label>
                    <input type="number" value={configData.smtp_port || 465} onChange={(e) => handleConfigChange("smtp_port", Number(e.target.value))} className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Username</label>
                    <input type="text" value={configData.smtp_username || ""} onChange={(e) => handleConfigChange("smtp_username", e.target.value)} className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]" placeholder="user@example.com" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Password</label>
                    <input type="password" value={configData.smtp_password || ""} onChange={(e) => handleConfigChange("smtp_password", e.target.value)} className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]" placeholder="********" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Sender Email</label>
                    <input type="text" value={configData.smtp_sender || ""} onChange={(e) => handleConfigChange("smtp_sender", e.target.value)} className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]" placeholder="sender@example.com" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Receiver Email</label>
                    <input type="text" value={configData.notification_email || ""} onChange={(e) => handleConfigChange("notification_email", e.target.value)} className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]" placeholder="receiver@example.com" />
                  </div>
                </div>
              )}
            </div>


            {/* Audio Auto-Cleanup Panel */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-4 animate-fade-in transition-colors duration-300">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-primary)]/10 text-[var(--accent-red)]">
                <Trash2 size={16} />
                <h3 className="font-bold text-sm text-[var(--text-primary)]">{t("自动清理音频", "Audio Auto-Cleanup")}</h3>
              </div>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed font-medium">
                {t("自动删除本地缓存的播客音频源文件以节省硬盘空间。对应的文本转录和 AI 总结报告将完好保留。", "Automatically delete downloaded podcast audio files to free up disk space. Transcripts and AI summaries will be fully preserved.")}
              </p>
              <div className="flex items-center justify-between p-3.5 bg-[var(--bg-secondary)]/30 rounded-lg border border-[var(--border-primary)]/20">
                <div>
                  <h4 className="font-bold text-xs text-[var(--text-primary)]">{t("启用自动清理", "Enable Auto-Cleanup")}</h4>
                  <p className="text-[var(--text-muted)] text-[10px] mt-0.5">{t("开启后将定时清除过期音频。", "Regularly clean up expired audio files.")}</p>
                </div>
                <input type="checkbox" checked={configData.enable_auto_cleanup || false} onChange={(e) => handleConfigChange("enable_auto_cleanup", e.target.checked)} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[var(--accent-red)] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
              </div>
              {configData.enable_auto_cleanup && (
                <div className="flex flex-col gap-2 animate-fade-in">
                  <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("清理时效周期", "Cleanup Threshold")}</label>
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

            {/* Core Dependencies */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-primary)]/20">
                <Terminal size={18} className="text-[var(--accent-red)]" />
                <h3 className="text-lg font-bold text-[var(--text-primary)]">Core Dependencies</h3>
              </div>
              <div className="flex items-center gap-3 p-4 rounded-lg border border-[var(--border-primary)]/30 bg-[var(--bg-secondary)]/20">
                <div className={`w-3 h-3 rounded-full flex-shrink-0 ${ffmpegStatus?.available ? "bg-green-500" : ffmpegStatus === null ? "bg-yellow-400 animate-pulse" : "bg-red-500"}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-[var(--text-primary)]">
                    {ffmpegStatus === null ? "Detecting FFmpeg..." : ffmpegStatus?.available ? `FFmpeg ${ffmpegStatus.version || ""}` : "FFmpeg not found"}
                  </div>
                  {ffmpegStatus?.available && ffmpegStatus?.path && <div className="text-xs text-[var(--text-muted)] font-mono truncate mt-0.5">{ffmpegStatus.path.split(/[\\/]/).slice(-2).join("/")}</div>}
                  {!ffmpegStatus?.available && ffmpegStatus !== null && <div className="text-xs text-[var(--accent-red)] mt-1">Install: winget install Gyan.FFmpeg</div>}
                </div>
                <button onClick={() => handleVerifyFfmpeg(configData.ffmpeg_path)} className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-primary)]/40 text-[var(--text-muted)] hover:bg-[var(--bg-hover)] transition-colors font-semibold cursor-pointer bg-transparent">Re-check</button>
              </div>
              {/* FFmpeg 路径已内置，无需手动配置 */}
            </div>

            {/* GitHub Repo & Version Info */}
            <a
              href={versionInfo?.has_update ? versionInfo.release_url : "https://github.com/quentin2001/whisperMe"}
              target="_blank"
              rel="noopener noreferrer"
              style={{ textDecoration: 'none' }}
              className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs hover:border-[var(--accent-red)]/55 hover:shadow-xs transition-all flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[var(--bg-hover)]/65 flex items-center justify-center text-[var(--text-primary)] group-hover:scale-105 transition-all">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
                </div>
                <div>
                  <h4 className="font-bold text-sm text-[var(--text-primary)] font-display group-hover:text-[var(--accent-red)] transition-all">{t("GitHub 仓库", "GitHub Repository")}</h4>
                  <p className="text-[11px] text-[var(--text-muted)] font-semibold mt-0.5">quentin2001/whisperMe</p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <span className={`text-[10px] font-extrabold tracking-wider uppercase px-2.5 py-1 rounded-full border font-mono ${
                  versionInfo?.has_update
                    ? "bg-[var(--accent-red-light)] text-[var(--accent-red)] border-[var(--accent-red-light)] animate-pulse"
                    : "bg-[var(--bg-hover)]/60 text-[var(--text-muted)] border-[var(--border-primary)]/30"
                }`}>
                  {versionInfo?.has_update
                    ? `${t("有新版本", "UPDATE")} v${versionInfo.latest_version}`
                    : `v${versionInfo?.current_version || "1.0.0"}`
                  }
                </span>
                <button type="button" onClick={(e) => { e.preventDefault(); e.stopPropagation(); onCheckVersion(true); }}
                  className="text-[10px] text-[var(--accent-red)] hover:underline bg-transparent border-0 cursor-pointer font-bold mt-1 flex items-center gap-1 select-none outline-none"
                  disabled={checkingVersion}>
                  {checkingVersion ? (
                    <><Loader2 size={10} className="animate-spin text-[var(--accent-red)]" /><span>{t("检查中...", "Checking...")}</span></>
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
