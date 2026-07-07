import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? '/whisperMe/' : '/',
  plugins: [react(), tailwindcss()],
  server: {
    port: 9173,
  },
})
