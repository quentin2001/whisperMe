import React, { useState, useEffect, useRef } from 'react';
import SlotMachineModal from './SlotMachineModal';
import AiColliderModal from './AiColliderModal';

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
  Upload: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>,
  Rewind15: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><polyline points="3 3 3 8 8 8"></polyline><text x="12" y="15.5" fontSize="8" fontFamily="system-ui, -apple-system, sans-serif" fontWeight="bold" fill="currentColor" stroke="none" textAnchor="middle">15</text></svg>,
  Forward30: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><polyline points="21 3 21 8 16 8"></polyline><text x="12" y="15.5" fontSize="8" fontFamily="system-ui, -apple-system, sans-serif" fontWeight="bold" fill="currentColor" stroke="none" textAnchor="middle">30</text></svg>,
  PlayPlayer: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: '2px' }}><polygon points="6 3 21 12 6 21"></polygon></svg>,
  PausePlayer: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="4" width="4" height="16" rx="1"></rect><rect x="15" y="4" width="4" height="16" rx="1"></rect></svg>,
  Volume: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5z"></path><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>,
  Mute: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5z"></path><line x1="22" y1="9" x2="16" y2="15"></line><line x1="16" y1="9" x2="22" y2="15"></line></svg>,
  Sandbox: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>,
  ExternalLink: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
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
    parts.push(<strong key={match.index} style={{ color: 'var(--text-primary)', fontWeight: '700' }}>{match[1]}</strong>);
    lastIndex = boldRegex.lastIndex;
  }
  
  const remaining = text.substring(lastIndex);
  if (remaining) parts.push(remaining);
  
  return parts.length > 0 ? parts : text;
}

function formatSpeakerName(speakerId, mappings) {
  if (mappings && mappings[speakerId]) {
    return mappings[speakerId];
  }
  if (speakerId && speakerId.startsWith('SPEAKER_')) {
    const num = parseInt(speakerId.replace('SPEAKER_', ''), 10);
    if (!isNaN(num)) {
      return `声音 ${num + 1}`;
    }
  }
  return speakerId || '未知声音';
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
          color: 'var(--text-primary)', 
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
        <h1 key={i} style={{ fontSize: '19px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px' }}>
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

// ==================== 🎙️ 节目简介结构化与时点跳转渲染器 ====================
function parseTimestampToSeconds(timestampStr) {
  const cleanStr = timestampStr.replace(/[\[\]\(\)]/g, '').trim();
  const parts = cleanStr.split(':').map(Number);
  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    return parts[0] * 60 + parts[1];
  }
  return 0;
}

function parseShownotesToBlocks(text) {
  if (!text) return [];
  const rawLines = text.split(/\r?\n/);
  const tempItems = [];
  const timeRegex = /(?:\[|\()?\b(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\b(?:\]|\))?/;

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i].trim();
    if (!line) {
      tempItems.push({ type: 'empty' });
      continue;
    }

    const timeMatch = line.match(timeRegex);
    if (timeMatch) {
      const fullMatch = timeMatch[0]; // e.g., "03:28" or "[03:28]"
      const rawTime = fullMatch.replace(/[\[\]\(\)]/g, '').trim();
      const seconds = parseTimestampToSeconds(rawTime);
      let rest = line.replace(fullMatch, '').trim();
      rest = rest.replace(/^[:：\-—\s]+/, '').trim(); // clean leading dashes/colons

      // If the rest of the line is empty, see if we can steal the next line as the text!
      if (rest === '' && i + 1 < rawLines.length) {
        const nextLine = rawLines[i + 1].trim();
        if (nextLine && !nextLine.match(timeRegex)) {
          rest = nextLine;
          i++; // skip next line in loop
        }
      }

      tempItems.push({
        type: 'timestamp',
        timestamp: rawTime,
        seconds: seconds,
        text: rest
      });
    } else {
      tempItems.push({
        type: 'text',
        text: line
      });
    }
  }

  // Group consecutive timestamps into timeline blocks
  const blocks = [];
  let currentTimeline = [];

  const flushTimeline = () => {
    if (currentTimeline.length > 0) {
      blocks.push({
        type: 'timeline',
        items: [...currentTimeline]
      });
      currentTimeline = [];
    }
  };

  for (const item of tempItems) {
    if (item.type === 'timestamp') {
      currentTimeline.push(item);
    } else if (item.type === 'empty') {
      flushTimeline();
      blocks.push({ type: 'space' });
    } else {
      flushTimeline();
      blocks.push(item);
    }
  }
  flushTimeline();

  return blocks;
}

function ShownotesRenderer({ text, onTimeJump }) {
  if (!text) return <p style={{ color: 'var(--text-secondary)' }}>本集暂无节目简介。</p>;

  const blocks = parseShownotesToBlocks(text);
  const headerRegex = /^(?:#+\s+|[一二三四五六七八九十]+[、.]|[0-9]+\.|part\s*\d|【|🎙️|⏳|📅|💡|📌|「|『)/i;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {blocks.map((block, index) => {
        if (block.type === 'space') {
          return <div key={index} style={{ height: '8px' }} />;
        }

        if (block.type === 'timeline') {
          return (
            <div key={index} style={{
              position: 'relative',
              paddingLeft: '20px',
              borderLeft: '2px solid var(--border-color)',
              marginLeft: '8px',
              marginTop: '12px',
              marginBottom: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              {block.items.map((item, idx) => (
                <div key={idx} style={{ position: 'relative' }}>
                  {/* Timeline bullet dot */}
                  <div style={{
                    position: 'absolute',
                    left: '-26px',
                    top: '12px',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: 'var(--bg-surface)',
                    border: '2px solid var(--primary)',
                    boxShadow: '0 0 6px var(--primary-glow)',
                    zIndex: 2
                  }} />
                  
                  {/* Card representing this timeline segment */}
                  <div 
                    className="timeline-card"
                    onClick={(e) => {
                      e.stopPropagation();
                      onTimeJump(item.seconds);
                    }}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="shownotes-timestamp-link" style={{ margin: 0, fontSize: '13px' }}>
                        ⏱️ {item.timestamp}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px', opacity: 0.8 }}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" style={{ verticalAlign: 'middle' }}><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                        点击跳转播放
                      </span>
                    </div>
                    {item.text && (
                      <div style={{ 
                        fontSize: '13.5px', 
                        color: 'var(--text-secondary)',
                        lineHeight: '1.6',
                        fontWeight: '500',
                        marginTop: '2px'
                      }}>
                        {parseInlineMarkdown(item.text)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          );
        }

        // normal text blocks
        const isHeader = headerRegex.test(block.text);
        const isListItem = block.text.startsWith('- ') || block.text.startsWith('* ');

        if (isHeader) {
          return (
            <div key={index} style={{
              fontSize: '15.5px',
              fontWeight: '700',
              color: 'var(--text-primary)',
              marginTop: '14px',
              marginBottom: '6px',
              paddingLeft: block.text.includes('【') ? '8px' : '2px',
              borderLeft: block.text.includes('【') ? '3px solid var(--primary)' : 'none',
            }}>
              {parseInlineMarkdown(block.text)}
            </div>
          );
        }

        if (isListItem) {
          const content = block.text.replace(/^[-*]\s+/, '');
          return (
            <div key={index} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
              paddingLeft: '12px',
              marginBottom: '6px',
              color: 'var(--text-secondary)',
              fontSize: '14px',
              lineHeight: '1.7'
            }}>
              <span style={{ color: 'var(--primary)', marginTop: '6px', fontSize: '6px' }}>●</span>
              <span style={{ flex: 1 }}>{parseInlineMarkdown(content)}</span>
            </div>
          );
        }

        return (
          <p key={index} style={{
            margin: '0 0 8px 0',
            color: 'var(--text-secondary)',
            lineHeight: '1.75',
            fontSize: '14px',
            textIndent: '0em',
            letterSpacing: '0.1px'
          }}>
            {parseInlineMarkdown(block.text)}
          </p>
        );
      })}
    </div>
  );
}

function CommentRenderer({ text, onTimeJump }) {
  if (!text) return null;
  const timeRegex = /(?:([0-9]{1,2}):)?([0-9]{1,2}):([0-9]{2})/g;
  
  const parts = [];
  let lastIndex = 0;
  let match;
  
  while ((match = timeRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    
    const timeStr = match[0];
    const hrs = match[1] ? parseInt(match[1], 10) : 0;
    const mins = parseInt(match[2], 10);
    const secs = parseInt(match[3], 10);
    const totalSeconds = hrs * 3600 + mins * 60 + secs;
    
    parts.push(
      <button 
        key={`time-${match.index}`}
        className="time-badge" 
        onClick={(e) => { e.stopPropagation(); onTimeJump(totalSeconds); }}
        style={{
          background: 'rgba(122, 162, 247, 0.1)',
          color: 'var(--primary)',
          border: '1px solid rgba(122, 162, 247, 0.2)',
          borderRadius: '4px',
          padding: '2px 6px',
          fontSize: '12px',
          margin: '0 4px',
          cursor: 'pointer',
          fontFamily: 'monospace'
        }}
        title={`跳转到 ${timeStr}`}
      >
        <span style={{ fontSize: '10px', marginRight: '3px' }}>⏱️</span>
        {timeStr}
      </button>
    );
    
    lastIndex = timeRegex.lastIndex;
  }
  
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  
  return <>{parts}</>;
}

const PRESETS = {
  light: {
    'Default Light': { background: '#FDF6E3', foreground: '#586E75', primary: '#268BD2', accent: '#CB4B16' },
    'Pure White': { background: '#FFFFFF', foreground: '#111827', primary: '#3B82F6', accent: '#8B5CF6' },
    'Soft Green': { background: '#F0FDF4', foreground: '#1E293B', primary: '#0D9488', accent: '#D97706' }
  },
  dark: {
    'Default Dark': { background: '#272822', foreground: '#F8F8F2', primary: '#66D9EF', accent: '#F92672' },
    'Antigravity Slate': { background: '#0F172A', foreground: '#F8FAFC', primary: '#38BDF8', accent: '#EC4899' },
    'Midnight Obsidian': { background: '#0B0F19', foreground: '#E2E8F0', primary: '#8B5CF6', accent: '#D946EF' }
  }
};

const getSourceLabel = (task) => {
  const url = task.url || '';
  const metadata = task.metadata || {};
  const source = metadata.source || '';
  
  if (source.includes('bilibili')) return { text: 'Bilibili', color: '#ff6699', bg: 'rgba(255, 102, 153, 0.12)' };
  if (source.includes('xiaoyuzhou')) return { text: '小宇宙', color: '#ff8800', bg: 'rgba(255, 136, 0, 0.12)' };
  if (url.includes('uploaded_') || source === 'upload' || source === 'local') return { text: '本地上传', color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' };
  
  // Fallback detection from URL
  if (url.includes('bilibili.com') || url.includes('b23.tv')) return { text: 'Bilibili', color: '#ff6699', bg: 'rgba(255, 102, 153, 0.12)' };
  if (url.includes('xiaoyuzhoufm.com')) return { text: '小宇宙', color: '#ff8800', bg: 'rgba(255, 136, 0, 0.12)' };
  
  return { text: '其他来源', color: 'var(--text-muted)', bg: 'rgba(255,255,255,0.05)' };
};

const getWhisperModelName = (path) => {
  if (!path) return 'Large V3';
  const normalized = path.replace(/\\/g, '/');
  const parts = normalized.split('/');
  const last = parts[parts.length - 1] || parts[parts.length - 2] || 'Large V3';
  return last;
};

const BACKEND_URL = "http://127.0.0.1:8000";

const TRANSLATIONS = {
  'zh-CN': {
    'dashboard': '我的播客库',
    'sandbox': '认知沙盒',
    'settings': '系统设置',
    'center_sub': '本地播客声纹自动化处理中心',
    'cpu': 'CPU 占用率',
    'ram': '系统内存 (RAM)',
    'gpu_name_lbl': '显卡名称',
    'gpu_temp_lbl': '核心温度',
    'gpu_load': 'GPU 核心负载',
    'vram': '显存占用 (VRAM)',
    'gpu_cpu': 'GPU 运行状态',
    'gpu_cpu_off': '未启用 (CPU)',
    'disk': '存储空间 (Disk)',
    'queue_tasks': '排队中任务',
    'asr_engine': '转录 (ASR)',
    'llm_engine': '总结 (LLM)',
    'connected': '🟢 本地已联通',
    'online_mode': '☁️ 云端 API',
    'offline': '🔴 本地未开启',
    'my_podcast_lib': '我的播客库',
    'transcribe_asr': '转录 (ASR)',
    'summary_llm': '总结 (LLM)',
    'local': '本地',
    'online': '在线',
    'local_trans': '本地模式',
    'online_trans': '在线模式',
    'input_placeholder': '粘贴小宇宙或Bilibili链接...',
    'fetch_audio': '抓取音频',
    'upload_audio': '上传音频',
    'initiating': '发起中...',
    'uploading': '上传中...',
    'empty_lib': '您的播客库空空如也',
    'empty_lib_sub': '在右上方输入播客单集链接或点击“上传音频”，即可开始体验自动排队、声纹切分与 AI 总结服务',
    'local_asr_badge': '本地转录',
    'online_asr_badge': '在线转录',
    'failed': '处理失败',
    'completed': '已完成',
    'warning_llm_off': '⚠️ 本地 AI 总结大模型 (LLM) 未开启提示：检测到当前选择“本地总结模式”，但本地推理接口端口（Ollama/LM Studio）处于未启动状态，总结任务将无法进行。请启动对应本地端口，或在“系统设置”中切换为云端模式。',
    'back': '返回',
    'script_dialogue': '剧本对话流',
    'script_dialogue_sub': '点击说话人旁的编辑图标可修改昵称，点击对话行跳转音频',
    'script_loading': '正在为您进行 GPU 识别...',
    'script_loading_sub': '转录完成后此处将按顺序显示剧本。',
    'script_empty': '暂无剧本数据，可能是降级未包含声纹/识别出错',
    'ai_report': 'AI 总结报告',
    'shownotes_comments': 'Shownotes & 热门评论',
    'speaker_list': '说话人声纹特征库',
    'regenerate_summary': '重新生成 AI 报告',
    'sys_config_header': '系统设置',
    'tab_appearance': '🎨 外观与语言',
    'tab_asr': '🎙️ 语音转录 (ASR)',
    'tab_llm': '📝 AI 总结 (LLM)',
    'tab_notifications': '✉️ 消息通知 (SMTP)',
    'theme_appearance': '🎨 主题外观设置 (Appearance)',
    'theme_sub': '配置系统的视觉主题与色彩显示偏好。',
    'display_mode': '显示模式 (Appearance)',
    'display_mode_sub': '选择浅色、深色，或跟随系统。',
    'light_theme_title': '☀️ 浅色主题配置 (Light Theme)',
    'dark_theme_title': '🌙 深色主题配置 (Dark Theme)',
    'preset': '预设方案 (Preset)',
    'bg_color': '背景色 (Background)',
    'fg_color': '前景色 (Foreground)',
    'accent_color': '强调色 (Accent)',
    'language_setting': '🌐 语言设置 (Language)',
    'language_setting_sub': '选择系统界面的显示语言。',
    'select_lang': '系统语言 (Language)',
    'auto_save_chk': '💡 自动保存更改',
    'save_status_saving': '⏳ 正在自动保存...',
    'save_status_saved': '✅ 配置已自动保存并实时应用',
    'save_status_unsaved': '✍️ 正在修改，稍后将自动保存...',
    'save_status_unsaved_manual': '⚠️ 有未保存的更改',
    'save_status_error': '❌ 保存失败，请检查网络与后端',
    'save_status_idle': '✨ 配置已加载',
    'save_btn': '保存参数配置',
    'ffmpeg_exe_path': 'FFmpeg 物理主程序路径 (.exe)',
    'ffmpeg_bin_dir': 'FFmpeg Bin 二进制文件夹目录',
    'whisper_path': '本地 Whisper 大模型路径 (如 model_large_v3)',
    'hf_token_lbl': 'Hugging Face User Access Token (以 hf_ 开头，声纹识别必需)',
    'hf_token_placeholder': '如果您需要声纹分角色功能，请在此粘贴 HF Token',
    'hf_token_sub': '* 说明：请确保您在 Hugging Face 账号中已经接受了 pyannote/speaker-diarization-3.1 模型的共享协议。不填将直接熔断降级为单轨道转录，不崩盘。',
    'mimo_key_lbl': 'Mimo / OpenAI 兼容 API Key (密钥)',
    'mimo_key_placeholder': '在此粘贴您的 tp-xxxxxx 密钥',
    'mimo_url_lbl': '在线 API Base URL (请求网关)',
    'mimo_model_lbl': '在线 ASR 模型代号',
    'local_api_url': '本地 API 地址 (Ollama/LM Studio)',
    'local_model_id': '所选分析模型代号',
    'online_api_url': '在线 API 代理地址 (Base URL)',
    'online_model_id': '在线分析模型代号 (Model ID)',
    'online_api_key': '在线 API 授权秘钥 (API Key)',
    'smtp_server': 'SMTP 服务器（如 smtp.qq.com）',
    'smtp_port': 'SMTP 端口',
    'smtp_user': '邮箱登录用户名',
    'smtp_pass': '邮箱 SMTP 授权码/授权密钥',
    'smtp_sender': '发送人签名邮箱',
    'smtp_receiver': '提醒接收人目标邮箱',
    'enable_win_notify': '开启 Windows 右下角桌面气泡推送提醒',
    'enable_email_notify': '开启邮件通知（当转录/总结完成后发送邮件提醒）',
    'summarizing': '本地大模型正在拼命为您总结中...',
    'summarizing_sub': '这会占用少量显卡显存并执行推理，大约需要 30-90 秒。'
  },
  'zh-TW': {
    'dashboard': '我的播客庫',
    'sandbox': '認知沙盒',
    'settings': '系統設定',
    'center_sub': '在地播客聲紋自動化處理中心',
    'cpu': 'CPU 使用率',
    'ram': '系統記憶體 (RAM)',
    'gpu_name_lbl': '顯示卡名稱',
    'gpu_temp_lbl': '核心溫度',
    'gpu_load': 'GPU 核心負載',
    'vram': '顯示記憶體 (VRAM)',
    'gpu_cpu': 'GPU 運行狀態',
    'gpu_cpu_off': '未啟用 (CPU)',
    'disk': '儲存空間 (Disk)',
    'queue_tasks': '排隊中任務',
    'asr_engine': '轉錄 (ASR)',
    'llm_engine': '總結 (LLM)',
    'connected': '🟢 在地已聯通',
    'online_mode': '☁️ 雲端 API',
    'offline': '🔴 在地未開啟',
    'my_podcast_lib': '我的播客庫',
    'transcribe_asr': '轉錄 (ASR)',
    'summary_llm': '總結 (LLM)',
    'local': '在地',
    'online': '線上',
    'local_trans': '在地模式',
    'online_trans': '線上模式',
    'input_placeholder': '貼上小宇宙或Bilibili連結...',
    'fetch_audio': '擷取音訊',
    'upload_audio': '上傳音訊',
    'initiating': '發起中...',
    'uploading': '上傳中...',
    'empty_lib': '您的播客庫空空如也',
    'empty_lib_sub': '在右上方輸入播客單集連結或點擊「上傳音訊」，即可開始體驗自動排隊、聲紋切分與 AI 總結服務',
    'local_asr_badge': '在地轉錄',
    'online_asr_badge': '線上轉錄',
    'failed': '處理失敗',
    'completed': '已完成',
    'warning_llm_off': '⚠️ 在地 AI 總結大模型 (LLM) 未開啟提示：檢測到當前選擇「在地總結模式」，但在地推理介面端口（Ollama/LM Studio）處於未啟動狀態，總結任務將無法進行。請啟動對應在地端口，或在「系統設定」中切換為雲端模式。',
    'back': '返回',
    'script_dialogue': '劇本對話流',
    'script_dialogue_sub': '點擊說話人旁的編輯圖示可修改暱稱，點擊對話行跳轉音訊',
    'script_loading': '正在為您進行 GPU 識別...',
    'script_loading_sub': '轉錄完成後此處將按順序顯示劇本。',
    'script_empty': '暫無劇本資料，可能是降級未包含聲紋/識別出錯',
    'ai_report': 'AI 總結報告',
    'shownotes_comments': 'Shownotes & 熱門評論',
    'speaker_list': '說話人聲紋特徵庫',
    'regenerate_summary': '重新生成 AI 報告',
    'sys_config_header': '系統設定',
    'tab_appearance': '🎨 外觀與語言',
    'tab_asr': '🎙️ 語音轉錄 (ASR)',
    'tab_llm': '📝 AI 總結 (LLM)',
    'tab_notifications': '✉️ 消息通知 (SMTP)',
    'theme_appearance': '🎨 主題外觀設置 (Appearance)',
    'theme_sub': '配置系統的視覺主題與色彩顯示偏好。',
    'display_mode': '顯示模式 (Appearance)',
    'display_mode_sub': '選擇淺色、深色，或跟隨系統。',
    'light_theme_title': '☀️ 淺色主題配置 (Light Theme)',
    'dark_theme_title': '🌙 深色主題配置 (Dark Theme)',
    'preset': '預設方案 (Preset)',
    'bg_color': '背景色 (Background)',
    'fg_color': '前景色 (Foreground)',
    'accent_color': '強調色 (Accent)',
    'language_setting': '🌐 語言設置 (Language)',
    'language_setting_sub': '選擇系統介面的顯示語言。',
    'select_lang': '系統語言 (Language)',
    'auto_save_chk': '💡 自動保存更改',
    'save_status_saving': '⏳ 正在自動保存...',
    'save_status_saved': '✅ 配置已自動保存並即時應用',
    'save_status_unsaved': '✍️ 正在修改，稍後將自動保存...',
    'save_status_unsaved_manual': '⚠️ 有未保存的更改',
    'save_status_error': '❌ 保存失敗，請檢查網路與後端',
    'save_status_idle': '✨ 配置已載入',
    'save_btn': '保存參數配置',
    'ffmpeg_exe_path': 'FFmpeg 物理主程序路徑 (.exe)',
    'ffmpeg_bin_dir': 'FFmpeg Bin 二進位資料夾目錄',
    'whisper_path': '在地 Whisper 大模型路徑 (如 model_large_v3)',
    'hf_token_lbl': 'Hugging Face User Access Token (以 hf_ 開頭，聲紋識別必需)',
    'hf_token_placeholder': '如果您需要聲紋分角色功能，請在此貼上 HF Token',
    'hf_token_sub': '* 說明：請確保您在 Hugging Face 帳號中已經接受了 pyannote/speaker-diarization-3.1 模型的共享協議。不填將直接熔斷降級為單軌道轉錄，不崩盤。',
    'mimo_key_lbl': 'Mimo / OpenAI 相容 API Key (金鑰)',
    'mimo_key_placeholder': '在此貼上您的 tp-xxxxxx 金鑰',
    'mimo_url_lbl': '線上 API Base URL (請求網關)',
    'mimo_model_lbl': '線上 ASR 模型代號',
    'local_api_url': '在地 API 地址 (Ollama/LM Studio)',
    'local_model_id': '所選分析模型代號',
    'online_api_url': '線上 API 代理地址 (Base URL)',
    'online_model_id': '線上分析模型代號 (Model ID)',
    'online_api_key': '線上 API 授權金鑰 (API Key)',
    'smtp_server': 'SMTP 伺服器（如 smtp.qq.com）',
    'smtp_port': 'SMTP 端口',
    'smtp_user': '郵箱登入使用者名稱',
    'smtp_pass': '郵箱 SMTP 授權碼/授權金鑰',
    'smtp_sender': '發送人簽名郵箱',
    'smtp_receiver': '提醒接收人目標郵箱',
    'enable_win_notify': '開啟 Windows 右下角桌面氣泡推送提醒',
    'enable_email_notify': '開啟郵件通知（當轉錄/總結完成後發送郵件提醒）',
    'summarizing': '在地大模型正在拼命為您總結中...',
    'summarizing_sub': '這會佔用少量顯卡顯存並執行推理，大約需要 30-90 秒。'
  },
  'en-US': {
    'dashboard': 'My Podcast Library',
    'sandbox': 'Cognitive Sandbox',
    'settings': 'Settings',
    'center_sub': 'Local Podcast Voiceprint Automation Center',
    'cpu': 'CPU Usage',
    'ram': 'System Memory (RAM)',
    'gpu_name_lbl': 'GPU Name',
    'gpu_temp_lbl': 'GPU Temp',
    'gpu_load': 'GPU Core Load',
    'vram': 'VRAM Usage',
    'gpu_cpu': 'GPU Status',
    'gpu_cpu_off': 'Not Enabled (CPU)',
    'disk': 'Disk Space',
    'queue_tasks': 'Queued Tasks',
    'asr_engine': 'ASR Engine',
    'llm_engine': 'LLM Engine',
    'connected': '🟢 Connected',
    'online_mode': '☁️ Cloud API',
    'offline': '🔴 Offline',
    'my_podcast_lib': 'My Podcast Library',
    'transcribe_asr': 'ASR',
    'summary_llm': 'LLM',
    'local': 'Local',
    'online': 'Online',
    'local_trans': 'Local ASR',
    'online_trans': 'Online ASR',
    'input_placeholder': 'Paste Xiaoyuzhou or Bilibili URL...',
    'fetch_audio': 'Fetch Audio',
    'upload_audio': 'Upload Audio',
    'initiating': 'Initiating...',
    'uploading': 'Uploading...',
    'empty_lib': 'Your podcast library is empty',
    'empty_lib_sub': 'Enter a podcast URL or click "Upload Audio" to start transcript, voiceprint and AI summary services.',
    'local_asr_badge': 'Local ASR',
    'online_asr_badge': 'Online ASR',
    'failed': 'Failed',
    'completed': 'Completed',
    'warning_llm_off': '⚠️ Local LLM Offline: The local summary mode is selected, but local service (Ollama/LM Studio) is not running. Please launch Ollama or switch to Cloud API in Settings.',
    'back': 'Back',
    'script_dialogue': 'Dialogue Transcript',
    'script_dialogue_sub': 'Click edit icon next to speakers to rename, click bubbles to jump in audio',
    'script_loading': 'Processing audio on GPU...',
    'script_loading_sub': 'Transcript will be displayed sequentially once processed.',
    'script_empty': 'No script data found. Voiceprint fallback or transcription error occurred.',
    'ai_report': 'AI Summary Report',
    'shownotes_comments': 'Shownotes & Hot Comments',
    'speaker_list': 'Speaker Voiceprints',
    'regenerate_summary': 'Regenerate Report',
    'sys_config_header': 'System Settings',
    'tab_appearance': '🎨 Appearance & Lang',
    'tab_asr': '🎙️ ASR Settings',
    'tab_llm': '📝 LLM Settings',
    'tab_notifications': '✉️ Notification (SMTP)',
    'theme_appearance': '🎨 Theme Settings (Appearance)',
    'theme_sub': 'Configure visual themes and color settings.',
    'display_mode': 'Display Mode',
    'display_mode_sub': 'Select Light, Dark, or System preference.',
    'light_theme_title': '☀️ Light Theme Configuration',
    'dark_theme_title': '🌙 Dark Theme Configuration',
    'preset': 'Preset',
    'bg_color': 'Background Color',
    'fg_color': 'Foreground Color',
    'accent_color': 'Accent Color',
    'language_setting': '🌐 Language Setting',
    'language_setting_sub': 'Select the interface language for the application.',
    'select_lang': 'System Language',
    'auto_save_chk': '💡 Auto-save settings',
    'save_status_saving': '⏳ Auto-saving...',
    'save_status_saved': '✅ Saved & applied',
    'save_status_unsaved': '✍️ Typing, will auto-save...',
    'save_status_unsaved_manual': '⚠️ Unsaved changes',
    'save_status_error': '❌ Save failed',
    'save_status_idle': '✨ Config loaded',
    'save_btn': 'Save Settings',
    'ffmpeg_exe_path': 'FFmpeg Executable Path (.exe)',
    'ffmpeg_bin_dir': 'FFmpeg Bin Directory',
    'whisper_path': 'Local Whisper Model Path',
    'hf_token_lbl': 'Hugging Face Access Token (diarization requirement)',
    'hf_token_placeholder': 'Paste HF token starting with hf_',
    'hf_token_sub': '* Agreement for pyannote/speaker-diarization-3.1 must be accepted on Hugging Face.',
    'mimo_key_lbl': 'OpenAI Compatible ASR API Key',
    'mimo_key_placeholder': 'Paste your API Key',
    'mimo_url_lbl': 'API Base URL',
    'mimo_model_lbl': 'ASR Model ID',
    'local_api_url': 'Local API URL (Ollama/LM Studio)',
    'local_model_id': 'Local LLM Model ID',
    'online_api_url': 'Online API Base URL',
    'online_model_id': 'Online Model ID',
    'online_api_key': 'Online API Key',
    'smtp_server': 'SMTP Server (e.g. smtp.gmail.com)',
    'smtp_port': 'SMTP Port',
    'smtp_user': 'SMTP Username',
    'smtp_pass': 'SMTP Password / Auth Key',
    'smtp_sender': 'Sender Email Address',
    'smtp_receiver': 'Notification Receiver Email',
    'enable_win_notify': 'Enable Windows notification bubbles',
    'enable_email_notify': 'Enable email notifications upon completion',
    'summarizing': 'AI summary generation in progress...',
    'summarizing_sub': 'This will occupy a small amount of VRAM and perform inference. Takes about 30-90 seconds.'
  },
  'ja-JP': {
    'dashboard': 'ポッドキャストライブラリ',
    'sandbox': '認知サンドボックス',
    'settings': 'システム設定',
    'center_sub': 'ローカル音声ダイアリゼーション処理センター',
    'cpu': 'CPU使用率',
    'ram': 'システムメモリ (RAM)',
    'gpu_name_lbl': 'グラフィックカード名',
    'gpu_temp_lbl': 'コア温度',
    'gpu_load': 'GPUコア負荷',
    'vram': 'VRAM使用率',
    'gpu_cpu': 'GPUステータス',
    'gpu_cpu_off': '未有効化 (CPU)',
    'disk': 'ストレージ空き容量',
    'queue_tasks': 'キューにあるタスク',
    'asr_engine': '文字起こし (ASR)',
    'llm_engine': 'AI 要約 (LLM)',
    'connected': '🟢 接続済み',
    'online_mode': '☁️ クラウド API',
    'offline': '🔴 未起動',
    'my_podcast_lib': 'ポッドキャストライブラリ',
    'transcribe_asr': 'ASR',
    'summary_llm': 'LLM',
    'local': 'ローカル',
    'online': 'オンライン',
    'local_trans': 'ローカル ASR',
    'online_trans': 'オンライン ASR',
    'input_placeholder': 'リンクを貼り付けてください...',
    'fetch_audio': '取得開始',
    'upload_audio': 'アップロード',
    'initiating': '送信中...',
    'uploading': '送信中...',
    'empty_lib': 'ライブラリは空です',
    'empty_lib_sub': 'URLを貼り付けるか、「アップロード」をクリックして自動処理を開始してください。',
    'local_asr_badge': 'ローカル文字起こし',
    'online_asr_badge': 'オンライン文字起こし',
    'failed': '失敗',
    'completed': '完了',
    'warning_llm_off': '⚠️ ローカル大模型 (LLM) オフライン警告: ローカル要約モードが選択されていますが、ローカルポート (Ollama/LM Studio) が起動していません。Ollama を起動するか、クラウドAPIに切り替えてください。',
    'back': '戻る',
    'script_dialogue': '台本テキストストリーム',
    'script_dialogue_sub': '話者のニックネームをクリックして編集、テキストをクリックして再生位置移動',
    'script_loading': 'GPUで処理中...',
    'script_loading_sub': '文字起こしが完了すると台本が表示されます。',
    'script_empty': 'データがありません。音声認識エラーの可能性があります。',
    'ai_report': 'AI 要約レポート',
    'shownotes_comments': 'Shownotes & 人気コメント',
    'speaker_list': '話者一覧',
    'regenerate_summary': 'レポート再生成',
    'sys_config_header': 'システム設定',
    'tab_appearance': '🎨 外観と言語',
    'tab_asr': '🎙️ 文字起こし (ASR)',
    'tab_llm': '📝 AI 要約 (LLM)',
    'tab_notifications': '✉️ メール通知 (SMTP)',
    'theme_appearance': '🎨 テーマ外観設定',
    'theme_sub': 'ビジュアルテーマとカラー設定を設定します。',
    'display_mode': '表示モード',
    'display_mode_sub': 'ライト、ダーク、またはシステム設定を選択してください。',
    'light_theme_title': '☀️ ライトテーマ設定',
    'dark_theme_title': '🌙 ダークテーマ設定',
    'preset': 'プリセット',
    'bg_color': '背景色',
    'fg_color': '前景色',
    'accent_color': 'アクセントカラー',
    'language_setting': '🌐 言語設定 (Language)',
    'language_setting_sub': 'システム画面の表示言語を設定します。',
    'select_lang': 'システム言語',
    'auto_save_chk': '💡 自動保存を有効化',
    'save_status_saving': '⏳ 自動保存中...',
    'save_status_saved': '✅ 設定保存完了',
    'save_status_unsaved': '✍️ 入力中、自動保存されます...',
    'save_status_unsaved_manual': '⚠️ 未保存の変更あり',
    'save_status_error': '❌ 保存失敗、ネットワークを確認してください',
    'save_status_idle': '✨ 設定ロード完了',
    'save_btn': '設定を保存',
    'ffmpeg_exe_path': 'FFmpeg 実行パス (.exe)',
    'ffmpeg_bin_dir': 'FFmpeg Bin フォルダ',
    'whisper_path': 'ローカル Whisper モデルパス',
    'hf_token_lbl': 'Hugging Face Access Token (話者分離に必要)',
    'hf_token_placeholder': 'hf_で始まるトークンを入力',
    'hf_token_sub': '* Hugging Faceでpyannote/speaker-diarization-3.1のライセンス同意が必要です。',
    'mimo_key_lbl': 'ASR APIキー',
    'mimo_key_placeholder': 'APIキーを入力してください',
    'mimo_url_lbl': 'API Base URL',
    'mimo_model_lbl': 'ASR モデル代号',
    'local_api_url': 'ローカル API URL (Ollama/LM Studio)',
    'local_model_id': 'ローカル LLM モデルID',
    'online_api_url': 'オンライン API Base URL',
    'online_model_id': 'オンライン分析モデルID',
    'online_api_key': 'オンライン APIキー',
    'smtp_server': 'SMTP サーバー (smtp.gmail.com など)',
    'smtp_port': 'SMTP ポート',
    'smtp_user': 'SMTP ユーザー名',
    'smtp_pass': 'SMTP パスワード / 認証キー',
    'smtp_sender': '送信元メールアドレス',
    'smtp_receiver': '通知受信用メールアドレス',
    'enable_win_notify': 'Windowsトースト通知を有効にする',
    'enable_email_notify': '完了時にメール通知を送信する',
    'summarizing': 'ローカルAIモデルが要約を作成しています...',
    'summarizing_sub': '推論処理を行うため、少量のVRAMを消費します。完了まで約30〜90秒かかります。'
  }
};

// ==================== 🃏 认知沙盒卡片单项组件 (带 3D 翻转) ====================
function CardItem({ card, shouldDim, isHoveredSelf, setHoveredCardId, setActiveTab, setActiveTaskId, targetParagraphIdRef, handleTimeJump }) {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleAnchorClick = (e) => {
    e.stopPropagation(); // 阻止卡片翻转
    
    // 溯源跳转
    setActiveTaskId(card.podcast_id);
    setActiveTab('detail');
    targetParagraphIdRef.current = card.paragraph_id;
  };

  const isSynthesis = !!card.is_synthesis;

  return (
    <div 
      id={`card-${card.id}`}
      onMouseEnter={() => setHoveredCardId(card.id)}
      onMouseLeave={() => setHoveredCardId(null)}
      onClick={() => setIsFlipped(!isFlipped)}
      className="perspective-container"
      style={{
        height: '240px',
        cursor: 'pointer',
        opacity: shouldDim ? 0.35 : 1,
        transform: isHoveredSelf ? 'scale(1.03) translateY(-4px)' : 'scale(1) translateY(0)',
        boxShadow: isSynthesis
          ? (isHoveredSelf ? '0 12px 30px rgba(212, 175, 55, 0.45)' : '0 4px 15px rgba(212, 175, 55, 0.15)')
          : (isHoveredSelf ? '0 12px 30px rgba(0, 0, 0, 0.4)' : '0 4px 12px rgba(0, 0, 0, 0.15)'),
        transition: 'opacity 0.3s, transform 0.3s, box-shadow 0.3s',
        zIndex: isHoveredSelf ? 2 : 1
      }}
    >
      <div className={`flip-card-inner ${isFlipped ? 'is-flipped' : ''}`}>
        
        {/* 卡牌正面 */}
        <div className="flip-card-front glass-panel" style={{
          padding: '16px',
          background: isSynthesis ? 'linear-gradient(135deg, rgba(38, 30, 10, 0.95) 0%, rgba(13, 10, 3, 0.98) 100%)' : 'var(--bg-surface)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          border: isSynthesis ? '2px solid #ffd700' : '1px solid var(--border-color)',
          height: '100%'
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', width: '80%' }}>
              {isSynthesis ? (
                <span style={{ fontSize: '16px', filter: 'drop-shadow(0 0 4px #ffd700)' }}>💥</span>
              ) : card.podcast_image_url ? (
                <img src={card.podcast_image_url} alt="cover" style={{ width: '22px', height: '22px', borderRadius: '4px', objectFit: 'cover' }} />
              ) : (
                <span style={{ fontSize: '14px' }}>🎙️</span>
              )}
              <span style={{ fontSize: '11px', color: isSynthesis ? '#ffd700' : 'var(--text-secondary)', fontWeight: '600', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {card.podcast_name}
              </span>
            </div>
            
            {/* 🧭 溯源锚点（合成卡片不需要此锚点） */}
            {!isSynthesis && (
              <button
                onClick={handleAnchorClick}
                className="btn-ghost"
                style={{
                  padding: '4px',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  color: 'var(--primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '50%',
                  transition: 'transform 0.2s'
                }}
                title="🧭 跳转到播客原点播放"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
              </button>
            )}
          </div>

          {/* Body */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px', justifyContent: 'center', overflow: 'hidden' }}>
            <h4 style={{ fontSize: '13.5px', fontWeight: '750', color: isSynthesis ? '#fff' : 'var(--text-primary)', margin: 0, lineBreak: 'anywhere', lineHeight: '1.4' }}>
              {card.spark_title}
            </h4>
            <p style={{
              fontSize: '11.5px',
              color: isSynthesis ? 'rgba(255, 255, 255, 0.75)' : 'var(--text-secondary)',
              margin: 0,
              lineHeight: '1.5',
              fontStyle: 'italic',
              display: '-webkit-box',
              WebkitLineClamp: '4',
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden'
            }}>
              "{card.quote}"
            </p>
          </div>

          {/* Footer (Metadata indicator) */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '9px', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '6px' }}>
            <span>{isSynthesis ? 'Synthesis Card' : `E-Factor: ${card.efactor?.toFixed(1)}`}</span>
            <span style={{
              color: isSynthesis ? '#ffd700' : (card.status === 'warning' ? 'var(--error)' : 'var(--success)'),
              fontWeight: '800'
            }}>
              {isSynthesis ? '✨ 灵感合题' : (card.status === 'warning' ? '🔥 警报' : '🟢 记忆稳固')}
            </span>
          </div>
        </div>

        {/* 卡牌背面 */}
        <div className="flip-card-back glass-panel" style={{
          padding: '18px',
          background: isSynthesis ? 'linear-gradient(135deg, rgba(20, 15, 5, 0.98) 0%, rgba(5, 4, 1, 0.99) 100%)' : 'var(--bg-surface-hover)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          border: isSynthesis ? '2px solid #ffd700' : '1px solid var(--accent)',
          height: '100%'
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', height: '100%', justifyContent: 'center' }}>
            {isSynthesis ? (
              <>
                <span style={{ fontSize: '10px', color: '#ffd700', fontWeight: 'bold', letterSpacing: '1px' }}>🔮 对撞脑洞来源 (Collision Source)</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
                  <div style={{ fontSize: '11.5px', color: 'rgba(255,255,255,0.7)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={card.parent_titles?.[0]}>
                    1️⃣ {card.parent_titles?.[0] || '观点 A'}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'rgba(255,255,255,0.7)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={card.parent_titles?.[1]}>
                    2️⃣ {card.parent_titles?.[1] || '观点 B'}
                  </div>
                </div>
              </>
            ) : (
              <span style={{ fontSize: '10px', color: 'var(--accent)', fontWeight: 'bold', letterSpacing: '1px' }}>💡 AI 为何重要 (Why It Matters)</span>
            )}
            
            <p style={{
              fontSize: '12.5px',
              color: 'var(--text-primary)',
              lineHeight: '1.6',
              margin: 0,
              textAlign: 'left'
            }}>
              {card.why_it_matters}
            </p>
          </div>
          
          <div style={{ textAlign: 'center', fontSize: '9px', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
            点击卡片翻回正面
          </div>
        </div>

      </div>
    </div>
  );
}

const DEFAULT_BASE_PROMPT = `请根据下面提供的【播客单集 Shownotes】、【听众热门评论】和【播客对话转录文本】，生成一份详尽、结构清晰的【播客价值总结分析报告】。

核心防伪守则（必须严格遵守，否则视为失败）：
1. 严禁臆测发散：所有分析结论、嘉宾立场、议题提炼及评级，必须100%基于下方提供的事实源数据。严禁使用你自身固有知识库中的外部信息去扩展或脑补播客中未提及的事情或技术细节。
2. 拒绝幻觉，空值如实报告：如果播客转录本中完全没有提及某人、某事或某个观点，哪怕该词出现在了 Shownotes 简介里，也绝对不得在总结中编造其对话内容，必须如实标注转录文本中未讨论或未提及。
3. 精准引用：提炼核心观点和发言人立场时，必须直接引用（或高度提炼）转录文本中的原话、金句或提及的具体事例，并指明是谁说的。
4. 客观呈现听众反馈：舆情分析部分必须完全基于热门听众评论列表中的实际留言，不得凭空编造听众情感走向。`;

const DEFAULT_ACTION_PROMPT = `请以 Markdown 格式输出以下结构的内容（严禁输出结构外的发散废话，直接输出报告正文）：

## 1. 播客概要与含金量评级
- **核心主旨**：用2-3句话精准总结这期播客实际讨论的核心主题（拒绝大话空话，紧扣转录事实）。
- **目标受众**：根据播客讨论内容的专业深度，说明适合哪些细分人群收听。
- **含金量评级与判定理由**：请给出评级（A+ / A / B / C / D 之一），并从内容信息密度、观点的独特性和知识实用度三个维度，基于转录中的干货多寡简述判定理由。
- **推荐等级**：是否值得花时间复听（值得去听 / 仅看总结即可 / 建议避坑）。

## 2. 核心观点与议题提炼
请梳理出播客实际讨论的3-5个核心议题。对每个议题：
- **议题名称**
- **核心论点**：结合不同人的发言总结其达成共识或分歧。
- **关键论据/金句**：必须包含转录中发言人提到过的原话、金句或他们讲到的具体案例。

## 3. 发言人画像与立场分析
- **角色定位**：说明都有谁参与了说话，谁是主持人（Host），谁是嘉宾（Guest）。
- **立场与风格**：简述各位发言人的核心立场、讨论风格以及观点倾向，切忌根据发言人的名气脑补其背景，只分析其在此单集中的言论表现。
- **互动氛围**：他们之间的互动如何（比如是和谐互补，还是存在观点的交锋摩擦）。

## 4. 听众口碑与评论区舆情分析
- **听众主要反馈**：评论区大家最赞同的观点是什么？有没有提出不同的质疑？（必须从提供的评论列表中提取，无评论则写暂无评论数据）。
- **评论情感极性**：正向期待为主 / 中立探讨 / 存在争议偏见。
- **社会共鸣点**：这期播客勾起了听众什么共鸣或情绪。

## 5. 事实一致性与局限性声明
请在此处特别说明：本报告有哪些内容是简介（Shownotes）中提到但转录对话中实际并未展开讨论的？（若有，请逐一列出；若无，写 Shownotes 提及内容与实际转录文本一致）。`;

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'detail', 'config'
  
  // ==================== 🧠 认知沙盒 (The Mind Sandbox) 状态 ====================
  const [hoveredParagraphId, setHoveredParagraphId] = useState(null);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVisible, setToastVisible] = useState(false);
  const showToast = (msg) => {
    setToastMessage(msg);
    setToastVisible(true);
    setTimeout(() => setToastVisible(false), 3000);
  };
  
  const [sandboxCards, setSandboxCards] = useState([]);
  const [dueCards, setDueCards] = useState([]);
  const [cardLinks, setCardLinks] = useState([]);
  const [isSpinning, setIsSpinning] = useState(false);
  const [isSlotOpen, setIsSlotOpen] = useState(false);
  const [leverActive, setLeverActive] = useState(false);
  const [spinReelsResolved, setSpinReelsResolved] = useState([false, false, false]);
  const [reviewedCardIds, setReviewedCardIds] = useState(new Set());
  const [forgottenCardIds, setForgottenCardIds] = useState(new Set());
  const [selectedCardId, setSelectedCardId] = useState(null);
  const [linkingSourceCardId, setLinkingSourceCardId] = useState(null);
  const [slotTheme, setSlotTheme] = useState('gold');
  const [isAudioMissing, setIsAudioMissing] = useState(false);
  const [isRedownloading, setIsRedownloading] = useState(false);
  
  const [activeCollider, setActiveCollider] = useState(null);
  const [colliderSynthesis, setColliderSynthesis] = useState('');
  const [colliderLoading, setColliderLoading] = useState(false);
  const [radarSurprise, setRadarSurprise] = useState(null);
  const [radarScanning, setRadarScanning] = useState(false);
  
  const targetParagraphIdRef = useRef(null);
  const [hoveredCardId, setHoveredCardId] = useState(null);
  const [svgPaths, setSvgPaths] = useState([]);
  const svgRef = useRef(null);
  const gridRef = useRef(null);
  
  const t = (key) => {
    const langDict = TRANSLATIONS[language] || TRANSLATIONS['zh-CN'];
    return langDict[key] || key;
  };
  const [tasks, setTasks] = useState([]);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [newUrl, setNewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isRefreshingMetadata, setIsRefreshingMetadata] = useState(false);
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
    enable_email_notification: false,
    asr_mode: 'online',
    online_api_key: '',
    online_base_url: 'https://token-plan-sgp.xiaomimimo.com/v1',
    online_model: 'mimo-v2.5-asr',
    summary_mode: 'online',
    online_summary_api_key: '',
    online_summary_base_url: 'https://api.openai.com/v1',
    online_summary_model: 'gpt-4o-mini',
    custom_storage_dir: ''
  });

  const [asrMode, setAsrMode] = useState('online'); // 'local' | 'online'

  // Prompt 编辑状态
  const [promptData, setPromptData] = useState({
    base_prompt: DEFAULT_BASE_PROMPT,
    action_prompt: DEFAULT_ACTION_PROMPT
  });
  const [promptSaveStatus, setPromptSaveStatus] = useState('idle'); // 'idle' | 'saving' | 'saved' | 'error'
  
  // 配置热保存/状态辅助变量
  const [isDirty, setIsDirty] = useState(false);
  const [saveStatus, setSaveStatus] = useState('idle'); // 'idle' | 'saving' | 'saved' | 'unsaved' | 'error'
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(() => {
    return localStorage.getItem('autoSaveSettings') !== 'false';
  });
  const isFetchingConfig = useRef(false);

  const updateConfigField = (field, value) => {
    if (isFetchingConfig.current) return;
    setConfigData(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);
    setSaveStatus('unsaved');
  };

  // 播放器状态绑定
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [volume, setVolume] = useState(0.8);
  const [showSpeakerModal, setShowSpeakerModal] = useState(false);
  const audioPlayerRef = useRef(null);
  const activeBubbleRef = useRef(null);
  const activeTaskRef = useRef(null);
  useEffect(() => {
    activeTaskRef.current = activeTask;
  }, [activeTask]);

  // 可拖拽的分栏布局状态
  const [leftWidth, setLeftWidth] = useState(55); // 初始左侧占比百分比
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const newWidth = ((e.clientX - rect.left) / rect.width) * 100;
      // 限制拖拽占比在 25% ~ 75% 之间
      if (newWidth >= 25 && newWidth <= 75) {
        setLeftWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const togglePlay = () => {
    if (!audioPlayerRef.current) return;
    if (isPlaying) {
      audioPlayerRef.current.pause();
    } else {
      audioPlayerRef.current.play().catch(err => console.log("播放失败:", err));
    }
  };

  const skipTime = (amount) => {
    if (!audioPlayerRef.current) return;
    let newTime = audioPlayerRef.current.currentTime + amount;
    if (newTime < 0) newTime = 0;
    if (newTime > duration) newTime = duration;
    audioPlayerRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const changePlaybackRate = (rate) => {
    if (!audioPlayerRef.current) return;
    audioPlayerRef.current.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const handleSeek = (e) => {
    if (!audioPlayerRef.current) return;
    const time = parseFloat(e.target.value);
    audioPlayerRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '00:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const pad = (num) => num.toString().padStart(2, '0');
    if (h > 0) {
      return `${h}:${pad(m)}:${pad(s)}`;
    }
    return `${pad(m)}:${pad(s)}`;
  };

  // 配置页面二级分类及多语言状态
  const [configSubTab, setConfigSubTab] = useState('llm'); // 'general', 'asr', 'llm', 'notifications'
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('appLanguage') || 'zh-CN';
  });

  useEffect(() => {
    localStorage.setItem('appLanguage', language);
  }, [language]);

  // 硬件性能监控数据
  const [perfData, setPerfData] = useState(null);

  // 主题与外观模式状态定义
  const [themeMode, setThemeMode] = useState(() => {
    return localStorage.getItem('themeMode') || 'dark';
  });

  const [lightTheme, setLightTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('lightTheme');
      return saved ? JSON.parse(saved) : PRESETS.light['Default Light'];
    } catch (e) {
      return PRESETS.light['Default Light'];
    }
  });

  const [darkTheme, setDarkTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('darkTheme');
      return saved ? JSON.parse(saved) : PRESETS.dark['Default Dark'];
    } catch (e) {
      return PRESETS.dark['Default Dark'];
    }
  });

  const [lightPresetName, setLightPresetName] = useState(() => {
    return localStorage.getItem('lightPresetName') || 'Default Light';
  });

  const [darkPresetName, setDarkPresetName] = useState(() => {
    return localStorage.getItem('darkPresetName') || 'Default Dark';
  });

  useEffect(() => {
    localStorage.setItem('themeMode', themeMode);
    localStorage.setItem('lightTheme', JSON.stringify(lightTheme));
    localStorage.setItem('darkTheme', JSON.stringify(darkTheme));
    localStorage.setItem('lightPresetName', lightPresetName);
    localStorage.setItem('darkPresetName', darkPresetName);

    const hexToRgb = (hex) => {
      if (!hex) return { r: 122, g: 162, b: 247 };
      const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
      const fullHex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(fullHex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : { r: 122, g: 162, b: 247 };
    };

    const applyColors = () => {
      const activeMode = themeMode === 'system' 
        ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
        : themeMode;
      
      const colors = activeMode === 'dark' ? darkTheme : lightTheme;
      const root = document.documentElement;
      
      let bgBase = colors.background;
      let bgSurface = 'rgba(255, 255, 255, 0.03)';
      let bgSurfaceHover = 'rgba(255, 255, 255, 0.06)';
      let borderColor = 'rgba(255, 255, 255, 0.06)';
      let borderHover = 'rgba(255, 255, 255, 0.12)';
      
      if (activeMode === 'dark') {
        bgSurface = 'rgba(255, 255, 255, 0.03)';
        bgSurfaceHover = 'rgba(255, 255, 255, 0.06)';
        borderColor = 'rgba(255, 255, 255, 0.06)';
        borderHover = 'rgba(255, 255, 255, 0.12)';
      } else {
        const bgLower = colors.background.toLowerCase();
        if (bgLower === '#ffffff') {
          bgBase = '#f1f5f9';
          bgSurface = '#ffffff';
          bgSurfaceHover = '#f8fafc';
        } else if (bgLower === '#fdf6e3') {
          bgSurface = '#eee8d5';
          bgSurfaceHover = '#e4ddca';
        } else if (bgLower === '#f0fdf4') {
          bgBase = '#f0fdf4';
          bgSurface = '#ffffff';
          bgSurfaceHover = '#f1fbf4';
        } else {
          bgBase = '#f1f7fc';
          bgSurface = '#ffffff';
          bgSurfaceHover = '#f8fafc';
        }
        borderColor = 'rgba(0, 0, 0, 0.08)';
        borderHover = 'rgba(0, 0, 0, 0.15)';
      }
      
      root.style.setProperty('--bg-base', bgBase);
      root.style.setProperty('--bg-surface', bgSurface);
      root.style.setProperty('--bg-surface-hover', bgSurfaceHover);
      root.style.setProperty('--border-color', borderColor);
      root.style.setProperty('--border-hover', borderHover);
      
      // 动态音频播放器面板背景色（跟随主题模式自动改变，保障亮色/暗色一致性）
      const playerBg = activeMode === 'dark' ? 'rgba(10, 10, 12, 0.92)' : 'rgba(255, 255, 255, 0.95)';
      root.style.setProperty('--player-bg', playerBg);
      
      root.style.setProperty('--text-primary', colors.foreground);
      
      const primaryColor = colors.primary || colors.accent;
      const accentColor = colors.accent;
      
      root.style.setProperty('--primary', primaryColor);
      root.style.setProperty('--accent', accentColor);
      
      const fgRgb = hexToRgb(colors.foreground);
      const priRgb = hexToRgb(primaryColor);
      const accRgb = hexToRgb(accentColor);
      
      const secOpacity = activeMode === 'light' ? 0.88 : 0.65;
      const mutOpacity = activeMode === 'light' ? 0.62 : 0.4;
      
      root.style.setProperty('--text-secondary', `rgba(${fgRgb.r}, ${fgRgb.g}, ${fgRgb.b}, ${secOpacity})`);
      root.style.setProperty('--text-muted', `rgba(${fgRgb.r}, ${fgRgb.g}, ${fgRgb.b}, ${mutOpacity})`);
      root.style.setProperty('--primary-glow', `rgba(${priRgb.r}, ${priRgb.g}, ${priRgb.b}, 0.12)`);
      root.style.setProperty('--accent-glow', `rgba(${accRgb.r}, ${accRgb.g}, ${accRgb.b}, 0.12)`);
    };

    applyColors();

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemThemeChange = () => {
      if (themeMode === 'system') {
        applyColors();
      }
    };

    mediaQuery.addEventListener('change', handleSystemThemeChange);
    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
    };
  }, [themeMode, lightTheme, darkTheme, lightPresetName, darkPresetName]);

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
    fetchPrompt();
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
    setIsAudioMissing(false);
    setIsRedownloading(false);
    if (activeTaskId) {
      fetchTaskDetail(activeTaskId);
      // 开启专属的详情轮询，如果任务正在执行中或正在修复中
      const detailInterval = setInterval(() => {
        const t = activeTaskRef.current;
        if (t && (t.status === 'downloading' || t.status === 'transcribing' || t.status === 'summarizing' || t.restoring)) {
          fetchTaskDetail(activeTaskId, true);
        }
      }, 3000);
      return () => clearInterval(detailInterval);
    } else {
      setActiveTask(null);
    }
  }, [activeTaskId]);

  // 3.1 监听修复状态完成，触发重新载入音频播放器
  useEffect(() => {
    if (activeTask && !activeTask.restoring && activeTask.restore_progress === 100.0) {
      fetch(`${BACKEND_URL}${activeTask.audio_url}`, { method: 'HEAD' })
        .then(res => {
          if (res.status === 200) {
            setIsAudioMissing(false);
            setIsRedownloading(false);
            if (audioPlayerRef.current) {
              audioPlayerRef.current.load();
            }
          }
        })
        .catch(err => console.error("HEAD check failed for audio URL", err));
    }
  }, [activeTask]);

  // 4. 切换到配置页时动态刷新配置参数，避免组件挂载时后端未就绪导致显示为空
  useEffect(() => {
    if (activeTab === 'config') {
      fetchConfig();
      fetchPrompt();
    }
  }, [activeTab]);

  // ==================== 🧠 认知沙盒 生命周期与数据拉取 ====================
  // URL 参数解析溯源跳转
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const taskId = params.get('task_id');
    const paragraphId = params.get('paragraph_id');
    if (taskId) {
      setActiveTaskId(taskId);
      setActiveTab('detail');
      targetParagraphIdRef.current = paragraphId;
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // 监听任务详情加载，并在段落列表渲染后执行定位与播放
  useEffect(() => {
    if (activeTask && targetParagraphIdRef.current && activeTask.paragraphs) {
      const paraId = targetParagraphIdRef.current;
      targetParagraphIdRef.current = null; // 消费
      
      const targetPara = activeTask.paragraphs.find(p => p.id === paraId);
      if (targetPara) {
        // 跳转播放时间
        handleTimeJump(targetPara.start_time);
        
        // 滚动并高亮闪烁
        setTimeout(() => {
          const el = document.getElementById(paraId);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.classList.add('glow-highlight');
            setTimeout(() => {
              el.classList.remove('glow-highlight');
            }, 3000);
          }
        }, 600);
      }
    }
  }, [activeTask]);

  // 切换到沙盒时自动更新所有数据
  useEffect(() => {
    if (activeTab === 'sandbox') {
      fetchSandboxData();
    }
  }, [activeTab]);

  const fetchSandboxData = async () => {
    try {
      // 1. 获取所有卡片
      const cardsRes = await fetch(`${BACKEND_URL}/api/cards`);
      let cards = [];
      if (cardsRes.status === 200) {
        cards = await cardsRes.json();
        setSandboxCards(cards);
      }
      
      // 2. 获取连线数据
      const linksRes = await fetch(`${BACKEND_URL}/api/links`);
      if (linksRes.status === 200) {
        const links = await linksRes.json();
        setCardLinks(links);
      }
      
      // 3. 获取待复习卡片
      const dueRes = await fetch(`${BACKEND_URL}/api/cards/due`);
      if (dueRes.status === 200) {
        const due = await dueRes.json();
        setDueCards(due);
      }

      // 4. 自动认知雷达：如果卡片数 >= 2，且当前没有雷达惊喜结果，在后台偷偷发起一次探测
      if (cards.length >= 2 && !radarSurprise) {
        triggerRadarScan();
      }
    } catch (err) {
      console.error("无法加载认知沙盒数据:", err);
    }
  };

  // 动态计算卡片网格连线坐标
  const calculateLinks = () => {
    if (!svgRef.current || !gridRef.current || sandboxCards.length === 0 || cardLinks.length === 0) {
      setSvgPaths([]);
      return;
    }

    const svgRect = svgRef.current.getBoundingClientRect();
    const paths = [];

    cardLinks.forEach(link => {
      const elA = document.getElementById(`card-${link.source_card_id}`);
      const elB = document.getElementById(`card-${link.target_card_id}`);
      
      if (elA && elB) {
        const rectA = elA.getBoundingClientRect();
        const rectB = elB.getBoundingClientRect();
        
        // 计算两张卡片的中心坐标（相对于 SVG 容器）
        const x1 = rectA.left - svgRect.left + rectA.width / 2;
        const y1 = rectA.top - svgRect.top + rectA.height / 2;
        const x2 = rectB.left - svgRect.left + rectB.width / 2;
        const y2 = rectB.top - svgRect.top + rectB.height / 2;
        
        // 绘制一条平滑的贝塞尔曲线
        const dx = x2 - x1;
        const dy = y2 - y1;
        const cx1 = x1 + dx * 0.25;
        const cy1 = y1 + dy * 0.1;
        const cx2 = x1 + dx * 0.75;
        const cy2 = y2 - dy * 0.1;
        
        paths.push({
          id: link.id,
          source: link.source_card_id,
          target: link.target_card_id,
          synthesis: link.my_synthesis,
          d: `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`,
          isGold: !!link.my_synthesis
        });
      }
    });
    setSvgPaths(paths);
  };

  // 监听窗口缩放与卡片变化，动态刷新路径
  useEffect(() => {
    if (activeTab === 'sandbox') {
      const timer = setTimeout(calculateLinks, 500);
      window.addEventListener('resize', calculateLinks);
      return () => {
        clearTimeout(timer);
        window.removeEventListener('resize', calculateLinks);
      };
    }
  }, [activeTab, sandboxCards, cardLinks]);

  // ==================== 🧠 认知沙盒 操作处理器 ====================
  // 浏览器音频合成提醒声音
  const playAudioSynth = (type) => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      const time = ctx.currentTime;
      
      if (type === 'spin') {
        // 低频嗡嗡声 + 齿轮刻度声
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(90, time);
        osc.frequency.exponentialRampToValueAtTime(320, time + 1.2);
        gain.gain.setValueAtTime(0.04, time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + 1.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(time);
        osc.stop(time + 1.2);
        
        // 6声齿轮点击音效
        for (let i = 0; i < 6; i++) {
          const tickOsc = ctx.createOscillator();
          const tickGain = ctx.createGain();
          tickOsc.type = 'triangle';
          tickOsc.frequency.setValueAtTime(700 - i * 60, time + i * 0.2);
          tickGain.gain.setValueAtTime(0.03, time + i * 0.2);
          tickGain.gain.exponentialRampToValueAtTime(0.001, time + i * 0.2 + 0.04);
          tickOsc.connect(tickGain);
          tickGain.connect(ctx.destination);
          tickOsc.start(time + i * 0.2);
          tickOsc.stop(time + i * 0.2 + 0.04);
        }
      } else if (type === 'resolve') {
        // 清脆风铃声 (大三和弦)
        const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, time + idx * 0.04);
          gain.gain.setValueAtTime(0.05, time + idx * 0.04);
          gain.gain.exponentialRampToValueAtTime(0.001, time + idx * 0.04 + 0.45);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(time + idx * 0.04);
          osc.stop(time + idx * 0.04 + 0.45);
        });
      } else if (type === 'tamed') {
        // 成功音效 (上行音阶)
        const notes = [523.25, 659.25, 783.99, 1046.5];
        notes.forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, time + idx * 0.08);
          gain.gain.setValueAtTime(0.06, time + idx * 0.08);
          gain.gain.exponentialRampToValueAtTime(0.001, time + idx * 0.08 + 0.25);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(time + idx * 0.08);
          osc.stop(time + idx * 0.08 + 0.25);
        });
      } else if (type === 'forgot') {
        // 警示音效
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(140, time);
        osc.frequency.linearRampToValueAtTime(100, time + 0.35);
        gain.gain.setValueAtTime(0.06, time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + 0.35);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(time);
        osc.stop(time + 0.35);
      }
    } catch (e) {
      console.warn("Web Audio API warning:", e);
    }
  };

  // 老虎机摇杆动作
  const triggerLeverPull = () => {
    if (isSpinning) return;
    setLeverActive(true);
    setTimeout(() => {
      setLeverActive(false);
      handleSpinSlotMachine();
    }, 300);
  };

  const handleSpinSlotMachine = async () => {
    if (isSpinning) return;
    
    setIsSpinning(true);
    setSpinReelsResolved([false, false, false]);
    setReviewedCardIds(new Set());
    setForgottenCardIds(new Set());
    playAudioSynth('spin');
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/cards/due`);
      if (res.status === 200) {
        const cards = await res.json();
        setDueCards(cards);
        
        // 滚轮停滞动画时间
        setTimeout(() => {
          setSpinReelsResolved([true, false, false]);
          playAudioSynth('resolve');
        }, 800);
        
        setTimeout(() => {
          setSpinReelsResolved([true, true, false]);
          playAudioSynth('resolve');
        }, 1400);
        
        setTimeout(() => {
          setSpinReelsResolved([true, true, true]);
          playAudioSynth('resolve');
          setIsSpinning(false);
          if (cards.length === 0) {
            showToast("ℹ️ 当前没有待复习的历史卡片，请先去详情页沉淀一些吧！");
          } else {
            showToast("🎰 卡片打捞出舱！命运之轮已选定观点");
          }
        }, 2000);
      } else {
        setIsSpinning(false);
        showToast("❌ 捞取卡片失败，请重试");
      }
    } catch (err) {
      setIsSpinning(false);
      showToast("❌ 无法连接到后端服务");
    }
  };

  // 卡片滑块提交复习
  const handleReviewCard = async (cardId, direction) => {
    playAudioSynth(direction === 'left' ? 'tamed' : 'forgot');
    
    // 乐观更新
    const nextReviewed = new Set(reviewedCardIds);
    nextReviewed.add(cardId);
    setReviewedCardIds(nextReviewed);
    
    if (direction === 'right') {
      const nextForgotten = new Set(forgottenCardIds);
      nextForgotten.add(cardId);
      setForgottenCardIds(nextForgotten);
    }
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/cards/${cardId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction })
      });
      if (res.status === 200) {
        if (direction === 'left') {
          showToast("✅ 卡片已驯服！已自动推迟下一次复习时间。");
        } else {
          showToast("🔥 卡片已置为警告状态！今晚将自动推送移动端复习。");
        }
        fetchSandboxData();
      } else {
        showToast("❌ 提交复习失败");
      }
    } catch (err) {
      console.error(err);
      showToast("❌ 无法连接到后端服务");
    }
  };

  // 触发认知雷达扫描
  const triggerRadarScan = async () => {
    setRadarScanning(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/cards/collider`);
      if (res.status === 200) {
        const data = await res.json();
        setRadarSurprise(data);
      }
    } catch (err) {
      console.error("认知雷达巡航扫描失败:", err);
    } finally {
      setRadarScanning(false);
    }
  };

  const handleTriggerRadarCollider = (surprise) => {
    setActiveCollider(surprise);
    setColliderSynthesis('');
    setRadarSurprise(null); // 消耗掉该惊喜，以便下次对撞完重新扫描
  };

  // 启动 AI 对撞机
  const handleOpenCollider = async () => {
    setColliderLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/cards/collider`);
      if (res.status === 200) {
        const data = await res.json();
        setActiveCollider(data);
        setColliderSynthesis('');
        setColliderLoading(false);
      } else {
        const errData = await res.json();
        setColliderLoading(false);
        alert(errData.detail || "无法启动对撞机，请先去详情页沉淀至少2张卡片！");
      }
    } catch (err) {
      setColliderLoading(false);
      alert("启动对撞机失败，请检查后端服务是否就绪！");
    }
  };

  // 提交对撞合成灵感
  const handleCollideSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!colliderSynthesis.trim() || !activeCollider) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/links`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_card_id: activeCollider.card_a.id,
          target_card_id: activeCollider.card_b.id,
          my_synthesis: colliderSynthesis.trim()
        })
      });
      if (res.status === 200) {
        playAudioSynth('resolve');
        showToast("💥 跨界观点成功对撞！金色的灵感连线已永久镌刻！");
        setActiveCollider(null);
        setColliderSynthesis('');
        setRadarSurprise(null); // 清理缓存的惊喜，重新触发扫描
        fetchSandboxData();
      } else {
        showToast("❌ 保存对撞灵感失败");
      }
    } catch (err) {
      console.error(err);
      showToast("❌ 无法连接到后端服务");
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setTasks(data);
        } else {
          console.error("/api/tasks did not return an array:", data);
        }
      }
    } catch (e) {
      console.error("无法获取任务列表:", e);
    }
  };

  const fetchConfig = async () => {
    isFetchingConfig.current = true;
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`);
      const data = await res.json();
      setConfigData(data);
      if (data.theme_mode) {
        setThemeMode(data.theme_mode);
      }
      if (data.light_theme) {
        setLightTheme(data.light_theme);
      }
      if (data.dark_theme) {
        setDarkTheme(data.dark_theme);
      }
      if (data.asr_mode) {
        setAsrMode(data.asr_mode);
      }
      setIsDirty(false);
      setSaveStatus('idle');
    } catch (e) {
      console.error("无法加载系统配置:", e);
    } finally {
      // 延迟重置以防 React 状态异步更新未落盘
      setTimeout(() => {
        isFetchingConfig.current = false;
      }, 100);
    }
  };



  const handleResetPrompt = () => {
    if (window.confirm("确定要恢复默认 Prompt 模板吗？这会覆盖您当前的输入。")) {
      setPromptData({
        base_prompt: DEFAULT_BASE_PROMPT,
        action_prompt: DEFAULT_ACTION_PROMPT
      });
    }
  };

  // 加载 Prompt 配置
  const fetchPrompt = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/prompt`);
      if (res.ok) {
        const data = await res.json();
        setPromptData(data);
      }
    } catch (e) {
      console.error('无法加载 Prompt 配置:', e);
    }
  };

  // 保存 Prompt 配置
  const handleSavePrompt = async () => {
    setPromptSaveStatus('saving');
    try {
      const res = await fetch(`${BACKEND_URL}/api/prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(promptData)
      });
      if (res.ok) {
        setPromptSaveStatus('saved');
        setTimeout(() => setPromptSaveStatus('idle'), 3000);
      } else {
        setPromptSaveStatus('error');
      }
    } catch (e) {
      setPromptSaveStatus('error');
    }
  };

  // 快捷切换 ASR 模式并保存到后端配置
  const handleToggleAsrMode = async (mode) => {
    setAsrMode(mode);
    const updatedConfig = { ...configData, asr_mode: mode };
    setConfigData(updatedConfig);
    try {
      await fetch(`${BACKEND_URL}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig)
      });
    } catch (e) {
      console.error("快捷更新 ASR 模式失败:", e);
    }
  };

  // 快捷切换 LLM 总结模式并保存到后端配置
  const handleToggleSummaryMode = async (mode) => {
    const updatedConfig = { ...configData, summary_mode: mode };
    setConfigData(updatedConfig);
    try {
      await fetch(`${BACKEND_URL}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig)
      });
      // 立即刷新性能与大模型状态
      fetchPerformance();
    } catch (e) {
      console.error("快捷更新 LLM 模式失败:", e);
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

  const handleRestoreAudio = async (taskId) => {
    if (isRedownloading) return;
    setIsRedownloading(true);
    showToast("正在后台重新下载并修复音频...");
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${taskId}/redownload`, {
        method: 'POST'
      });
      if (res.status === 200) {
        let checkCount = 0;
        const checkInterval = setInterval(async () => {
          checkCount++;
          try {
            const checkRes = await fetch(`${BACKEND_URL}/api/tasks/${taskId}`);
            if (checkRes.status === 200) {
              const data = await checkRes.json();
              const audioRes = await fetch(`${BACKEND_URL}${data.audio_url}`, { method: 'HEAD' });
              if (audioRes.status === 200) {
                clearInterval(checkInterval);
                setIsAudioMissing(false);
                setIsRedownloading(false);
                showToast("音频文件已修复，正在重新加载播放器！");
                if (audioPlayerRef.current) {
                  audioPlayerRef.current.load();
                }
              }
            }
          } catch (err) {
            console.error(err);
          }
          if (checkCount > 40) {
            clearInterval(checkInterval);
            setIsRedownloading(false);
            showToast("音频修复超时，请稍后刷新重试。");
          }
        }, 3000);
      } else {
        const errorData = await res.json();
        showToast(`发起音频修复失败: ${errorData.detail || '未知错误'}`);
        setIsRedownloading(false);
      }
    } catch (e) {
      showToast("连接服务器失败，请检查网络！");
      setIsRedownloading(false);
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

  // 刷新节目元数据 (实时获取点赞、评论等)
  const handleRefreshMetadata = async () => {
    if (!activeTaskId || isRefreshingMetadata) return;
    setIsRefreshingMetadata(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/tasks/${activeTaskId}/metadata/refresh`, {
        method: 'POST'
      });
      if (res.status === 200) {
        const result = await res.json();
        if (result.success) {
          // 重新获取详情和任务列表以更新主界面
          await fetchTaskDetail(activeTaskId, true);
          await fetchTasks();
        } else {
          alert("刷新数据失败：" + (result.detail || "未知错误"));
        }
      } else {
        const errorData = await res.json();
        alert("刷新数据失败：" + (errorData.detail || "服务器内部错误"));
      }
    } catch (e) {
      alert("网络请求失败，请检查后端服务");
    } finally {
      setIsRefreshingMetadata(false);
    }
  };

  // 保存系统配置
  const handleSaveConfig = async (e, options = { silent: false }) => {
    if (e && e.preventDefault) e.preventDefault();
    setSaveStatus('saving');
    try {
      const res = await fetch(`${BACKEND_URL}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });
      if (res.status === 200) {
        setSaveStatus('saved');
        setIsDirty(false);
        if (!options.silent) {
          alert("配置已成功更新，并实时应用！");
          setActiveTab('dashboard');
        }
      } else {
        setSaveStatus('error');
      }
    } catch (e) {
      setSaveStatus('error');
      if (!options.silent) {
        alert("保存失败");
      }
    }
  };

  // 监听并执行防抖自动保存
  useEffect(() => {
    localStorage.setItem('autoSaveSettings', autoSaveEnabled);
  }, [autoSaveEnabled]);

  useEffect(() => {
    if (!autoSaveEnabled || !isDirty || isFetchingConfig.current) return;
    
    const delayDebounceFn = setTimeout(() => {
      handleSaveConfig(null, { silent: true });
    }, 1200);

    return () => clearTimeout(delayDebounceFn);
  }, [configData, autoSaveEnabled, isDirty]);

  // 点击跳转到指定秒数播放
  const handleTimeJump = (seconds) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.currentTime = seconds;
      audioPlayerRef.current.play().catch(err => console.log("播放被浏览器拦截", err));
    }
    
    // 智能定位：当点击外部时间戳时，左侧剧本流自动滚动至对应段落并居中
    if (activeTask && activeTask.paragraphs && activeTask.paragraphs.length > 0) {
      let targetPara = activeTask.paragraphs.find(p => seconds >= p.start_time && seconds <= p.end_time);
      if (!targetPara) {
        // 如果点击的时间点正好落在静音间隙，则寻找时间最接近的段落
        targetPara = activeTask.paragraphs.reduce((prev, curr) => {
          return (Math.abs(curr.start_time - seconds) < Math.abs(prev.start_time - seconds) ? curr : prev);
        });
      }
      if (targetPara) {
        // 使用 setTimeout 确保 DOM 状态稳定
        setTimeout(() => {
          const el = document.getElementById(targetPara.id);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // 添加闪烁高亮效果提醒用户
            el.classList.add('glow-highlight');
            setTimeout(() => {
              el.classList.remove('glow-highlight');
            }, 2000);
          }
        }, 100);
      }
    }
  };

  // 沉淀段落为卡片 (乐观更新)
  const handleSedimentParagraph = async (paragraphId, podcastId) => {
    let isSedimented = false;
    if (activeTask && activeTask.paragraphs) {
      const p = activeTask.paragraphs.find(p => p.id === paragraphId);
      if (p) isSedimented = p.sedimented;
    }

    // 1. 乐观更新：立刻在前端改变状态，实现真正的“零延迟”点击体验
    if (activeTask && activeTask.paragraphs) {
      const optimisticParas = activeTask.paragraphs.map(p => 
        p.id === paragraphId ? { ...p, sedimented: !isSedimented } : p
      );
      setActiveTask({ ...activeTask, paragraphs: optimisticParas });
    }

    // 2. 后台静默发起真正的网络请求
    try {
      if (isSedimented) {
        // 取消沉淀
        const res = await fetch(`${BACKEND_URL}/api/cards/paragraph/${paragraphId}`, {
          method: 'DELETE'
        });
        if (res.status !== 200) {
          // 失败回退状态
          if (activeTask && activeTask.paragraphs) {
            const rollbackParas = activeTask.paragraphs.map(p => 
              p.id === paragraphId ? { ...p, sedimented: true } : p
            );
            setActiveTask({ ...activeTask, paragraphs: rollbackParas });
          }
          showToast("❌ 取消沉淀失败，请重试");
        }
      } else {
        // 沉淀
        const res = await fetch(`${BACKEND_URL}/api/cards/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ paragraph_id: paragraphId, podcast_id: podcastId })
        });
        if (res.status !== 200) {
          // 失败回退状态
          if (activeTask && activeTask.paragraphs) {
            const rollbackParas = activeTask.paragraphs.map(p => 
              p.id === paragraphId ? { ...p, sedimented: false } : p
            );
            setActiveTask({ ...activeTask, paragraphs: rollbackParas });
          }
          showToast("❌ 沉淀卡片失败，请重试");
        }
      }
    } catch (err) {
      console.error(err);
      // 失败回退状态
      if (activeTask && activeTask.paragraphs) {
        const rollbackParas = activeTask.paragraphs.map(p => 
          p.id === paragraphId ? { ...p, sedimented: isSedimented } : p
        );
        setActiveTask({ ...activeTask, paragraphs: rollbackParas });
      }
      showToast("❌ 无法连接到后端服务");
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
          <div style={{ padding: '4px 8px' }}>
            <h1 style={{ fontSize: '25px', fontWeight: '750', letterSpacing: '1px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
              <img src="/logo.svg" alt="logo" style={{ width: '36px', height: '36px' }} />
              whisperMe
            </h1>
          </div>

          {/* 导航按钮 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button 
              onClick={() => { setActiveTab('dashboard'); setActiveTaskId(null); }}
              className="btn-ghost" 
              style={{ 
                justifyContent: 'flex-start', 
                background: activeTab === 'dashboard' ? 'var(--primary-glow)' : 'transparent',
                borderColor: activeTab === 'dashboard' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'dashboard' ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'dashboard' ? '700' : '500'
              }}
            >
              <Icons.Home />
              {t('dashboard')}
            </button>

            <button 
              onClick={() => { setActiveTab('sandbox'); setActiveTaskId(null); }}
              className="btn-ghost" 
              style={{ 
                justifyContent: 'flex-start', 
                background: activeTab === 'sandbox' ? 'var(--primary-glow)' : 'transparent',
                borderColor: activeTab === 'sandbox' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'sandbox' ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'sandbox' ? '700' : '500'
              }}
            >
              <Icons.Sandbox />
              {t('sandbox')}
            </button>
            
            <button 
              onClick={() => setActiveTab('config')}
              className="btn-ghost" 
              style={{ 
                justifyContent: 'flex-start', 
                background: activeTab === 'config' ? 'var(--primary-glow)' : 'transparent',
                borderColor: activeTab === 'config' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'config' ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'config' ? '700' : '500'
              }}
            >
              <Icons.Settings />
              {t('settings')}
            </button>
          </div>
        </div>

        {/* 微型仪表盘 (Micro-Dashboard) */}
        <div style={{ 
          padding: '12px 10px', 
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          {/* CPU & RAM & Disk - 紧凑网格 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px' }}>
            
            {/* CPU & Queue 一行两列 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {/* CPU */}
              <div style={{ background: 'rgba(0,0,0,0.15)', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>CPU</span>
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{perfData ? `${perfData.cpu}%` : '--'}</span>
                </div>
                <div style={{ width: '100%', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', overflow: 'hidden', marginTop: '6px' }}>
                  <div style={{ width: `${perfData?.cpu || 0}%`, height: '100%', background: (perfData?.cpu > 80) ? 'var(--error)' : 'var(--primary)' }}></div>
                </div>
              </div>

              {/* Queue */}
              <div style={{ background: 'rgba(0,0,0,0.15)', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{t('queue_tasks')}</span>
                </div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: perfData?.queue?.size > 0 ? 'var(--primary)' : 'var(--text-muted)', marginTop: '2px' }}>
                  {perfData?.queue ? perfData.queue.size : '--'}
                </div>
              </div>
            </div>

            {/* RAM (全宽) */}
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>RAM</span>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{perfData?.ram?.percent || 0}%</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)', marginTop: '2px' }}>
                {perfData ? `${perfData.ram.used}G / ${perfData.ram.total}G` : '--'}
              </div>
              {perfData?.ram && (
                <div style={{ width: '100%', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', overflow: 'hidden', marginTop: '4px' }}>
                  <div style={{ width: `${perfData.ram.percent}%`, height: '100%', background: perfData.ram.percent > 85 ? 'var(--error)' : 'linear-gradient(90deg, #3b82f6, #60a5fa)' }}></div>
                </div>
              )}
            </div>

            {/* Disk (全宽) */}
            {perfData?.disk && (
              <div style={{ background: 'rgba(0,0,0,0.15)', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>Disk</span>
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{perfData.disk.percent}%</span>
                </div>
                <div style={{ fontSize: '12px', fontWeight: '600', color: '#10b981', marginTop: '2px' }}>
                  {perfData.disk.used}G / {perfData.disk.total}G
                </div>
                <div style={{ width: '100%', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', overflow: 'hidden', marginTop: '4px' }}>
                  <div style={{ width: `${perfData.disk.percent}%`, height: '100%', background: 'linear-gradient(90deg, #10b981, #059669)' }}></div>
                </div>
              </div>
            )}
          </div>

          {/* GPU - 只在有 GPU 时渲染，高度压缩 */}
          {perfData?.vram?.has_gpu && (
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '10px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '120px' }} title={perfData.vram.gpu_name}>
                  {perfData.vram.gpu_name}
                </span>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{perfData.vram.gpu_temp}°C | {perfData.vram.gpu_util}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>VRAM</span>
                <span style={{ fontSize: '10px', color: perfData.vram.percent > 85 ? 'var(--error)' : 'var(--text-primary)', fontWeight: '600' }}>
                  {(perfData.vram.used / 1024).toFixed(1)}G / {(perfData.vram.total / 1024).toFixed(1)}G
                </span>
              </div>
              <div style={{ width: '100%', height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '1.5px', overflow: 'hidden', marginTop: '4px' }}>
                <div style={{ width: `${perfData.vram.percent}%`, height: '100%', background: perfData.vram.percent > 85 ? 'var(--error)' : 'linear-gradient(90deg, var(--primary), var(--accent))' }}></div>
              </div>
            </div>
          )}

          {/* 模式 Badges */}
          <div style={{ display: 'flex', gap: '6px' }}>
            <div style={{ 
              flex: 1, 
              padding: '6px 4px', 
              background: 'rgba(0,0,0,0.2)', 
              border: '1px solid rgba(255,255,255,0.05)', 
              borderRadius: '6px', 
              textAlign: 'center', 
              fontSize: '11px', 
              fontWeight: '500', 
              color: asrMode === 'local' ? 'var(--primary)' : 'var(--accent)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                {asrMode === 'local' ? `💻` : `🌐`} <span style={{ fontWeight: '600' }}>ASR</span>
              </div>
              <div 
                style={{ 
                  fontSize: '9px', 
                  color: 'var(--text-secondary)', 
                  opacity: 0.8,
                  marginTop: '3px', 
                  maxWidth: '100%', 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis', 
                  whiteSpace: 'nowrap',
                  padding: '0 2px'
                }} 
                title={asrMode === 'local' ? (configData.local_whisper_model_path ? getWhisperModelName(configData.local_whisper_model_path) : 'Large V3') : (configData.online_model || 'MiMo ASR')}
              >
                {asrMode === 'local' ? (configData.local_whisper_model_path ? getWhisperModelName(configData.local_whisper_model_path) : 'Large V3') : (configData.online_model || 'MiMo ASR')}
              </div>
            </div>
            {perfData?.llm_status && (
              <div style={{ 
                flex: 1, 
                padding: '6px 4px', 
                background: 'rgba(0,0,0,0.2)', 
                border: '1px solid rgba(255,255,255,0.05)', 
                borderRadius: '6px', 
                textAlign: 'center', 
                fontSize: '11px', 
                fontWeight: '500', 
                color: perfData.llm_status === 'connected' ? '#10b981' : (perfData.llm_status === 'online_mode' ? 'var(--primary)' : 'var(--error)'),
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                  {perfData.llm_status === 'connected' ? `🧠` : (perfData.llm_status === 'online_mode' ? `☁️` : `❌`)} <span style={{ fontWeight: '600' }}>LLM</span>
                </div>
                <div 
                  style={{ 
                    fontSize: '9px', 
                    color: 'var(--text-secondary)', 
                    opacity: 0.8,
                    marginTop: '3px', 
                    maxWidth: '100%', 
                    overflow: 'hidden', 
                    textOverflow: 'ellipsis', 
                    whiteSpace: 'nowrap',
                    padding: '0 2px'
                  }}
                  title={configData.summary_mode === 'local' ? (configData.ollama_model || 'qwen2.5:7b') : (configData.online_summary_model || 'gpt-4o-mini')}
                >
                  {configData.summary_mode === 'local' ? (configData.ollama_model || 'qwen2.5:7b') : (configData.online_summary_model || 'gpt-4o-mini')}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ==================== 💻 右侧主内容区域 ==================== */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {/* 本地 AI 总结大模型 (LLM) 未开启提示条 */}
        {perfData?.llm_status === 'offline' && (
          <div style={{ 
            background: 'rgba(239, 68, 68, 0.15)', 
            borderBottom: '1px solid var(--error)', 
            color: 'var(--error)', 
            padding: '10px 32px', 
            fontSize: '13px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontWeight: '600',
            zIndex: '5'
          }}>
            <span>{t('warning_llm_off')}</span>
          </div>
        )}
        
        {/* TOP BAR */}
        <div style={{ height: '70px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', padding: '0 32px', justifyContent: 'space-between' }}>
          <div>
            {activeTab === 'detail' && activeTask ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button className="btn-ghost" style={{ padding: '8px 12px' }} onClick={() => { setActiveTab('dashboard'); setActiveTaskId(null); }}>
                  <Icons.ArrowLeft />
                  {t('back')}
                </button>
                <div>
                  <h2 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>{activeTask.title}</h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{activeTask.podcast_name}</p>
                </div>
              </div>
            ) : (
              <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>
                {activeTab === 'dashboard'
                  ? t('my_podcast_lib')
                  : activeTab === 'sandbox'
                    ? '认知沙盒'
                    : t('sys_config_header')}
              </h2>
            )}
          </div>
          
          {/* 详情页右侧：跳转原链接 */}
          {activeTab === 'detail' && activeTask?.url && (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <button 
                className="btn-ghost" 
                style={{ padding: '8px 16px', gap: '8px', fontSize: '13px', fontWeight: '500' }}
                onClick={() => window.open(activeTask.url, '_blank', 'noopener,noreferrer')}
                title="在新标签页中打开原始链接"
              >
                <Icons.ExternalLink />
                访问原文
              </button>
            </div>
          )}

          {/* 右侧快速任务新建栏 */}
          {activeTab === 'dashboard' && (
            <form onSubmit={handleCreateTask} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>


              <input 
                type="text" 
                placeholder={t('input_placeholder')}
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                className="glass-input"
                style={{ width: '300px' }}
                disabled={loading}
              />
              <button type="submit" className="btn-glow" disabled={loading}>
                {loading && !uploading ? t('initiating') : <><Icons.Plus /> {t('fetch_audio')}</>}
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
                {uploading ? t('uploading') : <><Icons.Upload /> {t('upload_audio')}</>}
              </button>
            </form>
          )}
        </div>

        {/* 主展示区 */}
        <div style={{ 
          flex: '1', 
          overflowY: activeTab === 'detail' ? 'hidden' : 'auto', 
          padding: activeTab === 'detail' ? '24px 32px 0 32px' : '32px', 
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0
        }}>
          
          {/* ==================== PANEL 1: DASHBOARD ==================== */}
          {activeTab === 'dashboard' && (
            <div>
              {/* 卡片列表 */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
                {tasks.length === 0 ? (
                  <div className="glass-panel" style={{ gridColumn: '1/-1', padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    <p style={{ fontSize: '16px', fontWeight: '500' }}>{t('empty_lib')}</p>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>{t('empty_lib_sub')}</p>
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
                        padding: '16px', 
                        cursor: 'pointer', 
                        display: 'flex', 
                        flexDirection: 'row', 
                        gap: '16px',
                        borderLeft: task.asr_mode === 'online' ? '4px solid var(--accent)' : '4px solid var(--primary)',
                        position: 'relative',
                        transition: 'transform 0.2s, box-shadow 0.2s',
                        alignItems: 'flex-start'
                      }}
                    >
                      {/* Trash button positioned absolutely at top right */}
                      <button 
                        className="btn-ghost" 
                        style={{ 
                          position: 'absolute', 
                          top: '12px', 
                          right: '12px', 
                          border: 'none', 
                          background: 'transparent', 
                          padding: '6px', 
                          borderRadius: '50%', 
                          color: 'var(--text-muted)',
                          opacity: 0.6,
                          transition: 'opacity 0.2s',
                          zIndex: 5
                        }}
                        onClick={(e) => handleDeleteTask(task.id, e)}
                      >
                        <Icons.Trash />
                      </button>

                      {/* Left side: Cover image wrapper (centered vertically in stretched flex card) */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        alignSelf: 'stretch',
                        flexShrink: 0
                      }}>
                        {/* Cover image or gradient placeholder */}
                        <div style={{ 
                          width: '96px', 
                          height: '96px', 
                          borderRadius: '8px', 
                          overflow: 'hidden', 
                          background: 'var(--bg-base)',
                          border: '1px solid var(--border-color)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                        }}>
                          {task.image_url ? (
                            <img 
                              src={task.image_url} 
                              alt={task.title} 
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              onError={(e) => { e.target.style.display = 'none'; }} 
                            />
                          ) : (
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.2 }}><path d="M3 18v-6a9 9 0 0 1 18 0v6"></path><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path></svg>
                          )}
                        </div>
                      </div>

                      {/* Right side: stats & title info */}
                      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '24px' }}>
                        <div>
                          {/* Title & Podcast Name */}
                          <h3 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', lineBreak: 'anywhere', lineHeight: '1.4', marginBottom: '4px', paddingRight: '8px' }}>
                            {task.title}
                          </h3>
                          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>{task.podcast_name}</p>
                          
                          {/* Badges row */}
                          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '4px' }}>
                            <span style={{ 
                              fontSize: '10px', 
                              padding: '2px 6px', 
                              borderRadius: '10px', 
                              background: task.status === 'completed' ? 'var(--success-glow)' : 'rgba(255,255,255,0.05)',
                              border: task.status === 'completed' ? '1px solid rgba(115, 218, 202, 0.2)' : '1px solid var(--border-color)',
                              color: task.status === 'completed' ? 'var(--success)' : 'var(--text-secondary)'
                            }}>
                              {renderStatus(task)}
                            </span>
                            <span style={{ 
                              fontSize: '10px', 
                              padding: '2px 6px', 
                              borderRadius: '10px', 
                              background: task.asr_mode === 'online' ? 'var(--accent-glow)' : 'var(--primary-glow)',
                              border: task.asr_mode === 'online' ? '1px solid var(--accent)' : '1px solid var(--primary)',
                              color: task.asr_mode === 'online' ? 'var(--accent)' : 'var(--primary)',
                              fontWeight: '600'
                            }}>
                              {task.asr_mode === 'online' ? t('online_asr_badge') : t('local_asr_badge')}
                            </span>
                            {(() => {
                              const srcInfo = getSourceLabel(task);
                              return (
                                <span style={{ 
                                  fontSize: '10px', 
                                  padding: '2px 6px', 
                                  borderRadius: '10px', 
                                  background: srcInfo.bg,
                                  border: `1px solid ${srcInfo.color}40`,
                                  color: srcInfo.color,
                                  fontWeight: '600'
                                }}>
                                  {srcInfo.text}
                                </span>
                              );
                            })()}
                          </div>
                        </div>

                        {/* Bottom stats / progress */}
                        <div style={{ marginTop: 'auto' }}>
                          {task.status !== 'completed' && task.status !== 'failed' ? (
                            <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                              <div className="progress-bar-animated" style={{ width: `${task.progress}%`, height: '100%' }}></div>
                            </div>
                          ) : (
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              flexWrap: 'wrap',
                              fontSize: '11px',
                              borderTop: '1px solid var(--border-color)',
                              paddingTop: '8px',
                              marginTop: '4px'
                            }}>
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                whiteSpace: 'nowrap',
                                padding: '2px 8px',
                                borderRadius: '20px',
                                background: 'rgba(255, 255, 255, 0.03)',
                                border: '1px solid var(--border-color)',
                                fontSize: '10px',
                                color: 'var(--text-secondary)'
                              }}>
                                <Icons.Clock /> 
                                {task.metadata?.pub_date 
                                  ? task.metadata.pub_date.substring(0, 10) 
                                  : (task.created_at ? task.created_at.substring(0, 10) : '')}
                              </span>
                              {task.status === 'completed' && (
                                <>
                                  <span style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '3px',
                                    padding: '2px 8px',
                                    borderRadius: '20px',
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    border: '1px solid var(--border-color)',
                                    fontSize: '10px',
                                    color: 'var(--text-secondary)'
                                  }}>
                                    <Icons.ThumbsUp /> {task.like_count}
                                  </span>
                                  <span style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '3px',
                                    padding: '2px 8px',
                                    borderRadius: '20px',
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    border: '1px solid var(--border-color)',
                                    fontSize: '10px',
                                    color: 'var(--text-secondary)'
                                  }}>
                                    <Icons.MessageCircle /> {task.comment_count}
                                  </span>
                                </>
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
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* ==================== PANEL 4: COGNITIVE SANDBOX ==================== */}
          {activeTab === 'sandbox' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', width: '100%', maxWidth: '1100px', margin: '0 auto', paddingBottom: '60px' }}>
              
              {/* ── 顶部组件：时间轴画布标题栏与功能按钮 ── */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ fontSize: '18px', fontWeight: '750', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                      <circle cx="12" cy="12" r="10" />
                      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
                    </svg>
                    认知时间轴画布 (Networked Timeline)
                  </h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
                    您在节目中高亮沉淀的所有卡片都将平铺于此。悬停卡片可直观观察大块脑图中的关联连线。
                  </p>
                </div>
                
                <div style={{ display: 'flex', gap: '12px' }}>
                  {/* 老虎机入口按钮 */}
                  <button 
                    onClick={() => setIsSlotOpen(true)}
                    className="btn-glow" 
                    style={{ 
                      padding: '8px 20px', 
                      fontSize: '13px', 
                      height: '38px', 
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'linear-gradient(135deg, var(--primary), var(--accent))',
                      border: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                      <line x1="3" y1="9" x2="21" y2="9" />
                      <line x1="9" y1="9" x2="9" y2="21" />
                      <line x1="15" y1="9" x2="15" y2="21" />
                    </svg>
                    启动灵感老虎机
                  </button>

                  {/* AI对撞机按钮 */}
                  <button 
                    onClick={handleOpenCollider}
                    disabled={colliderLoading}
                    className="btn-ghost" 
                    style={{ 
                      padding: '8px 18px', 
                      fontSize: '12.5px', 
                      height: '38px', 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      border: '1px solid var(--accent-glow)',
                      color: 'var(--accent)',
                      background: 'var(--accent-glow)'
                    }}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                    启动 AI 强力对撞机
                  </button>
                </div>
              </div>

              {/* 📡 智能认知雷达 (Inspiration Radar Scout) */}
              {(radarScanning || radarSurprise) && (
                <div style={{
                  background: 'linear-gradient(90deg, rgba(224, 175, 104, 0.08) 0%, rgba(255, 158, 100, 0.12) 100%)',
                  border: '1px dashed rgba(224, 175, 104, 0.4)',
                  borderRadius: '12px',
                  padding: '12px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2), 0 0 15px rgba(224, 175, 104, 0.05)',
                  animation: radarSurprise ? 'pulse-glow 3s infinite' : 'none'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '20px', display: 'inline-block', animation: radarScanning ? 'spin 2s linear infinite' : 'bounce-slow 2s infinite' }}>
                      {radarScanning ? '📡' : '⚡'}
                    </span>
                    <div>
                      <h4 style={{ fontSize: '13px', fontWeight: '800', color: '#ffd700', margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {radarScanning ? '认知雷达正在巡航探测深层思维共鸣...' : `认知雷达捕捉：跨界思维奇点已锁定！(异界张力: ${radarSurprise.dissonance_index}%)`}
                      </h4>
                      <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', margin: '4px 0 0 0', lineHeight: '1.4' }}>
                        {radarScanning ? '雷达正在卡片盒中扫描无关联的灵感粒子...' : `系统发现：《${radarSurprise.card_a?.spark_title}》与《${radarSurprise.card_b?.spark_title}》底层映射极强。`}
                      </p>
                    </div>
                  </div>
                  {radarSurprise && (
                    <button 
                      onClick={() => handleTriggerRadarCollider(radarSurprise)}
                      className="btn-glow" 
                      style={{
                        padding: '8px 16px',
                        fontSize: '12px',
                        background: 'linear-gradient(135deg, #ffd700, #ff9e64)',
                        color: '#0d0d15',
                        fontWeight: '800',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        boxShadow: '0 0 10px rgba(255, 215, 0, 0.3)'
                      }}
                    >
                      💥 开启对撞惊喜
                    </button>
                  )}
                </div>
              )}

              {/* 网格画布包容器 */}
              <div 
                ref={gridRef}
                style={{ 
                  position: 'relative', 
                  width: '100%', 
                  backgroundColor: 'rgba(10, 10, 15, 0.25)',
                  backgroundImage: 'radial-gradient(rgba(255, 255, 255, 0.08) 1.2px, transparent 1.2px)',
                  backgroundSize: '24px 24px',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)',
                  minHeight: '480px',
                  padding: '32px 24px',
                  boxShadow: 'inset 0 0 20px rgba(0, 0, 0, 0.4)',
                  overflow: 'hidden'
                }}
              >
                {/* SVG 画布层 */}
                <svg 
                  ref={svgRef}
                  style={{ 
                    position: 'absolute', 
                    top: 0, 
                    left: 0, 
                    width: '100%', 
                    height: '100%', 
                    pointerEvents: 'none', 
                    zIndex: 0 
                  }}
                >
                  <defs>
                    <linearGradient id="gold-neon" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#e0af68" />
                      <stop offset="100%" stopColor="#ff9e64" />
                    </linearGradient>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                  </defs>
                  
                  {svgPaths.map((path) => {
                    const isHovered = hoveredCardId === path.source || hoveredCardId === path.target;
                    
                    return (
                      <g key={path.id}>
                        <path 
                          d={path.d} 
                          fill="none" 
                          stroke={isHovered ? (path.isGold ? 'url(#gold-neon)' : '#73daca') : (path.isGold ? 'rgba(224, 175, 104, 0.25)' : 'rgba(122, 162, 247, 0.12)')} 
                          strokeWidth={isHovered ? 3.5 : 1.5}
                          filter={isHovered ? 'url(#glow)' : 'none'}
                          className={isHovered ? "flow-path" : ""}
                          style={{ 
                            transition: 'stroke 0.3s, stroke-width 0.3s, filter 0.3s',
                            strokeDasharray: !isHovered && path.isGold ? '5,5' : 'none'
                          }}
                        />
                        {isHovered && path.synthesis && (
                          <foreignObject 
                            x={(path.d.match(/M\s+([\d.]+)/)?.[1] * 1 + path.d.match(/,\s+([\d.]+)\s*$/)?.[1] * 1) / 2 - 80 || 100}
                            y={(path.d.match(/M\s+[\d.]+\s+([\d.]+)/)?.[1] * 1 + path.d.match(/,\s+[\d.]+\s+([\d.]+)\s*$/)?.[1] * 1) / 2 - 35 || 100}
                            width="160"
                            height="70"
                          >
                            <div style={{
                              background: 'rgba(18, 18, 24, 0.95)',
                              border: '1px solid #e0af68',
                              borderRadius: '6px',
                              padding: '6px 8px',
                              fontSize: '10px',
                              color: '#e0af68',
                              textAlign: 'center',
                              boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              lineHeight: '1.4'
                            }}>
                              💡 跨界感悟: "{path.synthesis}"
                            </div>
                          </foreignObject>
                        )}
                      </g>
                    );
                  })}
                </svg>

                {/* 卡片实体列表网格 */}
                {sandboxCards.length === 0 ? (
                  <div className="glass-panel" style={{ padding: '80px 20px', textAlign: 'center', color: 'var(--text-muted)', zIndex: 1, position: 'relative' }}>
                    <span style={{ fontSize: '36px' }}>🧭</span>
                    <p style={{ fontSize: '14px', marginTop: '12px' }}>沙盒中目前还没有沉淀任何观点卡牌</p>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>请先打开播客库详情页，鼠标悬停到语义段落上，点击 ⭐ 按钮进行沉淀吧！</p>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '24px', position: 'relative', zIndex: 1 }}>
                    {sandboxCards.map((card) => {
                      const isHoveredSelf = hoveredCardId === card.id;
                      // Determine if we should dim this card:
                      const isAnyCardHovered = hoveredCardId !== null;
                      const isConnected = isAnyCardHovered && cardLinks.some(link => 
                        (link.source_card_id === hoveredCardId && link.target_card_id === card.id) ||
                        (link.target_card_id === hoveredCardId && link.source_card_id === card.id)
                      );
                      const shouldDim = isAnyCardHovered && !isHoveredSelf && !isConnected;

                      return (
                        <CardItem 
                          key={card.id}
                          card={card}
                          shouldDim={shouldDim}
                          isHoveredSelf={isHoveredSelf}
                          setHoveredCardId={setHoveredCardId}
                          setActiveTab={setActiveTab}
                          setActiveTaskId={setActiveTaskId}
                          targetParagraphIdRef={targetParagraphIdRef}
                          handleTimeJump={handleTimeJump}
                        />
                      );
                    })}
                  </div>
                )}
              </div>

              {/* ── 隐藏彩蛋：AI 强力对撞机 Modal ── */}
              <AiColliderModal
                isOpen={!!activeCollider}
                onClose={() => setActiveCollider(null)}
                activeCollider={activeCollider}
                colliderLoading={colliderLoading}
                colliderSynthesis={colliderSynthesis}
                setColliderSynthesis={setColliderSynthesis}
                handleCollideSubmit={handleCollideSubmit}
              />

              {/* ── 🎰 灵感捞取：JUMBO 老虎机 Modal 遮罩层 ── */}
              <SlotMachineModal
                isOpen={isSlotOpen}
                onClose={() => setIsSlotOpen(false)}
                isSpinning={isSpinning}
                spinReelsResolved={spinReelsResolved}
                dueCards={dueCards}
                reviewedCardIds={reviewedCardIds}
                forgottenCardIds={forgottenCardIds}
                leverActive={leverActive}
                triggerLeverPull={triggerLeverPull}
                handleReviewCard={handleReviewCard}
                handleSpinSlotMachine={handleSpinSlotMachine}
                slotTheme={slotTheme}
                setSlotTheme={setSlotTheme}
              />
            </div>
          )}
          {/* ==================== PANEL 2: DETAIL WORKSPACE ==================== */}
          {activeTab === 'detail' && activeTask && (
            <div ref={containerRef} style={{ display: 'flex', flex: '1', height: '100%', minHeight: 0, overflow: 'hidden', position: 'relative', gap: '0' }}>
              {isDragging && (
                <div style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  width: '100vw',
                  height: '100vh',
                  cursor: 'col-resize',
                  zIndex: 9999,
                  background: 'transparent'
                }} />
              )}
              
              {/* 左侧：语音转文字剧本流动 (2指针联动) */}
              <div className="glass-panel" style={{ 
                width: `${leftWidth}%`, 
                display: 'flex', 
                flexDirection: 'column', 
                height: '100%', 
                overflow: 'hidden', 
                flexShrink: 0,
                position: 'relative',
                transition: isDragging ? 'none' : 'var(--transition-smooth)'
              }}>
                <div style={{
                  padding: '12px 20px',
                  borderBottom: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  height: '56px',
                  flexShrink: 0,
                  borderTopLeftRadius: 'var(--radius-md)',
                  borderTopRightRadius: 'var(--radius-md)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)' }}>{t('script_dialogue')}</h3>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>(点击对话行跳转播放)</span>
                  </div>
                  <button 
                    className="btn-ghost" 
                    style={{ padding: '6px 12px', fontSize: '12px', height: '32px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    onClick={() => setShowSpeakerModal(true)}
                  >
                    🗣️ 发言人管理
                  </button>
                </div>

                {(isAudioMissing || activeTask.restoring) && (
                  <div style={{
                    padding: '10px 20px',
                    background: 'rgba(239, 68, 68, 0.15)',
                    borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#f87171',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    flexShrink: 0,
                    zIndex: 15
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>⚠️</span>
                      <span>本地音频文件已丢失。</span>
                    </div>
                    <button 
                      onClick={() => handleRestoreAudio(activeTask.id)}
                      disabled={isRedownloading || activeTask.restoring}
                      style={{
                        background: 'rgba(239, 68, 68, 0.25)',
                        border: '1px solid #f87171',
                        color: '#fff',
                        padding: '4px 10px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: (isRedownloading || activeTask.restoring) ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                      onMouseEnter={(e) => { if(!(isRedownloading || activeTask.restoring)) e.currentTarget.style.background = 'rgba(239, 68, 68, 0.4)'; }}
                      onMouseLeave={(e) => { if(!(isRedownloading || activeTask.restoring)) e.currentTarget.style.background = 'rgba(239, 68, 68, 0.25)'; }}
                    >
                      {(isRedownloading || activeTask.restoring) ? (
                        <>
                          正在下载修复 {activeTask.restore_progress !== undefined ? Math.round(activeTask.restore_progress) : 0}%
                        </>
                      ) : '[点击重新下载修复]'}
                    </button>
                  </div>
                )}

                {/* 发言人昵称管理悬浮卡片 (非全屏阻挡，局部绝对定位) */}
                {showSpeakerModal && (
                  <div className="glass-panel" style={{
                    position: 'absolute',
                    top: '56px',
                    right: '16px',
                    width: '340px',
                    maxHeight: 'calc(100% - 72px)',
                    background: 'var(--bg-surface)',
                    backdropFilter: 'blur(30px)',
                    WebkitBackdropFilter: 'blur(30px)',
                    border: '1px solid var(--border-hover)',
                    borderRadius: '12px',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
                    zIndex: 100,
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '16px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                      <h3 style={{ fontSize: '13.5px', fontWeight: '700', color: 'var(--text-primary)' }}>
                        🗣️ 发言人昵称管理
                      </h3>
                      <button 
                        className="btn-ghost" 
                        style={{ padding: '2px 6px', fontSize: '11px', border: 'none', background: 'transparent' }}
                        onClick={() => setShowSpeakerModal(false)}
                      >
                        ✕
                      </button>
                    </div>
                    
                    <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '12px' }}>
                      修改节目中识别出的发言人昵称。修改后将实时更新。
                    </p>
                    
                    <div style={{ flex: '1', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '2px' }}>
                      {getUniqueSpeakers().length === 0 ? (
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', padding: '10px 0' }}>暂无发言人数据</p>
                      ) : (
                        getUniqueSpeakers().map((spId) => {
                          const currentName = formatSpeakerName(spId, activeTask.speaker_mappings);
                          const isEditing = panelRenamingSpeakerId === spId;
                          
                          return (
                            <div key={spId} style={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'space-between',
                              background: 'rgba(255,255,255,0.01)', 
                              border: '1px solid var(--border-color)', 
                              borderRadius: '8px', 
                              padding: '8px 10px' 
                            }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: '1', marginRight: '8px' }}>
                                <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>系统标识: {spId.startsWith('SPEAKER_') ? `声音 ${parseInt(spId.replace('SPEAKER_', ''), 10) + 1}` : spId}</span>
                                {!isEditing ? (
                                  <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: '600' }}>{currentName}</span>
                                ) : (
                                  <input 
                                    type="text" 
                                    value={panelRenameValue}
                                    onChange={(e) => setPanelRenameValue(e.target.value)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter') handleRenameSpeakerPanel(spId);
                                      if (e.key === 'Escape') setPanelRenamingSpeakerId(null);
                                    }}
                                    className="glass-input"
                                    style={{ padding: '2px 8px', fontSize: '12px', width: '100%' }}
                                    autoFocus
                                  />
                                )}
                              </div>
                              
                              <div style={{ display: 'flex', gap: '4px' }}>
                                {!isEditing ? (
                                  <button 
                                    className="btn-ghost" 
                                    style={{ padding: '4px 8px', fontSize: '11px' }}
                                    onClick={() => {
                                      setPanelRenamingSpeakerId(spId);
                                      setPanelRenameValue(currentName);
                                    }}
                                  >
                                    编辑
                                  </button>
                                ) : (
                                  <>
                                    <button 
                                      className="btn-glow" 
                                      style={{ padding: '4px 8px', fontSize: '11px', background: 'var(--success)' }}
                                      onClick={() => handleRenameSpeakerPanel(spId)}
                                    >
                                      保存
                                    </button>
                                    <button 
                                      className="btn-ghost" 
                                      style={{ padding: '4px 8px', fontSize: '11px' }}
                                      onClick={() => {
                                        setPanelRenamingSpeakerId(null);
                                        setPanelRenameValue('');
                                      }}
                                    >
                                      取消
                                    </button>
                                  </>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                )}
                
                {/* 剧本对话渲染区 */}
                <div style={{ flex: '1', overflowY: 'auto', padding: '20px' }}>
                  {activeTask.paragraphs && activeTask.paragraphs.length > 0 ? (
                    <div className="dialogue-container">
                      {activeTask.paragraphs.map((para, idx) => {
                        const isPlayingLine = currentTime >= para.start_time && currentTime <= para.end_time;
                        const speakerName = formatSpeakerName(para.speaker, activeTask.speaker_mappings);
                        
                        return (
                          <div 
                            key={para.id} 
                            id={para.id}
                            onMouseEnter={() => setHoveredParagraphId(para.id)}
                            onMouseLeave={() => setHoveredParagraphId(null)}
                            onClick={() => handleTimeJump(para.start_time)}
                            className={`dialogue-bubble dialogue-bubble-para ${isPlayingLine ? 'active-playing' : ''}`}
                            style={{ 
                              position: 'relative',
                              padding: '12px',
                              paddingRight: '45px',
                              cursor: 'pointer',
                              transition: 'border 0.2s, box-shadow 0.2s',
                              borderRadius: '8px',
                              marginBottom: '10px'
                            }}
                          >
                            <div className="dialogue-meta" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                <span className="speaker-badge" style={{ background: 'var(--border-hover)', color: 'var(--text-primary)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                                  {speakerName}
                                </span>
                                {hoveredParagraphId === para.id && (
                                  <span className="fade-in" style={{ fontSize: '12px', color: 'var(--primary)', display: 'flex', alignItems: 'center', marginLeft: '4px' }}>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                                    <span style={{ marginLeft: '4px', fontSize: '11px', fontWeight: '500' }}>点击从头播放此段落</span>
                                  </span>
                                )}
                              </div>
                              <span className="time-stamp" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                                {(() => {
                                  const startMin = Math.floor(para.start_time / 60);
                                  const startSec = Math.floor(para.start_time % 60);
                                  const startHour = Math.floor(startMin / 60);
                                  const minRem = startMin % 60;
                                  return `[${startHour.toString().padStart(2, '0')}:${minRem.toString().padStart(2, '0')}:${startSec.toString().padStart(2, '0')}]`;
                                })()}
                              </span>
                            </div>
                            <div className="dialogue-text" style={{ fontSize: '13.5px', color: 'var(--text-primary)', lineHeight: '1.6', wordBreak: 'break-all' }}>
                              {para.sentences && para.sentences.length > 0 ? (
                                para.sentences.map((sentence, sIdx) => {
                                  const isPlayingSentence = currentTime >= sentence.start && currentTime <= sentence.end;
                                  return (
                                    <span 
                                      key={sIdx}
                                      className={`sentence-span ${isPlayingSentence ? 'active-sentence' : ''}`}
                                      style={{
                                        padding: '1px 3px',
                                        borderRadius: '4px',
                                        background: isPlayingSentence ? 'rgba(122, 162, 247, 0.22)' : 'transparent',
                                        color: isPlayingSentence ? 'var(--primary)' : 'inherit',
                                        transition: 'background 0.2s, color 0.2s',
                                        marginRight: '4px',
                                        display: 'inline',
                                      }}
                                    >
                                      {sentence.text}
                                    </span>
                                  );
                                })
                              ) : (
                                para.content
                              )}
                            </div>
                            
                            {/* 一键沉淀星号图标 (鼠标 Hover 时显现) */}
                            <button
                              className="sediment-star-btn btn-ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSedimentParagraph(para.id, activeTask.id);
                              }}
                              style={{
                                position: 'absolute',
                                right: '12px',
                                top: '50%',
                                transform: 'translateY(-50%)',
                                padding: '6px',
                                border: 'none',
                                background: 'transparent',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                zIndex: 10,
                                color: para.sedimented ? 'var(--warning)' : 'var(--text-muted)'
                              }}
                            >
                              {para.sedimented ? (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--warning)" stroke="var(--warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                              ) : (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                              )}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  ) : activeTask.transcript && activeTask.transcript.length > 0 ? (
                    <div className="dialogue-container">
                      {activeTask.transcript.map((seg, idx) => {
                        const isPlayingLine = currentTime >= seg.start && currentTime <= seg.end;
                        const speakerName = formatSpeakerName(seg.speaker, activeTask.speaker_mappings);
                        
                        return (
                          <div 
                            key={idx} 
                            ref={isPlayingLine ? activeBubbleRef : null}
                            onClick={() => handleTimeJump(seg.start)}
                            className={`dialogue-bubble ${isPlayingLine ? 'active-playing' : ''}`}
                            style={{ padding: '12px', marginBottom: '10px', borderRadius: '8px', cursor: 'pointer' }}
                          >
                            <div className="dialogue-meta" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                <span className="speaker-badge" style={{ background: 'var(--border-hover)', color: 'var(--text-primary)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                                  {speakerName}
                                </span>
                              </div>
                              <span className="time-stamp" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{seg.timestamp_str}</span>
                            </div>
                            <div className="dialogue-text" style={{ fontSize: '13.5px', color: 'var(--text-primary)', lineHeight: '1.6', wordBreak: 'break-all' }}>{seg.text}</div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      {activeTask.status !== 'completed' && activeTask.status !== 'failed' ? (
                        <div>
                          <p style={{ fontSize: '14px' }}>{t('script_loading')}</p>
                          <p style={{ fontSize: '12px', marginTop: '6px' }}>{t('script_loading_sub')}</p>
                        </div>
                      ) : (
                        <p>{t('script_empty')}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* 可拖拽的分隔条 */}
              <div 
                onMouseDown={handleMouseDown}
                style={{
                  width: '16px',
                  cursor: 'col-resize',
                  alignSelf: 'stretch',
                  position: 'relative',
                  zIndex: '10',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  userSelect: 'none',
                  flexShrink: 0
                }}
              >
                <div style={{
                  width: '2px',
                  height: '40px',
                  borderRadius: '1px',
                  background: isDragging ? 'var(--primary)' : 'var(--border-color)',
                  transition: 'background 0.2s'
                }} />
              </div>

              {/* 右侧：总结报告与元数据评论 (三栏切换) */}
              <div className="glass-panel" style={{ 
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column', 
                height: '100%', 
                overflow: 'hidden',
                transition: isDragging ? 'none' : 'var(--transition-smooth)'
              }}>
                {/* 选项卡栏 */}
                <div style={{
                  display: 'flex',
                  borderBottom: '1px solid var(--border-color)',
                  flexShrink: 0,
                  borderTopLeftRadius: 'var(--radius-md)',
                  borderTopRightRadius: 'var(--radius-md)',
                  overflow: 'hidden'
                }}>
                  <button 
                    onClick={() => setDetailSubTab('summary')}
                    style={{ 
                      flex: '1', 
                      background: 'transparent', 
                      border: 'none', 
                      padding: '16px', 
                      color: detailSubTab === 'summary' ? 'var(--primary)' : 'var(--text-secondary)',
                      fontWeight: detailSubTab === 'summary' ? '700' : '500',
                      borderBottom: detailSubTab === 'summary' ? '2px solid var(--primary)' : 'none',
                      cursor: 'pointer'
                    }}
                  >
                    {t('ai_report')}
                  </button>
                  <button 
                    onClick={() => setDetailSubTab('shownotes')}
                    style={{ 
                      flex: '1', 
                      background: 'transparent', 
                      border: 'none', 
                      padding: '16px', 
                      color: detailSubTab === 'shownotes' ? 'var(--primary)' : 'var(--text-secondary)',
                      fontWeight: detailSubTab === 'shownotes' ? '700' : '500',
                      borderBottom: detailSubTab === 'shownotes' ? '2px solid var(--primary)' : 'none',
                      cursor: 'pointer'
                    }}
                  >
                    节目简介
                  </button>
                  <button 
                    onClick={() => setDetailSubTab('comments')}
                    style={{ 
                      flex: '1', 
                      background: 'transparent', 
                      border: 'none', 
                      padding: '16px', 
                      color: detailSubTab === 'comments' ? 'var(--primary)' : 'var(--text-secondary)',
                      fontWeight: detailSubTab === 'comments' ? '700' : '500',
                      borderBottom: detailSubTab === 'comments' ? '2px solid var(--primary)' : 'none',
                      cursor: 'pointer'
                    }}
                  >
                    听友热评 ({activeTask.metadata?.comments?.length || 0})
                  </button>
                </div>

                <div style={{ flex: '1', overflowY: 'auto', padding: '24px' }}>
                  
                  {/* SUBTAB 1: AI Summary Markdown */}
                  {detailSubTab === 'summary' && (
                    <div>
                      {activeTask.status === 'summarizing' && (
                        <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
                          <p style={{ fontWeight: '500' }}>🤖 {t('summarizing')}</p>
                          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>{t('summarizing_sub')}</p>
                        </div>
                      )}
                      
                      {activeTask.status !== 'summarizing' && (
                        <div>
                          {/* 刷新总结按钮 */}
                          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
                            <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px' }} onClick={handleRegenerateSummary}>
                              <Icons.Refresh /> {t('regenerate_summary')}
                            </button>
                          </div>
                          
                          <MarkdownRenderer text={activeTask.summary} />
                          
                          {activeTask.metadata?.time_stats && (
                            <div style={{
                              background: 'rgba(255,255,255,0.02)',
                              border: '1px solid var(--border-color)',
                              borderRadius: '12px',
                              padding: '16px',
                              fontSize: '13px',
                              color: 'var(--text-secondary)',
                              marginTop: '24px'
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
                                <span style={{ fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  ⏱️ 分析用时统计
                                </span>
                                <span style={{ color: 'var(--primary)', fontWeight: '700' }}>
                                  总用时: {(() => {
                                    const total = activeTask.metadata.time_stats.total_time;
                                    if (total < 60) return `${total}秒`;
                                    const m = Math.floor(total / 60);
                                    const s = Math.round(total % 60);
                                    return `${m}分${s}秒`;
                                  })()}
                                </span>
                              </div>
                              <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(1, 1fr)',
                                gap: '8px'
                              }}>
                                {(() => {
                                  const stepNames = {
                                    downloading: '1. 播客下载与元数据解析',
                                    preprocessing: '2. 音频预处理 (重采样混合)',
                                    diarization: '3. PyAnnote 声纹角色分割',
                                    transcribing: '4. Whisper 语音识别与时间轴对齐',
                                    chunking: '5. 语义段落聚合',
                                    embeddings_and_renaming: '6. 声纹特征提取与智能改名',
                                    interjection_labelling: '7. 语气词发言人过滤',
                                    summarizing: '8. AI 总结报告生成'
                                  };
                                  return Object.entries(activeTask.metadata.time_stats.steps || {}).map(([key, val]) => {
                                    const formattedVal = (() => {
                                      if (val < 60) return `${val}秒`;
                                      const m = Math.floor(val / 60);
                                      const s = Math.round(val % 60);
                                      return `${m}分${s}秒`;
                                    })();
                                    return (
                                      <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{stepNames[key] || key}</span>
                                        <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{formattedVal}</span>
                                      </div>
                                    );
                                  });
                                })()}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* SUBTAB 2: Shownotes */}
                  {detailSubTab === 'shownotes' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '18px' }}>🎙️</span>
                          <h3 style={{ fontSize: '15px', color: 'var(--text-primary)', fontWeight: '700' }}>单集节目简介</h3>
                        </div>
                        {activeTask.url && (
                          <button 
                            className="btn-ghost" 
                            style={{ fontSize: '12px', padding: '6px 12px' }} 
                            onClick={handleRefreshMetadata}
                            disabled={isRefreshingMetadata}
                          >
                            <Icons.Refresh className={isRefreshingMetadata ? "spin-animation" : ""} /> {isRefreshingMetadata ? "正在刷新..." : "刷新数据"}
                          </button>
                        )}
                      </div>
                      <div style={{ 
                        background: 'rgba(255,255,255,0.01)', 
                        border: '1px solid var(--border-color)', 
                        borderRadius: '12px', 
                        padding: '24px', 
                        fontSize: '14px', 
                        color: 'var(--text-secondary)',
                        lineHeight: '1.8',
                        letterSpacing: '0.2px'
                      }}>
                        <ShownotesRenderer text={activeTask.metadata?.shownotes} onTimeJump={handleTimeJump} />
                      </div>
                    </div>
                  )}

                  {/* SUBTAB 3: Comments */}
                  {detailSubTab === 'comments' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '18px' }}>💬</span>
                          <h3 style={{ fontSize: '15px', color: 'var(--text-primary)', fontWeight: '700' }}>听友热门评论</h3>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>共计 {activeTask.metadata?.comments?.length || 0} 条精彩留言</span>
                          {activeTask.url && (
                            <button 
                              className="btn-ghost" 
                              style={{ fontSize: '12px', padding: '6px 12px' }} 
                              onClick={handleRefreshMetadata}
                              disabled={isRefreshingMetadata}
                            >
                              <Icons.Refresh className={isRefreshingMetadata ? "spin-animation" : ""} /> {isRefreshingMetadata ? "正在刷新..." : "刷新数据"}
                            </button>
                          )}
                        </div>
                      </div>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {activeTask.metadata?.comments && activeTask.metadata.comments.length > 0 ? (
                          activeTask.metadata.comments.map((comment, cIdx) => {
                            const hasManyLikes = comment.likes >= 20;
                            return (
                              <div 
                                key={cIdx} 
                                className="glass-panel" 
                                style={{ 
                                  padding: '16px 20px',
                                  borderRadius: '12px',
                                  border: hasManyLikes ? '1px solid rgba(224, 175, 104, 0.25)' : '1px solid var(--border-color)',
                                  background: hasManyLikes ? 'rgba(224, 175, 104, 0.02)' : 'rgba(255, 255, 255, 0.01)',
                                  boxShadow: 'none',
                                  transition: 'transform 0.2s, border-color 0.2s'
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div style={{
                                      width: '24px',
                                      height: '24px',
                                      borderRadius: '50%',
                                      background: hasManyLikes ? 'linear-gradient(135deg, var(--warning), var(--accent))' : 'linear-gradient(135deg, var(--primary), var(--accent))',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      fontSize: '11px',
                                      fontWeight: '700',
                                      color: '#fff'
                                    }}>
                                      {comment.author ? comment.author.charAt(0).toUpperCase() : 'U'}
                                    </div>
                                    <span style={{ color: 'var(--text-primary)', fontWeight: '600', fontSize: '13px' }}>{comment.author}</span>
                                  </div>
                                  <span style={{ 
                                    color: hasManyLikes ? 'var(--warning)' : 'var(--text-secondary)', 
                                    display: 'inline-flex', 
                                    alignItems: 'center', 
                                    gap: '4px',
                                    fontSize: '12px',
                                    fontWeight: '500'
                                  }}>
                                    <Icons.ThumbsUp /> {comment.likes}
                                  </span>
                                </div>
                                <div style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.6', paddingLeft: '32px' }}>
                                  <CommentRenderer text={comment.content} onTimeJump={handleTimeJump} />
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                            <p style={{ fontSize: '13.5px' }}>暂无评论数据（可能非小宇宙链接）</p>
                          </div>
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
            <div style={{ display: 'flex', gap: '24px', alignItems: 'stretch', width: '100%' }}>

              {/* ── Left Sidebar Navigation ── */}
              <div style={{
                width: '230px',
                flexShrink: 0,
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                position: 'sticky',
                top: '24px',
                alignSelf: 'flex-start',
                background: 'var(--bg-surface)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                boxShadow: '0 10px 30px -10px rgba(0, 0, 0, 0.7)',
                minHeight: '400px'
              }}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  letterSpacing: '0.12em',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  padding: '4px 8px 10px 8px',
                  borderBottom: '1px solid var(--border-color)',
                  marginBottom: '8px'
                }}>{t('sys_config_header')}</div>
                {[
                  { id: 'llm',     icon: '✨', label: 'AI 总结',    desc: 'LLM 模型与 Prompt' },
                  { id: 'asr',     icon: '🎙️', label: '语音转录',   desc: 'ASR 引擎配置' },
                  { id: 'notifications', icon: '✉️', label: '消息通知', desc: 'SMTP 邮件推送' },
                  { id: 'general', icon: '🎨', label: '外观与语言', desc: '主题、配色、语言' },
                ].map(tab => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setConfigSubTab(tab.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 14px',
                      borderRadius: '10px',
                      border: configSubTab === tab.id ? '1px solid var(--primary)' : '1px solid transparent',
                      background: configSubTab === tab.id ? 'var(--primary-glow)' : 'rgba(255,255,255,0.02)',
                      color: configSubTab === tab.id ? 'var(--primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s ease',
                      width: '100%',
                    }}
                    onMouseEnter={e => { if (configSubTab !== tab.id) e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
                    onMouseLeave={e => { if (configSubTab !== tab.id) e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; }}
                  >
                    <span style={{ fontSize: '18px', flexShrink: 0 }}>{tab.icon}</span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'hidden' }}>
                      <span style={{ fontSize: '13px', fontWeight: configSubTab === tab.id ? '700' : '600', whiteSpace: 'nowrap' }}>{tab.label}</span>
                      <span style={{ fontSize: '10.5px', color: configSubTab === tab.id ? 'var(--primary)' : 'var(--text-muted)', opacity: 0.9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{tab.desc}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* ── Right Content Panel ── */}
              <div className="glass-panel" style={{ flex: 1, minWidth: 0, padding: '24px', position: 'relative' }}>
              <form id="settings-form" onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>

                {/* Horizontal Save & Auto-Save Control Bar */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '16px',
                  borderBottom: '1px solid var(--border-color)',
                  marginBottom: '10px',
                  flexWrap: 'wrap',
                  gap: '16px'
                }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {configSubTab === 'general' && <>🎨外观与语言</>}
                      {configSubTab === 'asr' && <>🎙️语音转录</>}
                      {configSubTab === 'llm' && <>✨AI 总结</>}
                      {configSubTab === 'notifications' && <>✉️消息通知</>}
                    </h3>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                      <input
                        type="checkbox"
                        checked={autoSaveEnabled}
                        onChange={(e) => setAutoSaveEnabled(e.target.checked)}
                        style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                      />
                      <span>{t('auto_save_chk')}</span>
                    </label>

                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '500', minHeight: '16px', display: 'inline-block' }}>
                      {saveStatus === 'saving' && t('save_status_saving')}
                      {saveStatus === 'saved' && t('save_status_saved')}
                      {saveStatus === 'unsaved' && (autoSaveEnabled ? t('save_status_unsaved') : t('save_status_unsaved_manual'))}
                      {saveStatus === 'error' && t('save_status_error')}
                    </span>

                    {!autoSaveEnabled && (
                      <button 
                        type="submit" 
                        form="settings-form"
                        className="btn-glow" 
                        style={{ padding: '6px 16px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        <Icons.Check /> {t('save_btn')}
                      </button>
                    )}
                  </div>
                </div>

                {/* 0. 外观与语言设置 (Appearance & Language Settings) */}
                {configSubTab === 'general' && (
                  <div className="settings-container">
                    
                    {/* Theme Preference Settings Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">{t('theme_appearance')}</h3>
                        <p className="settings-card-subtitle">{t('theme_sub')}</p>
                      </div>

                      {/* Display Mode Settings Row */}
                      <div className="settings-row">
                        <div className="settings-row-info">
                          <span className="settings-row-title">{t('display_mode')}</span>
                          <span className="settings-row-desc">{t('display_mode_sub')}</span>
                        </div>
                        <select
                          value={themeMode}
                          onChange={(e) => setThemeMode(e.target.value)}
                          className="glass-input"
                          style={{ width: '160px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', color: 'var(--text-primary)' }}
                        >
                          <option value="light" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>Light (浅色)</option>
                          <option value="dark" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>Dark (深色)</option>
                          <option value="system" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>System (跟随系统)</option>
                        </select>
                      </div>

                      {/* Light & Dark Theme Presets Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '10px' }}>
                        {/* Light Theme Sub-card */}
                        <div style={{
                          background: 'rgba(255, 255, 255, 0.015)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '12px',
                          padding: '16px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px'
                        }}>
                          <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: '600', margin: 0 }}>
                            {t('light_theme_title')}
                          </h4>
                          
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>{t('preset')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <button 
                                type="button"
                                onClick={() => setLightTheme(PRESETS.light[lightPresetName])}
                                title="重置为当前预设默认颜色"
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: 'var(--text-secondary)',
                                  cursor: 'pointer',
                                  padding: '4px',
                                  fontSize: '15px',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  transition: 'color 0.2s'
                                }}
                              >
                                ↶
                              </button>
                              <select
                                value={lightPresetName}
                                onChange={(e) => {
                                  const name = e.target.value;
                                  setLightPresetName(name);
                                  setLightTheme(PRESETS.light[name]);
                                }}
                                className="glass-input"
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px', background: 'rgba(0,0,0,0.3)', color: 'var(--text-primary)' }}
                              >
                                {Object.keys(PRESETS.light).map(k => (
                                  <option key={k} value={k} style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>{k}</option>
                                ))}
                              </select>
                            </div>
                          </div>

                          {/* Light Background Color */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t('bg_color')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                backgroundColor: lightTheme.background,
                                border: '1px solid rgba(255,255,255,0.15)',
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'hidden'
                              }}>
                                <input 
                                  type="color" 
                                  value={lightTheme.background} 
                                  onChange={(e) => setLightTheme({ ...lightTheme, background: e.target.value })} 
                                  style={{
                                    position: 'absolute',
                                    top: '-5px',
                                    left: '-5px',
                                    width: '34px',
                                    height: '34px',
                                    opacity: 0,
                                    cursor: 'pointer'
                                  }} 
                                />
                              </div>
                              <input 
                                type="text" 
                                value={lightTheme.background} 
                                onChange={(e) => setLightTheme({ ...lightTheme, background: e.target.value })}
                                className="glass-input" 
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px' }} 
                              />
                            </div>
                          </div>

                          {/* Light Foreground Color */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t('fg_color')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                backgroundColor: lightTheme.foreground,
                                border: '1px solid rgba(255,255,255,0.15)',
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'hidden'
                              }}>
                                <input 
                                  type="color" 
                                  value={lightTheme.foreground} 
                                  onChange={(e) => setLightTheme({ ...lightTheme, foreground: e.target.value })} 
                                  style={{
                                    position: 'absolute',
                                    top: '-5px',
                                    left: '-5px',
                                    width: '34px',
                                    height: '34px',
                                    opacity: 0,
                                    cursor: 'pointer'
                                  }} 
                                />
                              </div>
                              <input 
                                type="text" 
                                value={lightTheme.foreground} 
                                onChange={(e) => setLightTheme({ ...lightTheme, foreground: e.target.value })}
                                className="glass-input" 
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px' }} 
                              />
                            </div>
                          </div>

                          {/* Light Accent Color */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t('accent_color')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                backgroundColor: lightTheme.accent,
                                border: '1px solid rgba(255,255,255,0.15)',
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'hidden'
                              }}>
                                <input 
                                  type="color" 
                                  value={lightTheme.accent} 
                                  onChange={(e) => setLightTheme({ ...lightTheme, accent: e.target.value })} 
                                  style={{
                                    position: 'absolute',
                                    top: '-5px',
                                    left: '-5px',
                                    width: '34px',
                                    height: '34px',
                                    opacity: 0,
                                    cursor: 'pointer'
                                  }} 
                                />
                              </div>
                              <input 
                                type="text" 
                                value={lightTheme.accent} 
                                onChange={(e) => setLightTheme({ ...lightTheme, accent: e.target.value })}
                                className="glass-input" 
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px' }} 
                              />
                            </div>
                          </div>
                        </div>

                        {/* Dark Theme Sub-card */}
                        <div style={{
                          background: 'rgba(255, 255, 255, 0.015)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '12px',
                          padding: '16px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px'
                        }}>
                          <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: '600', margin: 0 }}>
                            {t('dark_theme_title')}
                          </h4>
                          
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>{t('preset')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <button 
                                type="button"
                                onClick={() => setDarkTheme(PRESETS.dark[darkPresetName])}
                                title="重置为当前预设默认颜色"
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: 'var(--text-secondary)',
                                  cursor: 'pointer',
                                  padding: '4px',
                                  fontSize: '15px',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  transition: 'color 0.2s'
                                }}
                              >
                                ↶
                              </button>
                              <select
                                value={darkPresetName}
                                onChange={(e) => {
                                  const name = e.target.value;
                                  setDarkPresetName(name);
                                  setDarkTheme(PRESETS.dark[name]);
                                }}
                                className="glass-input"
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px', background: 'rgba(0,0,0,0.3)', color: 'var(--text-primary)' }}
                              >
                                {Object.keys(PRESETS.dark).map(k => (
                                  <option key={k} value={k} style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>{k}</option>
                                ))}
                              </select>
                            </div>
                          </div>

                          {/* Dark Background Color */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t('bg_color')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                backgroundColor: darkTheme.background,
                                border: '1px solid rgba(255,255,255,0.15)',
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'hidden'
                              }}>
                                <input 
                                  type="color" 
                                  value={darkTheme.background} 
                                  onChange={(e) => setDarkTheme({ ...darkTheme, background: e.target.value })} 
                                  style={{
                                    position: 'absolute',
                                    top: '-5px',
                                    left: '-5px',
                                    width: '34px',
                                    height: '34px',
                                    opacity: 0,
                                    cursor: 'pointer'
                                  }} 
                                />
                              </div>
                              <input 
                                type="text" 
                                value={darkTheme.background} 
                                onChange={(e) => setDarkTheme({ ...darkTheme, background: e.target.value })}
                                className="glass-input" 
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px' }} 
                              />
                            </div>
                          </div>

                          {/* Dark Foreground Color */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t('fg_color')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                backgroundColor: darkTheme.foreground,
                                border: '1px solid rgba(255,255,255,0.15)',
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'hidden'
                              }}>
                                <input 
                                  type="color" 
                                  value={darkTheme.foreground} 
                                  onChange={(e) => setDarkTheme({ ...darkTheme, foreground: e.target.value })} 
                                  style={{
                                    position: 'absolute',
                                    top: '-5px',
                                    left: '-5px',
                                    width: '34px',
                                    height: '34px',
                                    opacity: 0,
                                    cursor: 'pointer'
                                  }} 
                                />
                              </div>
                              <input 
                                type="text" 
                                value={darkTheme.foreground} 
                                onChange={(e) => setDarkTheme({ ...darkTheme, foreground: e.target.value })}
                                className="glass-input" 
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px' }} 
                              />
                            </div>
                          </div>

                          {/* Dark Accent Color */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t('accent_color')}</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                backgroundColor: darkTheme.accent,
                                border: '1px solid rgba(255,255,255,0.15)',
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'hidden'
                              }}>
                                <input 
                                  type="color" 
                                  value={darkTheme.accent} 
                                  onChange={(e) => setDarkTheme({ ...darkTheme, accent: e.target.value })} 
                                  style={{
                                    position: 'absolute',
                                    top: '-5px',
                                    left: '-5px',
                                    width: '34px',
                                    height: '34px',
                                    opacity: 0,
                                    cursor: 'pointer'
                                  }} 
                                />
                              </div>
                              <input 
                                type="text" 
                                value={darkTheme.accent} 
                                onChange={(e) => setDarkTheme({ ...darkTheme, accent: e.target.value })}
                                className="glass-input" 
                                style={{ flex: 1, padding: '6px 10px', fontSize: '12.5px' }} 
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Language Settings Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">{t('language_setting')}</h3>
                        <p className="settings-card-subtitle">{t('language_setting_sub')}</p>
                      </div>
                      
                      <div className="settings-row">
                        <div className="settings-row-info">
                          <span className="settings-row-title">{t('select_lang')}</span>
                        </div>
                        <select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="glass-input"
                          style={{ width: '160px', padding: '8px 12px', background: 'rgba(0,0,0,0.35)', color: 'var(--text-primary)' }}
                        >
                          <option value="zh-CN" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>简体中文</option>
                          <option value="zh-TW" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>繁體中文</option>
                          <option value="en-US" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>English</option>
                          <option value="ja-JP" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>日本語</option>
                        </select>
                      </div>
                    </div>

                  </div>
                )}

                {/* 1. 🎙️ 语音转录与分轨配置 (ASR Engine) */}
                {configSubTab === 'asr' && (
                  <div className="settings-container">
                    
                    {/* ASR Mode Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">{t('tab_asr')}</h3>
                        <p className="settings-card-subtitle">配置您默认使用的转录模式与前置依赖路径</p>
                      </div>
                      
                      <div className="settings-row">
                        <div className="settings-row-info">
                          <span className="settings-row-title">默认转录模式 (Default ASR Mode)</span>
                          <span className="settings-row-desc">可选择本地离线大模型或第三方高精兼容在线接口</span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button 
                            type="button"
                            onClick={() => updateConfigField('asr_mode', 'local')}
                            style={{
                              padding: '8px 16px',
                              borderRadius: '6px',
                              border: configData.asr_mode === 'local' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                              background: configData.asr_mode === 'local' ? 'var(--primary-glow)' : 'rgba(0,0,0,0.25)',
                              color: configData.asr_mode === 'local' ? 'var(--primary)' : 'var(--text-secondary)',
                              cursor: 'pointer',
                              fontWeight: '600',
                              fontSize: '12.5px',
                              transition: 'all 0.2s'
                            }}
                          >
                            💻 {t('local_trans')}
                          </button>
                          <button 
                            type="button"
                            onClick={() => updateConfigField('asr_mode', 'online')}
                            style={{
                              padding: '8px 16px',
                              borderRadius: '6px',
                              border: configData.asr_mode === 'online' ? '1px solid var(--accent)' : '1px solid var(--border-color)',
                              background: configData.asr_mode === 'online' ? 'var(--accent-glow)' : 'rgba(0,0,0,0.25)',
                              color: configData.asr_mode === 'online' ? 'var(--accent)' : 'var(--text-secondary)',
                              cursor: 'pointer',
                              fontWeight: '600',
                              fontSize: '12.5px',
                              transition: 'all 0.2s'
                            }}
                          >
                            🌐 {t('online_trans')}
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Pre-dependencies Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">🛠️ 存储与前置依赖 (Storage & Dependencies)</h3>
                        <p className="settings-card-subtitle">配置外挂存储路径以及底层运行库参数</p>
                      </div>

                      <div className="settings-field" style={{ marginBottom: '16px' }}>
                        <label className="settings-field-label">📁 外挂存储目录 (可选)</label>
                        <input 
                          type="text" 
                          placeholder="例如: D:\WhisperData (默认存放在系统根目录)"
                          value={configData.custom_storage_dir || ''} 
                          onChange={(e) => updateConfigField('custom_storage_dir', e.target.value)}
                          className="glass-input" 
                        />
                        <p className="settings-field-desc">留空则默认使用项目内部文件夹。设置后，所有下载的音频与转录数据将存放于此，方便打包发布系统本身。</p>
                      </div>

                      <div className="settings-grid">
                        <div className="settings-field">
                          <label className="settings-field-label">{t('ffmpeg_exe_path')}</label>
                          <input 
                            type="text" 
                            value={configData.ffmpeg_path} 
                            onChange={(e) => updateConfigField('ffmpeg_path', e.target.value)}
                            className="glass-input" 
                          />
                        </div>
                        
                        <div className="settings-field">
                          <label className="settings-field-label">{t('ffmpeg_bin_dir')}</label>
                          <input 
                            type="text" 
                            value={configData.ffmpeg_bin_dir} 
                            onChange={(e) => updateConfigField('ffmpeg_bin_dir', e.target.value)}
                            className="glass-input" 
                          />
                        </div>
                      </div>

                      <div className="settings-field" style={{ borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '16px' }}>
                        <label className="settings-field-label">{t('hf_token_lbl')}</label>
                        <input 
                          type="password" 
                          placeholder={t('hf_token_placeholder')}
                          value={configData.hf_token} 
                          onChange={(e) => updateConfigField('hf_token', e.target.value)}
                          className="glass-input" 
                        />
                        <p className="settings-field-desc">{t('hf_token_sub')}</p>
                      </div>
                    </div>

                    {/* ASR Parameters Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">🔌 ASR 引擎详细参数</h3>
                        <p className="settings-card-subtitle">
                          {configData.asr_mode === 'local' ? '配置本地 Faster-Whisper 转录参数' : '配置在线 ASR API 兼容转录参数'}
                        </p>
                      </div>

                      {configData.asr_mode === 'local' ? (
                        <div className="settings-field">
                          <label className="settings-field-label">{t('whisper_path')}</label>
                          <input 
                            type="text" 
                            value={configData.local_whisper_model_path} 
                            onChange={(e) => updateConfigField('local_whisper_model_path', e.target.value)}
                            className="glass-input" 
                          />
                        </div>
                      ) : (
                        <div className="settings-grid">
                          <div className="settings-field">
                            <label className="settings-field-label">{t('mimo_key_lbl')}</label>
                            <input 
                              type="password" 
                              placeholder={t('mimo_key_placeholder')}
                              value={configData.online_api_key || ''} 
                              onChange={(e) => updateConfigField('online_api_key', e.target.value)}
                              className="glass-input" 
                            />
                          </div>
                          
                          <div className="settings-field">
                            <label className="settings-field-label">{t('mimo_url_lbl')}</label>
                            <input 
                              type="text" 
                              placeholder="默认: https://token-plan-sgp.xiaomimimo.com/v1"
                              value={configData.online_base_url || ''} 
                              onChange={(e) => updateConfigField('online_base_url', e.target.value)}
                              className="glass-input" 
                            />
                          </div>

                          <div className="settings-field" style={{ gridColumn: 'span 2' }}>
                            <label className="settings-field-label">{t('mimo_model_lbl')}</label>
                            <input 
                              type="text" 
                              placeholder="默认: mimo-v2.5-asr"
                              value={configData.online_model || ''} 
                              onChange={(e) => updateConfigField('online_model', e.target.value)}
                              className="glass-input" 
                            />
                          </div>
                        </div>
                      )}
                    </div>

                  </div>
                )}

                {/* 2. 📝 AI 总结与文本分析引擎 (LLM Engine) */}
                {configSubTab === 'llm' && (
                  <div className="settings-container">
                    
                    {/* Summary Engine Mode Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">{t('tab_llm')}</h3>
                        <p className="settings-card-subtitle">选择并配置总结生成使用的 AI 大模型</p>
                      </div>

                      <div className="settings-row">
                        <div className="settings-row-info">
                          <span className="settings-row-title">总结推理模式 (Summary Mode)</span>
                          <span className="settings-row-desc">选择本地离线运行的大模型，或云端商业在线 API</span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button 
                            type="button"
                            onClick={() => updateConfigField('summary_mode', 'local')}
                            style={{
                              padding: '8px 16px',
                              borderRadius: '6px',
                              border: configData.summary_mode === 'local' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                              background: configData.summary_mode === 'local' ? 'var(--primary-glow)' : 'rgba(0,0,0,0.25)',
                              color: configData.summary_mode === 'local' ? 'var(--primary)' : 'var(--text-secondary)',
                              cursor: 'pointer',
                              fontWeight: '600',
                              fontSize: '12.5px',
                              transition: 'all 0.2s'
                            }}
                          >
                            💻 {t('local')}
                          </button>
                          <button 
                            type="button"
                            onClick={() => updateConfigField('summary_mode', 'online')}
                            style={{
                              padding: '8px 16px',
                              borderRadius: '6px',
                              border: configData.summary_mode === 'online' ? '1px solid var(--accent)' : '1px solid var(--border-color)',
                              background: configData.summary_mode === 'online' ? 'var(--accent-glow)' : 'rgba(0,0,0,0.25)',
                              color: configData.summary_mode === 'online' ? 'var(--accent)' : 'var(--text-secondary)',
                              cursor: 'pointer',
                              fontWeight: '600',
                              fontSize: '12.5px',
                              transition: 'all 0.2s'
                            }}
                          >
                            ☁️ {t('online')}
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* LLM parameters Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">🔌 LLM 引擎参数配置</h3>
                        <p className="settings-card-subtitle">
                          {configData.summary_mode === 'local' ? '配置本地大语言模型连接参数' : '配置云端大语言模型连接参数'}
                        </p>
                      </div>

                      {configData.summary_mode === 'local' ? (
                        <div className="settings-grid">
                          <div className="settings-field">
                            <label className="settings-field-label">{t('local_api_url')}</label>
                            <input 
                              type="text" 
                              value={configData.ollama_url} 
                              onChange={(e) => updateConfigField('ollama_url', e.target.value)}
                              className="glass-input" 
                              placeholder="http://localhost:11434 或 http://localhost:1234"
                            />
                          </div>
                          
                          <div className="settings-field">
                            <label className="settings-field-label">{t('local_model_id')}</label>
                            <input 
                              type="text" 
                              value={configData.ollama_model} 
                              onChange={(e) => updateConfigField('ollama_model', e.target.value)}
                              className="glass-input" 
                              placeholder="qwen2.5:7b-instruct 等"
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="settings-grid">
                          <div className="settings-field">
                            <label className="settings-field-label">{t('online_api_url')}</label>
                            <input 
                              type="text" 
                              value={configData.online_summary_base_url} 
                              onChange={(e) => updateConfigField('online_summary_base_url', e.target.value)}
                              className="glass-input" 
                              placeholder="https://api.openai.com/v1"
                            />
                          </div>
                          
                          <div className="settings-field">
                            <label className="settings-field-label">{t('online_model_id')}</label>
                            <input 
                              type="text" 
                              value={configData.online_summary_model} 
                              onChange={(e) => updateConfigField('online_summary_model', e.target.value)}
                              className="glass-input" 
                              placeholder="gpt-4o-mini 或 deepseek-chat 等"
                            />
                          </div>

                          <div className="settings-field" style={{ gridColumn: 'span 2' }}>
                            <label className="settings-field-label">{t('online_api_key')}</label>
                            <input 
                              type="password" 
                              value={configData.online_summary_api_key} 
                              onChange={(e) => updateConfigField('online_summary_api_key', e.target.value)}
                              className="glass-input" 
                              placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* ── Prompt 编辑卡片 ── */}
                    <div className="settings-card" style={{ gap: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                        <div>
                          <h3 className="settings-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            🧠 总结 Prompt 模板
                          </h3>
                          <p className="settings-card-subtitle">自定义发给大模型的系统指令与输出格式要求，修改后立即对新任务生效</p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                          <button
                            type="button"
                            onClick={handleResetPrompt}
                            style={{
                              padding: '8px 16px',
                              borderRadius: '8px',
                              border: '1px solid var(--border-color)',
                              background: 'rgba(255,255,255,0.03)',
                              color: 'var(--text-secondary)',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: '600',
                              transition: 'all 0.2s',
                              whiteSpace: 'nowrap'
                            }}
                            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                          >
                            ↩️ 恢复默认
                          </button>
                          
                          <button
                            type="button"
                            onClick={handleSavePrompt}
                            style={{
                              padding: '8px 20px',
                              borderRadius: '8px',
                              border: '1px solid var(--primary)',
                              background: promptSaveStatus === 'saved' ? 'var(--primary-glow)' : promptSaveStatus === 'error' ? 'rgba(255,80,80,0.12)' : 'var(--primary-glow)',
                              color: promptSaveStatus === 'error' ? '#ff5050' : 'var(--primary)',
                              cursor: 'pointer',
                              fontSize: '13px',
                              fontWeight: '700',
                              transition: 'all 0.2s',
                              whiteSpace: 'nowrap',
                              flexShrink: 0
                            }}
                          >
                            {promptSaveStatus === 'saving' ? '⏳ 保存中...' : promptSaveStatus === 'saved' ? '✅ 已保存' : promptSaveStatus === 'error' ? '❌ 保存失败' : '💾 保存 Prompt'}
                          </button>
                        </div>
                      </div>

                      {/* Base Prompt */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                          🔒 防幻觉守则 / 基础指令 (Base Prompt)
                        </label>
                        <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', margin: 0, lineHeight: '1.5' }}>
                          注入给大模型的核心行为准则（防止脑补/幻觉）。数据块（转录文本、评论等）会自动注入在本段与 Action Prompt 之间。
                        </p>
                        <textarea
                          value={promptData.base_prompt}
                          onChange={(e) => setPromptData(prev => ({ ...prev, base_prompt: e.target.value }))}
                          className="glass-input"
                          rows={10}
                          style={{
                            width: '100%',
                            padding: '12px 14px',
                            fontFamily: 'ui-monospace, "Cascadia Code", "Fira Code", monospace',
                            fontSize: '12px',
                            lineHeight: '1.7',
                            resize: 'vertical',
                            borderRadius: '8px',
                            background: 'rgba(0,0,0,0.25)',
                            color: 'var(--text-primary)',
                            boxSizing: 'border-box',
                            minHeight: '200px'
                          }}
                          placeholder="输入基础 Prompt（角色定义、防幻觉规则等）..."
                        />
                      </div>

                      {/* Action Prompt */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                          📋 输出格式指令 (Action Prompt)
                        </label>
                        <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', margin: 0, lineHeight: '1.5' }}>
                          定义总结报告的具体输出章节与格式（章节结构、评级维度等）。这部分出现在数据块之后。
                        </p>
                        <textarea
                          value={promptData.action_prompt}
                          onChange={(e) => setPromptData(prev => ({ ...prev, action_prompt: e.target.value }))}
                          className="glass-input"
                          rows={14}
                          style={{
                            width: '100%',
                            padding: '12px 14px',
                            fontFamily: 'ui-monospace, "Cascadia Code", "Fira Code", monospace',
                            fontSize: '12px',
                            lineHeight: '1.7',
                            resize: 'vertical',
                            borderRadius: '8px',
                            background: 'rgba(0,0,0,0.25)',
                            color: 'var(--text-primary)',
                            boxSizing: 'border-box',
                            minHeight: '280px'
                          }}
                          placeholder="输入输出格式 Prompt（要求的章节、格式、评级等）..."
                        />
                      </div>

                      {/* 结构说明 */}
                      <div style={{
                        padding: '10px 14px',
                        borderRadius: '8px',
                        background: 'rgba(var(--primary-rgb, 122,162,247), 0.06)',
                        border: '1px solid rgba(var(--primary-rgb, 122,162,247), 0.15)',
                        fontSize: '11.5px',
                        color: 'var(--text-secondary)',
                        lineHeight: '1.6'
                      }}>
                        💡 <strong>最终 Prompt 拼接顺序：</strong>
                        <code style={{ display: 'block', marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace', lineHeight: '1.8' }}>
                          [Base Prompt] → [播客元数据 + 评论 + 转录文本（自动注入）] → [Action Prompt]
                        </code>
                      </div>
                    </div>

                  </div>
                )}

                {/* 3. ✉️ 邮件与通知配置 (Notifications) */}
                {configSubTab === 'notifications' && (
                  <div className="settings-container">
                    
                    {/* Notification Switches Card */}
                    <div className="settings-card">
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">{t('tab_notifications')}</h3>
                        <p className="settings-card-subtitle">开启后当任务成功或异常时会通过特定形式通知您</p>
                      </div>

                      {/* Desktop notifications row */}
                      <div className="settings-row">
                        <div className="settings-row-info">
                          <span className="settings-row-title">{t('enable_win_notify')}</span>
                          <span className="settings-row-desc">转录/总结完成后，在系统右下角弹出 Windows 原生推送通知气泡</span>
                        </div>
                        <input 
                          type="checkbox" 
                          id="enable-win" 
                          checked={configData.enable_win_notification}
                          onChange={(e) => updateConfigField('enable_win_notification', e.target.checked)}
                          style={{ cursor: 'pointer', width: '18px', height: '18px' }}
                        />
                      </div>

                      {/* Email notifications row */}
                      <div className="settings-row">
                        <div className="settings-row-info">
                          <span className="settings-row-title">{t('enable_email_notify')}</span>
                          <span className="settings-row-desc">转录/总结完成后，自动将内容总结以精美格式投递到目标邮箱</span>
                        </div>
                        <input 
                          type="checkbox" 
                          id="enable-email" 
                          checked={configData.enable_email_notification}
                          onChange={(e) => updateConfigField('enable_email_notification', e.target.checked)}
                          style={{ cursor: 'pointer', width: '18px', height: '18px' }}
                        />
                      </div>
                    </div>

                    {/* SMTP Mail Server Settings Card */}
                    <div className="settings-card" style={{ opacity: configData.enable_email_notification ? 1 : 0.6, transition: 'all 0.3s ease' }}>
                      <div className="settings-row-info">
                        <h3 className="settings-card-title">✉️ SMTP 邮件推送服务设置</h3>
                        <p className="settings-card-subtitle">用于自动推送服务的邮箱发件服务器配置</p>
                      </div>

                      <div className="settings-grid">
                        <div className="settings-field">
                          <label className="settings-field-label">{t('smtp_server')}</label>
                          <input 
                            type="text" 
                            value={configData.smtp_server} 
                            onChange={(e) => updateConfigField('smtp_server', e.target.value)}
                            disabled={!configData.enable_email_notification}
                            className="glass-input" 
                          />
                        </div>
                        
                        <div className="settings-field">
                          <label className="settings-field-label">{t('smtp_port')}</label>
                          <input 
                            type="number" 
                            value={configData.smtp_port} 
                            onChange={(e) => updateConfigField('smtp_port', parseInt(e.target.value) || 465)}
                            disabled={!configData.enable_email_notification}
                            className="glass-input" 
                          />
                        </div>

                        <div className="settings-field">
                          <label className="settings-field-label">{t('smtp_user')}</label>
                          <input 
                            type="text" 
                            placeholder="如 QQ 邮箱号"
                            value={configData.smtp_username} 
                            onChange={(e) => updateConfigField('smtp_username', e.target.value)}
                            disabled={!configData.enable_email_notification}
                            className="glass-input" 
                          />
                        </div>

                        <div className="settings-field">
                          <label className="settings-field-label">{t('smtp_pass')}</label>
                          <input 
                            type="password" 
                            placeholder="在邮箱设置中开启 SMTP 服务获得密钥"
                            value={configData.smtp_password} 
                            onChange={(e) => updateConfigField('smtp_password', e.target.value)}
                            disabled={!configData.enable_email_notification}
                            className="glass-input" 
                          />
                        </div>

                        <div className="settings-field">
                          <label className="settings-field-label">{t('smtp_sender')}</label>
                          <input 
                            type="text" 
                            value={configData.smtp_sender} 
                            onChange={(e) => updateConfigField('smtp_sender', e.target.value)}
                            disabled={!configData.enable_email_notification}
                            className="glass-input" 
                          />
                        </div>

                        <div className="settings-field">
                          <label className="settings-field-label">{t('smtp_receiver')}</label>
                          <input 
                            type="text" 
                            placeholder="转录成功后向此邮箱发送总结提醒"
                            value={configData.notification_email} 
                            onChange={(e) => updateConfigField('notification_email', e.target.value)}
                            disabled={!configData.enable_email_notification}
                            className="glass-input" 
                          />
                        </div>
                      </div>
                    </div>

                  </div>
                )}

              </form>
              </div>
            </div>
          )}

        </div>

        {/* ==================== 🎧 粘性底部音频播放器 ==================== */}
        {activeTab === 'detail' && activeTask && activeTask.audio_url && (
          <div className="glass-panel" style={{ 
            height: '92px', 
            borderRadius: '0', 
            borderLeft: 'none', 
            borderRight: 'none', 
            borderBottom: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 32px',
            zIndex: '100',
            background: 'var(--player-bg)',
            backdropFilter: 'blur(30px)',
            WebkitBackdropFilter: 'blur(30px)',
            borderTop: '1px solid var(--border-color)',
            boxShadow: '0 -10px 40px -10px rgba(0, 0, 0, 0.3)'
          }}>
            {/* 隐藏的 HTML5 播放器，利用 React state 和 ref 控制 */}
            <audio 
              ref={audioPlayerRef}
              src={`${BACKEND_URL}${activeTask.audio_url}`}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
              onDurationChange={(e) => setDuration(e.target.duration)}
              onCanPlay={(e) => { e.target.playbackRate = playbackRate; }}
              onError={() => setIsAudioMissing(true)}
              style={{ display: 'none' }}
            />

            {/* 左侧：节目封面与基本信息 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '28%', minWidth: '180px' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                borderRadius: '8px', 
                overflow: 'hidden',
                background: 'linear-gradient(135deg, var(--primary-glow), var(--accent-glow))',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {activeTask.image_url || activeTask.metadata?.image_url ? (
                  <img 
                    src={activeTask.image_url || activeTask.metadata?.image_url} 
                    alt="cover" 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                ) : (
                  <span style={{ fontSize: '18px' }}>🎧</span>
                )}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <h4 style={{ 
                  fontSize: '13.5px', 
                  fontWeight: '600', 
                  color: 'var(--text-primary)',
                  margin: 0,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  lineHeight: '1.4'
                }} title={activeTask.title}>
                  {activeTask.title}
                </h4>
                <p style={{ 
                  fontSize: '11px', 
                  color: 'var(--text-secondary)',
                  margin: '2px 0 0 0',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {activeTask.podcast_name}
                </p>
              </div>
            </div>

            {/* 中间：播放进度与核心按钮 */}
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              width: '44%', 
              gap: '6px'
            }}>
              {/* 控制按钮列 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                {/* 后退 15 秒 */}
                <button 
                  onClick={() => skipTime(-15)}
                  className="btn-ghost"
                  style={{ 
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%', 
                    border: '1px solid var(--border-color)', 
                    background: 'var(--bg-surface)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'color 0.2s, border-color 0.2s, background 0.2s, transform 0.1s',
                    padding: 0
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.color = 'var(--primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                  onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.95)'; }}
                  onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
                  title="快退15秒"
                >
                  <Icons.Rewind15 />
                </button>

                {/* 播放/暂停大圆钮 */}
                <button 
                  onClick={togglePlay}
                  style={{ 
                    width: '50px', 
                    height: '50px', 
                    borderRadius: '50%', 
                    border: '1px solid var(--primary)',
                    background: 'var(--primary-glow)',
                    color: 'var(--primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 15px var(--primary-glow)',
                    transition: 'transform 0.15s, background 0.15s, box-shadow 0.15s'
                  }}
                  onMouseEnter={(e) => { 
                    e.currentTarget.style.transform = 'scale(1.08)'; 
                    e.currentTarget.style.background = 'rgba(122, 162, 247, 0.25)'; 
                    e.currentTarget.style.boxShadow = '0 0 20px rgba(122, 162, 247, 0.5)';
                  }}
                  onMouseLeave={(e) => { 
                    e.currentTarget.style.transform = 'scale(1)'; 
                    e.currentTarget.style.background = 'var(--primary-glow)'; 
                    e.currentTarget.style.boxShadow = '0 0 15px var(--primary-glow)';
                  }}
                  title={isPlaying ? "暂停" : "播放"}
                >
                  {isPlaying ? <Icons.PausePlayer /> : <Icons.PlayPlayer />}
                </button>

                {/* 快进 30 秒 */}
                <button 
                  onClick={() => skipTime(30)}
                  className="btn-ghost"
                  style={{ 
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%', 
                    border: '1px solid var(--border-color)', 
                    background: 'var(--bg-surface)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'color 0.2s, border-color 0.2s, background 0.2s, transform 0.1s',
                    padding: 0
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.color = 'var(--primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                  onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.95)'; }}
                  onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
                  title="快进30秒"
                >
                  <Icons.Forward30 />
                </button>
              </div>

              {/* 进度条与时间指示 */}
              <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: '12px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-secondary)', width: '45px', textAlign: 'right' }}>
                  {formatTime(currentTime)}
                </span>
                
                {/* 自定义进度条输入 */}
                <input 
                  type="range"
                  min="0"
                  max={duration || 100}
                  value={currentTime}
                  onChange={handleSeek}
                  className="player-progress-bar"
                  style={{ 
                    flex: '1', 
                    height: '4px', 
                    borderRadius: '2px', 
                    background: `linear-gradient(to right, var(--primary) ${duration > 0 ? (currentTime / duration) * 100 : 0}%, rgba(255, 255, 255, 0.1) ${duration > 0 ? (currentTime / duration) * 100 : 0}%)`,
                    outline: 'none',
                    cursor: 'pointer',
                    accentColor: 'var(--primary)',
                    WebkitAppearance: 'none'
                  }}
                />

                <span style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-secondary)', width: '45px', textAlign: 'left' }}>
                  {formatTime(duration)}
                </span>
              </div>
            </div>

            {/* 右侧：播放速度与音量 */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'flex-end',
              width: '28%', 
              gap: '16px'
            }}>
              {/* 倍速选择器 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>倍速:</span>
                <select 
                  value={playbackRate}
                  onChange={(e) => changePlaybackRate(parseFloat(e.target.value))}
                  className="glass-input"
                  style={{ 
                    padding: '4px 8px', 
                    fontSize: '12px', 
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    outline: 'none'
                  }}
                >
                  <option value="0.75" style={{ color: 'var(--text-primary)' }}>0.75x</option>
                  <option value="1" style={{ color: 'var(--text-primary)' }}>1.0x</option>
                  <option value="1.25" style={{ color: 'var(--text-primary)' }}>1.25x</option>
                  <option value="1.5" style={{ color: 'var(--text-primary)' }}>1.5x</option>
                  <option value="1.75" style={{ color: 'var(--text-primary)' }}>1.75x</option>
                  <option value="2" style={{ color: 'var(--text-primary)' }}>2.0x</option>
                </select>
              </div>

              {/* 音量滑块 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button 
                  onClick={() => {
                    if (!audioPlayerRef.current) return;
                    const newVol = volume > 0 ? 0 : 0.8;
                    audioPlayerRef.current.volume = newVol;
                    setVolume(newVol);
                  }}
                  style={{ 
                    border: 'none', 
                    background: 'transparent', 
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  {volume === 0 ? <Icons.Mute /> : <Icons.Volume />}
                </button>
                <input 
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={volume}
                  onChange={(e) => {
                    const newVol = parseFloat(e.target.value);
                    if (audioPlayerRef.current) audioPlayerRef.current.volume = newVol;
                    setVolume(newVol);
                  }}
                  style={{ 
                    width: '70px', 
                    height: '3px',
                    accentColor: 'var(--primary)',
                    cursor: 'pointer'
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* 全局丝滑 Toast 提示层 */}
        {toastVisible && (
          <div style={{
            position: 'fixed',
            bottom: '40px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(18, 18, 28, 0.95)',
            border: '1px solid var(--primary)',
            boxShadow: '0 8px 32px rgba(122, 162, 247, 0.4)',
            color: 'var(--text-primary)',
            padding: '12px 24px',
            borderRadius: '10px',
            zIndex: 99999,
            fontSize: '13px',
            fontWeight: '600',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            animation: 'star-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
          }}>
            {toastMessage}
          </div>
        )}

      </div>
    </div>
  );
}
