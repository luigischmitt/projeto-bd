"use client"

import { FormEvent, useState } from "react"
import { AlertTriangle, CheckCircle2, ListPlus, Loader2, PlusCircle, Trash2 } from "lucide-react"

import { Field, SelectField } from "@/components/form-fields"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { api } from "@/lib/api"

type PacienteOption = { id_pessoa: number; nome: string }
type ProfissionalOption = { id_profissional: number; nome: string }
type UnidadeOption = { id_unidade: number; nome: string }

type ProcedimentoDraft = {
  key: number
  id_procedimento: string
  quantidade: string
  tempo_real_minutos: string
  data_hora_inicio: string
  observacao: string
}

function emptyProcedimento(key: number): ProcedimentoDraft {
  return {
    key,
    id_procedimento: "",
    quantidade: "1",
    tempo_real_minutos: "",
    data_hora_inicio: "",
    observacao: "",
  }
}

type SubmitResult =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; idAtendimento: number }
  | { kind: "rollback"; detail: string }
  | { kind: "error"; detail: string }

export function AtendimentoCompletoSection({
  catalogReady,
  pacientes,
  residentes,
  preceptores,
  unidades,
  onCreated,
}: {
  catalogReady: boolean
  pacientes: PacienteOption[]
  residentes: ProfissionalOption[]
  preceptores: ProfissionalOption[]
  unidades: UnidadeOption[]
  onCreated?: () => void
}) {
  const [dataHora, setDataHora] = useState("")
  const [duracao, setDuracao] = useState("")
  const [idPaciente, setIdPaciente] = useState("")
  const [idResidente, setIdResidente] = useState("")
  const [idPreceptor, setIdPreceptor] = useState("")
  const [idUnidade, setIdUnidade] = useState("")
  const [nextKey, setNextKey] = useState(1)
  const [procedimentos, setProcedimentos] = useState<ProcedimentoDraft[]>([emptyProcedimento(0)])
  const [result, setResult] = useState<SubmitResult>({ kind: "idle" })

  function addProcedimento() {
    setProcedimentos((current) => [...current, emptyProcedimento(nextKey)])
    setNextKey((key) => key + 1)
  }

  function removeProcedimento(key: number) {
    setProcedimentos((current) =>
      current.length > 1 ? current.filter((item) => item.key !== key) : current
    )
  }

  function updateProcedimento(key: number, patch: Partial<ProcedimentoDraft>) {
    setProcedimentos((current) =>
      current.map((item) => (item.key === key ? { ...item, ...patch } : item))
    )
  }

  function resetForm() {
    setDataHora("")
    setDuracao("")
    setIdPaciente("")
    setIdResidente("")
    setIdPreceptor("")
    setIdUnidade("")
    setProcedimentos([emptyProcedimento(nextKey)])
    setNextKey((key) => key + 1)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setResult({ kind: "loading" })
    try {
      const response = await fetch(`${api}/atendimentos/completo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          // Envia o valor local do <input datetime-local> sem converter para UTC: a
          // procedure espera TIMESTAMP (sem timezone) e o backend não faz esse ajuste.
          data_hora: dataHora,
          duracao_minutos: Number(duracao),
          id_paciente: Number(idPaciente),
          id_residente: Number(idResidente),
          id_preceptor: Number(idPreceptor),
          id_unidade: Number(idUnidade),
          procedimentos: procedimentos.map((item) => ({
            id_procedimento: Number(item.id_procedimento),
            quantidade: Number(item.quantidade),
            tempo_real_minutos: Number(item.tempo_real_minutos),
            data_hora_inicio: item.data_hora_inicio || null,
            observacao: item.observacao || null,
          })),
        }),
      })
      const data = await response.json()
      if (response.status === 400) {
        setResult({ kind: "rollback", detail: data.detail ?? "Procedimento inválido rejeitado pelo banco." })
        return
      }
      if (!response.ok) {
        setResult({ kind: "error", detail: data.detail ?? "Não foi possível registrar o atendimento." })
        return
      }
      setResult({ kind: "success", idAtendimento: data.id_atendimento })
      resetForm()
      onCreated?.()
    } catch {
      setResult({ kind: "error", detail: "Erro de rede ao registrar o atendimento." })
    }
  }

  const submitting = result.kind === "loading"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ListPlus className="size-4 text-primary" /> Atendimento completo
        </CardTitle>
        <CardDescription>
          Registra o atendimento e todos os procedimentos realizados em uma única chamada a{" "}
          <code>sp_registrar_atendimento_completo</code>. Se qualquer procedimento for inválido, o
          banco reverte a transação inteira: nem o atendimento nem os procedimentos anteriores da
          lista são criados.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6">
        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Data e hora"
              name="data_hora"
              type="datetime-local"
              value={dataHora}
              onChange={setDataHora}
              required
            />
            <Field
              label="Duração (minutos)"
              name="duracao_minutos"
              type="number"
              min="1"
              value={duracao}
              onChange={setDuracao}
              required
            />
            <SelectField
              label="Paciente"
              value={idPaciente}
              onChange={setIdPaciente}
              required
              disabled={!catalogReady}
              placeholder="Selecione o paciente"
              options={pacientes.map((item) => ({ value: String(item.id_pessoa), label: item.nome }))}
            />
            <SelectField
              label="Residente"
              value={idResidente}
              onChange={setIdResidente}
              required
              disabled={!catalogReady}
              placeholder="Selecione o residente"
              options={residentes.map((item) => ({
                value: String(item.id_profissional),
                label: item.nome,
              }))}
            />
            <SelectField
              label="Preceptor"
              value={idPreceptor}
              onChange={setIdPreceptor}
              required
              disabled={!catalogReady}
              placeholder="Selecione o preceptor"
              options={preceptores.map((item) => ({
                value: String(item.id_profissional),
                label: item.nome,
              }))}
            />
            <SelectField
              label="Unidade"
              value={idUnidade}
              onChange={setIdUnidade}
              required
              disabled={!catalogReady}
              placeholder="Selecione a unidade"
              options={unidades.map((item) => ({ value: String(item.id_unidade), label: item.nome }))}
            />
          </div>

          <div className="grid gap-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Procedimentos realizados</p>
              <Button type="button" variant="outline" size="sm" onClick={addProcedimento}>
                <PlusCircle className="size-4" /> Adicionar procedimento
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Use os códigos cadastrados no seed (id_procedimento 1 a 5). Um id inexistente ou uma
              quantidade/tempo fora do permitido dispara o rollback de toda a operação.
            </p>
            <div className="grid gap-3">
              {procedimentos.map((item, index) => (
                <div
                  key={item.key}
                  className="grid gap-3 rounded-lg border p-3 sm:grid-cols-5 sm:items-start"
                >
                  <Field
                    label={`Procedimento #${index + 1} — id`}
                    type="number"
                    min="1"
                    value={item.id_procedimento}
                    onChange={(value) => updateProcedimento(item.key, { id_procedimento: value })}
                    required
                  />
                  <Field
                    label="Quantidade"
                    type="number"
                    min="1"
                    value={item.quantidade}
                    onChange={(value) => updateProcedimento(item.key, { quantidade: value })}
                    required
                  />
                  <Field
                    label="Tempo real (min)"
                    type="number"
                    min="1"
                    value={item.tempo_real_minutos}
                    onChange={(value) =>
                      updateProcedimento(item.key, { tempo_real_minutos: value })
                    }
                    required
                  />
                  <Field
                    label="Início (opcional)"
                    type="datetime-local"
                    value={item.data_hora_inicio}
                    onChange={(value) => updateProcedimento(item.key, { data_hora_inicio: value })}
                  />
                  <div className="flex items-end gap-2 sm:col-span-1">
                    <Field
                      label="Observação"
                      value={item.observacao}
                      onChange={(value) => updateProcedimento(item.key, { observacao: value })}
                    />
                    <Button
                      type="button"
                      variant="destructive"
                      size="icon"
                      className="mb-0"
                      disabled={procedimentos.length === 1}
                      onClick={() => removeProcedimento(item.key)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Button type="submit" className="w-fit" disabled={!catalogReady || submitting}>
            {submitting && <Loader2 className="size-4 animate-spin" />}
            Registrar atendimento completo
          </Button>
        </form>

        {result.kind === "success" && (
          <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>
              Atendimento #{result.idAtendimento} registrado com sucesso, junto com todos os
              procedimentos informados.
            </p>
          </div>
        )}
        {result.kind === "rollback" && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <div>
              <p className="font-medium">
                Rollback: nenhum atendimento ou procedimento foi criado.
              </p>
              <p>
                A API respondeu 400 porque a procedure rejeitou um dos procedimentos. Como tudo
                roda em uma única transação, o banco desfez até o INSERT do atendimento.
              </p>
              <p className="mt-1 font-mono text-xs">{result.detail}</p>
            </div>
          </div>
        )}
        {result.kind === "error" && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <p>{result.detail}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
