# Design: Split PodcastDetailView

## Directory Structure
We will establish a dedicated directory for podcast-related components to keep the components folder organized:
```
frontend/src/components/podcast/
  ├── AudioPlayerControl.jsx
  ├── TranscriptList.jsx
  ├── SpeakerManagerModal.jsx
  └── QAChatPanel.jsx
```

## Component Boundaries
1. **`AudioPlayerControl.jsx`**
   - **Responsibilities**: Render the bottom/floating playback bar. Control time tracking, progress bar sliding, volume adjustments, and playback speed toggles.
   - **State**: Consumes `usePlayerStore` (currentTime, isPlaying, duration, etc.).

2. **`TranscriptList.jsx`**
   - **Responsibilities**: Render the main list of transcription segments. Handle jump-to-time logic, inline editing triggers, and search keyword highlighting.
   - **Props Needed**: `segments`, `searchWord`, `onTimeClick`, `onSegmentEdit`.

3. **`SpeakerManagerModal.jsx`**
   - **Responsibilities**: Present the dialog to remap/rename `SPEAKER_XX` identifiers to real names. Provide UI for saving to the backend.
   - **Props Needed**: `isOpen`, `onClose`, `speakers`, `onSave`.

4. **`QAChatPanel.jsx`**
   - **Responsibilities**: Manage local chat history (`qaMessages`), user input (`qaInput`), and backend fetch logic for the RAG-based AI assistant.
   - **Props Needed**: `taskId` (to send queries to the right context).

5. **`PodcastDetailView.jsx`** (Orchestrator)
   - Retains the core wrapper layout (Left/Right split panes).
   - Manages top-level tabs (`shownotes`, `comments`, `summary`, `qa`).
   - Imports and mounts the 4 subcomponents in their designated UI slots.
