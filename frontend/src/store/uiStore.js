import { create } from 'zustand';

export const useUIStore = create((set) => ({
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
}));
