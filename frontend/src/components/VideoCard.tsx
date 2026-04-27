interface Props {
  videoId: string
  videoUrl: string
  onDelete?: (id: string) => void
}

export function VideoCard({ videoId, videoUrl, onDelete }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #eee', padding: '0.5rem 0.75rem', borderRadius: 6, marginBottom: '0.4rem' }}>
      <a href={videoUrl} target="_blank" rel="noreferrer" style={{ fontSize: '0.9rem' }}>{videoId}</a>
      {onDelete && (
        <button onClick={() => onDelete(videoId)} style={{ background: 'none', border: 'none', color: '#c00', cursor: 'pointer', fontSize: '0.8rem' }}>
          Remove
        </button>
      )}
    </div>
  )
}
