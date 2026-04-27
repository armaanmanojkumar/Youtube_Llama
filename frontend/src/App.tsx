import { useState } from 'react'
import { ChatWindow } from './components/ChatWindow'
import { VideoCard } from './components/VideoCard'
import { useIngest } from './hooks/useIngest'
import { useOllama } from './hooks/useOllama'
import { useQuery } from './hooks/useQuery'
import { deleteVideo, listVideos } from './api/client'

export default function App() {
  const [url, setUrl] = useState('')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<any[]>([])
  const [videos, setVideos] = useState<any[]>([])
  const [showVideos, setShowVideos] = useState(false)

  const { ingest, loading: ingesting, result: ingestResult, error: ingestError } = useIngest()
  const { query, loading: querying } = useQuery()
  const { available } = useOllama()

  async function handleIngest() {
    const result = await ingest(url)
    if (result) setUrl('')
  }

  async function handleQuery() {
    if (!question.trim()) return
    const q = question
    setQuestion('')
    setMessages(prev => [...prev, { role: 'user', content: q }])
    const result = await query(q)
    if (result) {
      setMessages(prev => [...prev, { role: 'assistant', content: result.answer, sources: result.sources }])
    }
  }

  async function handleLoadVideos() {
    const data = await listVideos()
    setVideos(data)
    setShowVideos(true)
  }

  async function handleDelete(videoId: string) {
    await deleteVideo(videoId)
    setVideos(prev => prev.filter(v => v.video_id !== videoId))
  }

  return (
    <main style={{ maxWidth: 820, margin: '0 auto', padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>YouTube RAG</h1>
        <span style={{ fontSize: '0.8rem', padding: '4px 10px', borderRadius: 12, background: available ? '#d4edda' : '#f8d7da', color: available ? '#155724' : '#721c24' }}>
          Ollama {available === null ? '...' : available ? 'connected' : 'offline'}
        </span>
      </div>

      <section style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Index a Video</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            style={{ flex: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: 6 }}
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleIngest()}
          />
          <button onClick={handleIngest} disabled={ingesting || !url} style={{ padding: '0.5rem 1rem', borderRadius: 6, cursor: 'pointer' }}>
            {ingesting ? 'Indexing…' : 'Index'}
          </button>
        </div>
        {ingestResult && <p style={{ color: 'green', margin: '0.4rem 0 0', fontSize: '0.85rem' }}>Indexed {ingestResult.chunks_indexed} chunks for {ingestResult.video_id}</p>}
        {ingestError && <p style={{ color: 'red', margin: '0.4rem 0 0', fontSize: '0.85rem' }}>{ingestError}</p>}
      </section>

      <section style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Chat</h2>
          <button onClick={handleLoadVideos} style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: 6, cursor: 'pointer' }}>
            {showVideos ? 'Hide' : 'Show'} indexed videos
          </button>
        </div>

        {showVideos && (
          <div style={{ marginBottom: '1rem' }}>
            {videos.length === 0 ? <p style={{ fontSize: '0.85rem', color: '#888' }}>No videos indexed yet.</p> : videos.map(v => (
              <VideoCard key={v.video_id} videoId={v.video_id} videoUrl={v.video_url} onDelete={handleDelete} />
            ))}
          </div>
        )}

        <div style={{ border: '1px solid #eee', borderRadius: 8, padding: '1rem', minHeight: 200, marginBottom: '0.75rem' }}>
          {messages.length === 0
            ? <p style={{ color: '#aaa', textAlign: 'center', marginTop: '3rem' }}>Index a video and ask a question</p>
            : <ChatWindow messages={messages} />}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            style={{ flex: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: 6 }}
            placeholder="What did they say about…?"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleQuery()}
            disabled={querying}
          />
          <button onClick={handleQuery} disabled={querying || !question} style={{ padding: '0.5rem 1rem', borderRadius: 6, cursor: 'pointer' }}>
            {querying ? 'Thinking…' : 'Ask'}
          </button>
        </div>
      </section>
    </main>
  )
}
