// In dev, Vite proxies /api/* to the backend (see vite.config.js).
// In production, set VITE_API_BASE to your deployed backend URL.
const BASE = import.meta.env.VITE_API_BASE ?? ''

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Upload failed (${res.status})`)
  }
  return res.json()
}

export async function runAutoMode(filePath, totalFrames) {
  const form = new FormData()
  form.append('file_path', filePath)
  form.append('total_frames', totalFrames)
  const res = await fetch(`${BASE}/api/auto-mode`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Auto mode failed (${res.status})`)
  }
  return res.json()
}

export async function runPilotMode(userQuery, collectionName) {
  const res = await fetch(`${BASE}/api/pilot-mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_query: userQuery, collection_name: collectionName }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Pilot mode failed (${res.status})`)
  }
  return res.json()
}
