import { useEffect, useState } from 'react'
import { ChatWindow } from './components/ChatWindow'
import { useIngest } from './hooks/useIngest'
import { useOllama } from './hooks/useOllama'
import { useQuery } from './hooks/useQuery'
import { deleteVideo, getModels, getPerformance, getStats } from './api/client'

const SUGGESTED = [
  'Give me a summary of this video',
  'What are the main topics covered?',
  'At what timestamps is the most important content?',
  'Explain the key concepts discussed',
]

type Tab = 'chat' | 'database' | 'models'

export default function App() {
  const [tab, setTab] = useState<Tab>('chat')
  const [url, setUrl] = useState('')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<any[]>([])
  const [indexedVideo, setIndexedVideo] = useState<{ id: string; url: string } | null>(null)
  const [dbStats, setDbStats] = useState<any>(null)
  const [dbLoading, setDbLoading] = useState(false)
  const [activeModel, setActiveModel] = useState<string>('llama3.1:latest')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [perfData, setPerfData] = useState<any>(null)
  const [perfLoading, setPerfLoading] = useState(false)

  const { ingest, loading: ingesting, error: ingestError } = useIngest()
  const { query, loading: querying } = useQuery()
  const { available } = useOllama()

  // Poll active model from .env every 3s so UI stays in sync
  useEffect(() => {
    function refresh() {
      getModels().then(d => {
        setActiveModel(d.current)
        setAvailableModels(d.models)
      }).catch(() => {})
    }
    refresh()
    const id = setInterval(refresh, 30000)
    return () => clearInterval(id)
  }, [])

  async function handleIngest() {
    if (!url.trim()) return
    const result = await ingest(url.trim())
    if (result) {
      setIndexedVideo({ id: result.video_id, url: url.trim() })
      setMessages([])
      setUrl('')
    }
  }

  async function handleAsk(q: string) {
    if (!q.trim() || querying) return
    setQuestion('')
    setMessages(prev => [...prev, { role: 'user', content: q }])
    const result = await query(q)
    if (result) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.answer,
        sources: result.sources,
        meta: result.meta,
      }])
    }
  }

  async function handleLoadDb() {
    setDbLoading(true)
    const data = await getStats()
    setDbStats(data)
    setDbLoading(false)
  }

  async function handleLoadPerf() {
    setPerfLoading(true)
    const data = await getPerformance()
    setPerfData(data)
    setPerfLoading(false)
  }

  async function handleDelete(videoId: string) {
    await deleteVideo(videoId)
    setDbStats((prev: any) => ({
      ...prev,
      total_videos: prev.total_videos - 1,
      total_chunks: prev.total_chunks - (prev.videos.find((v: any) => v.video_id === videoId)?.chunks ?? 0),
      videos: prev.videos.filter((v: any) => v.video_id !== videoId),
    }))
  }

  function handleTabChange(t: Tab) {
    setTab(t)
    if (t === 'database') handleLoadDb()
    if (t === 'models') handleLoadPerf()
  }

  return (
    <main style={{ maxWidth: 860, margin: '0 auto', padding: '2rem 1.5rem', fontFamily: 'system-ui, sans-serif' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.4rem' }}>YouTube RAG</h1>
          <p style={{ margin: '2px 0 0', fontSize: '0.8rem', color: '#888' }}>Ask anything about any YouTube video</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <span style={{
            fontSize: '0.75rem', padding: '4px 10px', borderRadius: 20,
            background: available ? '#d4edda' : available === false ? '#f8d7da' : '#fff3cd',
            color: available ? '#155724' : available === false ? '#721c24' : '#856404',
          }}>
            Ollama {available === null ? 'checking…' : available ? 'connected' : 'offline'}
          </span>
          <span style={{ fontSize: '0.72rem', color: '#888' }}>
            Model: <strong>{activeModel}</strong> · edit <code>.env</code> to switch
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>
        {([['chat', '💬 Chat'], ['database', '🗄️ Database'], ['models', '🤖 Models']] as [Tab, string][]).map(([t, label]) => (
          <button key={t} onClick={() => handleTabChange(t)}
            style={{ padding: '4px 16px', borderRadius: 20, border: '1px solid', cursor: 'pointer', fontWeight: tab === t ? 600 : 400, background: tab === t ? '#111' : '#fff', color: tab === t ? '#fff' : '#555', borderColor: tab === t ? '#111' : '#ddd' }}>
            {label}
          </button>
        ))}
      </div>

      {/* ── CHAT TAB ── */}
      {tab === 'chat' && (
        <>
          <section style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                style={{ flex: 1, padding: '0.6rem 0.75rem', border: '1px solid #ccc', borderRadius: 8, fontSize: '0.95rem' }}
                placeholder="Paste a YouTube URL…"
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleIngest()}
              />
              <button onClick={handleIngest} disabled={ingesting || !url.trim()}
                style={{ padding: '0.6rem 1.2rem', borderRadius: 8, background: '#0070f3', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, opacity: ingesting || !url.trim() ? 0.6 : 1 }}>
                {ingesting ? 'Indexing…' : 'Index'}
              </button>
            </div>
            {ingestError && <p style={{ color: '#c00', fontSize: '0.82rem', margin: '0.4rem 0 0' }}>{ingestError}</p>}
          </section>

          {indexedVideo && (
            <section style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.8rem', background: '#e8f4fd', color: '#0070f3', padding: '3px 10px', borderRadius: 20, fontWeight: 500 }}>
                  ✓ Indexed: <a href={indexedVideo.url} target="_blank" rel="noreferrer" style={{ color: '#0070f3' }}>{indexedVideo.id}</a>
                </span>
                <button onClick={() => { setIndexedVideo(null); setMessages([]) }}
                  style={{ fontSize: '0.75rem', background: 'none', border: 'none', color: '#888', cursor: 'pointer' }}>clear</button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {SUGGESTED.map(q => (
                  <button key={q} onClick={() => handleAsk(q)} disabled={querying}
                    style={{ fontSize: '0.8rem', padding: '4px 12px', borderRadius: 20, border: '1px solid #ddd', background: '#fafafa', cursor: 'pointer' }}>
                    {q}
                  </button>
                ))}
              </div>
            </section>
          )}

          <section>
            <div style={{ border: '1px solid #eee', borderRadius: 10, padding: '1rem', minHeight: 240, marginBottom: '0.75rem', overflowY: 'auto', maxHeight: 480 }}>
              {messages.length === 0
                ? <p style={{ color: '#bbb', textAlign: 'center', marginTop: '4rem', fontSize: '0.9rem' }}>
                    {indexedVideo ? 'Ask a question or pick a suggestion above' : 'Index a video to get started'}
                  </p>
                : <ChatWindow messages={messages} />}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                style={{ flex: 1, padding: '0.6rem 0.75rem', border: '1px solid #ccc', borderRadius: 8, fontSize: '0.95rem' }}
                placeholder={indexedVideo ? 'Ask anything about this video…' : 'Index a video first'}
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAsk(question)}
                disabled={querying || !indexedVideo}
              />
              <button onClick={() => handleAsk(question)} disabled={querying || !question.trim() || !indexedVideo}
                style={{ padding: '0.6rem 1.2rem', borderRadius: 8, background: '#111', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, opacity: querying || !question.trim() || !indexedVideo ? 0.5 : 1 }}>
                {querying ? '…' : 'Ask'}
              </button>
            </div>
          </section>
        </>
      )}

      {/* ── DATABASE TAB ── */}
      {tab === 'database' && (
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1rem' }}>Vector Store</h2>
            <button onClick={handleLoadDb} style={{ fontSize: '0.8rem', padding: '4px 12px', borderRadius: 6, border: '1px solid #ddd', cursor: 'pointer' }}>
              {dbLoading ? 'Loading…' : '↻ Refresh'}
            </button>
          </div>
          {dbStats && (
            <>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                {[{ label: 'Videos indexed', value: dbStats.total_videos }, { label: 'Total chunks', value: dbStats.total_chunks }, { label: 'Embedding dim', value: 768 }].map(card => (
                  <div key={card.label} style={{ flex: 1, border: '1px solid #eee', borderRadius: 8, padding: '0.75rem 1rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{card.value}</div>
                    <div style={{ fontSize: '0.75rem', color: '#888', marginTop: 2 }}>{card.label}</div>
                  </div>
                ))}
              </div>
              {dbStats.videos.length === 0
                ? <p style={{ color: '#aaa', textAlign: 'center' }}>No videos indexed yet.</p>
                : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
                        <th style={{ padding: '0.5rem' }}>Video ID</th>
                        <th style={{ padding: '0.5rem' }}>Chunks</th>
                        <th style={{ padding: '0.5rem' }}>Link</th>
                        <th style={{ padding: '0.5rem' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dbStats.videos.map((v: any) => (
                        <tr key={v.video_id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                          <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{v.video_id}</td>
                          <td style={{ padding: '0.5rem' }}>{v.chunks}</td>
                          <td style={{ padding: '0.5rem' }}><a href={v.video_url} target="_blank" rel="noreferrer" style={{ color: '#0070f3', fontSize: '0.8rem' }}>Open ↗</a></td>
                          <td style={{ padding: '0.5rem' }}>
                            <button onClick={() => handleDelete(v.video_id)}
                              style={{ fontSize: '0.75rem', color: '#c00', background: 'none', border: '1px solid #fcc', borderRadius: 4, padding: '2px 8px', cursor: 'pointer' }}>
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
            </>
          )}
        </section>
      )}

      {/* ── MODELS TAB ── */}
      {tab === 'models' && (
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1rem' }}>Model Performance</h2>
            <button onClick={handleLoadPerf} style={{ fontSize: '0.8rem', padding: '4px 12px', borderRadius: 6, border: '1px solid #ddd', cursor: 'pointer' }}>
              {perfLoading ? 'Loading…' : '↻ Refresh'}
            </button>
          </div>

          {/* Available models — read only, edit .env to switch */}
          <div style={{ marginBottom: '1.5rem', background: '#fafafa', border: '1px solid #eee', borderRadius: 8, padding: '0.75rem 1rem' }}>
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#555', fontWeight: 600 }}>Available models</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {availableModels.map(m => (
                <span key={m} style={{
                  fontSize: '0.8rem', padding: '4px 12px', borderRadius: 20, border: '1px solid',
                  background: m === activeModel ? '#111' : '#fff',
                  color: m === activeModel ? '#fff' : '#555',
                  borderColor: m === activeModel ? '#111' : '#ddd',
                }}>
                  {m} {m === activeModel ? '← active' : ''}
                </span>
              ))}
            </div>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', color: '#aaa' }}>
              To switch: edit <code>MODEL=...</code> in <code>.env</code> — takes effect on the next query, no restart needed.
            </p>
          </div>

          {/* Performance table */}
          {perfData && (
            <>
              {perfData.summary.length === 0
                ? <p style={{ color: '#aaa' }}>No queries recorded yet. Ask some questions in the Chat tab first.</p>
                : (
                  <>
                    <p style={{ fontSize: '0.8rem', color: '#666', margin: '0 0 0.5rem', fontWeight: 600 }}>Performance by model</p>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', marginBottom: '2rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
                          <th style={{ padding: '0.5rem' }}>Model</th>
                          <th style={{ padding: '0.5rem' }}>Runs</th>
                          <th style={{ padding: '0.5rem' }}>Avg time</th>
                          <th style={{ padding: '0.5rem' }}>Avg length</th>
                        </tr>
                      </thead>
                      <tbody>
                        {perfData.summary.map((s: any) => (
                          <tr key={s.model} style={{ borderBottom: '1px solid #f0f0f0', background: s.model === activeModel ? '#f0f7ff' : 'transparent' }}>
                            <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 600 }}>{s.model} {s.model === activeModel ? '←' : ''}</td>
                            <td style={{ padding: '0.5rem' }}>{s.queries}</td>
                            <td style={{ padding: '0.5rem' }}>{s.avg_time_s}s</td>
                            <td style={{ padding: '0.5rem' }}>{s.avg_chars} chars</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    <p style={{ fontSize: '0.8rem', color: '#666', margin: '0 0 0.5rem', fontWeight: 600 }}>Recent runs</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      {[...perfData.records].reverse().slice(0, 20).map((r: any, i: number) => (
                        <div key={i} style={{ fontSize: '0.8rem', background: '#fafafa', border: '1px solid #eee', borderRadius: 6, padding: '0.5rem 0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                          <span style={{ color: '#333', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>"{r.query}"</span>
                          <span style={{ color: '#888', whiteSpace: 'nowrap', fontFamily: 'monospace', fontSize: '0.75rem' }}>{r.model} · {r.response_time_s}s · {r.answer_chars} chars</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
            </>
          )}
        </section>
      )}
    </main>
  )
}
