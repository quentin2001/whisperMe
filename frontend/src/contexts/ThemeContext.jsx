import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

const ThemeContext = createContext();

/**
 * themeMode: "light" | "dark" | "system"
 * resolvedTheme: "light" | "dark" (实际生效主题)
 */
export function ThemeProvider({ children }) {
  const [themeMode, setThemeMode] = useState(() => {
    const saved = localStorage.getItem("whisperme_theme_mode");
    if (saved === "light" || saved === "dark" || saved === "system") return saved;
    return "system";
  });

  const [resolvedTheme, setResolvedTheme] = useState(() => {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  // 跟随系统
  useEffect(() => {
    if (themeMode === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      setResolvedTheme(mq.matches ? "dark" : "light");
      const handler = (e) => setResolvedTheme(e.matches ? "dark" : "light");
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    } else {
      setResolvedTheme(themeMode);
    }
  }, [themeMode]);

  // 应用 DOM: 切换 .dark class → index.css .dark 变量自动生效
  useEffect(() => {
    const root = document.documentElement;
    if (resolvedTheme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [resolvedTheme]);

  // 持久化
  useEffect(() => {
    localStorage.setItem("whisperme_theme_mode", themeMode);
  }, [themeMode]);

  // 循环切换 light → dark → system → light
  const cycleTheme = useCallback(() => {
    setThemeMode(prev => prev === "light" ? "dark" : prev === "dark" ? "system" : "light");
  }, []);

  return (
    <ThemeContext.Provider value={{ themeMode, resolvedTheme, setThemeMode, cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
