---
name: whisperMe AI Workspace
colors:
  primary: "#FF6A1C"
  secondary: "#FFAE56"
  tertiary: "#FFDA62"
  accent: "#F5788B"
---

# whisperMe — AI Podcast Workstation Specification

This document defines the functional scope, data pipelines, and design constraints for **whisperMe** (a self-hosted, open-source podcast transcription and knowledge extraction tool). 

Stitch (and other AI design agents) should use this specification to freely design a highly condensed, modern, and beautiful workspace, utilizing the custom color palette (`#FF6A1C`, `#FFAE56`, `#FFDA62`, `#F5788B`) for visual accents.

---

## 1. Project Context & Aesthetic
- **Open-source & Self-hosted**: This is a local utility. There are **NO** login pages, **NO** registration, and **NO** subscription/paywall features. 
- **Workspace Focus**: Once settings are configured, the user only interacts with their local podcasts. The design should feel like a developer tool or a high-productivity workspace (like a code editor or a clean audio workstation).
- **Color Accents**: Use the primary orange (`#FF6A1C`), warm apricot (`#FFAE56`), bright gold (`#FFDA62`), and coral red (`#F5788B`) for active states, indicators, action buttons, progress bars, and high-priority visual items. The background and base interface can be dark or high-contrast to keep the workspace focused and modern.

---

## 2. Core Functional Requirements & Data Pipelines

To design the page layouts, Stitch must accommodate the following backend data pipelines and interactions:

### A. Podcast Ingest Pipeline
- **Inputs**: 
  - A text input box for pasting a podcast URL (supports Xiaoyuzhou, Bilibili).
  - A file uploader component for local audio files (e.g., MP3, WAV).
- **Triggers**: Submission kicks off an asynchronous backend task queue.

### B. Transcription & Speaker Diarization Pipeline
- **Backend Flow**: Audio is downloaded -> voiceprints are segmented (Diarization) -> audio is transcribed to text.
- **Diarization Interactions**: 
  - The UI must display text grouped by Speaker (e.g., "SPEAKER_00", "SPEAKER_01").
  - The user can hover and click to **rename a speaker** globally (e.g., changing "SPEAKER_00" to "Host Name").
  - The text must support clickable word/sentence timestamps that seek the audio player to that exact time.

### C. AI Summary & Shownotes Extraction Pipeline
- **LLM Output**: The backend generates a structured markdown analysis report containing:
  - Executive Summary.
  - Key Takeaways (bulleted lists).
  - Quotes (highlighted callouts).
  - Shownotes timestamps (a timeline of topics mentioned, e.g. `[12:34] Topic description`, which must be clickable to jump the audio player).
  - Performance Stats: precise execution duration for each step (download, transcribe, summary).

### D. System Performance Monitor
- **Micro Dashboard**: A small persistent visual widget showing real-time host resource metrics:
  - CPU usage percentage.
  - RAM usage stats (Used G / Total G).
  - Background task queue size (e.g., "3 tasks in queue").

### E. Configuration Dashboard
- Forms to configure local and online API keys:
  - **ASR settings**: Model paths, Hugging Face read tokens, MiMo API keys.
  - **LLM Summary settings**: Model select (Ollama or Online APIs), endpoint URLs, API keys.
  - **System/SMTP notifications**: Toggle for desktop notifications, email configuration.
  - **Appearance**: Language selection (简体/繁體/EN/JP) and custom base styling.

---

## 3. Stitch Design Freedom & Guidelines

Stitch has complete creative control to restructure, consolidate, or condense the user interface. Consider the following:

- **Page Consolidation**: Instead of a traditional multi-page structure, Stitch is encouraged to group the workstation into a highly efficient **Single-Workspace (SPA)** or **Split-Screen Console** (e.g., Library on the left, active Detail Workspace in the center, and Settings collapsible on the right or in a slide-out drawer).
- **Text & Audio Harmony**: Since reading transcripts while listening to audio is the primary activity, the audio control bar should be easily accessible, and the split between the transcript text and AI summaries should be clean, balanced, and readable.
- **Status Visibility**: Make the pipeline state (Downloading -> Transcribing -> Summarizing -> Completed) visually clear, active, and interactive.
- **Resource Stats Integration**: Keep the performance metrics (CPU, RAM, Queue) compact, integrated organically into the sidebar or status bar.
