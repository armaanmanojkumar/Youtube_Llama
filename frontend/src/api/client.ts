const BASE = 'http://localhost:8000'

export async function ingestVideo(url: string) {
  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function queryVideos(query: string, model?: string, top_k?: number) {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, ...(model && { model }), ...(top_k !== undefined && { top_k }) }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function listVideos() {
  const res = await fetch(`${BASE}/videos`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getStats() {
  const res = await fetch(`${BASE}/stats`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getModels() {
  const res = await fetch(`${BASE}/models`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getPerformance() {
  const res = await fetch(`${BASE}/performance`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteVideo(videoId: string) {
  const res = await fetch(`${BASE}/video/${videoId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
