import { create } from 'zustand';

export const useTaskStore = create((set) => ({
  tasks: [],
  activeTaskId: null,
  activeTask: null,
  newUrl: "",
  audioSource: "link",

  setTasks: (tasks) => set({ tasks }),
  setActiveTaskId: (id) => set({ activeTaskId: id }),
  setActiveTask: (task) => set({ activeTask: task }),
  setNewUrl: (url) => set({ newUrl: url }),
  setAudioSource: (source) => set({ audioSource: source }),
}));
