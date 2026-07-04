import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useUIStore = create(
  persist(
    (set) => ({
      activeTab: "dashboard",
      detailSourceTab: "dashboard",
      isIngestModalOpen: false,
      isAudioMissing: false,
      loading: false,
      detailLoading: false,
      uploading: false,

      setActiveTab: (tab) => set({ activeTab: tab }),
      setDetailSourceTab: (tab) => set({ detailSourceTab: tab }),
      setIsIngestModalOpen: (isOpen) => set({ isIngestModalOpen: isOpen }),
      setIsAudioMissing: (isMissing) => set({ isAudioMissing: isMissing }),
      setLoading: (loading) => set({ loading }),
      setDetailLoading: (loading) => set({ detailLoading: loading }),
      setUploading: (uploading) => set({ uploading }),
    }),
    {
      name: 'whisperme-ui-storage',
      partialize: (state) => ({ activeTab: state.activeTab }),
    }
  )
);
