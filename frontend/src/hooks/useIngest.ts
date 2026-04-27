import { useState } from 'react'
import { ingestVideo } from '../api/client'

export function useIngest() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  async function ingest(url: string) {
    setLoading(true)
    setError(null)
    try {
      const data = await ingestVideo(url)
      setResult(data)
      return data
    } catch (e: any) {
      setError(e.message)
      return null
    } finally {
      setLoading(false)
    }
  }

  return { ingest, loading, result, error }
}
