import { useState } from 'react'
import { queryVideos } from '../api/client'

export function useQuery() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  async function query(q: string, top_k = 4) {
    setLoading(true)
    setError(null)
    try {
      const data = await queryVideos(q, top_k)
      setResult(data)
      return data
    } catch (e: any) {
      setError(e.message)
      return null
    } finally {
      setLoading(false)
    }
  }

  return { query, loading, result, error }
}
