import { useEffect } from 'react'
import { useTheme } from '../theme/ThemeProvider.jsx'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const { isDark, toggle } = useTheme()

  useEffect(() => {}, [isDark])

  return (
    <button className="btn" aria-label="Toggle theme" onClick={toggle}>
      {isDark ? <Sun size={16} /> : <Moon size={16} />} {isDark ? 'Light' : 'Dark'}
    </button>
  )
}


