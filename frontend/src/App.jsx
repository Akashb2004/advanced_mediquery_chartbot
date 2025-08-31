import { Outlet, Link, useLocation } from 'react-router-dom'
import ThemeToggle from './components/ThemeToggle.jsx'
import BackgroundFX from './components/BackgroundFX.jsx'

function App() {
  const location = useLocation()

  return (
    <div className="container-app">
      <BackgroundFX />
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-gray-900/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-gray-900/60 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-lg sm:text-xl font-semibold tracking-tight">MediQuery</Link>
          <nav className="flex items-center gap-2">
            <Link className={`btn ${location.pathname==='/'?'!bg-blue-600 !text-white':''}`} to="/">Chat</Link>
            <Link className={`btn ${location.pathname.startsWith('/history')?'!bg-blue-600 !text-white':''}`} to="/history">History</Link>
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main className="flex-1 pb-6">
        <Outlet />
      </main>
      <footer className="py-6 text-xs text-gray-500 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-4xl mx-auto px-4">Built with React, Flask, and Gemini.</div>
      </footer>
    </div>
  )
}

export default App
