interface Source {
  video_id: string
  video_url: string
  start_time: number
  score: number
  chunk: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  meta?: { model: string; response_time_s: number; chunks: number }
}

interface Props {
  messages: Message[]
}

function formatTs(seconds: number): string {
  const s = Math.floor(seconds)
  const mins = Math.floor(s / 60)
  const secs = s % 60
  const hrs = Math.floor(mins / 60)
  if (hrs) return `${hrs}:${String(mins % 60).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  return `${mins}:${String(secs).padStart(2, '0')}`
}

export function ChatWindow({ messages }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {messages.map((msg, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>

          <div style={{
            maxWidth: '85%',
            background: msg.role === 'user' ? '#0070f3' : '#f4f4f5',
            color: msg.role === 'user' ? '#fff' : '#111',
            borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            padding: '0.65rem 0.9rem',
            fontSize: '0.9rem',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
          }}>
            {msg.content}
          </div>

          {/* Sources as timestamp chips */}
          {msg.meta && (
            <div style={{ fontSize: '0.72rem', color: '#aaa', marginTop: 4, textAlign: 'left' }}>
              {msg.meta.model} · {msg.meta.response_time_s}s · {msg.meta.chunks} chunks
            </div>
          )}
          {msg.sources && msg.sources.length > 0 && (
            <div style={{ marginTop: '0.4rem', display: 'flex', flexWrap: 'wrap', gap: '0.3rem', maxWidth: '85%' }}>
              {msg.sources.map((s, j) => (
                <a
                  key={j}
                  href={`${s.video_url}&t=${Math.floor(s.start_time)}`}
                  target="_blank"
                  rel="noreferrer"
                  title={s.chunk}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    background: '#fff', border: '1px solid #e0e0e0',
                    borderRadius: 20, padding: '2px 10px',
                    fontSize: '0.75rem', color: '#444', textDecoration: 'none',
                  }}
                >
                  <span style={{ color: '#e00' }}>▶</span>
                  {formatTs(s.start_time)}
                  <span style={{ color: '#aaa' }}>· {(s.score * 100).toFixed(0)}%</span>
                </a>
              ))}
            </div>
          )}

        </div>
      ))}
    </div>
  )
}
