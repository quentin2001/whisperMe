import React, { useState, useEffect, useRef } from 'react';

// ==================== 🛠️ 像素级 SVG 图标组件 ====================
const Icons = {
  Plus: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>,
  Settings: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.5 1z"></path></svg>,
  Trash: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>,
  Clock: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>,
  ThumbsUp: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>,
  MessageCircle: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>,
  ArrowLeft: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>,
  Refresh: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>,
  Play: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>,
  Check: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>,
  Home: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>,
  Edit: () => <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>,
  Upload: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
};

// ==================== 📝 自研高性能 Markdown 渲染器 ====================
function parseInlineMarkdown(text) {
  const parts = [];
  const boldRegex = /\*\*([^*]+)\*\*/g;
  let match;
  let lastIndex = 0;

  while ((match = boldRegex.exec(text)) !== null) {
    const textBefore = text.substring(lastIndex, match.index);
    if (textBefore) parts.push(textBefore);
    parts.push(<strong key={match.index} style={{ color: '#fff', fontWeight: '700' }}>{match[1]}</strong>);
    lastIndex = boldRegex.lastIndex;
  }
  
  const remaining = text.substring(lastIndex);
  if (remaining) parts.push(remaining);
  
  return parts.length > 0 ? parts : text;
}

function MarkdownRenderer({ text }) {
  if (!text) return <p style={{ color: 'var(--text-secondary)' }}>暂无分析报告</p>;
  
  const lines = text.split('\n');
  let inList = false;
  let listItems = [];
  const renderedElements = [];

  const flushList = (key) => {
    if (listItems.length > 0) {
      renderedElements.push(
        <ul key={`list-${key}`} style={{ paddingLeft: '20px', marginBottom: '14px', listStyleType: 'disc' }}>
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 解析列表项
    if (line.startsWith('- ') || line.startsWith('* ')) {
      inList = true;
      const content = line.substring(2);
      listItems.push(
        <li key={`li-${i}`} style={{ marginBottom: '6px', color: 'var(--text-secondary)', fontSize: '13.5px' }}>
          {parseInlineMarkdown(content)}
        </li>
      );
      continue;
    }
    
    // 如果之前在列表里，但本行不是列表项，先刷新列表
    if (inList && !line.startsWith('- ') && !line.startsWith('* ')) {
      flushList(i);
    }

    if (line === '') {
      continue;
    }

    // 解析 Header 2
    if (line.startsWith('## ')) {
      renderedElements.push(
        <h2 key={i} style={{ 
          fontSize: '16.5px', 
          fontWeight: '700', 
          color: '#fff', 
          marginTop: '24px', 
          marginBottom: '12px',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '8px',
          letterSpacing: '0.3px'
        }}>
          {parseInlineMarkdown(line.substring(3))}
        </h2>
      );
    } 
    // 解析 Header 3
    else if (line.startsWith('### ')) {
      renderedElements.push(
        <h3 key={i} style={{ 
          fontSize: '14.5px', 
          fontWeight: '600', 
          color: 'var(--primary)', 
          marginTop: '16px', 
          marginBottom: '8px' 
        }}>
          {parseInlineMarkdown(line.substring(4))}
        </h3>
      );
    } 
    // 解析 Header 1
    else if (line.startsWith('# ')) {
      renderedElements.push(
        <h1 key={i} style={{ fontSize: '19px', fontWeight: '700', color: '#fff', marginBottom: '16px' }}>
          {parseInlineMarkdown(line.substring(2))}
        </h1>
      );
    }
    // 解析 Blockquote
    else if (line.startsWith('> ')) {
      renderedElements.push(
        <blockquote key={i} style={{
          borderLeft: '4px solid var(--accent)',
          background: 'rgba(157, 124, 216, 0.05)',
          padding: '12px 16px',
          borderRadius: '0 8px 8px 0',
          margin: '12px 0',
          fontStyle: 'italic',
          color: 'var(--text-secondary)'
        }}>
          {parseInlineMarkdown(line.substring(2))}
        </blockquote>
      );
    } 
    // 普通段落
    else {
      renderedElements.push(
        <p key={i} style={{ marginBottom: '12px', color: 'var(--text-secondary)', lineHeight: '1.65', fontSize: '13.5px' }}>
          {parseInlineMarkdown(line)}
        </p>
      );
    }
  }
  
  if (inList) {
    flushList(lines.length);
  }

  return <div className="markdown-body">{renderedElements}</div>;
}

const BACKEND_URL = "http://127.0.0.1:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'detail', 'config'
  const [tasks, setTasks] = useState([]);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [newUrl, setNewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  
  // 详情页内部子标签卡：'summary' | 'shownotes'
  const [detailSubTab, setDetailSubTab] = useState('summary');
  
  // 角色昵称修改状态
  const [renamingSpeakerId, setRenamingSpeakerId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [panelRenamingSpeakerId, setPanelRenamingSpeakerId] = useState(null);
  const [panelRenameValue, setPanelRenameValue] = useState('');
  const isRenamingRef = useRef(false);
  const cancelRenameRef = useRef(false);
  
  // 配置状态
  const [configData, setConfigData] = useState({
    ffmpeg_path: '',
    ffmpeg_bin_dir: '',
    local_whisper_model_path: '',
    hf_token: '',
    ollama_url: '',
    ollama_model: '',
    smtp_server: '',
    smtp_port: 465,
    smtp_username: '',
    smtp_password: '',
    smtp_sender: '',
    notification_email: '',
    enable_win_notification: true,
    asr_mode: 'local',
    online_api_key: '',
    online_base_url: 'https://token-plan-sgp.xiaomimimo.com/v1',
    online_model: 'mimo-v2.5-asr',
    summary_mode: 'local',
    online_summary_api_key: '',
    online_summary_base_url: 'https://api.openai.com/v1',
    online_summary_model: 'gpt-4o-mini'
  });

  const [asrMode, setAsrMode] = useState('local'); // 'local' | 'online'
  
  // 播放器状态绑定
  const [currentTime, setCurrentTime] = useState(0);
  const audioPlayerRef = useRef(null);
  const activeBubbleRef = useRef(null);

  // 硬件性能监控数据
  const [perfData, setPerfData] = useState(null);

  // 获取硬件性能监控
  const fetchPerformance = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/performance`);
      if (res.status === 200) {
        const data = await res.json();
        setPerfData(data);
      }
    } catch (e) {
      console.error("无法加载性能数据:", e);
    }
  };

  // 1. 定时拉取任务列表与系统性能
  useEffect(() => {
    fetchTasks();
    fetchConfig();
    fetchPerformance();
    const interval = setInterval(fetchTasks, 4000); // 4秒轮询一次任务状态
    const perfInterval = setInterval(fetchPerformance, 5000); // 5秒轮询一次性能状态
    return () => {
      clearInterval(interval);
      clearInterval(perfInterval);
    };
  }, []);

  // 2. 音频播放时间轴高亮与滚动自动对齐
  useEffect(() => {
    if (activeBubbleRef.current) {
      activeBubbleRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }, [currentTime]);

  // 3. 当 activeTaskId 变化时加载详情
  useEffect(() => {
    if (activeTaskId) {
      fetchTaskDetail(activeTaskId);
      // 开启专属的详情轮询，如果任务正在执行中
      const detailInterval = setInterval(() => {
        if (activeTask && (activeTask.status === 'downloading' || activeTask.status === 'transcribing' || activeTask.status === 'summarizing')) {
          fetchTaskDetail(activeTaskId, true);
        }
      }, 3000);
      return () => clearInterval(detailInterval);
    } else {
      setActiveTask(null);
    }
  }, [activeTaskId]);

  // 4. 切换到配置页时动态刷新配置参数，避免组件挂载时后端未就绪导致显示为空
  useEffect(() => {
    if (activeTab === 'config') {
      fetchConfig();
    }
  }, [activeTab]);

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`);
      const data = await res.json();
      setTasks(data);
    } catch (e) {
      console.error("无法获取任务列表:", e);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`);
      const data = await res.json();
      setConfigData(data);
      if (data.asr_mode) {
        setAsrMode(data.asr_mode);
      }
    } catch (e) {
      console.error("无法加载系统配置:", e);
    }
  };

  const fetchTaskDetail = async (id, isSilent = false) => {
    if (!isSilent) setDetailLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${id}`);
      if (res.status === 200) {
        const data = await res.json();
        setActiveTask(data);
      }
    } catch (e) {
      console.error("获取任务详情失败:", e);
    } finally {
      if (!isSilent) setDetailLoading(false);
    }
  };

  // 创建新转录任务
  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!newUrl.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: newUrl.trim(), asr_mode: asrMode })
      });
      if (res.status === 200) {
        setNewUrl('');
        fetchTasks();
      }
    } catch (e) {
      alert("发起任务失败，请检查后端服务是否启动！");
    } finally {
      setLoading(false);
    }
  };

  // 触发本地音频文件选择
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // 处理文件上传与任务创建
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 500 * 1024 * 1024) {
      alert("音频文件过大，请控制在 500MB 以内！");
      return;
    }

    setUploading(true);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('asr_mode', asrMode);

    try {
      const res = await fetch(`${BACKEND_URL}/api/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.status === 200) {
        fetchTasks();
        e.target.value = null; // 重置以允许重复上传相同文件
      } else {
        const err = await res.json();
        alert(`上传音频失败: ${err.detail || "未知错误"}`);
      }
    } catch (err) {
      alert("上传文件请求失败，请检查网络与后端服务！");
    } finally {
      setUploading(false);
      setLoading(false);
    }
  };

  // 删除任务
  const handleDeleteTask = async (id, e) => {
    e.stopPropagation(); // 阻止卡片点击穿透进入详情
    if (!confirm("确定要删除此任务并清除本地音频缓存吗？")) return;
    try {
      await fetch(`${BACKEND_URL}/api/tasks/${id}`, { method: 'DELETE' });
      fetchTasks();
      if (activeTaskId === id) {
        setActiveTaskId(null);
        setActiveTab('dashboard');
      }
    } catch (e) {
      alert("删除失败");
    }
  };

  // 重命名 Speaker
  const handleRenameSpeaker = async (speakerId) => {
    if (cancelRenameRef.current) {
      cancelRenameRef.current = false;
      setRenamingSpeakerId(null);
      setRenameValue('');
      return;
    }
    if (!renameValue.trim()) {
      setRenamingSpeakerId(null);
      return;
    }
    if (isRenamingRef.current) return;
    isRenamingRef.current = true;
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${activeTaskId}/speaker/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speaker_id: speakerId, new_name: renameValue.trim() })
      });
      if (res.status === 200) {
        setRenamingSpeakerId(null);
        setRenameValue('');
        fetchTaskDetail(activeTaskId, true);
      }
    } catch (e) {
      alert("修改昵称失败");
    } finally {
      isRenamingRef.current = false;
    }
  };

  // 面板侧重命名 Speaker
  const handleRenameSpeakerPanel = async (speakerId) => {
    if (!panelRenameValue.trim()) {
      setPanelRenamingSpeakerId(null);
      return;
    }
    if (isRenamingRef.current) return;
    isRenamingRef.current = true;
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${activeTaskId}/speaker/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speaker_id: speakerId, new_name: panelRenameValue.trim() })
      });
      if (res.status === 200) {
        setPanelRenamingSpeakerId(null);
        setPanelRenameValue('');
        fetchTaskDetail(activeTaskId, true);
      }
    } catch (e) {
      alert("修改昵称失败");
    } finally {
      isRenamingRef.current = false;
    }
  };

  // 重新生成总结
  const handleRegenerateSummary = async () => {
    if (!activeTaskId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${activeTaskId}/summary/regenerate`, {
        method: 'POST'
      });
      if (res.status === 200) {
        alert("已重新触发本地大模型（Ollama）总结！请在报告栏关注进度。");
        fetchTaskDetail(activeTaskId, true);
      }
    } catch (e) {
      alert("请求总结失败");
    }
  };

  // 保存系统配置
  const handleSaveConfig = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });
      if (res.status === 200) {
        alert("配置已成功更新，并实时应用！");
        setActiveTab('dashboard');
      }
    } catch (e) {
      alert("保存失败");
    }
  };

  // 点击跳转到指定秒数播放
  const handleTimeJump = (seconds) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.currentTime = seconds;
      audioPlayerRef.current.play().catch(err => console.log("播放被浏览器拦截", err));
    }
  };

  // 获取所有说话人唯一列表
  const getUniqueSpeakers = () => {
    if (!activeTask || !activeTask.transcript) return [];
    const speakers = new Set();
    activeTask.transcript.forEach(seg => {
      if (seg.speaker) {
        speakers.add(seg.speaker);
      }
    });
    return Array.from(speakers);
  };

  // 辅助渲染状态
  const renderStatus = (task) => {
    const { status, progress, queue_position } = task;
    switch (status) {
      case 'pending': 
        if (queue_position && queue_position > 0) {
          return <span style={{ color: 'var(--warning)' }}>排队中 (第 {queue_position} 位)</span>;
        }
        return <span style={{ color: 'var(--text-secondary)' }}>排队中</span>;
      case 'downloading': return <span style={{ color: 'var(--primary)' }}>下载音频 ({Math.round(progress)}%)</span>;
      case 'transcribing': return <span style={{ color: 'var(--accent)' }}>声纹识别转录 ({Math.round(progress)}%)</span>;
      case 'summarizing': return <span style={{ color: 'var(--success)' }}>AI 总结评估中 ({Math.round(progress)}%)</span>;
      case 'completed': return <span style={{ color: 'var(--success)' }}>已完成</span>;
      case 'failed': return <span style={{ color: 'var(--error)' }}>处理失败</span>;
      default: return <span>{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'var(--bg-base)' }}>
      
      {/* ==================== 🗂️ 左侧侧边导航栏 ==================== */}
      <div className="glass-panel" style={{ 
        width: '260px', 
        height: '100%', 
        borderRadius: '0', 
        borderLeft: 'none', 
        borderTop: 'none', 
        borderBottom: 'none',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 16px',
        zIndex: '10'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          {/* Logo 标题 */}
          <div style={{ padding: '0 8px' }}>
            <h1 style={{ fontSize: '20px', fontWeight: '700', letterSpacing: '1px', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ 
                background: 'linear-gradient(135deg, var(--primary), var(--accent))', 
                padding: '6px 10px', 
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '800'
              }}>wM</span>
              whisperMe
            </h1>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>本地播客声纹自动化处理中心</p>
          </div>

          {/* 导航按钮 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button 
              onClick={() => { setActiveTab('dashboard'); setActiveTaskId(null); }}
              className="btn-ghost" 
              style={{ 
                justifyContent: 'flex-start', 
                background: activeTab === 'dashboard' ? 'rgba(255,255,255,0.06)' : 'transparent',
                borderColor: activeTab === 'dashboard' ? 'var(--border-hover)' : 'transparent',
                color: activeTab === 'dashboard' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              <Icons.Home />
              控制面板
            </button>
            
            <button 
              onClick={() => setActiveTab('config')}
              className="btn-ghost" 
              style={{ 
                justifyContent: 'flex-start', 
                background: activeTab === 'config' ? 'rgba(255,255,255,0.06)' : 'transparent',
                borderColor: activeTab === 'config' ? 'var(--border-hover)' : 'transparent',
                color: activeTab === 'config' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              <Icons.Settings />
              系统设置
            </button>
          </div>
        </div>

        {/* 性能监控栏 */}
        <div style={{ 
          fontSize: '11px', 
          color: 'var(--text-muted)', 
          padding: '14px 8px 0 8px', 
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {/* CPU & RAM */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-secondary)' }}>CPU 占用率:</span>
            <span style={{ color: '#fff', fontWeight: '600' }}>{perfData ? `${perfData.cpu}%` : '--'}</span>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-secondary)' }}>系统内存 (RAM):</span>
            <span style={{ color: '#fff', fontWeight: '600' }}>
              {perfData ? `${perfData.ram.used}G / ${perfData.ram.total}G` : '--'}
            </span>
          </div>

          {/* GPU 性能指标 */}
          {perfData?.vram?.has_gpu ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '2px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: '0.8' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '10px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '140px' }} title={perfData.vram.gpu_name}>
                  {perfData.vram.gpu_name}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: '600' }}>
                  {perfData.vram.gpu_temp}°C
                </span>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-secondary)' }}>GPU 核心负载:</span>
                <span style={{ color: '#fff', fontWeight: '600' }}>{perfData.vram.gpu_util}%</span>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>显存占用 (VRAM):</span>
                  <span style={{ 
                    color: perfData.vram.percent > 85 ? 'var(--error)' : (perfData.vram.percent > 60 ? 'var(--warning)' : '#fff'),
                    fontWeight: '600' 
                  }}>
                    {(perfData.vram.used / 1024).toFixed(1)}G / {(perfData.vram.total / 1024).toFixed(1)}G
                  </span>
                </div>
                <div style={{ width: '100%', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${perfData.vram.percent}%`, 
                    height: '100%', 
                    background: perfData.vram.percent > 85 ? 'var(--error)' : 'linear-gradient(90deg, var(--primary), var(--accent))' 
                  }}></div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--error)' }}>
              <span>GPU 运行状态:</span>
              <span>未启用 (CPU)</span>
            </div>
          )}

          {/* 存储空间 (Disk) */}
          {perfData?.disk && (
            <div style={{ marginTop: '2px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>存储空间 (Disk):</span>
                <span style={{ color: '#fff', fontWeight: '600' }}>
                  {perfData.disk.used}G / {perfData.disk.total}G
                </span>
              </div>
              <div style={{ width: '100%', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', overflow: 'hidden' }}>
                <div style={{ 
                  width: `${perfData.disk.percent}%`, 
                  height: '100%', 
                  background: 'linear-gradient(90deg, #10b981, #059669)' 
                }}></div>
              </div>
            </div>
          )}

          {/* 队列状况 */}
          {perfData?.queue && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px dashed rgba(255,255,255,0.08)', paddingTop: '8px', marginTop: '2px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>排队中任务:</span>
              <span style={{ 
                color: perfData.queue.size > 0 ? 'var(--primary)' : 'var(--text-muted)', 
                fontWeight: '700' 
              }}>
                {perfData.queue.size} 个
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ==================== 💻 右侧主内容区域 ==================== */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        
        {/* TOP BAR */}
        <div style={{ height: '70px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', padding: '0 32px', justifyContent: 'space-between' }}>
          <div>
            {activeTab === 'detail' && activeTask ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button className="btn-ghost" style={{ padding: '8px 12px' }} onClick={() => { setActiveTab('dashboard'); setActiveTaskId(null); }}>
                  <Icons.ArrowLeft />
                  返回
                </button>
                <div>
                  <h2 style={{ fontSize: '15px', fontWeight: '700', color: '#fff' }}>{activeTask.title}</h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{activeTask.podcast_name}</p>
                </div>
              </div>
            ) : (
              <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#fff' }}>
                {activeTab === 'dashboard' ? '我的播客库' : '系统参数配置'}
              </h2>
            )}
          </div>
          
          {/* 右侧快速任务新建栏 */}
          {activeTab === 'dashboard' && (
            <form onSubmit={handleCreateTask} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {/* 在线/本地模式切换按钮组 */}
              <div style={{ 
                display: 'inline-flex', 
                background: 'rgba(0, 0, 0, 0.25)', 
                border: '1px solid var(--border-color)', 
                borderRadius: '8px',
                padding: '3px'
              }}>
                <button
                  type="button"
                  onClick={() => setAsrMode('local')}
                  style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: asrMode === 'local' ? '600' : '400',
                    borderRadius: '6px',
                    border: 'none',
                    background: asrMode === 'local' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                    color: asrMode === 'local' ? 'var(--primary)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span style={{ 
                    display: 'inline-block', 
                    width: '6px', 
                    height: '6px', 
                    borderRadius: '50%', 
                    background: asrMode === 'local' ? 'var(--primary)' : 'transparent',
                    border: asrMode === 'local' ? 'none' : '1px solid var(--text-muted)'
                  }}></span>
                  本地模式
                </button>
                <button
                  type="button"
                  onClick={() => setAsrMode('online')}
                  style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: asrMode === 'online' ? '600' : '400',
                    borderRadius: '6px',
                    border: 'none',
                    background: asrMode === 'online' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                    color: asrMode === 'online' ? 'var(--accent)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span style={{ 
                    display: 'inline-block', 
                    width: '6px', 
                    height: '6px', 
                    borderRadius: '50%', 
                    background: asrMode === 'online' ? 'var(--accent)' : 'transparent',
                    border: asrMode === 'online' ? 'none' : '1px solid var(--text-muted)'
                  }}></span>
                  在线模式
                </button>
              </div>

              <input 
                type="text" 
                placeholder="粘贴小宇宙或Bilibili链接..."
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                className="glass-input"
                style={{ width: '300px' }}
                disabled={loading}
              />
              <button type="submit" className="btn-glow" disabled={loading}>
                {loading && !uploading ? "发起中..." : <><Icons.Plus /> 抓取音频</>}
              </button>

              <input 
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".mp3,.wav,.m4a,.aac,.flac,.ogg"
                style={{ display: 'none' }}
              />
              <button 
                type="button" 
                className="btn-glow" 
                style={{ 
                  background: 'linear-gradient(135deg, var(--accent) 0%, #a855f7 100%)',
                  boxShadow: '0 0 15px rgba(168, 85, 247, 0.4)'
                }}
                onClick={handleUploadClick}
                disabled={loading}
              >
                {uploading ? "上传中..." : <><Icons.Upload /> 上传音频</>}
              </button>
            </form>
          )}
        </div>

        {/* 主展示区 */}
        <div style={{ flex: '1', overflowY: 'auto', padding: '32px', position: 'relative' }}>
          
          {/* ==================== PANEL 1: DASHBOARD ==================== */}
          {activeTab === 'dashboard' && (
            <div>
              {/* 卡片列表 */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
                {tasks.length === 0 ? (
                  <div className="glass-panel" style={{ gridColumn: '1/-1', padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    <p style={{ fontSize: '16px', fontWeight: '500' }}>您的播客库空空如也</p>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>在右上方输入播客单集链接或点击“上传音频”，即可开始体验自动排队、声纹切分与 AI 总结服务</p>
                  </div>
                ) : (
                  tasks.map((task) => (
                    <div 
                      key={task.id} 
                      className="glass-panel" 
                      onClick={() => {
                        setActiveTaskId(task.id);
                        setActiveTab('detail');
                      }}
                      style={{ 
                        padding: '20px', 
                        cursor: 'pointer', 
                        display: 'flex', 
                        flexDirection: 'column', 
                        justifyContent: 'space-between',
                        minHeight: '180px'
                      }}
                    >
                      <div>
                        {/* 状态指示 */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{ 
                              fontSize: '11px', 
                              padding: '3px 8px', 
                              borderRadius: '12px', 
                              background: task.status === 'completed' ? 'rgba(115, 218, 202, 0.12)' : 'rgba(255,255,255,0.05)',
                              border: task.status === 'completed' ? '1px solid rgba(115, 218, 202, 0.2)' : '1px solid var(--border-color)',
                              color: task.status === 'completed' ? 'var(--success)' : 'var(--text-secondary)'
                            }}>
                              {renderStatus(task)}
                            </span>
                            <span style={{ 
                              fontSize: '10px', 
                              padding: '2px 6px', 
                              borderRadius: '10px', 
                              background: task.asr_mode === 'online' ? 'rgba(157, 124, 216, 0.12)' : 'rgba(122, 162, 247, 0.12)',
                              border: task.asr_mode === 'online' ? '1px solid rgba(157, 124, 216, 0.2)' : '1px solid rgba(122, 162, 247, 0.2)',
                              color: task.asr_mode === 'online' ? 'var(--accent)' : 'var(--primary)',
                              fontWeight: '600'
                            }}>
                              {task.asr_mode === 'online' ? '在线' : '本地'}
                            </span>
                          </div>
                          
                          <button 
                            className="btn-ghost" 
                            style={{ border: 'none', background: 'transparent', padding: '4px', borderRadius: '50%', color: 'var(--text-muted)' }}
                            onClick={(e) => handleDeleteTask(task.id, e)}
                          >
                            <Icons.Trash />
                          </button>
                        </div>

                        {/* 标题 */}
                        <h3 style={{ fontSize: '14.5px', fontWeight: '700', color: '#fff', lineBreak: 'anywhere', lineHeight: '1.4', marginBottom: '6px' }}>
                          {task.title}
                        </h3>
                        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>{task.podcast_name}</p>
                      </div>

                      {/* 统计指标 / 进度条 */}
                      <div>
                        {task.status !== 'completed' && task.status !== 'failed' ? (
                          <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                            <div className="progress-bar-animated" style={{ width: `${task.progress}%`, height: '100%' }}></div>
                          </div>
                        ) : (
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Icons.Clock /> {task.created_at ? task.created_at.substring(0, 10) : ''}</span>
                            {task.status === 'completed' && (
                              <div style={{ display: 'flex', gap: '10px' }}>
                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}><Icons.ThumbsUp /> {task.like_count}</span>
                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}><Icons.MessageCircle /> {task.comment_count}</span>
                              </div>
                            )}
                          </div>
                        )}
                        {task.status === 'failed' && (
                          <div style={{ fontSize: '11px', color: 'var(--error)', marginTop: '4px', lineBreak: 'anywhere' }}>
                            ❌ {task.error_message || "未知报错，请检查终端日志"}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* ==================== PANEL 2: DETAIL WORKSPACE ==================== */}
          {activeTab === 'detail' && activeTask && (
            <div style={{ display: 'flex', gap: '24px', height: 'calc(100vh - 180px)', overflow: 'hidden' }}>
              
              {/* 左侧：语音转文字剧本流动 (2指针联动) */}
              <div className="glass-panel" style={{ flex: '1.2', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>剧本对话流</h3>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>点击说话人旁的编辑图标可修改昵称，点击对话行跳转音频</span>
                </div>
                
                {/* 剧本对话渲染区 */}
                <div style={{ flex: '1', overflowY: 'auto', padding: '20px' }}>
                  {activeTask.transcript && activeTask.transcript.length > 0 ? (
                    <div className="dialogue-container">
                      {activeTask.transcript.map((seg, idx) => {
                        const isPlayingLine = currentTime >= seg.start && currentTime <= seg.end;
                        const speakerName = activeTask.speaker_mappings[seg.speaker] || seg.speaker;
                        
                        return (
                          <div 
                            key={idx} 
                            ref={isPlayingLine ? activeBubbleRef : null}
                            onClick={() => handleTimeJump(seg.start)}
                            className={`dialogue-bubble ${isPlayingLine ? 'active-playing' : ''}`}
                          >
                            <div className="dialogue-meta">
                              {renamingSpeakerId === seg.speaker ? (
                                <input 
                                  type="text" 
                                  value={renameValue}
                                  onChange={(e) => setRenameValue(e.target.value)}
                                  onBlur={() => handleRenameSpeaker(seg.speaker)}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleRenameSpeaker(seg.speaker);
                                    if (e.key === 'Escape') {
                                      cancelRenameRef.current = true;
                                      setRenamingSpeakerId(null);
                                    }
                                  }}
                                  className="glass-input"
                                  style={{ padding: '2px 8px', fontSize: '11px', width: '120px' }}
                                  autoFocus
                                  onClick={(e) => e.stopPropagation()} // 阻止触发时间跳转
                                />
                              ) : (
                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                  <span className="speaker-badge">
                                    {speakerName}
                                  </span>
                                  <button 
                                    className="edit-speaker-btn"
                                    onClick={(e) => {
                                      e.stopPropagation(); // 阻止播放跳转
                                      setRenamingSpeakerId(seg.speaker);
                                      setRenameValue(speakerName);
                                    }}
                                    title="修改说话人名称"
                                  >
                                    <Icons.Edit />
                                  </button>
                                </div>
                              )}
                              <span className="time-stamp">{seg.timestamp_str}</span>
                            </div>
                            <div className="dialogue-text">{seg.text}</div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      {activeTask.status !== 'completed' && activeTask.status !== 'failed' ? (
                        <div>
                          <p style={{ fontSize: '14px' }}>正在为您进行 GPU 识别...</p>
                          <p style={{ fontSize: '12px', marginTop: '6px' }}>转录完成后此处将按顺序显示剧本。</p>
                        </div>
                      ) : (
                        <p>暂无剧本数据，可能是降级未包含声纹/识别出错</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* 右侧：总结报告与元数据评论 (两栏切换) */}
              <div className="glass-panel" style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                {/* 选项卡栏 */}
                <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)' }}>
                  <button 
                    onClick={() => setDetailSubTab('summary')}
                    style={{ 
                      flex: '1', 
                      background: 'transparent', 
                      border: 'none', 
                      padding: '16px', 
                      color: detailSubTab === 'summary' ? '#fff' : 'var(--text-secondary)',
                      fontWeight: detailSubTab === 'summary' ? '700' : '500',
                      borderBottom: detailSubTab === 'summary' ? '2px solid var(--primary)' : 'none',
                      cursor: 'pointer'
                    }}
                  >
                    AI 总结报告
                  </button>
                  <button 
                    onClick={() => setDetailSubTab('shownotes')}
                    style={{ 
                      flex: '1', 
                      background: 'transparent', 
                      border: 'none', 
                      padding: '16px', 
                      color: detailSubTab === 'shownotes' ? '#fff' : 'var(--text-secondary)',
                      fontWeight: detailSubTab === 'shownotes' ? '700' : '500',
                      borderBottom: detailSubTab === 'shownotes' ? '2px solid var(--primary)' : 'none',
                      cursor: 'pointer'
                    }}
                  >
                    Shownotes & 热门评论
                  </button>
                  <button 
                    onClick={() => setDetailSubTab('speakers')}
                    style={{ 
                      flex: '1', 
                      background: 'transparent', 
                      border: 'none', 
                      padding: '16px', 
                      color: detailSubTab === 'speakers' ? '#fff' : 'var(--text-secondary)',
                      fontWeight: detailSubTab === 'speakers' ? '700' : '500',
                      borderBottom: detailSubTab === 'speakers' ? '2px solid var(--primary)' : 'none',
                      cursor: 'pointer'
                    }}
                  >
                    发言人管理
                  </button>
                </div>

                <div style={{ flex: '1', overflowY: 'auto', padding: '24px' }}>
                  
                  {/* SUBTAB 1: AI Summary Markdown */}
                  {detailSubTab === 'summary' && (
                    <div>
                      {activeTask.status === 'summarizing' && (
                        <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
                          <p style={{ fontWeight: '500' }}>🤖 本地大模型正在拼命为您总结中...</p>
                          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>这会占用少量显卡显存并执行推理，大约需要 30-90 秒。</p>
                        </div>
                      )}
                      
                      {activeTask.status !== 'summarizing' && (
                        <div>
                          {/* 刷新总结按钮 */}
                          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
                            <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px' }} onClick={handleRegenerateSummary}>
                              <Icons.Refresh /> 重新生成报告
                            </button>
                          </div>
                          
                          <MarkdownRenderer text={activeTask.summary} />
                        </div>
                      )}
                    </div>
                  )}

                  {/* SUBTAB 2: Shownotes and Top Comments */}
                  {detailSubTab === 'shownotes' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      {/* Shownotes */}
                      <div>
                        <h3 style={{ fontSize: '14px', color: '#fff', fontWeight: '700', marginBottom: '8px' }}>节目简介 (Shownotes)</h3>
                        <div style={{ 
                          background: 'rgba(255,255,255,0.02)', 
                          border: '1px solid var(--border-color)', 
                          borderRadius: '8px', 
                          padding: '16px', 
                          fontSize: '13px', 
                          color: 'var(--text-secondary)',
                          lineHeight: '1.6',
                          whiteSpace: 'pre-wrap',
                          maxHeight: '220px',
                          overflowY: 'auto'
                        }}>
                          {activeTask.metadata?.shownotes || "无节目简介"}
                        </div>
                      </div>

                      {/* 热门评论 */}
                      <div>
                        <h3 style={{ fontSize: '14px', color: '#fff', fontWeight: '700', marginBottom: '10px' }}>听友热评 (第一页共 {activeTask.metadata?.comments?.length || 0} 条)</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          {activeTask.metadata?.comments && activeTask.metadata.comments.length > 0 ? (
                            activeTask.metadata.comments.map((comment, cIdx) => (
                              <div key={cIdx} style={{ 
                                background: 'rgba(255,255,255,0.01)', 
                                border: '1px solid rgba(255,255,255,0.02)', 
                                borderRadius: '8px', 
                                padding: '12px 14px' 
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '6px' }}>
                                  <span style={{ color: 'var(--primary)', fontWeight: '600' }}>{comment.author}</span>
                                  <span style={{ color: 'var(--warning)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}><Icons.ThumbsUp /> {comment.likes}</span>
                                </div>
                                <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{comment.content}</p>
                              </div>
                            ))
                          ) : (
                            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>暂无评论数据（可能非小宇宙链接）</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SUBTAB 3: Speaker Management */}
                  {detailSubTab === 'speakers' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      <h3 style={{ fontSize: '14px', color: '#fff', fontWeight: '700', marginBottom: '8px' }}>发言人昵称管理</h3>
                      <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                        在此统一修改节目中识别出的声纹角色昵称。修改后，左侧剧本对话流中的角色名字会实时更新，系统也将自动采用新昵称。
                      </p>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
                        {getUniqueSpeakers().length === 0 ? (
                          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>暂无发言人数据（请确保已启用声纹识别并且任务已分析出角色）</p>
                        ) : (
                          getUniqueSpeakers().map((spId) => {
                            const currentName = activeTask.speaker_mappings[spId] || spId;
                            const isEditing = panelRenamingSpeakerId === spId;
                            
                            return (
                              <div key={spId} style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'space-between',
                                background: 'rgba(255,255,255,0.01)', 
                                border: '1px solid var(--border-color)', 
                                borderRadius: '8px', 
                                padding: '12px 16px' 
                              }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>系统内部 ID: {spId}</span>
                                  {!isEditing ? (
                                    <span style={{ fontSize: '14.5px', color: '#fff', fontWeight: '600' }}>{currentName}</span>
                                  ) : (
                                    <input 
                                      type="text" 
                                      value={panelRenameValue}
                                      onChange={(e) => setPanelRenameValue(e.target.value)}
                                      onKeyDown={(e) => {
                                        if (e.key === 'Enter') handleRenameSpeakerPanel(spId);
                                        if (e.key === 'Escape') {
                                          setPanelRenamingSpeakerId(null);
                                        }
                                      }}
                                      className="glass-input"
                                      style={{ padding: '4px 10px', fontSize: '13px', width: '180px' }}
                                      autoFocus
                                    />
                                  )}
                                </div>
                                
                                <div>
                                  {!isEditing ? (
                                    <button 
                                      className="btn-glow" 
                                      style={{ padding: '6px 14px', fontSize: '12px' }}
                                      onClick={() => {
                                        setPanelRenamingSpeakerId(spId);
                                        setPanelRenameValue(currentName);
                                      }}
                                    >
                                      编辑昵称
                                    </button>
                                  ) : (
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                      <button 
                                        className="btn-glow" 
                                        style={{ padding: '6px 14px', fontSize: '12px', background: 'var(--success)' }}
                                        onClick={() => handleRenameSpeakerPanel(spId)}
                                      >
                                        保存
                                      </button>
                                      <button 
                                        className="btn-ghost" 
                                        style={{ padding: '6px 14px', fontSize: '12px' }}
                                        onClick={() => {
                                          setPanelRenamingSpeakerId(null);
                                          setPanelRenameValue('');
                                        }}
                                      >
                                        取消
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>
                  )}

                </div>
              </div>

            </div>
          )}

          {/* ==================== PANEL 3: CONFIG FORM ==================== */}
          {activeTab === 'config' && (
            <div className="glass-panel" style={{ maxWidth: '780px', margin: '0 auto', padding: '30px' }}>
              <form onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                
                {/* 1. 本地程序物理路径 */}
                <div>
                  <h3 style={{ fontSize: '14.5px', color: '#fff', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>🛠️ 本地核心组件路径</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>FFmpeg 物理主程序路径 (.exe)</label>
                      <input 
                        type="text" 
                        value={configData.ffmpeg_path} 
                        onChange={(e) => setConfigData({ ...configData, ffmpeg_path: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>FFmpeg Bin 二进制文件夹目录</label>
                      <input 
                        type="text" 
                        value={configData.ffmpeg_bin_dir} 
                        onChange={(e) => setConfigData({ ...configData, ffmpeg_bin_dir: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>本地 Whisper 大模型路径 (如 model_large_v3)</label>
                      <input 
                        type="text" 
                        value={configData.local_whisper_model_path} 
                        onChange={(e) => setConfigData({ ...configData, local_whisper_model_path: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                  </div>
                </div>

                {/* 2. Hugging Face 凭证 */}
                <div>
                  <h3 style={{ fontSize: '14.5px', color: '#fff', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>🔑 Hugging Face 凭证（用于声纹识别）</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Hugging Face User Access Token (以 hf_ 开头)
                    </label>
                    <input 
                      type="password" 
                      placeholder="如果您需要声纹分角色功能，请在此粘贴 HF Token"
                      value={configData.hf_token} 
                      onChange={(e) => setConfigData({ ...configData, hf_token: e.target.value })}
                      className="glass-input" 
                    />
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      * 说明：请确保您在 Hugging Face 账号中已经接受了 `pyannote/speaker-diarization-3.1` 和 `pyannote/segmentation-3.0` 模型的共享协议。不填将直接熔断降级为单轨道转录，不崩盘。
                    </p>
                  </div>
                </div>

                {/* 2.5 在线转录配置 */}
                <div>
                  <h3 style={{ fontSize: '14.5px', color: '#fff', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>🌐 在线 ASR 转录配置 (例如 Xiaomi MiMo)</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>在线模式默认 ASR 引擎</label>
                      <select
                        value={configData.asr_mode}
                        onChange={(e) => setConfigData({ ...configData, asr_mode: e.target.value })}
                        className="glass-input"
                        style={{ background: 'rgba(0, 0, 0, 0.25)', color: 'var(--text-primary)' }}
                      >
                        <option value="local" style={{ background: '#1c1c24' }}>本地转录模式 (Faster-Whisper)</option>
                        <option value="online" style={{ background: '#1c1c24' }}>在线转录模式 (OpenAI 协议兼容 ASR)</option>
                      </select>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Mimo / OpenAI 兼容 API Key (密钥)</label>
                      <input 
                        type="password" 
                        placeholder="在此粘贴您的 tp-xxxxxx 密钥"
                        value={configData.online_api_key || ''} 
                        onChange={(e) => setConfigData({ ...configData, online_api_key: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>在线 API Base URL (请求网关)</label>
                      <input 
                        type="text" 
                        placeholder="默认: https://token-plan-sgp.xiaomimimo.com/v1"
                        value={configData.online_base_url || ''} 
                        onChange={(e) => setConfigData({ ...configData, online_base_url: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>在线 ASR 模型代号</label>
                      <input 
                        type="text" 
                        placeholder="默认: mimo-v2.5-asr"
                        value={configData.online_model || ''} 
                        onChange={(e) => setConfigData({ ...configData, online_model: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                  </div>
                </div>

                {/* 3. AI 总结引擎配置 */}
                <div>
                  <h3 style={{ fontSize: '14.5px', color: '#fff', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>📝 AI 总结与文本分析引擎</h3>
                  
                  {/* 模式选择 */}
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>总结推理模式</label>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button 
                        type="button"
                        onClick={() => setConfigData({ ...configData, summary_mode: 'local' })}
                        style={{
                          flex: '1',
                          padding: '10px',
                          borderRadius: '8px',
                          border: configData.summary_mode === 'local' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                          background: configData.summary_mode === 'local' ? 'rgba(var(--primary-rgb), 0.15)' : 'rgba(255, 255, 255, 0.02)',
                          color: configData.summary_mode === 'local' ? 'var(--primary)' : 'var(--text-secondary)',
                          cursor: 'pointer',
                          fontWeight: '600',
                          transition: 'all 0.2s'
                        }}
                      >
                        本地大模型 (Ollama / LM Studio)
                      </button>
                      <button 
                        type="button"
                        onClick={() => setConfigData({ ...configData, summary_mode: 'online' })}
                        style={{
                          flex: '1',
                          padding: '10px',
                          borderRadius: '8px',
                          border: configData.summary_mode === 'online' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                          background: configData.summary_mode === 'online' ? 'rgba(var(--primary-rgb), 0.15)' : 'rgba(255, 255, 255, 0.02)',
                          color: configData.summary_mode === 'online' ? 'var(--primary)' : 'var(--text-secondary)',
                          cursor: 'pointer',
                          fontWeight: '600',
                          transition: 'all 0.2s'
                        }}
                      >
                        在线 OpenAI 兼容 API
                      </button>
                    </div>
                  </div>

                  {/* 输入字段切换 */}
                  {configData.summary_mode === 'local' ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>本地 API 地址 (Ollama/LM Studio)</label>
                        <input 
                          type="text" 
                          value={configData.ollama_url} 
                          onChange={(e) => setConfigData({ ...configData, ollama_url: e.target.value })}
                          className="glass-input" 
                          placeholder="http://localhost:11434 或 http://localhost:1234"
                        />
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>所选分析模型代号</label>
                        <input 
                          type="text" 
                          value={configData.ollama_model} 
                          onChange={(e) => setConfigData({ ...configData, ollama_model: e.target.value })}
                          className="glass-input" 
                          placeholder="qwen2.5:7b-instruct 等"
                        />
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>在线 API 代理地址 (Base URL)</label>
                          <input 
                            type="text" 
                            value={configData.online_summary_base_url} 
                            onChange={(e) => setConfigData({ ...configData, online_summary_base_url: e.target.value })}
                            className="glass-input" 
                            placeholder="https://api.openai.com/v1"
                          />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>在线分析模型代号 (Model ID)</label>
                          <input 
                            type="text" 
                            value={configData.online_summary_model} 
                            onChange={(e) => setConfigData({ ...configData, online_summary_model: e.target.value })}
                            className="glass-input" 
                            placeholder="gpt-4o-mini 或 deepseek-chat 等"
                          />
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>在线 API 授权秘钥 (API Key)</label>
                        <input 
                          type="password" 
                          value={configData.online_summary_api_key} 
                          onChange={(e) => setConfigData({ ...configData, online_summary_api_key: e.target.value })}
                          className="glass-input" 
                          placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* 4. 邮件与桌面通知提醒 */}
                <div>
                  <h3 style={{ fontSize: '14.5px', color: '#fff', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '12px' }}>✉️ 邮件提醒配置（SMTP）</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>SMTP 服务器（如 smtp.qq.com）</label>
                      <input 
                        type="text" 
                        value={configData.smtp_server} 
                        onChange={(e) => setConfigData({ ...configData, smtp_server: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>SMTP 端口</label>
                      <input 
                        type="number" 
                        value={configData.smtp_port} 
                        onChange={(e) => setConfigData({ ...configData, smtp_port: parseInt(e.target.value) || 465 })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>邮箱登录用户名</label>
                      <input 
                        type="text" 
                        placeholder="如 QQ 邮箱号"
                        value={configData.smtp_username} 
                        onChange={(e) => setConfigData({ ...configData, smtp_username: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>邮箱 SMTP 授权码/授权密钥</label>
                      <input 
                        type="password" 
                        placeholder="在邮箱设置中开启 SMTP 服务获得密钥"
                        value={configData.smtp_password} 
                        onChange={(e) => setConfigData({ ...configData, smtp_password: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>发送人签名邮箱</label>
                      <input 
                        type="text" 
                        value={configData.smtp_sender} 
                        onChange={(e) => setConfigData({ ...configData, smtp_sender: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>提醒接收人目标邮箱</label>
                      <input 
                        type="text" 
                        placeholder="转录成功后向此邮箱发送总结提醒"
                        value={configData.notification_email} 
                        onChange={(e) => setConfigData({ ...configData, notification_email: e.target.value })}
                        className="glass-input" 
                      />
                    </div>
                  </div>
                  
                  {/* 是否开启桌面通知 */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '16px' }}>
                    <input 
                      type="checkbox" 
                      id="enable-win" 
                      checked={configData.enable_win_notification}
                      onChange={(e) => setConfigData({ ...configData, enable_win_notification: e.target.checked })}
                      style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                    />
                    <label htmlFor="enable-win" style={{ fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                      开启 Windows 右下角桌面气泡推送提醒
                    </label>
                  </div>
                </div>

                {/* 保存按钮 */}
                <div style={{ marginTop: '10px', textAlign: 'right' }}>
                  <button type="submit" className="btn-glow" style={{ padding: '12px 32px' }}>
                    <Icons.Check /> 保存参数配置
                  </button>
                </div>

              </form>
            </div>
          )}

        </div>

        {/* ==================== 🎧 粘性底部音频播放器 ==================== */}
        {activeTab === 'detail' && activeTask && activeTask.audio_url && (
          <div className="glass-panel" style={{ 
            height: '80px', 
            borderRadius: '0', 
            borderLeft: 'none', 
            borderRight: 'none', 
            borderBottom: 'none',
            display: 'flex',
            alignItems: 'center',
            padding: '0 32px',
            zIndex: '15',
            background: 'rgba(15, 15, 20, 0.85)'
          }}>
            <audio 
              ref={audioPlayerRef}
              src={`${BACKEND_URL}${activeTask.audio_url}`}
              controls
              onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
              style={{ width: '100%', outline: 'none' }}
            />
          </div>
        )}

      </div>
    </div>
  );
}
