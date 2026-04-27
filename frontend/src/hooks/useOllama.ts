import { useEffect, useState } from 'react'

export function useOllama(host = 'http://localhost:11434') {
  const [available, setAvailable] = useState<boolean | null>(null)
  const [models, setModels] = useState<string[]>([])

  useEffect(() => {
    fetch(`${host}/api/tags`)
      .then(r => r.json())
      .then(data => {
        setAvailable(true)
        setModels(data.models?.map((m: any) => m.name) ?? [])
      })
      .catch(() => setAvailable(false))
  }, [host])

  return { available, models }
}
