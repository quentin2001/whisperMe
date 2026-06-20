import React, { useState } from 'react';

// Icons wrapper
const Icons = {
  Clock: () => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>,
  ThumbsUp: () => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>,
  MessageCircle: () => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>,
  Trash: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
};

const getSourceLabel = (task) => {
  const url = task.url || '';
  const metadata = task.metadata || {};
  const source = metadata.source || '';
  
  if (source.includes('bilibili')) return { text: 'Bilibili', color: '#ffb597', bg: '#ffb59715' };
  if (source.includes('xiaoyuzhou')) return { text: '小宇宙', color: '#ff6a1c', bg: '#ff6a1c15' };
  if (url.includes('uploaded_') || source === 'upload' || source === 'local') return { text: 'Local File', color: '#ffb86f', bg: '#ffb86f15' };
  
  if (url.includes('bilibili.com') || url.includes('b23.tv')) return { text: 'Bilibili', color: '#ffb597', bg: '#ffb59715' };
  if (url.includes('xiaoyuzhoufm.com')) return { text: '小宇宙', color: '#ff6a1c', bg: '#ff6a1c15' };
  
  return { text: 'External', color: '#e7c34e', bg: '#e7c34e15' };
};

export default function LibraryWorkspace({
  tasks,
  setActiveTaskId,
  setActiveTab,
  handleDeleteTask,
  t,
  onOpenIngestModal
}) {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter tasks
  const filteredTasks = tasks.filter(task => {
    const title = (task.title || '').toLowerCase();
    const name = (task.podcast_name || '').toLowerCase();
    const query = searchQuery.toLowerCase();
    return title.includes(query) || name.includes(query);
  });

  const renderStatusBadge = (task) => {
    const { status, progress, queue_position } = task;
    switch (status) {
      case 'pending':
        if (queue_position && queue_position > 0) {
          return (
            <div className="flex items-center gap-1.5 text-secondary border border-secondary bg-secondary/5 px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
              <span className="w-1.5 h-1.5 rounded-none bg-secondary"></span>
              QUEUE [{queue_position}]
            </div>
          );
        }
        return (
          <div className="flex items-center gap-1.5 text-on-surface-variant border border-outline-variant/30 bg-surface-container px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-none bg-on-surface-variant"></span>
            PENDING
          </div>
        );
      case 'downloading':
        return (
          <div className="flex items-center gap-1.5 text-primary border border-primary bg-primary/5 px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-none bg-primary animate-pulse"></span>
            DL [{Math.round(progress)}%]
          </div>
        );
      case 'transcribing':
        return (
          <div className="flex items-center gap-1.5 text-secondary border border-secondary bg-secondary/5 px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-none bg-secondary animate-pulse"></span>
            ASR [{Math.round(progress)}%]
          </div>
        );
      case 'summarizing':
        return (
          <div className="flex items-center gap-1.5 text-tertiary border border-tertiary bg-tertiary/5 px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-none bg-tertiary animate-pulse"></span>
            LLM [{Math.round(progress)}%]
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center gap-1.5 text-on-surface-variant border border-outline-variant/30 bg-surface-container px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-none bg-on-surface-variant/50"></span>
            DONE
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-1.5 text-error border border-error bg-error/5 px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-none bg-error"></span>
            ERR
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-1.5 text-on-surface-variant border border-outline-variant/30 bg-surface-container px-2 py-0.5 text-[10px] font-label-caps uppercase tracking-widest">
            <span>{status}</span>
          </div>
        );
    }
  };

  return (
    <div className="animate-fade-in p-lg h-full overflow-y-auto custom-scrollbar relative">
      <div className="scanline"></div>
      
      {/* Archive List Section */}
      <div className="mb-xl flex justify-between items-end relative z-10">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface uppercase">RECORDING ARCHIVE</h2>
          <p className="font-mono-data text-mono-data text-on-surface-variant">DIRECTORY: /USER/LOCAL_INGEST/CAPTURES</p>
        </div>
        <div className="flex gap-sm">
          <button className="p-2 border border-outline-variant text-on-surface hover:border-primary transition-all">
            <span className="material-symbols-outlined">grid_view</span>
          </button>
          <button className="p-2 border border-outline-variant text-on-surface-variant hover:text-on-surface transition-all">
            <span className="material-symbols-outlined">view_list</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-gutter relative z-10">
        {filteredTasks.length === 0 ? (
          <div className="col-span-full border border-outline-variant border-dashed text-center py-16 text-on-surface-variant/50">
            <span className="material-symbols-outlined text-[32px] opacity-30 mb-2">terminal</span>
            <p className="font-mono-data text-mono-data uppercase tracking-widest">ARCHIVE EMPTY. AWAITING INITIAL INPUT...</p>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const srcInfo = getSourceLabel(task);
            const isProcessing = ['pending', 'downloading', 'transcribing', 'summarizing'].includes(task.status);
            
            return (
              <div
                key={task.id}
                onClick={() => {
                  setActiveTaskId(task.id);
                  setActiveTab('detail');
                }}
                className={`p-md border transition-all group cursor-pointer relative overflow-hidden flex flex-col justify-between ${
                  isProcessing
                    ? 'bg-[#3D0000] border-[#FF0000] shadow-[0_0_10px_rgba(255,0,0,0.2)]'
                    : 'bg-surface border-outline-variant hover:border-primary'
                }`}
              >
                {/* Active Indicator for Processing Tasks */}
                {isProcessing && (
                  <div className="absolute top-0 right-0 px-3 py-1 bg-[#FF0000] text-black font-label-caps text-[10px] flex items-center gap-1 z-20">
                    <span className="w-1.5 h-1.5 bg-black rounded-full animate-pulse"></span>
                    LIVE MONITORING
                  </div>
                )}
                
                {/* Delete Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm(t('confirm_delete') || '确认删除该任务及关联的音频与数据吗？')) {
                      handleDeleteTask(task.id, e);
                    }
                  }}
                  className="absolute bottom-2 right-2 text-on-surface-variant/40 hover:text-error transition-colors p-1.5 hover:bg-surface-container-high z-20 opacity-0 group-hover:opacity-100"
                >
                  <Icons.Trash />
                </button>

                <div className="flex flex-col gap-3 z-10">
                  <div className="flex justify-between items-start mb-md">
                    <span className={`font-mono-data text-mono-data ${isProcessing ? 'text-[#FF0000]' : 'text-on-surface-variant'}`}>
                      ID: {task.id.substring(0, 8).toUpperCase()}
                    </span>
                    <span className={`font-mono-data text-mono-data ${isProcessing ? 'text-[#FF0000]' : 'text-on-surface-variant'}`}>
                      {task.created_at ? task.created_at.substring(0, 10) : ''}
                    </span>
                  </div>
                  
                  {isProcessing ? (
                    <>
                      <h3 className="font-title-md text-title-md text-white mb-xs truncate">
                        {task.title || 'UNTITLED_RECORDING'}
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mb-lg truncate">
                        {task.podcast_name || 'LOCAL_INGEST'}
                      </p>
                      
                      <div className="space-y-sm mt-4">
                        <div className="flex justify-between items-center">
                          {renderStatusBadge(task)}
                          <span className="font-label-caps text-[10px] text-[#FF0000]">SIGNAL STRENGTH: OPTIMAL</span>
                        </div>
                        <div className="w-full h-1 bg-black/40 relative">
                           <div className="absolute left-0 top-0 h-full bg-[#FF0000] shadow-[0_0_8px_#FF0000]" style={{width: `${task.progress || 10}%`}}></div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="aspect-video mb-md relative overflow-hidden bg-surface-container-lowest border border-outline-variant">
                        {task.image_url ? (
                          <img
                            src={task.image_url}
                            alt={task.title}
                            className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center opacity-20 text-primary">
                            <span className="material-symbols-outlined text-[48px]">audio_file</span>
                          </div>
                        )}
                        <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                          <span className="material-symbols-outlined text-primary text-[48px]">play_circle</span>
                        </div>
                      </div>
                      
                      <h3 className="font-title-md text-title-md text-on-surface mb-xs truncate">
                        {task.title || 'UNTITLED_RECORDING'}
                      </h3>
                      <div className="font-body-sm text-body-sm text-on-surface-variant truncate">
                        {task.podcast_name || 'LOCAL_INGEST'}
                      </div>
                    </>
                  )}
                </div>

                {!isProcessing && (
                  <div className="flex items-center justify-between mt-md pt-3 border-t border-outline-variant/30 z-10">
                     <div className="flex flex-wrap items-center gap-2">
                       {task.status === 'failed' ? (
                          <span className="text-[10px] font-label-caps text-error truncate max-w-[150px] uppercase bg-error/5 border border-error px-2 py-0.5">
                            {task.error_message || 'SYS_ERR_TRANSCRIPT'}
                          </span>
                       ) : (
                         <>
                            <span
                              className="text-[10px] font-label-caps uppercase tracking-widest px-2 py-0.5 border border-outline-variant"
                              style={{
                                backgroundColor: srcInfo.bg,
                                color: srcInfo.color,
                                borderColor: srcInfo.color + '40'
                              }}
                            >
                              {srcInfo.text}
                            </span>
                            {renderStatusBadge(task)}
                         </>
                       )}
                     </div>

                    {task.status === 'completed' && (
                      <div className="flex gap-4">
                        <div className="flex items-center gap-1.5 text-[10px] text-on-surface-variant/60 font-mono-data">
                          <Icons.ThumbsUp />
                          <span>{task.like_count || 0}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-on-surface-variant/60 font-mono-data">
                          <Icons.MessageCircle />
                          <span>{task.comment_count || 0}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Subtle noise effect for active cards */}
                {isProcessing && (
                  <div className="absolute inset-0 opacity-[0.03] pointer-events-none mix-blend-overlay"></div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
