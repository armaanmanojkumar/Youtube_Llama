import { useEffect, useState } from 'react'
import { getModels } from '../api/client'

export function useOllama() {
  const [available, setAvailable] = useState<boolean | null>(null)
  const [models, setModels] = useState<string[]>([])

  useEffect(() => {
    getModels()
      .then(data => {
        setAvailable(true)
        setModels(data.models ?? [])
      })
      .catch(() => setAvailable(false))
  }, [])

  return { available, models }
}
