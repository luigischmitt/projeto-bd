"use client"

import { FormEvent, useState } from "react"
import { AlertCircle, CheckCircle2, FlaskConical, Loader2, PlusCircle, Trash2 } from "lucide-react"

import { Field, SelectField } from "@/components/form-fields"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api, formatDateTime, useApiList } from "@/lib/api"

const RISCOS = [
  { value: "BAIXO", label: "BAIXO" },
  { value: "MEDIO", label: "MEDIO" },
  { value: "ALTO", label: "ALTO" },
]

type CatalogRow = {
  id_procedimento: number
  codigo: string
  nome: string
  tempo_medio_minutos: number
  nivel_risco: string
  media_tempo_procedimento: number | null
}

type ProcedimentoOption = {
  codigo: string
  nome_procedimento: string
  quantidade: number
  tempo_real_minutos: number
  faturado: boolean
}

type AtendimentoOption = {
  id_atendimento: number
  data_hora: string
  nome_paciente: string
}

type CreateState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success" }
  | { kind: "error"; detail: string }

function riscoClass(risco: string) {
  if (risco === "ALTO") return "text-destructive font-medium"
  if (risco === "MEDIO") return "text-amber-700 font-medium"
  return "text-muted-foreground"
}

export function ProcedimentosSection({
  catalogReady,
  atendimentos,
  attendanceId,
  procedureCode,
  procedimentosAtendimento,
  onSelectAttendance,
  onSelectProcedureCode,
  onRemove,
}: {
  catalogReady: boolean
  atendimentos: AtendimentoOption[]
  attendanceId: string
  procedureCode: string
  procedimentosAtendimento: ProcedimentoOption[]
  onSelectAttendance: (id: string) => void
  onSelectProcedureCode: (code: string) => void
  onRemove: () => void
}) {
  const { data, loading, error, reload } = useApiList<CatalogRow>("/procedimentos")
  const [codigo, setCodigo] = useState("")
  const [nome, setNome] = useState("")
  const [tempo, setTempo] = useState("")
  const [nivelRisco, setNivelRisco] = useState("BAIXO")
  const [createState, setCreateState] = useState<CreateState>({ kind: "idle" })

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreateState({ kind: "loading" })
    try {
      const response = await fetch(`${api}/procedimentos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          codigo,
          nome,
          tempo_medio_minutos: Number(tempo),
          nivel_risco: nivelRisco,
        }),
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) {
        setCreateState({
          kind: "error",
          detail: payload?.detail ?? "Não foi possível cadastrar o procedimento.",
        })
        return
      }
      setCreateState({ kind: "success" })
      setCodigo("")
      setNome("")
      setTempo("")
      setNivelRisco("BAIXO")
      await reload()
    } catch {
      setCreateState({ kind: "error", detail: "Erro de rede ao cadastrar procedimento." })
    }
  }

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlusCircle className="size-4 text-primary" /> Cadastrar procedimento
          </CardTitle>
          <CardDescription>
            Cria um item no catálogo com código, nome, tempo médio e nível de risco. Depois use
            esse procedimento em Atendimento completo ou nas consultas analíticas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Field label="Código" value={codigo} onChange={setCodigo} placeholder="PROC-06" required />
            <Field label="Nome" value={nome} onChange={setNome} required />
            <Field
              label="Tempo médio (min)"
              type="number"
              min="1"
              value={tempo}
              onChange={setTempo}
              required
            />
            <SelectField
              label="Nível de risco"
              value={nivelRisco}
              onChange={setNivelRisco}
              options={RISCOS}
              required
            />
            <Button type="submit" className="sm:mt-auto" disabled={createState.kind === "loading"}>
              {createState.kind === "loading" && <Loader2 className="size-4 animate-spin" />}
              Cadastrar
            </Button>
          </form>
          {createState.kind === "success" && (
            <p className="mt-3 flex items-center gap-2 text-sm text-emerald-700">
              <CheckCircle2 className="size-4" /> Procedimento cadastrado no catálogo.
            </p>
          )}
          {createState.kind === "error" && (
            <p className="mt-3 flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="size-4" /> {createState.detail}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="size-4 text-primary" /> Catálogo
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Carregando catálogo...
            </p>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {!loading && !error && data.length > 0 && (
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Nome</TableHead>
                    <TableHead>Tempo médio</TableHead>
                    <TableHead>Risco</TableHead>
                    <TableHead>id</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((row) => (
                    <TableRow key={row.id_procedimento}>
                      <TableCell>{row.codigo}</TableCell>
                      <TableCell>{row.nome}</TableCell>
                      <TableCell>{row.tempo_medio_minutos} min</TableCell>
                      <TableCell className={riscoClass(row.nivel_risco)}>{row.nivel_risco}</TableCell>
                      <TableCell>{row.id_procedimento}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="size-4 text-destructive" /> Remover procedimento realizado
          </CardTitle>
          <CardDescription>Procedimentos já faturados não podem ser removidos.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <SelectField
            label="Atendimento"
            value={attendanceId}
            onChange={onSelectAttendance}
            disabled={!catalogReady}
            placeholder="Selecione o atendimento"
            options={atendimentos.map((item) => ({
              value: String(item.id_atendimento),
              label: `#${item.id_atendimento} — ${item.nome_paciente} — ${formatDateTime(item.data_hora)}`,
            }))}
          />
          <SelectField
            label="Procedimento"
            value={procedureCode}
            onChange={onSelectProcedureCode}
            disabled={!attendanceId || procedimentosAtendimento.length === 0}
            placeholder={
              attendanceId
                ? procedimentosAtendimento.length
                  ? "Selecione o procedimento"
                  : "Nenhum procedimento neste atendimento"
                : "Selecione um atendimento primeiro"
            }
            options={procedimentosAtendimento.map((item) => ({
              value: item.codigo,
              label: item.faturado
                ? `${item.codigo} — ${item.nome_procedimento} (faturado)`
                : `${item.codigo} — ${item.nome_procedimento}`,
              disabled: item.faturado,
            }))}
          />
          <Button
            variant="destructive"
            className="sm:col-span-2 sm:w-fit"
            disabled={!attendanceId || !procedureCode}
            onClick={onRemove}
          >
            Remover procedimento
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
