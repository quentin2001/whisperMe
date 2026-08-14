/**
 * whisperMe 前端全局常量
 */
export const API_BASE = import.meta.env.DEV ? "http://127.0.0.1:9101" : "";

const isDemo =
  typeof window !== "undefined" &&
  (window.location.hostname.endsWith(".github.io") ||
   window.location.search.includes("demo=true") ||
   import.meta.env.VITE_DEMO === "true");

/**
 * 将图片 URL 通过后端代理加载，解决浏览器无法直接访问某些 CDN 的问题
 * 在 GitHub Pages 静态演示模式下直接返回原 URL（由 no-referrer 规避防盗链）
 * @param {string} url - 原始图片 URL
 * @returns {string} - 代理后的 URL 或原生 URL
 */
export function proxyImage(url) {
  if (!url) return url;
  // 静态 Demo 模式或者 GitHub Pages 下没有 Python 后端代理，直接使用图片原生 URL
  if (isDemo || url.startsWith("/") || url.startsWith("data:")) return url;
  return `${API_BASE}/api/proxy/image?url=${encodeURIComponent(url)}`;
}

