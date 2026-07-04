import React, { useState } from 'react';
import { Users, Trash2, GitMerge } from "lucide-react";
import { API_BASE } from "../../constants.js";
import { alert, confirm } from "../../components/Dialog.jsx";
import { useTranslation } from "../../contexts/I18nContext";

export default function SpeakerManagerModal({
  activeTask,
  showSpeakerModal,
  setShowSpeakerModal,
  onRefreshTask
}) {
  const { t } = useTranslation();
  const [editingSpeakerId, setEditingSpeakerId] = useState(null);
  const [editingSpeakerName, setEditingSpeakerName] = useState("");
  const [isSavingSpeaker, setIsSavingSpeaker] = useState(false);
  const [mergingSpeakerId, setMergingSpeakerId] = useState(null);
  const [mergeTargetId, setMergeTargetId] = useState(null);

  if (!showSpeakerModal) return null;

  const getUniqueSpeakers = () => {
    if (!activeTask || !activeTask.paragraphs) return [];
    const speakers = new Set();
    activeTask.paragraphs.forEach((p) => {
      if (p.speaker) {
        speakers.add(p.speaker);
      }
    });
    return Array.from(speakers).sort();
  };

  const handleRenameSpeaker = async (speakerId, newName) => {
    if (!newName.trim()) return;
    setIsSavingSpeaker(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${activeTask.id}/speaker/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speaker_id: speakerId, new_name: newName.trim() }),
      });
      if (res.ok) {
        setEditingSpeakerId(null);
        if (onRefreshTask) onRefreshTask();
      } else {
        await alert(t("重命名发言人失败，请重试。", "Failed to rename speaker. Please try again."));
      }
    } catch (err) {
      console.error(err);
      await alert(t("通信出错：", "Communication error: ") + err.message);
    } finally {
      setIsSavingSpeaker(false);
    }
  };

  const handleMergeSpeaker = async (sourceId, targetId) => {
    const sourceName = activeTask.speaker_mappings?.[sourceId] || sourceId;
    const targetName = activeTask.speaker_mappings?.[targetId] || targetId;
    if (!await confirm(t(`确认将 "${sourceName}" 合并到 "${targetName}"？合并后源说话人将被删除。`, `Merge "${sourceName}" into "${targetName}"? The source speaker will be removed.`))) return;
    try {
      const res = await fetch(`${API_BASE}/api/tasks/speakers/merge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_name: sourceName, target_name: targetName }),
      });
      if (res.ok) {
        const renameRes = await fetch(`${API_BASE}/api/tasks/${activeTask.id}/speaker/rename`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ speaker_id: sourceId, new_name: targetName }),
        });
        if (renameRes.ok && onRefreshTask) onRefreshTask();
        setMergingSpeakerId(null);
        setMergeTargetId(null);
      } else {
        const err = await res.json();
        await alert(err.detail || t("合并失败", "Merge failed"));
      }
    } catch (err) {
      await alert(t("通信出错：", "Communication error: ") + err.message);
    }
  };

  const handleForgetSpeaker = async (speakerId) => {
    const speakerName = activeTask.speaker_mappings?.[speakerId] || speakerId;
    if (!await confirm(t(`确认从全局声纹库中移除 "${speakerName}"？后续将不再自动识别此人。`, `Remove "${speakerName}" from the global voiceprint library? They won't be auto-recognized in the future.`))) return;
    try {
      const res = await fetch(`${API_BASE}/api/tasks/speakers/forget`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: speakerName }),
      });
      if (res.ok) {
        if (onRefreshTask) onRefreshTask();
      } else {
        const err = await res.json();
        await alert(err.detail || t("操作失败", "Operation failed"));
      }
    } catch (err) {
      await alert(t("通信出错：", "Communication error: ") + err.message);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-[150] p-6 animate-fade-in select-none">
      <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/50 rounded-xl max-w-lg w-full relative flex flex-col shadow-2xl">
        <div className="p-6 border-b border-[var(--border-primary)]/30 flex justify-between items-center bg-[var(--bg-secondary)]/50 rounded-t-xl">
          <h3 className="text-xl font-bold font-display text-[var(--text-primary)] flex items-center gap-2">
            <Users size={20} className="text-[var(--accent-red)]" />
            {t("发言人管理", "Speaker Management")}
          </h3>
          <button 
            onClick={() => {
              setShowSpeakerModal(false);
              setEditingSpeakerId(null);
            }} 
            className="text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors cursor-pointer border-0 bg-transparent text-lg"
          >
            ✕
          </button>
        </div>
        
        <div className="p-6 flex flex-col gap-4 max-h-[60vh] overflow-y-auto custom-scrollbar">
          <p className="text-sm text-[var(--text-muted)]">
            {t("在此处修改发言人名称。修改后将自动更新整个文本的发言人标签。", "Update speaker names here. The speaker tags across the entire transcript will be updated automatically.")}
          </p>

          <div className="flex flex-col gap-3">
            {getUniqueSpeakers().length === 0 ? (
              <div className="border border-[var(--border-primary)]/40 border-dashed p-8 text-center rounded-lg text-sm text-[var(--text-muted)] font-semibold">
                {t("未检测到发言人", "No speakers detected")}
              </div>
            ) : (
              getUniqueSpeakers().map((spId) => {
                const currentName = activeTask.speaker_mappings?.[spId] || spId;
                const isEditing = editingSpeakerId === spId;
                const confidenceData = activeTask.speaker_confidence?.[spId];
                const confidenceScore = confidenceData?.score;
                const confidenceSource = confidenceData?.source;
                const isMerging = mergingSpeakerId === spId;

                const getConfidenceLabel = (score, source) => {
                  if (source === "noise") return { text: t("语气词", "Interjection"), color: "bg-gray-100 text-gray-500" };
                  if (source === "manual") return { text: t("手动", "Manual"), color: "bg-blue-50 text-blue-600" };
                  if (source === "llm") return { text: t("AI推理", "AI Inferred"), color: "bg-purple-50 text-purple-600" };
                  if (!score && score !== 0) return null;
                  if (score >= 0.85) return { text: `${t("高置信", "High")} ${(score*100).toFixed(0)}%`, color: "bg-green-50 text-green-700" };
                  if (score >= 0.78) return { text: `${t("中置信", "Medium")} ${(score*100).toFixed(0)}%`, color: "bg-yellow-50 text-yellow-700" };
                  return { text: `${t("低置信", "Low")} ${(score*100).toFixed(0)}%`, color: "bg-orange-50 text-orange-600" };
                };
                const confLabel = getConfidenceLabel(confidenceScore, confidenceSource);

                return (
                  <div key={spId} className="flex items-center justify-between p-3 border border-[var(--border-primary)]/30 rounded-lg bg-[var(--bg-primary)]/30">
                    {isEditing ? (
                      <div className="flex items-center gap-2 w-full">
                        <input
                          type="text"
                          value={editingSpeakerName}
                          onChange={(e) => setEditingSpeakerName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleRenameSpeaker(spId, editingSpeakerName);
                            if (e.key === "Escape") setEditingSpeakerId(null);
                          }}
                          className="flex-1 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 focus:border-[#f62440] focus:ring-1 focus:ring-[#f62440] rounded px-3 py-1.5 text-sm text-[var(--text-primary)] outline-none"
                          autoFocus
                          disabled={isSavingSpeaker}
                        />
                        <button
                          onClick={() => handleRenameSpeaker(spId, editingSpeakerName)}
                          disabled={isSavingSpeaker || !editingSpeakerName.trim()}
                          className="px-3 py-1.5 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] disabled:opacity-50 text-white text-xs font-bold rounded cursor-pointer border-0 outline-none"
                        >
                          {t("保存", "Save")}
                        </button>
                        <button
                          onClick={() => setEditingSpeakerId(null)}
                          disabled={isSavingSpeaker}
                          className="px-3 py-1.5 bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded cursor-pointer border-0 outline-none"
                        >
                          {t("取消", "Cancel")}
                        </button>
                      </div>
                    ) : isMerging ? (
                      <div className="flex items-center gap-2 w-full">
                        <span className="text-xs text-[var(--text-secondary)] font-semibold whitespace-nowrap">{t("合并到:", "Merge to:")}</span>
                        <select
                          value={mergeTargetId || ""}
                          onChange={(e) => setMergeTargetId(e.target.value)}
                          className="flex-1 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded px-2 py-1.5 text-sm text-[var(--text-primary)] outline-none"
                        >
                          <option value="">{t("选择目标...", "Select target...")}</option>
                          {getUniqueSpeakers().filter(id => id !== spId).map(id => (
                            <option key={id} value={id}>{activeTask.speaker_mappings?.[id] || id}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => handleMergeSpeaker(spId, mergeTargetId)}
                          disabled={!mergeTargetId}
                          className="px-3 py-1.5 bg-[var(--accent-red)] hover:bg-[var(--accent-red-dark)] disabled:opacity-50 text-white text-xs font-bold rounded cursor-pointer border-0 outline-none"
                        >
                          {t("合并", "Merge")}
                        </button>
                        <button
                          onClick={() => { setMergingSpeakerId(null); setMergeTargetId(null); }}
                          className="px-3 py-1.5 bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded cursor-pointer border-0 outline-none"
                        >
                          {t("取消", "Cancel")}
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex flex-col min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-[var(--text-primary)] truncate">{currentName}</span>
                            {confLabel && (
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wide shrink-0 ${confLabel.color}`}>
                                {confLabel.text}
                              </span>
                            )}
                          </div>
                          {activeTask.speaker_mappings?.[spId] && (
                            <span className="text-[10px] text-[var(--text-muted)] font-semibold mt-0.5">{t("原始 ID: ", "Original ID: ")}{spId}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() => {
                              setEditingSpeakerId(spId);
                              setEditingSpeakerName(currentName);
                            }}
                            className="text-xs text-[var(--accent-red)] hover:underline font-bold bg-transparent border-0 outline-none cursor-pointer px-1"
                          >
                            {t("编辑", "Edit")}
                          </button>
                          <button
                            onClick={() => { setMergingSpeakerId(spId); setMergeTargetId(null); }}
                            className="p-1 text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors bg-transparent border-0 outline-none cursor-pointer"
                            title={t("合并到其他说话人", "Merge into another speaker")}
                          >
                            <GitMerge size={14} />
                          </button>
                          <button
                            onClick={() => handleForgetSpeaker(spId)}
                            className="p-1 text-[var(--text-muted)] hover:text-[var(--accent-red)] transition-colors bg-transparent border-0 outline-none cursor-pointer"
                            title={t("从声纹库中移除", "Remove from voiceprint library")}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
        
        <div className="p-6 border-t border-[var(--border-primary)]/30 flex justify-end bg-[var(--bg-secondary)]/20 rounded-b-xl">
          <button
            onClick={() => {
              setShowSpeakerModal(false);
              setEditingSpeakerId(null);
            }}
            className="px-4 py-2 bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:bg-[#e7bcbb]/30 text-xs font-bold rounded-lg cursor-pointer border-0 outline-none"
          >
            {t("关闭", "Close")}
          </button>
        </div>
      </div>
    </div>
  );
}
