# Proposal: Introduce Zustand for State Management

## Problem
Currently, `frontend/src/App.jsx` manages over 20 different state variables using React's `useState` hook. 
This monolithic state architecture causes two major issues:
1. **Performance Bottleneck (Render Waterfall)**: Frequent state updates, such as the audio player's `currentTime` updating every frame/second, trigger re-renders of the entire `App` component tree.
2. **Prop Drilling**: Complex state manipulation callbacks and state variables are passed down multiple levels to child components (e.g., `SettingsView`, `DetailView`, `Player`), making the codebase brittle and difficult to maintain.

## Proposed Solution
Introduce `zustand` as the frontend state management library. We will decouple the monolithic state into domain-specific stores located in `frontend/src/store/`:
- **`usePlayerStore`**: Manages `currentTime`, `isPlaying`, `duration`, `volume`, `playbackRate`.
- **`useConfigStore`**: Manages `configData`, `promptData`, `versionInfo`, `logs`.
- **`useTaskStore`**: Manages `tasks`, `activeTask`, `activeTaskId`.
- **`useUIStore`**: Manages navigation (`activeTab`, `detailSourceTab`) and global loading states.

## Goals
- Eliminate unnecessary re-renders of the root component.
- Simplify prop passing.
- Improve testability and separation of concerns.
