import { create } from 'zustand';

export const useConfigStore = create((set) => ({
  configData: {
    language: "zh",
    output_dir: "",
    default_model: "base",
    device: "auto",
    compute_type: "default",
    vad_filter: false,
    ollama_url: "http://localhost:11434",
    ollama_model: "qwen2.5:7b-instruct",
    online_summary_api_key: "",
    online_summary_base_url: "https://api.openai.com/v1",
    online_summary_model: "gpt-4o-mini",
    summary_mode: "local",
    theme: "dark",
    model_dir: "",
    hf_token: "",
    enable_speaker_inference: true
  },
  promptData: {
    prompt: ""
  },
  versionInfo: {
    version: "1.0.0",
    update_available: false,
    latest_version: "1.0.0",
    release_notes: ""
  },
  perfData: null,
  checkingVersion: false,
  promptSaveStatus: "idle",
  logs: [],

  setConfigData: (data) => set({ configData: data }),
  updateConfigData: (updates) => set((state) => ({ configData: { ...state.configData, ...updates } })),
  setPromptData: (data) => set({ promptData: data }),
  setVersionInfo: (info) => set({ versionInfo: info }),
  setPerfData: (data) => set({ perfData: data }),
  setCheckingVersion: (checking) => set({ checkingVersion: checking }),
  setPromptSaveStatus: (status) => set({ promptSaveStatus: status }),
  setLogs: (logsUpdater) => set((state) => ({ 
    logs: typeof logsUpdater === 'function' ? logsUpdater(state.logs) : logsUpdater 
  })),
}));
