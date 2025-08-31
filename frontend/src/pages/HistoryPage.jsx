import { useEffect, useState } from 'react'

const API_BASE = '/api'

export default function HistoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/history`)
        const data = await res.json()
        if (Array.isArray(data)) setItems(data)
        else setError(data.error || 'Failed to load history')
      } catch (e) {
        setError('Failed to load history')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) return <div>Loading...</div>
  if (error) return <div className="text-red-600">{error}</div>

  return (
    <div className="space-y-3">
      {items.map((it) => (
        <div key={it.id} className="rounded-md border border-gray-300 dark:border-gray-700 p-3">
          <div className="text-xs text-gray-500 mb-2">{new Date(it.timestamp).toLocaleString()}</div>
          <div className="mb-2">
            <span className="font-semibold">You:</span> {it.user_message}
          </div>
          <div className="whitespace-pre-wrap">
            <span className="font-semibold">MediQuery:</span> {it.bot_reply}
          </div>
        </div>
      ))}
      {items.length === 0 && <div>No history yet.</div>}
    </div>
  )
}


