import { useEffect, useState } from "react";

const STORAGE_KEY = "ayurip-theme";

function storedTheme() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    // Storage can be blocked (private mode, disabled site data)
    return null;
  }
}

function systemTheme() {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** Light/dark theme: follows the system until the user picks one. */
export function useTheme() {
  const [theme, setTheme] = useState(() => storedTheme() ?? systemTheme());

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#06110c" : "#f6f3ea");
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);

    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Not persisted; the choice still applies for this visit
    }
  };

  return [theme, toggleTheme];
}
