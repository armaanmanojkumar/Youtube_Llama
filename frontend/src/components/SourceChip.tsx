interface Props {
  videoId: string
  videoUrl: string
  startTime: number
  score: number
}

export function SourceChip({ videoId, videoUrl, startTime, score }: Props) {
  const url = `${videoUrl}&t=${Math.floor(startTime)}`
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      style={{ display: 'inline-block', background: '#f0f0f0', borderRadius: 12, padding: '2px 10px', marginRight: 6, marginTop: 4, fontSize: '0.78rem', textDecoration: 'none', color: '#333' }}
    >
      {videoId} @ {Math.floor(startTime)}s · {(score * 100).toFixed(0)}%
    </a>
  )
}
