import { SourceChip } from './SourceChip'

interface Source {
  video_id: string
  video_url: string
  start_time: number
  score: number
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

interface Props {
  messages: Message[]
}

export function ChatWindow({ messages }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {messages.map((msg, i) => (
        <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
          <div style={{ background: msg.role === 'user' ? '#0070f3' : '#f4f4f4', color: msg.role === 'user' ? '#fff' : '#111', borderRadius: 10, padding: '0.6rem 0.85rem', fontSize: '0.9rem', lineHeight: 1.5 }}>
            {msg.content}
          </div>
          {msg.sources && msg.sources.length > 0 && (
            <div style={{ marginTop: 4 }}>
              {msg.sources.map((s, j) => (
                <SourceChip key={j} videoId={s.video_id} videoUrl={s.video_url} startTime={s.start_time} score={s.score} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
