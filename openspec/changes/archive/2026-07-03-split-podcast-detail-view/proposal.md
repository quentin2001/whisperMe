# Proposal: Split PodcastDetailView into Subcomponents

## Problem
`PodcastDetailView.jsx` has ballooned to over 1,650 lines of code. This massive size severely degrades maintainability, hampers parallel development, and makes it challenging to pinpoint UI logic. A single file handling the audio player controls, transcription logic, modal dialogs, and QA chat violates the Single Responsibility Principle.

## Proposed Solution
We will systematically dismantle `PodcastDetailView.jsx` by extracting its major visual and logical blocks into isolated, reusable child components located in a new directory: `frontend/src/components/podcast/`.
The 4 main subcomponents to extract are:
1. `AudioPlayerControl.jsx`: Manages play/pause, seek, volume, and playback speed.
2. `TranscriptList.jsx`: Renders the timestamped text segments and manages keyword highlights/search.
3. `SpeakerManagerModal.jsx`: Handles the logic for renaming and mapping speakers.
4. `QAChatPanel.jsx`: Isolates the interactive AI conversational interface.

`PodcastDetailView.jsx` will be significantly reduced in size, functioning solely as an orchestrator and layout container.

## Goals
- Drastically reduce the line count of `PodcastDetailView.jsx`.
- Promote component reusability and isolated unit testing.
- Make the codebase cleaner, more scannable, and scalable.
