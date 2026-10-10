import { createContext, useContext, useState, useCallback } from "react";

export interface HistoryItem {
  id: string;
  question: string;
  timestamp: number;
}

const STORAGE_KEY = "test-insight-history";

function loadHistory(): HistoryItem[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(items: HistoryItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

interface HistoryContextType {
  history: HistoryItem[];
  addToHistory: (question: string) => void;
  clearHistory: () => void;
}

const HistoryContext = createContext<HistoryContextType>({
  history: [],
  addToHistory: () => {},
  clearHistory: () => {},
});

export function HistoryProvider({ children }: { children: React.ReactNode }) {
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory);

  const addToHistory = useCallback((question: string) => {
    setHistory((prev) => {
      const filtered = prev.filter(
        (h) => h.question.toLowerCase() !== question.toLowerCase()
      );
      const updated = [
        { id: Date.now().toString(), question, timestamp: Date.now() },
        ...filtered,
      ].slice(0, 30);
      saveHistory(updated);
      return updated;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return (
    <HistoryContext.Provider value={{ history, addToHistory, clearHistory }}>
      {children}
    </HistoryContext.Provider>
  );
}

export function useHistory() {
  return useContext(HistoryContext);
}
