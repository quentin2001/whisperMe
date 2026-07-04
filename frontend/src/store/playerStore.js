import { create } from 'zustand';

export const usePlayerStore = create((set) => ({
  currentTime: 0,
  isPlaying: false,
  duration: 0,
  playbackRate: 1.0,
  volume: 0.8,
  
  setCurrentTime: (time) => set({ currentTime: time }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setDuration: (duration) => set({ duration }),
  setPlaybackRate: (rate) => set({ playbackRate: rate }),
  setVolume: (volume) => set({ volume }),
}));
