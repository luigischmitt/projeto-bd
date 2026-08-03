"use client"

import { Fragment, useState } from "react"
import { AlertTriangle, CalendarClock, CheckCircle2, Loader2, ShieldAlert } from "lucide-react"

import { SelectField } from "@/components/form-fields"
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
import { api, useApiList } from "@/lib/api"

export type EscalaRow = {
  id_escala: number
  id_unidade: number
  nome_unidade: string
  dia_semana: string
  turno: string
  id_residente: number
  nome_residente: string
  id_preceptor: number
  nome_preceptor: string
}

const DIAS = [
  { value: "SEG", label: "Segunda" },
  { value: "TER", label: "Terça" },
  { value: "QUA", label: "Quarta" },
  { value: "QUI", label: "Quinta" },
  { value: "SEX", label: "Sexta" },
  { value: "SAB", label: "Sábado" },
  { value: "DOM", label: "Domingo" },
]

const TURNOS = [
  { value: "MANHA", label: "Manhã" },
  { value: "TARDE", label: "Tarde" },
  { value: "NOITE", label: "Noite" },
]

type ReajusteState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "conflict"; detail: string }
  | { kind: "error"; detail: string }

export function EscalasSection() {
  const { data, loading, error, reload } = useApiList<EscalaRow>("/escalas")
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [diaDestino, setDiaDestino] = useState("")
  const [turnoDestino, setTurnoDestino] = useState("")
  const [state, setState] = useState<ReajusteState>({ kind: "idle" })
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  function openReajuste(row: EscalaRow) {
    setExpandedId(row.id_escala)
    setDiaDestino("")
    setTurnoDestino("")
    setState({ kind: "idle" })
    setSuccessMessage(null)
  }

  function closeReajuste() {
    setExpandedId(null)
    setState({ kind: "idle" })
  }

  async function confirmReajuste(row: EscalaRow) {
    setState({ kind: "loading" })
    try {
      const response = await fetch(`${api}/escalas/reajustar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_residente: row.id_residente,
          dia_origem: row.dia_semana,
          turno_origem: row.turno,
          dia_destino: diaDestino,
          turno_destino: turnoDestino,
        }),
      })
      if (response.status === 409) {
        const data = await response.json()
        setState({ kind: "conflict", detail: data.detail ?? "Destino já ocupado." })
        return
      }
      if (!response.ok) {
        const data = await response.json().catch(() => null)
        setState({ kind: "error", detail: data?.detail ?? "Não foi possível reajustar a escala." })
        return
      }
      setExpandedId(null)
      setSuccessMessage(
        `Escala de ${row.nome_residente} movida de ${row.dia_semana}/${row.turno} para ${diaDestino}/${turnoDestino}.`
      )
      await reload()
    } catch {
      setState({ kind: "error", detail: "Erro de rede ao reajustar a escala." })
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="size-4 text-primary" /> Escalas
        </CardTitle>
        <CardDescription>
          Lista a grade semanal completa de plantões e permite mover um residente para outro
          dia/turno com <code>sp_reajustar_escala</code>. Se o destino já estiver ocupado, o
          banco recusa a troca e a API responde 409.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        {successMessage && (
          <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{successMessage}</p>
          </div>
        )}

        {loading && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Carregando escalas...
          </p>
        )}
        {error && (
          <p className="flex items-center gap-2 text-sm text-destructive">
            <AlertTriangle className="size-4" /> {error}
          </p>
        )}
        {!loading && !error && !data.length && (
          <p className="flex items-center gap-2 py-6 text-center text-sm text-muted-foreground">
            <ShieldAlert className="size-4" /> Nenhuma escala cadastrada no momento.
          </p>
        )}

        {!loading && !error && data.length > 0 && (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Residente</TableHead>
                  <TableHead>Unidade</TableHead>
                  <TableHead>Dia</TableHead>
                  <TableHead>Turno</TableHead>
                  <TableHead>Preceptor atual</TableHead>
                  <TableHead className="text-right">Ação</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <Fragment key={row.id_escala}>
                    <TableRow>
                      <TableCell className="font-medium">{row.nome_residente}</TableCell>
                      <TableCell>{row.nome_unidade}</TableCell>
                      <TableCell>{row.dia_semana}</TableCell>
                      <TableCell>{row.turno}</TableCell>
                      <TableCell>{row.nome_preceptor}</TableCell>
                      <TableCell className="text-right">
                        {expandedId === row.id_escala ? (
                          <Button variant="outline" size="sm" onClick={closeReajuste}>
                            Cancelar
                          </Button>
                        ) : (
                          <Button variant="outline" size="sm" onClick={() => openReajuste(row)}>
                            Reajustar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                    {expandedId === row.id_escala && (
                      <TableRow>
                        <TableCell colSpan={6} className="whitespace-normal bg-muted/30">
                          <div className="grid gap-3 py-2 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                            <SelectField
                              label="Dia de destino"
                              value={diaDestino}
                              onChange={setDiaDestino}
                              required
                              placeholder="Selecione o dia"
                              options={DIAS}
                            />
                            <SelectField
                              label="Turno de destino"
                              value={turnoDestino}
                              onChange={setTurnoDestino}
                              required
                              placeholder="Selecione o turno"
                              options={TURNOS}
                            />
                            <Button
                              disabled={!diaDestino || !turnoDestino || state.kind === "loading"}
                              onClick={() => confirmReajuste(row)}
                            >
                              {state.kind === "loading" && (
                                <Loader2 className="size-4 animate-spin" />
                              )}
                              Confirmar reajuste
                            </Button>
                          </div>
                          {state.kind === "conflict" && (
                            <div className="mt-2 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                              <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                              <div>
                                <p className="font-medium">
                                  Conflito de escala (HTTP 409): destino já ocupado.
                                </p>
                                <p className="font-mono text-xs">{state.detail}</p>
                              </div>
                            </div>
                          )}
                          {state.kind === "error" && (
                            <div className="mt-2 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                              <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                              <p>{state.detail}</p>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    )}
                  </Fragment>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
