# Design: Introduce Zustand State

## Store Architecture

We will create the following files in `frontend/src/store/`:

### 1. `playerStore.js`
```javascript
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
```

### 2. `configStore.js`
Manages application configuration, prompts, version info, and logs. Includes actions to update configs and persist if necessary.

### 3. `taskStore.js`
Manages the `tasks` array, `activeTask`, and `activeTaskId`.

### 4. `uiStore.js`
Manages `activeTab`, `detailSourceTab`, `isIngestModalOpen`, `loading`, `uploading`.

## Migration Plan
1. `npm install zustand`
2. Create the 4 store files.
3. Iteratively replace `useState` in `App.jsx` with zustand hooks.
4. Remove prop drilling: Update child components (`SettingsView.jsx`, `Player`, `DetailView`) to directly consume state from the stores using selectors.
