import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useTaskStore = create(
  persist(
    (set) => ({
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
    }),
    {
      name: 'whisperme-task-storage',
      partialize: (state) => ({ activeTaskId: state.activeTaskId }),
    }
  )
);
