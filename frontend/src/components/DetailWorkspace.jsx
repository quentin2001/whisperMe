import React, { useState, useRef, useEffect } from 'react';

// ==================== 🛠️ 像素级 SVG 图标 ====================
const Icons = {
  Refresh: ({ className }) => (
    <svg className={`w-3.5 h-3.5 ${className || ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M23 4v6h-6M1 20v-6h6" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
};

// ==================== 📝 Inline Markdown Parser ====================
function parseInlineMarkdown(text) {
  if (!text) return '';
  const parts = [];
  const boldRegex = /\*\*([^*]+)\*\*/g;
  let match;
  let lastIndex = 0;

  while ((match = boldRegex.exec(text)) !== null) {
    const textBefore = text.substring(lastIndex, match.index);
    if (textBefore) parts.push(textBefore);
    parts.push(
      <strong key={match.index} className="text-on-background font-bold">
        {match[1]}
      </strong>
    );
    lastIndex = boldRegex.lastIndex;
  }
  
  const remaining = text.substring(lastIndex);
  if (remaining) parts.push(remaining);
  
  return parts.length > 0 ? parts : text;
}

// ==================== 📝 High-Performance Markdown Parser ====================
function MarkdownRenderer({ text, t }) {
  if (!text) return <p className="text-on-surface-variant text-[12px]">{t('no_summary') || '暂无分析报告'}</p>;
  
  const lines = text.replace(/\\n/g, '\n').split('\n');
  let inList = false;
  let listItems = [];
  const renderedElements = [];

  const flushList = (key) => {
    if (listItems.length > 0) {
      renderedElements.push(
        <ul key={`list-${key}`} className="list-disc pl-5 mb-4 space-y-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Parse list items
    if (line.startsWith('- ') || line.startsWith('* ')) {
      inList = true;
      const content = line.substring(2);
      listItems.push(
        <li key={`li-${i}`} className="text-on-surface-variant/90 text-[12px]">
          {parseInlineMarkdown(content)}
        </li>
      );
      continue;
    }
    
    // Flush list if non-list item
    if (inList && !line.startsWith('- ') && !line.startsWith('* ')) {
      flushList(i);
    }

    if (line === '') continue;

    // Header 2
    if (line.startsWith('## ')) {
      renderedElements.push(
        <h2 key={i} className="font-label-caps text-[11px] text-white uppercase mb-1 mt-4">
          {parseInlineMarkdown(line.substring(3))}
        </h2>
      );
    } 
    // Header 3
    else if (line.startsWith('### ')) {
      renderedElements.push(
        <h3 key={i} className="font-label-caps text-[11px] text-primary uppercase mb-1 mt-4">
          {parseInlineMarkdown(line.substring(4))}
        </h3>
      );
    } 
    // Header 1
    else if (line.startsWith('# ')) {
      renderedElements.push(
        <h1 key={i} className="font-label-caps text-[12px] text-primary mb-4 flex items-center gap-2 uppercase">
          {parseInlineMarkdown(line.substring(2))}
        </h1>
      );
    }
    // Blockquote
    else if (line.startsWith('> ')) {
      renderedElements.push(
        <blockquote key={i} className="border-l-4 border-primary bg-primary/5 px-4 py-3 rounded-r-md my-4 italic text-on-surface-variant text-[12px]">
          {parseInlineMarkdown(line.substring(2))}
        </blockquote>
      );
    } 
    // Normal paragraph
    else {
      renderedElements.push(
        <p key={i} className="font-body-sm text-[12px] text-on-surface-variant mb-2">
          {parseInlineMarkdown(line)}
        </p>
      );
    }
  }
  
  if (inList) {
    flushList(lines.length);
  }

  return <div className="markdown-body select-text">{renderedElements}</div>;
}

// ==================== 🎙️ Shownotes parser and timeline renderer ====================
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
      const fullMatch = timeMatch[0];
      const rawTime = fullMatch.replace(/[\[\]\(\)]/g, '').trim();
      const seconds = parseTimestampToSeconds(rawTime);
      let rest = line.replace(fullMatch, '').trim();
      rest = rest.replace(/^[:：\-—\s]+/, '').trim();

      if (rest === '' && i + 1 < rawLines.length) {
        const nextLine = rawLines[i + 1].trim();
        if (nextLine && !nextLine.match(timeRegex)) {
          rest = nextLine;
          i++;
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
      blocks.push({ type: 'prose', text: item.text });
    }
  }
  flushTimeline();

  return blocks;
}

function ShownotesRenderer({ text, onTimeJump, t }) {
  if (!text) return <p className="font-body-sm text-[12px] text-on-surface-variant">{t('no_shownotes') || '本集暂无节目简介。'}</p>;

  const blocks = parseShownotesToBlocks(text);
  const headerRegex = /^(?:#+\s+|[一二三四五六七八九十]+[、.]|[0-9]+\.|part\s*\d|【|🎙️|⏳|📅|💡|📌|「|『)/i;

  return (
    <div className="flex flex-col gap-2">
      {blocks.map((block, index) => {
        if (block.type === 'space') {
          return <div key={index} className="h-2" />;
        }

        if (block.type === 'timeline') {
          return (
            <div key={index} className="space-y-2 mt-4 mb-4">
              {block.items.map((item, idx) => (
                <div key={idx} className="flex items-center gap-4 group cursor-pointer" onClick={() => onTimeJump(item.seconds)}>
                  <span className="font-mono-data text-[11px] w-12 text-on-surface-variant group-hover:text-primary transition-colors">
                    {item.timestamp}
                  </span>
                  <div className="flex-1 h-8 bg-surface-container border border-outline-variant flex items-center px-4 group-hover:border-primary group-hover:bg-primary-container/5 transition-all">
                    <p className="font-label-caps text-[10px] uppercase tracking-wide truncate">{item.text ? parseInlineMarkdown(item.text) : 'Timeline Event'}</p>
                  </div>
                </div>
              ))}
            </div>
          );
        }

        const isHeader = headerRegex.test(block.text);
        if (isHeader) {
          return (
            <div key={index} className="font-label-caps text-[11px] text-primary mb-2 mt-4 uppercase">
              {parseInlineMarkdown(block.text)}
            </div>
          );
        }

        return (
          <p key={index} className="font-body-sm text-[12px] text-on-surface-variant mb-1">
            {parseInlineMarkdown(block.text)}
          </p>
        );
      })}
    </div>
  );
}

const getSpeakerColors = (idx) => {
  const speakerStyles = [
    { nameClass: 'text-primary bg-primary-container/20', lineClass: 'border-primary-container' },
    { nameClass: 'text-secondary bg-secondary-container/20', lineClass: 'border-outline-variant' },
    { nameClass: 'text-white bg-surface-container-highest', lineClass: 'border-outline-variant' },
    { nameClass: 'text-primary bg-surface-container-lowest border border-primary', lineClass: 'border-primary' }
  ];
  return speakerStyles[idx % speakerStyles.length];
};

// ==================== 🏛️ Main Component ====================
export default function DetailWorkspace({
  activeTask,
  currentTime,
  detailSubTab,
  setDetailSubTab,
  showSpeakerModal,
  setShowSpeakerModal,
  handleTimeJump,
  handleRefreshMetadata,
  isRefreshingMetadata,
  handleRegenerateSummary,
  panelRenamingSpeakerId,
  setPanelRenamingSpeakerId,
  panelRenameValue,
  setPanelRenameValue,
  handleRenameSpeakerPanel,
  renamingSpeakerId,
  setRenamingSpeakerId,
  renameValue,
  setRenameValue,
  handleRenameSpeaker,
  t,
  formatSpeakerName,
  getUniqueSpeakers
}) {
  const [leftWidth, setLeftWidth] = useState(50); // Width in %
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);
  const activeBubbleRef = useRef(null);

  // Auto scroll transcript to active dialogue bubble
  useEffect(() => {
    if (activeBubbleRef.current) {
      activeBubbleRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }
  }, [currentTime]);

  // Handle Resizable Split Screen dragging
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const relativeX = e.clientX - rect.left;
      const percentage = (relativeX / rect.width) * 100;
      if (percentage > 25 && percentage < 75) {
        setLeftWidth(percentage);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const showRefreshBtn = activeTask && activeTask.url;

  return (
    <div ref={containerRef} className="flex flex-1 h-full min-h-0 overflow-hidden relative select-none bg-background">
      {/* Draggable Mouse Shield */}
      {isDragging && (
        <div className="fixed inset-0 cursor-col-resize z-[9999] bg-transparent" />
      )}

      {/* LEFT COLUMN: Transcript Dialogue Flow */}
      <section
        className="border-r border-outline-variant flex flex-col relative overflow-hidden shrink-0"
        style={{ width: `${leftWidth}%` }}
      >
        <div className="scanline"></div>
        <div className="p-lg border-b border-outline-variant bg-surface-container-lowest flex justify-between items-center z-10 shrink-0">
          <h2 className="font-label-caps text-[12px] uppercase text-primary flex items-center gap-2">
            <span className="w-2 h-2 bg-primary animate-pulse"></span>
            LIVE_TRANSCRIPT.LOG
          </h2>
          <div className="flex gap-2">
            <span className="px-2 py-1 bg-secondary-container text-[10px] font-mono-data text-white cursor-pointer hover:bg-secondary transition-colors" onClick={() => setShowSpeakerModal(true)}>SPEAKER_MANAGEMENT</span>
          </div>
        </div>

        {/* Dialogue Scroll Pane */}
        <div className="flex-1 overflow-y-auto p-lg space-y-lg custom-scrollbar">
          {/* Paragraph Mode */}
          {activeTask.paragraphs && activeTask.paragraphs.length > 0 ? (
            <div className="space-y-lg">
              {activeTask.paragraphs.map((para, i) => {
                const isPlayingLine = currentTime >= para.start_time && currentTime <= para.end_time;
                const speakerName = formatSpeakerName(para.speaker, activeTask.speaker_mappings);
                const isEditing = renamingSpeakerId === para.id;
                
                // Get brutalist styles based on speaker index to cycle styles
                const uniqueSpeakers = getUniqueSpeakers();
                const speakerIndex = Math.max(0, uniqueSpeakers.indexOf(para.speaker));
                const styles = getSpeakerColors(speakerIndex);

                return (
                  <div
                    key={para.id}
                    id={para.id}
                    ref={isPlayingLine ? activeBubbleRef : null}
                    className="space-y-sm"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono-data text-[11px] text-primary opacity-50 cursor-pointer hover:text-primary hover:opacity-100 transition-colors" onClick={() => handleTimeJump(para.start_time)}>
                        {(() => {
                          const startMin = Math.floor(para.start_time / 60);
                          const startSec = Math.floor(para.start_time % 60);
                          const startHour = Math.floor(startMin / 60);
                          const minRem = startMin % 60;
                          return `${startHour.toString().padStart(2, '0')}:${minRem.toString().padStart(2, '0')}:${startSec.toString().padStart(2, '0')}`;
                        })()}
                      </span>

                      {!isEditing ? (
                        <span 
                          onClick={(e) => {
                            e.stopPropagation();
                            setRenamingSpeakerId(para.id);
                            setRenameValue(speakerName);
                          }}
                          className={`font-label-caps text-[12px] px-2 cursor-pointer hover:opacity-80 transition-opacity ${styles.nameClass}`}
                        >
                          {speakerName}
                        </span>
                      ) : (
                        <div className="flex gap-1 z-20">
                          <input
                            type="text"
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleRenameSpeaker(para.speaker);
                              if (e.key === 'Escape') setRenamingSpeakerId(null);
                            }}
                            className="bg-black border-b border-primary text-primary font-mono-data text-[11px] w-24 outline-none px-1"
                            autoFocus
                          />
                          <button onClick={() => handleRenameSpeaker(para.speaker)} className="text-primary hover:text-white material-symbols-outlined text-sm">check</button>
                          <button onClick={() => setRenamingSpeakerId(null)} className="text-on-surface-variant hover:text-white material-symbols-outlined text-sm">close</button>
                        </div>
                      )}
                    </div>
                    
                    <p className={`font-body-lg text-on-surface leading-relaxed border-l-2 pl-4 transition-all duration-300 ${styles.lineClass} ${isPlayingLine ? 'bg-primary/5 border-primary shadow-[inset_2px_0_0_#ff0000]' : ''}`}>
                      {para.sentences && para.sentences.length > 0 ? (
                        para.sentences.map((sentence, sIdx) => {
                          const isPlayingSentence = currentTime >= sentence.start && currentTime <= sentence.end;
                          return (
                            <span
                              key={sIdx}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleTimeJump(sentence.start);
                              }}
                              className={`transition-colors duration-200 cursor-pointer ${
                                isPlayingSentence
                                  ? 'text-primary bg-primary/20'
                                  : 'hover:text-primary hover:bg-primary/10'
                              }`}
                            >
                              {sentence.text}
                            </span>
                          );
                        })
                      ) : (
                        para.content
                      )}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : activeTask.transcript && activeTask.transcript.length > 0 ? (
            /* Transcript fallback mode */
            <div className="space-y-lg">
              {activeTask.transcript.map((seg, idx) => {
                const isPlayingLine = currentTime >= seg.start && currentTime <= seg.end;
                const speakerName = formatSpeakerName(seg.speaker, activeTask.speaker_mappings);
                
                const uniqueSpeakers = getUniqueSpeakers();
                const speakerIndex = Math.max(0, uniqueSpeakers.indexOf(seg.speaker));
                const styles = getSpeakerColors(speakerIndex);

                return (
                  <div
                    key={idx}
                    ref={isPlayingLine ? activeBubbleRef : null}
                    className="space-y-sm"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono-data text-[11px] text-primary opacity-50 cursor-pointer hover:opacity-100 transition-colors" onClick={() => handleTimeJump(seg.start)}>
                        {seg.timestamp_str}
                      </span>
                      <span className={`font-label-caps text-[12px] px-2 ${styles.nameClass}`}>
                        {speakerName}
                      </span>
                    </div>
                    <p className={`font-body-lg text-on-surface leading-relaxed border-l-2 pl-4 cursor-pointer transition-colors ${styles.lineClass} ${isPlayingLine ? 'bg-primary/5 text-primary' : 'hover:bg-primary/10'} `} onClick={() => handleTimeJump(seg.start)}>
                      {seg.text}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Empty or loading state */
            <div className="py-24 flex flex-col items-center justify-center text-on-surface-variant select-none h-full">
              {activeTask.status !== 'completed' && activeTask.status !== 'failed' ? (
                <div className="text-center">
                  <span className="material-symbols-outlined text-4xl text-primary animate-pulse mb-4">graphic_eq</span>
                  <p className="font-label-caps text-primary uppercase tracking-widest">{t('script_loading')}</p>
                  <p className="font-mono-data text-[10px] mt-2 opacity-50">{t('script_loading_sub')}</p>
                </div>
              ) : (
                <div className="text-center border border-outline-variant p-8 border-dashed bg-surface-container-highest/50">
                  <span className="material-symbols-outlined text-4xl text-on-surface-variant mb-4">comments_disabled</span>
                  <p className="font-label-caps uppercase">{t('script_empty')}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* DRAGGABLE DIVIDER */}
      <div
        onMouseDown={handleMouseDown}
        className="w-1 cursor-col-resize flex justify-center items-center select-none shrink-0 bg-outline-variant hover:bg-primary transition-colors z-20"
      ></div>

      {/* RIGHT COLUMN: AI Intelligence Panel */}
      <section
        className="flex flex-col bg-surface-container-lowest shrink-0 overflow-hidden"
        style={{ width: `calc(${100 - leftWidth}% - 4px)` }}
      >
        <div className="flex border-b border-outline-variant bg-surface-container-lowest shrink-0 h-12">
          <button
            onClick={() => setDetailSubTab('summary')}
            className={`flex-1 font-label-caps text-[11px] uppercase tracking-widest transition-colors ${
              detailSubTab === 'summary'
                ? 'bg-primary text-on-primary'
                : 'text-on-surface-variant hover:text-primary hover:bg-primary/10'
            }`}
          >
            {t('ai_report')}
          </button>
          <button
            onClick={() => setDetailSubTab('shownotes')}
            className={`flex-1 font-label-caps text-[11px] uppercase tracking-widest transition-colors ${
              detailSubTab === 'shownotes'
                ? 'bg-primary text-on-primary'
                : 'text-on-surface-variant hover:text-primary hover:bg-primary/10'
            }`}
          >
            {t('shownotes_comments') || '简介 & 评论'}
          </button>
        </div>

        <div className="flex-1 p-lg flex flex-col gap-lg overflow-y-auto custom-scrollbar">
          {detailSubTab === 'summary' && (
            <>
              {/* Executive Summary Equivalent */}
              <div className="border border-outline-variant p-gutter relative overflow-hidden shrink-0">
                <div className="absolute top-0 right-0 p-2 opacity-10 pointer-events-none">
                  <span className="material-symbols-outlined text-4xl">psychology</span>
                </div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-label-caps text-[12px] text-primary flex items-center gap-2 uppercase">
                    <span className="material-symbols-outlined text-sm">description</span>
                    EXECUTIVE_SUMMARY
                  </h3>
                  <button onClick={handleRegenerateSummary} className="material-symbols-outlined text-sm text-on-surface-variant hover:text-primary transition-colors" title="Regenerate Summary">refresh</button>
                </div>
                <div className="font-body-lg text-on-surface leading-relaxed">
                   <MarkdownRenderer text={activeTask.summary_report} t={t} />
                </div>
              </div>

              {/* AI Analysis Shader at bottom */}
              <div className="mt-auto border border-outline-variant bg-black h-32 relative overflow-hidden shrink-0">
                <div className="scanline" style={{animationDuration: '2s'}}></div>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center">
                    <p className="font-label-caps text-[10px] text-primary animate-pulse tracking-[0.3em]">AI_ANALYSIS_ENGINE_READY</p>
                    <p className="font-mono-data text-[8px] text-on-surface-variant mt-1 opacity-50">SUMMARY_GENERATED</p>
                  </div>
                </div>
              </div>
            </>
          )}

          {detailSubTab === 'shownotes' && (
            <div className="space-y-lg flex flex-col h-full">
              {/* Shownotes block mimicking topic timeline style */}
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-label-caps text-[12px] text-primary flex items-center gap-2 uppercase">
                    <span className="material-symbols-outlined text-sm">timeline</span>
                    SHOWNOTES_TIMELINE
                  </h3>
                  {showRefreshBtn && (
                    <button
                      onClick={handleRefreshMetadata}
                      disabled={isRefreshingMetadata}
                      className="font-label-caps text-[10px] bg-surface-container-highest px-2 py-1 text-on-surface-variant border border-outline-variant hover:border-primary hover:text-primary transition-colors disabled:opacity-50 flex items-center gap-1"
                    >
                      <Icons.Refresh className={isRefreshingMetadata ? 'animate-spin' : ''} />
                      {isRefreshingMetadata ? 'SYNCING...' : 'SYNC'}
                    </button>
                  )}
                </div>
                <div className="space-y-2">
                  <ShownotesRenderer text={activeTask.metadata?.shownotes} onTimeJump={handleTimeJump} t={t} />
                </div>

                {/* Hot Comments as brutalist cards */}
                <div className="mt-8">
                  <h3 className="font-label-caps text-[12px] text-primary mb-4 flex items-center gap-2 uppercase">
                    <span className="material-symbols-outlined text-sm">forum</span>
                    HOT_COMMENTS
                  </h3>
                  <div className="grid grid-cols-1 gap-4">
                    {activeTask.metadata?.comments && activeTask.metadata.comments.length > 0 ? (
                      activeTask.metadata.comments.map((comment, cIdx) => (
                        <div key={cIdx} className="border border-outline-variant p-4 hover:border-primary transition-all">
                          <div className="flex justify-between items-center mb-2">
                            <h4 className="font-label-caps text-[11px] text-white uppercase flex items-center gap-2">
                               <span className="material-symbols-outlined text-[14px] text-primary">person</span>
                               {comment.author}
                            </h4>
                            <span className="font-mono-data text-[10px] text-primary flex items-center gap-1">
                                <span className="material-symbols-outlined text-[12px]">favorite</span>
                                {comment.likes}
                            </span>
                          </div>
                          <div className="font-body-sm text-[12px] text-on-surface-variant">
                            <ShownotesRenderer text={comment.text} onTimeJump={handleTimeJump} t={t} />
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="border border-outline-variant border-dashed p-4 text-center">
                         <span className="font-mono-data text-[10px] text-on-surface-variant opacity-50">NO_COMMENTS_FOUND</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* SLIDE-OUT PANEL: Speaker management drawer */}
      {showSpeakerModal && (
        <>
          <div
            onClick={() => setShowSpeakerModal(false)}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm z-40 transition-opacity"
          />
          
          <aside className="absolute right-0 top-0 h-full w-80 bg-background border-l-2 border-primary p-lg z-50 shadow-[-10px_0_30px_rgba(255,0,0,0.1)] flex flex-col animate-in slide-in-from-right duration-300">
            <div className="flex justify-between items-center pb-2 border-b border-primary mb-lg shrink-0">
              <h3 className="font-label-caps text-label-caps text-primary uppercase flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">settings_voice</span>
                SPEAKER_CONFIG
              </h3>
              <button
                onClick={() => setShowSpeakerModal(false)}
                className="text-on-surface-variant hover:text-primary material-symbols-outlined"
              >
                close
              </button>
            </div>

            <p className="font-mono-data text-[10px] text-on-surface-variant opacity-70 mb-4">
              // OVERRIDE SPEAKER IDENTIFIERS FOR TRANSCRIPT RENDERING
            </p>

            <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar pr-2">
              {getUniqueSpeakers().length === 0 ? (
                <div className="text-center py-8 border border-outline-variant border-dashed">
                  <span className="font-mono-data text-[10px] text-on-surface-variant opacity-50">NO_SPEAKERS_DETECTED</span>
                </div>
              ) : (
                getUniqueSpeakers().map((spId) => {
                  const currentName = formatSpeakerName(spId, activeTask.speaker_mappings);
                  const isEditing = panelRenamingSpeakerId === spId;

                  return (
                    <div key={spId} className="border border-outline-variant p-sm hover:border-primary transition-colors">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-mono-data text-[9px] text-on-surface-variant opacity-50 uppercase">
                          ID: {spId}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {!isEditing ? (
                          <>
                            <span className="font-label-caps text-[12px] text-white flex-1 truncate">{currentName}</span>
                            <button
                              onClick={() => {
                                setPanelRenamingSpeakerId(spId);
                                setPanelRenameValue(currentName);
                              }}
                              className="material-symbols-outlined text-[16px] text-on-surface-variant hover:text-primary transition-colors"
                            >
                              edit
                            </button>
                          </>
                        ) : (
                          <div className="flex flex-1 gap-2">
                            <input
                              type="text"
                              value={panelRenameValue}
                              onChange={(e) => setPanelRenameValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleRenameSpeakerPanel(spId);
                                if (e.key === 'Escape') setPanelRenamingSpeakerId(null);
                              }}
                              className="bg-black border-b border-primary text-primary font-mono-data text-[12px] flex-1 outline-none px-1"
                              autoFocus
                            />
                            <button onClick={() => handleRenameSpeakerPanel(spId)} className="material-symbols-outlined text-[16px] text-primary hover:text-white">check</button>
                            <button onClick={() => { setPanelRenamingSpeakerId(null); setPanelRenameValue(''); }} className="material-symbols-outlined text-[16px] text-on-surface-variant hover:text-white">close</button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            
            <button
              onClick={() => setShowSpeakerModal(false)}
              className="mt-lg w-full border border-primary text-primary hover:bg-primary-container font-label-caps text-[12px] uppercase py-2 transition-colors active:scale-95"
            >
              CLOSE_CONFIG
            </button>
          </aside>
        </>
      )}
    </div>
  );
}
