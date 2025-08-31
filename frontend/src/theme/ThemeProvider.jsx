import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const ThemeContext = createContext({ theme: 'system', isDark: false, setTheme: () => {}, toggle: () => {} })

function getSystemPrefersDark() {
  return typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyHtmlClass(isDark) {
  const root = document.documentElement
  if (isDark) root.classList.add('dark')
  else root.classList.remove('dark')
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    return localStorage.getItem('theme') || 'system'
  })

  const isDark = useMemo(() => (theme === 'system' ? getSystemPrefersDark() : theme === 'dark'), [theme])

  useEffect(() => {
    applyHtmlClass(isDark)
  }, [isDark])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (theme === 'system') applyHtmlClass(getSystemPrefersDark())
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  const value = useMemo(() => ({
    theme,
    isDark,
    setTheme: (t) => {
      localStorage.setItem('theme', t)
      setTheme(t)
    },
    toggle: () => {
      const next = isDark ? 'light' : 'dark'
      localStorage.setItem('theme', next)
      setTheme(next)
    }
  }), [theme, isDark])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  return useContext(ThemeContext)
}


