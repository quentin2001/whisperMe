import React, { useState, useEffect } from 'react';
import { MessageSquare, Trash2 } from "lucide-react";
import { API_BASE } from "../../constants.js";
import { alert, confirm } from "../../components/Dialog.jsx";

import { useTranslation } from "../../contexts/I18nContext";

export default function QAChatPanel({
  activeTask,
  MarkdownRenderer
}) {
  const { t } = useTranslation();
  const [qaMessages, setQaMessages] = useState([]);
  const [qaInput, setQaInput] = useState("");
  const [qaLoading, setQaLoading] = useState(false);

  useEffect(() => {
    setQaInput("");
    setQaLoading(false);
    if (activeTask?.id && activeTask?.status === "completed") {
        fetch(`${API_BASE}/api/tasks/${activeTask.id}/qa`)
            .then(res => res.ok ? res.json() : { history: [] })
            .then(data => {
                const history = (data.history || []).map(m => ({
                    role: m.role,
                    content: m.content,
                }));
                setQaMessages(history);
            })
            .catch(() => setQaMessages([]));
    } else {
        setQaMessages([]);
    }
  }, [activeTask?.id]);

  const handleQAClear = async () => {
    if (qaMessages.length === 0) return;
    if (!await confirm(t("确定要清空所有问答记录吗？", "Clear all Q&A history?"))) return;
    try {
      await fetch(`${API_BASE}/api/tasks/${activeTask.id}/qa`, { method: "DELETE" });
      setQaMessages([]);
    } catch (err) {
      console.error("清空问答历史失败:", err);
    }
  };

  const handleQASubmit = async () => {
    if (!qaInput.trim() || qaLoading) return;
    const question = qaInput.trim();
    setQaInput("");
    setQaMessages(prev => [...prev, { role: "user", content: question }]);
    setQaLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/tasks/${activeTask.id}/qa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      if (res.ok) {
        setQaMessages(data.history || []);
      } else {
        setQaMessages(prev => prev.slice(0, -1));
        setQaMessages(prev => [...prev, { role: "user", content: question }, { role: "assistant", content: `错误: ${data.detail || "请求失败"}` }]);
      }
    } catch (err) {
      setQaMessages(prev => {
        const withoutLast = prev.slice(0, -1);
        return [...withoutLast, { role: "user", content: question }, { role: "assistant", content: `网络错误: ${err.message}` }];
      });
    } finally {
      setQaLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full animate-fade-in">
      <div className="flex items-center justify-between pb-4 border-b border-[var(--border-primary)]/30 mb-5 text-[var(--accent-red)] select-none">
        <div className="flex items-center gap-2">
          <MessageSquare size={18} className="text-[var(--accent-red)]" />
          <h3 className="text-[13px] font-extrabold uppercase tracking-widest text-[var(--text-primary)] font-display">{t("与播客对话", "Ask the Podcast")}</h3>
        </div>
        {qaMessages.length > 0 && (
          <button
            onClick={handleQAClear}
            className="flex items-center gap-1.5 px-2 py-1.5 hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--accent-red)] rounded-lg transition-all cursor-pointer border-0 outline-none bg-transparent"
            title={t("清空对话", "Clear conversation")}
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-4 mb-4">
        {qaMessages.length === 0 && !qaLoading && (
          <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
            <MessageSquare size={32} className="text-[var(--text-muted)] opacity-40" />
            <p className="text-sm text-[var(--text-muted)]">{t("输入问题，基于转录文本为你解答", "Ask a question about this podcast")}</p>
          </div>
        )}
        {qaMessages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === "user"
                ? "bg-[var(--accent-red)] text-white"
                : "bg-[var(--bg-card)] border border-[var(--border-primary)]/40 text-[var(--text-primary)]"
            }`}>
              {msg.role === "assistant" ? (
                <MarkdownRenderer text={msg.content} />
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        {qaLoading && (
          <div className="flex justify-start">
            <div className="bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-xl px-4 py-3 flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-[var(--text-muted)]">{t("正在思考...", "Thinking...")}</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2 shrink-0 pt-2 border-t border-[var(--border-primary)]/30">
        <input
          type="text"
          value={qaInput}
          onChange={(e) => setQaInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleQASubmit()}
          placeholder={t("输入问题...", "Ask a question...")}
          className="flex-1 px-4 py-2.5 bg-[var(--bg-card)] border border-[var(--border-primary)]/40 rounded-lg text-sm text-[var(--text-primary)] outline-none focus:border-[var(--accent-red)]/50 transition-colors"
          disabled={qaLoading}
        />
        <button
          onClick={handleQASubmit}
          disabled={!qaInput.trim() || qaLoading}
          className="px-4 py-2.5 bg-[var(--accent-red)] text-white rounded-lg text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 transition-all cursor-pointer"
        >
          {t("发送", "Send")}
        </button>
      </div>
    </div>
  );
}
