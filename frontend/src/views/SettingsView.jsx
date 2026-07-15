import React, { useState, useRef, useEffect } from "react";
import { Sliders, Save, ShieldAlert, Cpu, Bell, ChevronDown, ChevronUp, RotateCcw, Check, Loader2, AlertCircle, Trash2, Globe, RefreshCw, FileText, Activity, Download, HardDrive, Folder, HelpCircle, Plus, Copy, X } from "lucide-react";
import { API_BASE } from "../constants.js";
import { useConfigStore } from "../store/configStore.js";
import { useTranslation } from "../contexts/I18nContext";
import { alert, confirm } from "../components/Dialog.jsx";

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

  useEffect(() => {
    if (!autoSaveEnabled || !configData) return;
    const timer = setTimeout(() => {
      if (typeof handleSaveConfig === 'function') {
        handleSaveConfig(null, true);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [configData, autoSaveEnabled, handleSaveConfig]);

  const [isFlashing, setIsFlashing] = useState(true);
  const [ffmpegStatus, setFfmpegStatus] = useState(null);
  const [dependencies, setDependencies] = useState(null);
  const [hfTokenStatus, setHfTokenStatus] = useState(null);
  const [hfChecking, setHfChecking] = useState(false);
  const [testingAsr, setTestingAsr] = useState(false);
  const [testAsrResult, setTestAsrResult] = useState(null); // 'success' | 'error' | null
  const [testAsrMessage, setTestAsrMessage] = useState("");
  const [testingLlm, setTestingLlm] = useState(false);

  const [testLlmResult, setTestLlmResult] = useState(null);
  const [testLlmMessage, setTestLlmMessage] = useState("");

  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editPrompt, setEditPrompt] = useState("");
  const [isNewTemplate, setIsNewTemplate] = useState(false);
  const [saveStatus, setSaveStatus] = useState("idle"); // 'idle' | 'saving' | 'saved' | 'error'
  
  const [showSaveAsModal, setShowSaveAsModal] = useState(false);
  const [saveAsName, setSaveAsName] = useState("");
  const [saveAsDesc, setSaveAsDesc] = useState("");
  
  const [infoModal, setInfoModal] = useState({ isOpen: false, type: "" });

  const testConnection = async (type) => {
    const isAsr = type === "asr";
    
    if (isAsr) {
      setTestingAsr(true);
      setTestAsrResult(null);
    } else {
      setTestingLlm(true);
      setTestLlmResult(null);
    }

    try {
      let endpoint = "";
      let payload = {};

      if (isAsr && configData.asr_mode === "local") {
        endpoint = `${API_BASE}/api/config/test/local_asr`;
        payload = { model_path: configData.local_whisper_model_path || "" };
      } else if (!isAsr && configData.summary_mode === "local") {
        endpoint = `${API_BASE}/api/config/test/llm`;
        payload = { api_key: "", base_url: configData.ollama_url || "", model: configData.ollama_model || "" };
        if (!payload.base_url) throw new Error("Base URL is empty");
      } else {
        const apiKey = isAsr ? configData.online_api_key : configData.online_summary_api_key;
        const baseUrl = isAsr ? configData.online_base_url : configData.online_summary_base_url;
        const model = isAsr ? configData.online_model : configData.online_summary_model;
        
        if (!baseUrl) {
          throw new Error("Base URL is empty");
        }
        endpoint = `${API_BASE}/api/config/test/${type}`;
        payload = { api_key: apiKey || "", base_url: baseUrl, model: model || "" };
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      if (data.success) {
        if (isAsr) {
          setTestAsrResult('success');
          setTestAsrMessage(data.message || t("测试成功", "Success"));
        } else {
          setTestLlmResult('success');
          setTestLlmMessage(data.message || t("测试成功", "Success"));
        }
      } else {
        if (isAsr) {
          setTestAsrResult('error');
          setTestAsrMessage(data.message || t("测试失败", "Failed"));
        } else {
          setTestLlmResult('error');
          setTestLlmMessage(data.message || t("测试失败", "Failed"));
        }
      }
    } catch (e) {
      if (isAsr) {
        setTestAsrResult('error');
        setTestAsrMessage(e.message || "Network Error");
      }
      else {
        setTestLlmResult('error');
        setTestLlmMessage(e.message || "Network Error");
      }
    } finally {
      if (isAsr) {
        setTestingAsr(false);
        setTimeout(() => {
          setTestAsrResult(null);
          setTestAsrMessage("");
        }, 5000);
      } else {
        setTestingLlm(false);
        setTimeout(() => {
          setTestLlmResult(null);
          setTestLlmMessage("");
        }, 5000);
      }
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
  const [selectedTemplate, setSelectedTemplate] = useState("standard");
  const [loadingTemplate, setLoadingTemplate] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/prompt/templates`)
      .then(r => r.json())
      .then(data => {
        if (data && typeof data === "object") {
          const list = Object.entries(data).map(([id, info]) => ({ id, ...info }));
          setTemplates(list);
          const standardTpl = list.find(t => t.id === "standard");
          if (standardTpl) {
            setEditName(standardTpl.name || "");
            setEditDesc(standardTpl.description || "");
          }
        }
      })
      .catch(() => {});

    // Auto-select standard template on mount
    setLoadingTemplate(true);
    fetch(`${API_BASE}/api/prompt/template/standard`)
      .then(r => r.json())
      .then(data => {
        if (data.prompt) {
          setPromptData({ prompt: data.prompt });
          setEditPrompt(data.prompt);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingTemplate(false));
  }, []);

  const refreshTemplates = async (selectId = null) => {
    try {
      const r = await fetch(`${API_BASE}/api/prompt/templates`);
      const data = await r.json();
      if (data && typeof data === "object") {
        const list = Object.entries(data).map(([id, info]) => ({ id, ...info }));
        setTemplates(list);
        
        if (selectId) {
          const savedTpl = list.find(t => t.id === selectId);
          if (savedTpl) {
            setSelectedTemplate(selectId);
            setEditName(savedTpl.name || "");
            setEditDesc(savedTpl.description || "");
            setIsNewTemplate(false);
            
            setLoadingTemplate(true);
            const promptRes = await fetch(`${API_BASE}/api/prompt/template/${selectId}`);
            const promptDataJson = await promptRes.json();
            if (promptDataJson.prompt !== undefined) {
              setEditPrompt(promptDataJson.prompt);
            }
            setLoadingTemplate(false);
          }
        }
      }
    } catch (e) {
      console.error("Failed to refresh templates:", e);
    }
  };

  const handleTemplateSelect = (templateId) => {
    if (!templateId) return;
    setSelectedTemplate(templateId);
    setIsNewTemplate(false);
    const tpl = templates.find(t => t.id === templateId);
    if (tpl) {
      setEditName(tpl.name || "");
      setEditDesc(tpl.description || "");
    }
    setLoadingTemplate(true);
    fetch(`${API_BASE}/api/prompt/template/${templateId}`)
      .then(r => r.json())
      .then(data => {
        if (data.prompt !== undefined) {
          setEditPrompt(data.prompt);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingTemplate(false));
  };

  const handleSaveCustomTemplate = async () => {
    if (!editName.trim()) {
      alert(t("请输入模板名称", "Please enter template name"), { variant: "warning" });
      return;
    }
    
    setSaveStatus("saving");
    try {
      const res = await fetch(`${API_BASE}/api/prompt/template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: isNewTemplate ? "" : selectedTemplate,
          name: editName,
          description: editDesc,
          prompt: editPrompt
        })
      });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        setSaveStatus("saved");
        alert(t("模板保存成功！", "Template saved successfully!"), { variant: "success" });
        await refreshTemplates(data.id);
      } else {
        setSaveStatus("error");
        alert(data.detail || t("保存模板失败", "Failed to save template"), { variant: "warning" });
      }
    } catch (e) {
      setSaveStatus("error");
      alert(e.message || t("网络错误", "Network error"), { variant: "warning" });
    } finally {
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  };

  const handleDeleteCustomTemplate = async () => {
    if (isNewTemplate) {
      handleTemplateSelect("standard");
      return;
    }
    const tpl = templates.find(t => t.id === selectedTemplate);
    if (!tpl || tpl.is_builtin) return;

    if (await confirm(t(`确定要删除自定义模板“${tpl.name}”吗？`, `Are you sure you want to delete the custom template "${tpl.name}"?`))) {
      try {
        const res = await fetch(`${API_BASE}/api/prompt/template/${selectedTemplate}`, {
          method: "DELETE"
        });
        if (res.ok) {
          await refreshTemplates("standard");
        } else {
          alert(t("删除模板失败", "Failed to delete template"), { variant: "warning" });
        }
      } catch (e) {
        alert(e.message || t("网络错误", "Network error"), { variant: "warning" });
      }
    }
  };

  const handleSaveAsNewTemplate = async () => {
    if (!saveAsName.trim()) {
      alert(t("请输入模板名称", "Please enter template name"), { variant: "warning" });
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE}/api/prompt/template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: "",
          name: saveAsName,
          description: saveAsDesc,
          prompt: editPrompt
        })
      });
      const data = await res.json();
      if (res.ok && data.status === "ok") {
        setShowSaveAsModal(false);
        setSaveAsName("");
        setSaveAsDesc("");
        alert(t("另存为新模板成功！", "Saved as new template successfully!"), { variant: "success" });
        await refreshTemplates(data.id);
      } else {
        alert(data.detail || t("保存模板失败", "Failed to save template"), { variant: "warning" });
      }
    } catch (e) {
      alert(e.message || t("网络错误", "Network error"), { variant: "warning" });
    }
  };

  const handleApplyAsSystemDefault = () => {
    setPromptData({ 
      prompt: editPrompt,
      default_template_id: selectedTemplate
    });
    setTimeout(() => {
      handleSavePrompt();
      setTimeout(() => {
        refreshTemplates(selectedTemplate);
      }, 500);
    }, 50);
  };

  const onResetPromptClick = async () => {
    await handleResetPrompt();
    const res = await fetch(`${API_BASE}/api/prompt/template/standard`);
    const data = await res.json();
    if (data.prompt) {
      setEditPrompt(data.prompt);
    }
    setTimeout(() => {
      refreshTemplates("standard");
    }, 500);
  };

  const handleMoveTemplate = async (index, direction) => {
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= templates.length) return;
    
    const updated = [...templates];
    const temp = updated[index];
    updated[index] = updated[nextIndex];
    updated[nextIndex] = temp;
    
    setTemplates(updated);
    
    try {
      const res = await fetch(`${API_BASE}/api/prompt/templates/reorder`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order: updated.map(t => t.id) })
      });
      if (!res.ok) {
        throw new Error("Failed to save template order");
      }
    } catch (e) {
      console.error(e);
      refreshTemplates(selectedTemplate);
    }
  };

  const handleSelectLocalModelPath = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/system/select-directory`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        if (data.directory) {
          handleConfigChange("local_whisper_model_path", data.directory);
        }
      }
    } catch (e) {
      console.error("Failed to pick directory:", e);
    }
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

  const isPlaceholder = (val) => {
    if (!val || typeof val !== "string") return false;
    const cleanVal = val.trim();
    const reverse = (str) => str.split("").reverse().join("");
    return (
      cleanVal === reverse("crmx2jbap5lltbitxkmdyx8bnts94m2npywgzwr9jvuof4hc-ks") ||
      cleanVal === reverse("db33f77aa810e3ba0634097dcaa4b362-ks") ||
      cleanVal === reverse("smmfBCsTrzdMXReSkqzDAAkFqapBYKsFpk_fh")
    );
  };

  const getHighlightClass = (val) => {
    const isInvalid = !val || String(val).trim() === "" || isPlaceholder(val);
    return isFlashing && isInvalid ? "highlight-flash" : "";
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
                <div className="flex items-center gap-2">
                  <button onClick={() => testConnection("asr")} disabled={testingAsr} className={`flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-md transition-all cursor-pointer disabled:opacity-50 whitespace-nowrap shrink-0 border outline-none
                    ${testAsrResult === 'success' ? 'bg-green-100/50 text-green-700 border-green-200'
                    : testAsrResult === 'error' ? 'bg-red-100/50 text-red-700 border-red-200'
                    : 'bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] border-[var(--border-primary)]/40'}
                  `}>
                    {testingAsr ? <Loader2 size={12} className="animate-spin" /> : 
                     testAsrResult === 'success' ? <Check size={12} className="text-green-600" /> :
                     testAsrResult === 'error' ? <AlertCircle size={12} className="text-red-600" /> :
                     <Activity size={12} className="text-[var(--accent-red)]" />}
                    <span>{testingAsr ? t("测试中...", "Testing...") : 
                           testAsrResult === 'success' ? t("测试成功", "Success") :
                           testAsrResult === 'error' ? t("测试失败", "Failed") :
                           t("测试连通性", "Test Connection")}</span>
                  </button>
                  {testAsrMessage && (
                    <span className={`text-[11px] ${testAsrResult === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                      {testAsrMessage}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("引擎工作模式", "ASR MODE")}</label>
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
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <div className="flex items-center gap-1.5">
                      <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                        {t("本地 ASR 模型文件夹路径", "Local ASR Model Path")}
                      </label>
                      <button
                        type="button"
                        onClick={() => setInfoModal({ isOpen: true, type: "asr" })}
                        className="text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors p-0.5 border-0 bg-transparent outline-none cursor-pointer flex items-center justify-center animate-fade-in"
                        title={t("获取配置 AI Agent 提示词", "Get AI Agent setup prompt")}
                      >
                        <HelpCircle size={14} />
                      </button>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={configData.local_whisper_model_path || ""}
                        onChange={(e) => handleConfigChange("local_whisper_model_path", e.target.value)}
                        className={`flex-1 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.local_whisper_model_path)}`}
                        placeholder="models/funasr"
                      />
                      <button
                        type="button"
                        onClick={handleSelectLocalModelPath}
                        className="px-4 py-2.5 bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] border border-[var(--border-primary)]/30 text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-bold rounded-lg transition-all cursor-pointer outline-none select-none flex items-center gap-1.5"
                      >
                        <Folder size={14} className="text-[var(--accent-red)]" />
                        <span>{t("选择目录", "Select Folder")}</span>
                      </button>
                    </div>
                    <span className="text-xs text-[var(--text-muted)] font-medium leading-relaxed">
                      {t("指定本地ASR模型目录例如：E:/Projects/whisperMe/models/funasr", "Specify the local ASR model directory, e.g., E:/Projects/whisperMe/models/funasr")}
                    </span>
                  </div>
                </>
              )}

                            {configData.asr_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("API Base URL", "ASR Base URL")}</label>
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
                <div className="flex items-center gap-2">
                  <button onClick={() => testConnection("llm")} disabled={testingLlm} className={`flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-md transition-all cursor-pointer disabled:opacity-50 whitespace-nowrap shrink-0 border outline-none
                    ${testLlmResult === 'success' ? 'bg-green-100/50 text-green-700 border-green-200'
                    : testLlmResult === 'error' ? 'bg-red-100/50 text-red-700 border-red-200'
                    : 'bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] border-[var(--border-primary)]/40'}
                  `}>
                    {testingLlm ? <Loader2 size={12} className="animate-spin" /> : 
                     testLlmResult === 'success' ? <Check size={12} className="text-green-600" /> :
                     testLlmResult === 'error' ? <AlertCircle size={12} className="text-red-600" /> :
                     <Activity size={12} className="text-[var(--accent-red)]" />}
                    <span>{testingLlm ? t("测试中...", "Testing...") : 
                           testLlmResult === 'success' ? t("测试成功", "Success") :
                           testLlmResult === 'error' ? t("测试失败", "Failed") :
                           t("测试连通性", "Test Connection")}</span>
                  </button>
                  {testLlmMessage && (
                    <span className={`text-[11px] ${testLlmResult === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                      {testLlmMessage}
                    </span>
                  )}
                </div>
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
                  <div className="flex flex-col gap-4 animate-fade-in">
                    <div className="flex flex-col gap-2">
                      <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("本地 LLM 接口地址", "Local LLM Model Path")}</label>
                      <input type="text" value={configData.ollama_url || ""} onChange={(e) => handleConfigChange("ollama_url", e.target.value)}
                        className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.ollama_url)}`}
                        placeholder="http://localhost:11434" />
                    </div>
                    <div className="flex flex-col gap-2">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-1.5">
                          <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("模型 ID", "Model ID")}</label>
                          <button
                            type="button"
                            onClick={() => setInfoModal({ isOpen: true, type: "llm" })}
                            className="text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors p-0.5 border-0 bg-transparent outline-none cursor-pointer flex items-center justify-center animate-fade-in"
                            title={t("获取配置 AI Agent 提示词", "Get AI Agent setup prompt")}
                          >
                            <HelpCircle size={14} />
                          </button>
                        </div>
                        <p className="text-[10px] text-[var(--text-muted)] opacity-85 italic">
                          {t("* Ollama 模式下模型 ID 须与本地已拉取名称（如 qwen2.5:7b-instruct）完全匹配；LM Studio 多模型加载下也须匹配具体加载的 ID", "* For Ollama, Model ID must match the downloaded name exactly. For LM Studio, it must match the loaded model ID.")}
                        </p>
                      </div>
                      <input type="text" value={configData.ollama_model || ""} onChange={(e) => handleConfigChange("ollama_model", e.target.value)}
                        className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.ollama_model)}`}
                        placeholder="qwen2.5:7b-instruct" />
                    </div>
                  </div>
                </>
              )}

                            {configData.summary_mode === "online" && (
                <>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("在线 API 基础地址", "LLM Base URL")}</label>
                    <input type="text" value={configData.online_summary_base_url || ""} onChange={(e) => handleConfigChange("online_summary_base_url", e.target.value)}
                      className={`bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] ${getHighlightClass(configData.online_summary_base_url)}`}
                      placeholder="https://api.openai.com/v1" />
                    <span className="text-xs text-[var(--text-muted)] font-medium">{t("样例：https://api.openai.com/v1 或第三方中转 API 地址", "Example: https://api.openai.com/v1 or a third-party OpenAI-compatible API base URL")}</span>
                  </div>
                  <div className="flex flex-col gap-2 animate-fade-in">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{t("在线大模型 ID", "Model ID")}</label>
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

            {/* AI Summary Prompt Template Manager Card */}
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl p-6 shadow-xs flex flex-col gap-5 transition-colors duration-300">
              <div className="flex items-center justify-between pb-4 border-b border-[var(--border-primary)]/20">
                <div className="flex items-center gap-2">
                  <FileText size={18} className="text-[var(--accent-red)]" />
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("AI 总结 Prompt 模板管理", "AI Summary Prompt Template Manager")}</h3>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Left Column - Template Sidebar List */}
                <div className="md:col-span-1 border-r border-[var(--border-primary)]/10 pr-4 flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                      {t("模板列表", "Templates")}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedTemplate("");
                        setEditName(t("新建自定义模板", "New Custom Template"));
                        setEditDesc("");
                        setEditPrompt("{{PODCAST_DATA}}\n\n");
                        setIsNewTemplate(true);
                      }}
                      className="p-1 text-[var(--accent-red)] hover:bg-[var(--bg-hover)] rounded transition-colors flex items-center justify-center border-0 bg-transparent cursor-pointer outline-none"
                      title={t("新建模板", "New Template")}
                    >
                      <Plus size={16} />
                    </button>
                  </div>

                  <div className="flex flex-col gap-1.5 max-h-[400px] overflow-y-auto pr-1">
                    {templates.map((tpl, index) => (
                      <div key={tpl.id} className="relative group/item flex items-center gap-1 w-full">
                        <button
                          type="button"
                          onClick={() => handleTemplateSelect(tpl.id)}
                          className={`flex-1 py-2.5 px-3 border rounded-lg text-left transition-all cursor-pointer outline-none select-none flex flex-col gap-0.5 min-w-0
                            ${selectedTemplate === tpl.id
                              ? 'border-[var(--accent-red)] bg-[var(--accent-red-light)]/10 text-[var(--text-primary)] font-bold'
                              : 'border-[var(--border-primary)]/20 hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] bg-transparent'
                            }
                          `}
                        >
                          <div className="flex items-center justify-between w-full min-w-0">
                            <span className="text-xs font-bold truncate pr-1 flex items-center gap-1.5 min-w-0">
                              <span className="truncate">{tpl.name}</span>
                              {tpl.is_default && (
                                <span className="shrink-0 text-[8px] bg-[var(--accent-red)] text-white px-1 py-0.2 rounded font-extrabold tracking-wide uppercase scale-90">
                                  {t("默认", "Default")}
                                </span>
                              )}
                            </span>
                            {tpl.is_builtin ? (
                              <span className="shrink-0 text-[9px] bg-[var(--border-primary)]/40 text-[var(--text-muted)] px-1 rounded scale-90 origin-right">
                                {t("内置", "Built-in")}
                              </span>
                            ) : (
                              <span className="shrink-0 text-[9px] bg-red-100/60 text-red-600 dark:bg-red-950/40 dark:text-red-400 px-1 rounded scale-90 origin-right">
                                {t("自定义", "Custom")}
                              </span>
                            )}
                          </div>
                          {tpl.description && (
                            <span className="text-[10px] text-[var(--text-muted)] truncate w-full font-medium">
                              {tpl.description}
                            </span>
                          )}
                        </button>

                        <div className="hidden group-hover/item:flex flex-col gap-0.5 justify-center pl-1 shrink-0">
                          <button
                            type="button"
                            disabled={index === 0}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMoveTemplate(index, -1);
                            }}
                            className="p-0.5 text-[var(--text-muted)] hover:text-[var(--accent-red)] bg-transparent border-0 outline-none cursor-pointer disabled:opacity-30 disabled:hover:text-[var(--text-muted)] flex items-center justify-center"
                            title={t("上移", "Move Up")}
                          >
                            <ChevronUp size={14} />
                          </button>
                          <button
                            type="button"
                            disabled={index === templates.length - 1}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMoveTemplate(index, 1);
                            }}
                            className="p-0.5 text-[var(--text-muted)] hover:text-[var(--accent-red)] bg-transparent border-0 outline-none cursor-pointer disabled:opacity-30 disabled:hover:text-[var(--text-muted)] flex items-center justify-center"
                            title={t("下移", "Move Down")}
                          >
                            <ChevronDown size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  {loadingTemplate && <span className="text-[10px] text-[var(--text-muted)] animate-pulse">{t("正在载入模板内容...", "Loading template content...")}</span>}
                </div>

                {/* Right Column - Editor */}
                <div className="md:col-span-3 flex flex-col gap-4">
                  {/* Template Metadata Info / Inputs */}
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                        {t("模板名称", "Template Name")}
                      </label>
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        disabled={!isNewTemplate && templates.find(t => t.id === selectedTemplate)?.is_builtin}
                        className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] disabled:opacity-60"
                        placeholder={t("请输入模板名称", "Enter template name")}
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                        {t("描述", "Description")}
                      </label>
                      <textarea
                        value={editDesc}
                        onChange={(e) => setEditDesc(e.target.value)}
                        disabled={!isNewTemplate && templates.find(t => t.id === selectedTemplate)?.is_builtin}
                        rows={2}
                        className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] disabled:opacity-60 resize-none leading-normal"
                        placeholder={t("请输入模板描述", "Enter template description")}
                      />
                    </div>
                  </div>

                  {/* Prompt Content Area */}
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center justify-between">
                      <span>{t("Prompt 内容", "Prompt Content")}</span>
                      {templates.find(t => t.id === selectedTemplate)?.is_builtin && !isNewTemplate && (
                        <span className="text-[10px] text-[var(--text-muted)] italic font-semibold normal-case">
                          {t("* 内置模板内容无法直接修改，保存修改需另存为新模板", "* Built-in template prompt is read-only. Save as new template to edit.")}
                        </span>
                      )}
                    </label>
                    <textarea
                      value={editPrompt}
                      onChange={(e) => setEditPrompt(e.target.value)}
                      rows={12}
                      className="w-full bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-3 text-xs font-mono text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)] resize-none select-text leading-relaxed font-medium"
                      placeholder={t("Prompt 内容...", "Prompt content...")}
                    />
                    <span className="text-[10px] text-[var(--text-muted)] leading-relaxed font-semibold">
                      {t("提示：使用 {{PODCAST_DATA}} 占位符作为播客转录内容的插入点。编辑后可保存自定义模板，或将其应用为系统全局总结所使用的默认 Prompt。", "Tip: Use {{PODCAST_DATA}} as the insertion point for podcast transcript. You can save it as a custom template, or apply it as the system's global default summary prompt.")}
                    </span>
                  </div>

                  {/* Actions Row */}
                  <div className="flex items-center justify-between gap-3 pt-2 border-t border-[var(--border-primary)]/10">
                    <div className="flex items-center gap-2">
                      {(isNewTemplate || !(templates.find(t => t.id === selectedTemplate)?.is_builtin)) ? (
                        <>
                          <button
                            type="button"
                            onClick={handleSaveCustomTemplate}
                            disabled={saveStatus === "saving"}
                            className="bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer border-0 outline-none"
                          >
                            <Save size={13} />
                            <span>
                              {saveStatus === "saving" ? t("保存中...", "Saving...") : t("保存模板", "Save Template")}
                            </span>
                          </button>
                          {!isNewTemplate && (
                            <button
                              type="button"
                              onClick={handleDeleteCustomTemplate}
                              className="border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-900/40 dark:text-red-400 dark:hover:bg-red-950/20 px-4 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer bg-transparent outline-none"
                            >
                              <Trash2 size={13} />
                              <span>{t("删除模板", "Delete")}</span>
                            </button>
                          )}
                          {isNewTemplate && (
                            <button
                              type="button"
                              onClick={() => handleTemplateSelect("standard")}
                              className="px-4 py-2 border border-[var(--border-primary)]/30 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] rounded-lg text-xs font-bold transition-all cursor-pointer outline-none bg-transparent"
                            >
                              {t("取消", "Cancel")}
                            </button>
                          )}
                        </>
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            setSaveAsName(`${editName} (${t("副本", "Copy")})`);
                            setSaveAsDesc(editDesc);
                            setShowSaveAsModal(true);
                          }}
                          className="bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] border border-[var(--border-primary)]/30 text-[var(--text-secondary)] px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer outline-none"
                        >
                          <Save size={13} className="text-[var(--accent-red)]" />
                          <span>{t("另存为新模板", "Save as New Template")}</span>
                        </button>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleApplyAsSystemDefault}
                        disabled={promptSaveStatus === "saving"}
                        className="bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] border border-[var(--border-primary)]/30 text-[var(--text-secondary)] px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer outline-none"
                      >
                        <Check size={13} className="text-[var(--accent-red)]" />
                        <span>
                          {promptSaveStatus === "saving" ? t("保存中...", "Saving...") :
                           promptSaveStatus === "saved" ? t("应用成功", "Applied Successfully") :
                           t("应用为系统默认 Prompt", "Apply as System Default")}
                        </span>
                      </button>
                      {templates.find(t => t.id === selectedTemplate)?.is_builtin && (
                        <button
                          type="button"
                          onClick={onResetPromptClick}
                          className="px-4 py-2 border border-[var(--border-primary)]/30 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] rounded-lg text-xs font-bold transition-all cursor-pointer outline-none bg-transparent"
                        >
                          {t("恢复系统默认值", "Reset System Default")}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
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
                <input type="checkbox" checked={configData.enable_win_notification !== false} onChange={(e) => handleConfigChange("enable_win_notification", e.target.checked)} style={{ color: '#f62440', backgroundColor: configData.enable_win_notification !== false ? '#f62440' : 'transparent' }} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[#f62440] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
              </div>
              <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)]/30 rounded-lg border border-[var(--border-primary)]/30">
                <div>
                  <h4 className="font-bold text-sm text-[var(--text-primary)]">{t("邮件提醒", "Email Alerts")}</h4>
                  <p className="text-[var(--text-muted)] text-xs mt-0.5">{t("任务结束时发送邮件通知（需要配置 SMTP）。", "Send mail alerts (SMTP) when task completes.")}</p>
                </div>
                <input type="checkbox" checked={configData.enable_email_notification === true} onChange={(e) => handleConfigChange("enable_email_notification", e.target.checked)} style={{ color: '#f62440', backgroundColor: configData.enable_email_notification === true ? '#f62440' : 'transparent' }} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[#f62440] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
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
                <input type="checkbox" checked={configData.enable_auto_cleanup || false} onChange={(e) => handleConfigChange("enable_auto_cleanup", e.target.checked)} style={{ color: '#f62440', backgroundColor: configData.enable_auto_cleanup ? '#f62440' : 'transparent' }} className="w-4 h-4 rounded border-[var(--border-primary)]/60 text-[#f62440] focus:ring-[var(--accent-red)] focus:ring-offset-0 transition-colors cursor-pointer" />
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

      {/* Save As Modal */}
      {showSaveAsModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[200] p-6 animate-fade-in">
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/50 rounded-xl max-w-sm w-full relative flex flex-col shadow-2xl transition-colors duration-300 p-6 gap-4 text-left font-sans">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-primary)]/20">
              <h3 className="text-base font-bold text-[var(--text-primary)]">
                {t("另存为新自定义模板", "Save as New Custom Template")}
              </h3>
              <button
                type="button"
                onClick={() => setShowSaveAsModal(false)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors border-0 bg-transparent cursor-pointer p-0.5 outline-none flex items-center justify-center"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  {t("新模板名称", "New Template Name")}
                </label>
                <input
                  type="text"
                  value={saveAsName}
                  onChange={(e) => setSaveAsName(e.target.value)}
                  className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]"
                  placeholder={t("请输入模板名称", "Enter template name")}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  {t("描述", "Description")}
                </label>
                <input
                  type="text"
                  value={saveAsDesc}
                  onChange={(e) => setSaveAsDesc(e.target.value)}
                  className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg p-2.5 text-sm font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-red)]"
                  placeholder={t("请输入模板描述", "Enter template description")}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={handleSaveAsNewTemplate}
                className="px-4 py-2 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer border-0 outline-none"
              >
                {t("保存", "Save")}
              </button>
              <button
                type="button"
                onClick={() => setShowSaveAsModal(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-[var(--border-primary)]/40 text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors cursor-pointer bg-transparent outline-none"
              >
                {t("取消", "Cancel")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Help Tooltip Prompt Modal */}
      {infoModal.isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[200] p-6 animate-fade-in">
          <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/50 rounded-xl max-w-lg w-full relative flex flex-col shadow-2xl transition-colors duration-300 p-6 gap-4 text-left font-sans">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-primary)]/20">
              <h3 className="text-base font-bold text-[var(--text-primary)]">
                {infoModal.type === "asr"
                  ? t("配置本地 ASR 的 AI Agent 提示词", "AI Agent Setup Prompt for Local ASR")
                  : t("配置本地 LLM 的 AI Agent 提示词", "AI Agent Setup Prompt for Local LLM")
                }
              </h3>
              <button
                type="button"
                onClick={() => setInfoModal({ isOpen: false, type: "" })}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors border-0 bg-transparent cursor-pointer p-0.5 outline-none flex items-center justify-center"
              >
                <X size={18} />
              </button>
            </div>
            
            <p className="text-xs text-[var(--text-muted)] leading-relaxed font-semibold">
              {t(
                "您可以复制以下提示词并直接发给您的 AI 编程助手（如 Cursor, Claude, GPT），让其帮您准备/拉取所需的本地模型文件：",
                "Copy the prompt below and send it to your AI assistant (e.g. Cursor, Claude, GPT) to automatically prepare/pull the local model files:"
              )}
            </p>

            <div className="bg-[var(--bg-secondary)]/60 border border-[var(--border-primary)]/30 rounded-lg p-3 relative">
              <pre className="text-xs font-mono text-[var(--text-primary)] whitespace-pre-wrap select-all font-semibold leading-relaxed max-h-60 overflow-y-auto">
                {infoModal.type === "asr"
                  ? `I am setting up whisperMe and need to configure a local ASR engine (FunASR) in the following absolute folder path:
E:/Projects/whisperMe/models/funasr

Please help me download and install the FunASR models into this directory, and ensure that all required files (such as model.pb, config.yaml) are present, so the backend can load them correctly without external internet queries.`
                  : `I am setting up whisperMe and want to configure a local LLM summary model using Ollama.
The Ollama URL is: http://localhost:11434
The Ollama model ID is: qwen2.5:7b-instruct

Please help me pull this model locally and verify that the Ollama service is running on my machine. Also, give me the terminal pull commands.`
                }
              </pre>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  const text = infoModal.type === "asr"
                    ? `I am setting up whisperMe and need to configure a local ASR engine (FunASR) in the following absolute folder path:\nE:/Projects/whisperMe/models/funasr\n\nPlease help me download and install the FunASR models into this directory, and ensure that all required files (such as model.pb, config.yaml) are present, so the backend can load them correctly without external internet queries.`
                    : `I am setting up whisperMe and want to configure a local LLM summary model using Ollama.\nThe Ollama URL is: http://localhost:11434\nThe Ollama model ID is: qwen2.5:7b-instruct\n\nPlease help me pull this model locally and verify that the Ollama service is running on my machine. Also, give me the terminal pull commands.`;
                  navigator.clipboard.writeText(text);
                  alert(t("提示词已复制到剪贴板！", "Prompt copied to clipboard!"), { variant: "success" });
                }}
                className="px-4 py-2 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer border-0 flex items-center gap-1.5 outline-none"
              >
                <Copy size={13} />
                <span>{t("复制提示词", "Copy Prompt")}</span>
              </button>
              <button
                type="button"
                onClick={() => setInfoModal({ isOpen: false, type: "" })}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-[var(--border-primary)]/40 text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors cursor-pointer bg-transparent outline-none"
              >
                {t("关闭", "Close")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
