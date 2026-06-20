import React from 'react';

export default function Topbar({ activeTab, activeTask, onNewRecording }) {
  if (activeTab === 'dashboard') {
    return (
      <nav className="bg-surface/80 backdrop-blur-md docked full-width top-0 flex justify-between items-center px-margin h-16 w-full z-40 fixed border-b border-outline-variant/30 md:left-64 md:w-[calc(100%-16rem)]">
        <div className="flex items-center gap-gutter">
          <div className="flex items-center gap-2 md:hidden">
            <span className="font-headline-md text-headline-md font-bold text-on-surface">whisperMe</span>
          </div>
        </div>
        <div className="flex items-center gap-sm">
          <div className="relative hidden lg:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
            <input className="bg-surface-container-high border-none rounded-full pl-10 pr-4 py-2 text-sm focus:ring-1 focus:ring-primary w-64 coral-glow" placeholder="Search sessions..." type="text" />
          </div>
          <button className="material-symbols-outlined p-2 text-on-surface-variant hover:text-primary transition-all">settings</button>
        </div>
      </nav>
    );
  }

  if (activeTab === 'workstation') {
    return (
      <header className="sticky top-0 z-40 bg-surface/80 backdrop-blur-md flex items-center justify-between w-full px-margin-desktop py-base h-16 border-b border-outline-variant/30">
        <div className="flex items-center gap-sm md:hidden">
          <h1 className="font-headline-lg-mobile text-headline-lg-mobile font-bold text-primary">whisperMe</h1>
        </div>
        <div className="hidden md:flex items-center gap-sm">
          <span className="font-headline-md text-headline-md font-medium text-primary">Workstation</span>
        </div>
        <div className="flex items-center gap-md ml-auto">
          <button className="text-on-surface-variant hover:text-primary transition-colors flex items-center gap-xs">
            <span className="material-symbols-outlined" data-icon="filter_list">filter_list</span>
            <span className="font-label-md text-label-md">Filters</span>
          </button>
          <div className="h-6 w-px bg-outline-variant/30"></div>
          <button 
            onClick={onNewRecording}
            className="bg-[#f62440] hover:bg-[#d41f37] text-white font-bold py-2 px-6 rounded-full flex items-center gap-2 transition-all active:scale-95 shadow-sm text-label-md"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
            New Recording
          </button>
        </div>
      </header>
    );
  }

  if (activeTab === 'config') {
    return (
      <header className="sticky top-0 w-full z-20 bg-surface/80 backdrop-blur-md flex justify-between items-center px-margin-desktop py-4 max-w-container-max mx-auto">
        <div className="flex items-center gap-2">
          <span className="font-headline-lg text-headline-lg font-black text-primary">System Settings</span>
        </div>
        <div className="flex items-center gap-stack-md">
          <div className="relative group">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant opacity-50" data-icon="search">search</span>
            <input className="pl-10 pr-4 py-2 bg-surface-container border border-outline-variant rounded-full text-label-md focus:outline-none focus:ring-2 focus:ring-primary/20 w-64 transition-all focus:w-80" placeholder="Search parameters..." type="text" />
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-surface-variant rounded-full transition-colors text-on-surface-variant">
              <span className="material-symbols-outlined" data-icon="notifications">notifications</span>
            </button>
          </div>
        </div>
      </header>
    );
  }

  if (activeTab === 'detail') {
    return (
      <header className="fixed top-0 right-0 left-64 flex justify-between items-center bg-surface px-margin-desktop h-16 z-30 border-b border-outline-variant/30">
        <div className="flex items-center gap-4">
          <span className="font-headline-md text-headline-md font-medium text-primary">{activeTask ? activeTask.title : 'Strategic Review 2024.wav'}</span>
          <span className="bg-secondary-container text-on-secondary-container px-3 py-1 rounded-full font-label-sm text-label-sm">In Progress</span>
        </div>
        <div className="flex items-center gap-stack-lg">
          <div className="relative hidden lg:block">
            <input className="bg-surface-container border-none rounded-full px-6 py-2 w-64 text-label-md focus:ring-1 focus:ring-primary" placeholder="Search transcript..." type="text" />
            <span className="material-symbols-outlined absolute right-3 top-2 text-on-surface-variant" data-icon="search">search</span>
          </div>
        </div>
      </header>
    );
  }

  return null;
}
