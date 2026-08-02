import { useCallback, useEffect, useState } from "react"

export const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function formatMonth(value: string) {
  return new Date(value).toLocaleDateString("pt-BR", {
    month: "long",
    year: "numeric",
  })
}

// Pydantic serializa `timedelta` em ISO 8601 ("P1DT2H3M4.5S"); convertemos para
// algo legível como "1d 2h 3min" para exibição em tabela.
export function formatDuration(iso: string) {
  const match = /^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?)?$/.exec(iso)
  if (!match) return iso
  const [, days, hours, minutes, seconds] = match
  const parts: string[] = []
  if (Number(days) > 0) parts.push(`${days}d`)
  if (Number(hours) > 0) parts.push(`${hours}h`)
  if (Number(minutes) > 0) parts.push(`${minutes}min`)
  if (!parts.length) parts.push(`${Math.round(Number(seconds ?? 0))}s`)
  return parts.join(" ")
}

/**
 * Busca uma lista em `path` ao montar o componente e expõe `reload` para
 * refazer a busca sob demanda (ex.: após uma ação que muda o resultado).
 */
export function useApiList<T>(path: string) {
  const [data, setData] = useState<T[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${api}${path}`)
      if (!response.ok) throw new Error("Não foi possível carregar os dados.")
      setData(await response.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.")
      setData([])
    } finally {
      setLoading(false)
    }
  }, [path])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch inicial da tela
    void reload()
  }, [reload])

  return { data, loading, error, reload }
}
