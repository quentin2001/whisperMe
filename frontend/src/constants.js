/**
 * whisperMe 前端全局常量
 */
export const API_BASE = import.meta.env.DEV ? "http://127.0.0.1:9101" : "";

/**
 * 将图片 URL 通过后端代理加载，解决浏览器无法直接访问某些 CDN 的问题
 * @param {string} url - 原始图片 URL
 * @returns {string} - 代理后的 URL
 */
export function proxyImage(url) {
  if (!url) return url;
  // 如果已经是本地代理或者是相对路径，直接返回
  if (url.startsWith("/") || url.startsWith("data:")) return url;
  return `${API_BASE}/api/proxy/image?url=${encodeURIComponent(url)}`;
}
