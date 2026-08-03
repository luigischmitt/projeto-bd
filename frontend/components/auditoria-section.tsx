"use client"

import { useEffect, useState } from "react"
import { AlertCircle, History, Loader2, Search } from "lucide-react"

import { Field } from "@/components/form-fields"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { api, formatDateTime } from "@/lib/api"

type AuditoriaRow = {
  id_auditoria: number
  id_atendimento: number
  operacao: "INSERT" | "UPDATE" | "DELETE" | string
  usuario: string
  data_hora: string
  dados_antigos: Record<string, unknown> | null
  dados_novos: Record<string, unknown> | null
}

const OPERACAO_STYLE: Record<string, string> = {
  INSERT: "bg-emerald-100 text-emerald-700",
  UPDATE: "bg-amber-100 text-amber-700",
  DELETE: "bg-destructive/10 text-destructive",
}

function formatValue(value: unknown) {
  if (value === null || value === undefined) return "—"
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

function DiffTable({ before, after }: { before: Record<string, unknown> | null; after: Record<string, unknown> | null }) {
  const keys = Array.from(new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})])).sort()
  if (!keys.length) {
    return <p className="text-sm text-muted-foreground">Sem dados registrados.</p>
  }
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="p-2 text-left font-medium">Campo</th>
            <th className="p-2 text-left font-medium">Antes (dados_antigos)</th>
            <th className="p-2 text-left font-medium">Depois (dados_novos)</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => {
            const beforeValue = before ? before[key] : undefined
            const afterValue = after ? after[key] : undefined
            const changed = JSON.stringify(beforeValue) !== JSON.stringify(afterValue)
            return (
              <tr key={key} className={changed ? "bg-amber-50" : undefined}>
                <td className="p-2 align-top font-medium whitespace-nowrap">{key}</td>
                <td className="p-2 align-top whitespace-pre-wrap text-muted-foreground">
                  {before ? formatValue(beforeValue) : "—"}
                </td>
                <td className={`p-2 align-top whitespace-pre-wrap ${changed ? "font-semibold" : ""}`}>
                  {after ? formatValue(afterValue) : "—"}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export function AuditoriaSection() {
  const [rows, setRows] = useState<AuditoriaRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [idAtendimentoFiltro, setIdAtendimentoFiltro] = useState("")

  async function load(idAtendimento?: string) {
    setLoading(true)
    setError(null)
    try {
      const query = idAtendimento ? `?id_atendimento=${idAtendimento}` : ""
      const response = await fetch(`${api}/auditoria/atendimentos${query}`)
      if (!response.ok) throw new Error("Não foi possível carregar o histórico de auditoria.")
      const data: AuditoriaRow[] = await response.json()
      setRows(data.sort((a, b) => b.id_auditoria - a.id_auditoria))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.")
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch inicial da tela
    void load()
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="size-4 text-primary" /> Auditoria de atendimentos
        </CardTitle>
        <CardDescription>
          Histórico gravado por <code>trg_audita_atendimento</code> em{" "}
          <code>auditoria_atendimento</code> a cada INSERT, UPDATE ou DELETE em atendimento, com o
          diff entre <code>dados_antigos</code> e <code>dados_novos</code>.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <form
          className="flex flex-col gap-2 sm:flex-row sm:items-end"
          onSubmit={(event) => {
            event.preventDefault()
            void load(idAtendimentoFiltro || undefined)
          }}
        >
          <div className="max-w-xs">
            <Field
              label="Filtrar por id do atendimento"
              type="number"
              min="1"
              placeholder="Ex.: 1"
              value={idAtendimentoFiltro}
              onChange={setIdAtendimentoFiltro}
            />
          </div>
          <Button type="submit" variant="outline">
            <Search className="size-4" /> Filtrar
          </Button>
          {idAtendimentoFiltro && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setIdAtendimentoFiltro("")
                void load()
              }}
            >
              Limpar filtro
            </Button>
          )}
        </form>

        {loading && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Carregando histórico de auditoria...
          </p>
        )}
        {error && (
          <p className="flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="size-4" /> {error}
          </p>
        )}
        {!loading && !error && !rows.length && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Nenhum registro de auditoria encontrado.
          </p>
        )}

        <div className="grid gap-3">
          {rows.map((row) => (
            <div key={row.id_auditoria} className="rounded-lg border p-3">
              <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    OPERACAO_STYLE[row.operacao] ?? "bg-muted text-muted-foreground"
                  }`}
                >
                  {row.operacao}
                </span>
                <span className="font-medium">Atendimento #{row.id_atendimento}</span>
                <span className="text-muted-foreground">
                  por {row.usuario} em {formatDateTime(row.data_hora, "utc")}
                </span>
              </div>
              <DiffTable before={row.dados_antigos} after={row.dados_novos} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
