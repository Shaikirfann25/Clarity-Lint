'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';

type Ctx = {
  active: string;
  setActive: (value: string) => void;
  compact: boolean;
  setCompact: (value: boolean) => void;
  theme: 'dark' | 'light';
  setTheme: (value: 'dark' | 'light') => void;
};

const Context = createContext<Ctx | null>(null);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [active, setActive] = useState('overview');
  const [compact, setCompact] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('light');

  useEffect(() => {
    const saved = localStorage.getItem('clarity-theme');
    if (saved === 'dark' || saved === 'light') {
      setTheme(saved);
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('clarity-theme', theme);
  }, [theme]);

  const value = useMemo(
    () => ({ active, setActive, compact, setCompact, theme, setTheme }),
    [active, compact, theme]
  );

  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useWorkspace() {
  const value = useContext(Context);
  if (!value) throw new Error('WorkspaceProvider missing');
  return value;
}
