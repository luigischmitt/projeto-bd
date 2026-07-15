"use client"

import { FormEvent, useCallback, useEffect, useState } from "react"
import {
  Activity,
  AlertCircle,
  CalendarPlus,
  CheckCircle2,
  Loader2,
  Search,
  Trash2,
} from "lucide-react"

import { AppSidebar } from "@/components/app-sidebar"
import {
  PacientesSection,
  PreceptoresSection,
  ResidentesSection,
  readPessoaFromForm,
  readProfissionalFromForm,
  toDateInput,
  type CadastroMode,
  type PacienteOption,
  type PreceptorOption,
  type ResidenteOption,
} from "@/components/cadastro-sections"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type Row = Record<string, unknown>
type Status = "idle" | "loading" | "success" | "error"

type AtendimentoOption = {
  id_atendimento: number
  data_hora: string
  duracao_minutos: number
  id_paciente: number
  nome_paciente: string
}

type ProcedimentoOption = {
  codigo: string
  nome_procedimento: string
  quantidade: number
  tempo_real_minutos: number
  faturado: boolean
}

const VIEWS = {
  novo: {
    group: "Atendimentos",
    title: "Novo atendimento",
    description: "Selecione paciente, residente e preceptor para registrar um atendimento.",
  },
  consultas: {
    group: "Atendimentos",
    title: "Consultas",
    description: "Consulte atendimentos, procedimentos e indicadores operacionais.",
  },
  pacientes: {
    group: "Cadastros",
    title: "Pacientes",
    description: "Cadastre novos pacientes ou atualize dados de pacientes existentes.",
  },
  residentes: {
    group: "Cadastros",
    title: "Residentes",
    description: "Cadastre médicos residentes ou atualize dados de residentes existentes.",
  },
  preceptores: {
    group: "Cadastros",
    title: "Preceptores",
    description: "Cadastre preceptores ou atualize dados de preceptores existentes.",
  },
  procedimentos: {
    group: "Cadastros",
    title: "Procedimentos",
    description: "Remova procedimentos realizados que ainda não foram faturados.",
  },
  relatorios: {
    group: "Relatórios",
    title: "Painel analítico",
    description: "Indicadores operacionais do hospital.",
  },
} as const

type ViewId = keyof typeof VIEWS

const selectClassName =
  "border-input bg-background ring-offset-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-xs transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"

function formatDateTime(value: string) {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function StatusPill({ status, message }: { status: Status; message: string }) {
  const styles: Record<Status, string> = {
    idle: "bg-muted text-muted-foreground",
    loading: "bg-accent text-accent-foreground",
    success: "bg-emerald-100 text-emerald-700",
    error: "bg-destructive/10 text-destructive",
  }
  const icons: Record<Status, React.ReactNode> = {
    idle: null,
    loading: <Loader2 className="size-3.5 animate-spin" />,
    success: <CheckCircle2 className="size-3.5" />,
    error: <AlertCircle className="size-3.5" />,
  }
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${styles[status]}`}>
      {icons[status]}
      {message}
    </span>
  )
}

function Results({ rows }: { rows: Row[] }) {
  if (!rows.length) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        Nenhum resultado para exibir ainda.
      </p>
    )
  }

  const columns = Object.keys(rows[0])
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column} className="whitespace-nowrap">
                {column.replaceAll("_", " ")}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={index}>
              {columns.map((column) => (
                <TableCell key={column} className="whitespace-nowrap">
                  {String(row[column] ?? "—")}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export default function Home() {
  const [view, setView] = useState<ViewId>("novo")
  const [result, setResult] = useState<Row[]>([])
  const [status, setStatus] = useState<Status>("idle")
  const [message, setMessage] = useState("Selecione uma ação para ver os resultados.")
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [catalogError, setCatalogError] = useState<string | null>(null)

  const [pacientes, setPacientes] = useState<PacienteOption[]>([])
  const [residentes, setResidentes] = useState<ResidenteOption[]>([])
  const [preceptores, setPreceptores] = useState<PreceptorOption[]>([])
  const [atendimentos, setAtendimentos] = useState<AtendimentoOption[]>([])
  const [procedimentosAtendimento, setProcedimentosAtendimento] = useState<ProcedimentoOption[]>([])

  const [patientId, setPatientId] = useState("")
  const [residenteId, setResidenteId] = useState("")
  const [preceptorId, setPreceptorId] = useState("")
  const [attendanceId, setAttendanceId] = useState("")
  const [procedureCode, setProcedureCode] = useState("")
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7))

  const [pacienteMode, setPacienteMode] = useState<CadastroMode>("novo")
  const [residenteMode, setResidenteMode] = useState<CadastroMode>("novo")
  const [preceptorMode, setPreceptorMode] = useState<CadastroMode>("novo")

  const [pNome, setPNome] = useState("")
  const [pCpf, setPCpf] = useState("")
  const [pDataNascimento, setPDataNascimento] = useState("")
  const [pTelefone, setPTelefone] = useState("")
  const [pIsFlamengo, setPIsFlamengo] = useState(false)
  const [convenio, setConvenio] = useState("")
  const [alergias, setAlergias] = useState("")
  const [grupoSanguineo, setGrupoSanguineo] = useState("")

  const [rNome, setRNome] = useState("")
  const [rCpf, setRCpf] = useState("")
  const [rDataNascimento, setRDataNascimento] = useState("")
  const [rTelefone, setRTelefone] = useState("")
  const [rIsFlamengo, setRIsFlamengo] = useState(false)
  const [rCrm, setRCrm] = useState("")
  const [rDataAdmissao, setRDataAdmissao] = useState("")
  const [rEspecialidade, setREspecialidade] = useState("")
  const [rAnoResidencia, setRAnoResidencia] = useState("")

  const [prNome, setPrNome] = useState("")
  const [prCpf, setPrCpf] = useState("")
  const [prDataNascimento, setPrDataNascimento] = useState("")
  const [prTelefone, setPrTelefone] = useState("")
  const [prIsFlamengo, setPrIsFlamengo] = useState(false)
  const [prCrm, setPrCrm] = useState("")
  const [prDataAdmissao, setPrDataAdmissao] = useState("")
  const [prEspecialidade, setPrEspecialidade] = useState("")
  const [prTitulacao, setPrTitulacao] = useState("")

  const loadCatalog = useCallback(async () => {
    setCatalogLoading(true)
    setCatalogError(null)
    try {
      const [pacientesRes, residentesRes, preceptoresRes, atendimentosRes] = await Promise.all([
        fetch(`${api}/pacientes`),
        fetch(`${api}/residentes`),
        fetch(`${api}/preceptores`),
        fetch(`${api}/atendimentos`),
      ])

      if (!pacientesRes.ok || !residentesRes.ok || !preceptoresRes.ok || !atendimentosRes.ok) {
        throw new Error("Não foi possível carregar os cadastros do hospital.")
      }

      setPacientes(await pacientesRes.json())
      setResidentes(await residentesRes.json())
      setPreceptores(await preceptoresRes.json())
      setAtendimentos(await atendimentosRes.json())
    } catch (error) {
      setCatalogError(error instanceof Error ? error.message : "Erro ao carregar cadastros.")
    } finally {
      setCatalogLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch inicial de cadastros
    void loadCatalog()
  }, [loadCatalog])

  function selectPatient(id: string) {
    setPatientId(id)
    const paciente = pacientes.find((item) => String(item.id_pessoa) === id)
    if (paciente) {
      setPNome(paciente.nome)
      setPCpf(paciente.cpf)
      setPDataNascimento(toDateInput(paciente.data_nascimento))
      setPTelefone(paciente.telefone)
      setPIsFlamengo(paciente.is_flamengo)
      setConvenio(paciente.num_convenio ?? "")
      setAlergias(paciente.alergias ?? "")
      setGrupoSanguineo(paciente.grupo_sanguineo ?? "")
    } else {
      setPNome("")
      setPCpf("")
      setPDataNascimento("")
      setPTelefone("")
      setPIsFlamengo(false)
      setConvenio("")
      setAlergias("")
      setGrupoSanguineo("")
    }
  }

  function selectResidente(id: string) {
    setResidenteId(id)
    const residente = residentes.find((item) => String(item.id_profissional) === id)
    if (residente) {
      setRNome(residente.nome)
      setRCpf(residente.cpf)
      setRDataNascimento(toDateInput(residente.data_nascimento))
      setRTelefone(residente.telefone)
      setRIsFlamengo(residente.is_flamengo)
      setRCrm(residente.crm)
      setRDataAdmissao(toDateInput(residente.data_admissao))
      setREspecialidade(residente.especialidade)
      setRAnoResidencia(residente.ano_residencia)
    } else {
      setRNome("")
      setRCpf("")
      setRDataNascimento("")
      setRTelefone("")
      setRIsFlamengo(false)
      setRCrm("")
      setRDataAdmissao("")
      setREspecialidade("")
      setRAnoResidencia("")
    }
  }

  function selectPreceptorCadastro(id: string) {
    setPreceptorId(id)
    const preceptor = preceptores.find((item) => String(item.id_profissional) === id)
    if (preceptor) {
      setPrNome(preceptor.nome)
      setPrCpf(preceptor.cpf)
      setPrDataNascimento(toDateInput(preceptor.data_nascimento))
      setPrTelefone(preceptor.telefone)
      setPrIsFlamengo(preceptor.is_flamengo)
      setPrCrm(preceptor.crm)
      setPrDataAdmissao(toDateInput(preceptor.data_admissao))
      setPrEspecialidade(preceptor.especialidade)
      setPrTitulacao(preceptor.titulacao)
    } else {
      setPrNome("")
      setPrCpf("")
      setPrDataNascimento("")
      setPrTelefone("")
      setPrIsFlamengo(false)
      setPrCrm("")
      setPrDataAdmissao("")
      setPrEspecialidade("")
      setPrTitulacao("")
    }
  }

  async function selectAttendance(id: string) {
    setAttendanceId(id)
    setProcedureCode("")
    if (!id) {
      setProcedimentosAtendimento([])
      return
    }

    try {
      const response = await fetch(`${api}/atendimentos/${id}/procedimentos`)
      if (!response.ok) throw new Error("Não foi possível carregar os procedimentos.")
      const data: ProcedimentoOption[] = await response.json()
      setProcedimentosAtendimento(data)
      const firstAvailable = data.find((item) => !item.faturado)
      setProcedureCode(firstAvailable?.codigo ?? "")
    } catch {
      setProcedimentosAtendimento([])
      setProcedureCode("")
    }
  }

  async function refreshProcedimentosAtendimento() {
    if (!attendanceId) return
    const response = await fetch(`${api}/atendimentos/${attendanceId}/procedimentos`)
    if (!response.ok) return
    const data: ProcedimentoOption[] = await response.json()
    setProcedimentosAtendimento(data)
    setProcedureCode("")
  }

  const atendimentosDoPaciente = patientId
    ? atendimentos.filter((item) => String(item.id_paciente) === patientId)
    : atendimentos

  async function request(path: string, options?: RequestInit) {
    setStatus("loading")
    setMessage("Carregando...")
    try {
      const response = await fetch(`${api}${path}`, {
        ...options,
        headers: { "Content-Type": "application/json", ...options?.headers },
      })
      const data = response.status === 204 ? null : await response.json()
      if (!response.ok) throw new Error(data.detail ?? "Não foi possível concluir a operação.")
      setResult(Array.isArray(data) ? data : data ? [data] : [])
      setStatus("success")
      setMessage(response.status === 204 ? "Procedimento removido." : "Operação concluída.")
      if (options?.method && ["POST", "PUT", "DELETE"].includes(options.method)) {
        await loadCatalog()
      }
      if (path.includes("/procedimentos/") && options?.method === "DELETE" && attendanceId) {
        await refreshProcedimentosAtendimento()
      }
    } catch (error) {
      setResult([])
      setStatus("error")
      setMessage(error instanceof Error ? error.message : "Erro inesperado.")
    }
  }

  function createAttendance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    request("/atendimentos", {
      method: "POST",
      body: JSON.stringify({
        data_hora: new Date(String(form.get("data_hora"))).toISOString(),
        duracao_minutos: Number(form.get("duracao_minutos")),
        id_paciente: Number(form.get("id_paciente")),
        id_residente: Number(form.get("id_residente")),
        id_preceptor: Number(form.get("id_preceptor")),
      }),
    })
  }

  function createPatient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    request("/pacientes", {
      method: "POST",
      body: JSON.stringify({
        ...readPessoaFromForm(form),
        num_convenio: form.get("num_convenio") || null,
        alergias: form.get("alergias") || null,
        grupo_sanguineo: form.get("grupo_sanguineo") || null,
      }),
    })
    event.currentTarget.reset()
  }

  function updatePatient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    request(`/pacientes/${patientId}`, {
      method: "PUT",
      body: JSON.stringify({
        nome: pNome,
        cpf: pCpf,
        data_nascimento: pDataNascimento,
        is_flamengo: pIsFlamengo,
        telefone: pTelefone,
        num_convenio: convenio || null,
        alergias: alergias || null,
        grupo_sanguineo: grupoSanguineo || null,
      }),
    })
  }

  function createResidente(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    request("/residentes", {
      method: "POST",
      body: JSON.stringify({
        ...readProfissionalFromForm(form),
        ano_residencia: String(form.get("ano_residencia")),
      }),
    })
    event.currentTarget.reset()
  }

  function updateResidente(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    request(`/residentes/${residenteId}`, {
      method: "PUT",
      body: JSON.stringify({
        nome: rNome,
        cpf: rCpf,
        data_nascimento: rDataNascimento,
        is_flamengo: rIsFlamengo,
        telefone: rTelefone,
        crm: rCrm,
        data_admissao: rDataAdmissao,
        especialidade: rEspecialidade,
        ano_residencia: rAnoResidencia,
      }),
    })
  }

  function createPreceptor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    request("/preceptores", {
      method: "POST",
      body: JSON.stringify({
        ...readProfissionalFromForm(form),
        titulacao: String(form.get("titulacao")),
      }),
    })
    event.currentTarget.reset()
  }

  function updatePreceptor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    request(`/preceptores/${preceptorId}`, {
      method: "PUT",
      body: JSON.stringify({
        nome: prNome,
        cpf: prCpf,
        data_nascimento: prDataNascimento,
        is_flamengo: prIsFlamengo,
        telefone: prTelefone,
        crm: prCrm,
        data_admissao: prDataAdmissao,
        especialidade: prEspecialidade,
        titulacao: prTitulacao,
      }),
    })
  }

  const view_ = VIEWS[view]
  const catalogReady = !catalogLoading && !catalogError

  return (
    <SidebarProvider>
      <AppSidebar activeId={view} onSelect={(id) => setView(id as ViewId)} />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-3 border-b px-4 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="h-4" />
          <div>
            <p className="text-xs font-medium text-muted-foreground">{view_.group}</p>
            <h1 className="text-sm font-semibold leading-none">{view_.title}</h1>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-6 p-4 md:p-6">
          <p className="text-sm text-muted-foreground">{view_.description}</p>

          {catalogLoading && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Carregando cadastros...
            </p>
          )}
          {catalogError && (
            <p className="text-sm text-destructive">{catalogError}</p>
          )}

          {view === "novo" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarPlus className="size-4 text-primary" /> Novo atendimento
                </CardTitle>
                <CardDescription>
                  Escolha quem participou do atendimento. Paciente, residente e preceptor devem estar cadastrados.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={createAttendance} className="grid gap-4 sm:grid-cols-2">
                  <Field label="Data e hora" name="data_hora" type="datetime-local" required />
                  <Field label="Duração (minutos)" name="duracao_minutos" type="number" min="1" required />
                  <SelectField
                    label="Paciente"
                    name="id_paciente"
                    required
                    disabled={!catalogReady}
                    placeholder="Selecione o paciente"
                    options={pacientes.map((item) => ({
                      value: String(item.id_pessoa),
                      label: `${item.nome} — convênio ${item.num_convenio ?? "N/A"}`,
                    }))}
                  />
                  <SelectField
                    label="Residente"
                    name="id_residente"
                    required
                    disabled={!catalogReady}
                    placeholder="Selecione o residente"
                    options={residentes.map((item) => ({
                      value: String(item.id_profissional),
                      label: `${item.nome} (${item.ano_residencia})`,
                    }))}
                  />
                  <SelectField
                    label="Preceptor"
                    name="id_preceptor"
                    required
                    disabled={!catalogReady}
                    placeholder="Selecione o preceptor"
                    options={preceptores.map((item) => ({
                      value: String(item.id_profissional),
                      label: `${item.nome} — ${item.titulacao}`,
                    }))}
                  />
                  <Button className="mt-auto" type="submit" disabled={!catalogReady}>
                    Cadastrar atendimento
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {view === "consultas" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="size-4 text-primary" /> Consultas operacionais
                </CardTitle>
                <CardDescription>
                  Liste atendimentos por paciente, procedimentos de um atendimento ou tempo médio por residente.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="flex flex-col gap-2 sm:flex-row">
                  <SelectField
                    label="Paciente"
                    value={patientId}
                    onChange={selectPatient}
                    disabled={!catalogReady}
                    placeholder="Selecione o paciente"
                    options={pacientes.map((item) => ({
                      value: String(item.id_pessoa),
                      label: item.nome,
                    }))}
                  />
                  <Button
                    variant="outline"
                    className="sm:mt-auto"
                    onClick={() => request(`/pacientes/${patientId}/atendimentos`)}
                    disabled={!patientId}
                  >
                    Ver atendimentos
                  </Button>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <SelectField
                    label="Atendimento"
                    value={attendanceId}
                    onChange={selectAttendance}
                    disabled={!catalogReady}
                    placeholder="Selecione o atendimento"
                    options={(patientId ? atendimentosDoPaciente : atendimentos).map((item) => ({
                      value: String(item.id_atendimento),
                      label: `#${item.id_atendimento} — ${item.nome_paciente} — ${formatDateTime(item.data_hora)}`,
                    }))}
                  />
                  <Button
                    variant="outline"
                    className="sm:mt-auto"
                    onClick={() => request(`/atendimentos/${attendanceId}/procedimentos`)}
                    disabled={!attendanceId}
                  >
                    Ver procedimentos
                  </Button>
                </div>
                <Separator />
                <Button variant="outline" onClick={() => request("/residentes/tempo-medio")}>
                  Tempo médio por residente
                </Button>
              </CardContent>
            </Card>
          )}

          {view === "pacientes" && (
            <PacientesSection
              mode={pacienteMode}
              onModeChange={setPacienteMode}
              catalogReady={catalogReady}
              pacientes={pacientes}
              patientId={patientId}
              onSelectPatient={selectPatient}
              form={{
                nome: pNome,
                cpf: pCpf,
                dataNascimento: pDataNascimento,
                telefone: pTelefone,
                isFlamengo: pIsFlamengo,
                convenio,
                alergias,
                grupoSanguineo,
                setNome: setPNome,
                setCpf: setPCpf,
                setDataNascimento: setPDataNascimento,
                setTelefone: setPTelefone,
                setIsFlamengo: setPIsFlamengo,
                setConvenio,
                setAlergias,
                setGrupoSanguineo,
              }}
              onCreate={createPatient}
              onUpdate={updatePatient}
            />
          )}

          {view === "residentes" && (
            <ResidentesSection
              mode={residenteMode}
              onModeChange={setResidenteMode}
              catalogReady={catalogReady}
              residentes={residentes}
              residenteId={residenteId}
              onSelectResidente={selectResidente}
              form={{
                nome: rNome,
                cpf: rCpf,
                dataNascimento: rDataNascimento,
                telefone: rTelefone,
                isFlamengo: rIsFlamengo,
                crm: rCrm,
                dataAdmissao: rDataAdmissao,
                especialidade: rEspecialidade,
                anoResidencia: rAnoResidencia,
                setNome: setRNome,
                setCpf: setRCpf,
                setDataNascimento: setRDataNascimento,
                setTelefone: setRTelefone,
                setIsFlamengo: setRIsFlamengo,
                setCrm: setRCrm,
                setDataAdmissao: setRDataAdmissao,
                setEspecialidade: setREspecialidade,
                setAnoResidencia: setRAnoResidencia,
              }}
              onCreate={createResidente}
              onUpdate={updateResidente}
            />
          )}

          {view === "preceptores" && (
            <PreceptoresSection
              mode={preceptorMode}
              onModeChange={setPreceptorMode}
              catalogReady={catalogReady}
              preceptores={preceptores}
              preceptorId={preceptorId}
              onSelectPreceptor={selectPreceptorCadastro}
              form={{
                nome: prNome,
                cpf: prCpf,
                dataNascimento: prDataNascimento,
                telefone: prTelefone,
                isFlamengo: prIsFlamengo,
                crm: prCrm,
                dataAdmissao: prDataAdmissao,
                especialidade: prEspecialidade,
                titulacao: prTitulacao,
                setNome: setPrNome,
                setCpf: setPrCpf,
                setDataNascimento: setPrDataNascimento,
                setTelefone: setPrTelefone,
                setIsFlamengo: setPrIsFlamengo,
                setCrm: setPrCrm,
                setDataAdmissao: setPrDataAdmissao,
                setEspecialidade: setPrEspecialidade,
                setTitulacao: setPrTitulacao,
              }}
              onCreate={createPreceptor}
              onUpdate={updatePreceptor}
            />
          )}

          {view === "procedimentos" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trash2 className="size-4 text-destructive" /> Remover procedimento
                </CardTitle>
                <CardDescription>
                  Procedimentos já faturados não podem ser removidos.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <SelectField
                  label="Atendimento"
                  value={attendanceId}
                  onChange={selectAttendance}
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
                  onChange={setProcedureCode}
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
                  onClick={() =>
                    request(`/atendimentos/${attendanceId}/procedimentos/${procedureCode}`, {
                      method: "DELETE",
                    })
                  }
                >
                  Remover procedimento
                </Button>
              </CardContent>
            </Card>
          )}

          {view === "relatorios" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="size-4 text-primary" /> Painel analítico
                </CardTitle>
                <CardDescription>Indicadores operacionais do hospital.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <Button
                    variant="outline"
                    className="h-auto min-h-16 justify-start text-left"
                    onClick={() => request("/analytics/ranking-residentes")}
                  >
                    Ranking de residentes
                  </Button>
                  <Button
                    variant="outline"
                    className="h-auto min-h-16 justify-start text-left"
                    onClick={() => request("/analytics/plantoes-por-unidade")}
                  >
                    Plantões por unidade
                  </Button>
                  <Button
                    variant="outline"
                    className="h-auto min-h-16 justify-start text-left"
                    onClick={() => request("/analytics/pacientes-sem-risco-alto")}
                  >
                    Pacientes sem risco alto
                  </Button>
                  <Button
                    variant="outline"
                    className="h-auto min-h-16 justify-start text-left"
                    onClick={() => request(`/analytics/preceptores-supervisao?mes=${month}`)}
                  >
                    Supervisões em {month}
                  </Button>
                </div>
                <div className="max-w-xs">
                  <Label htmlFor="month">Mês das supervisões</Label>
                  <Input
                    id="month"
                    value={month}
                    onChange={(event) => setMonth(event.target.value)}
                    type="month"
                    className="mt-2"
                  />
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">Resultado</CardTitle>
              <StatusPill status={status} message={message} />
            </CardHeader>
            <CardContent>
              <Results rows={result} />
            </CardContent>
          </Card>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

function Field({
  label,
  name,
  value,
  onChange,
  ...props
}: Omit<React.ComponentProps<typeof Input>, "onChange" | "value"> & {
  label: string
  name?: string
  value?: string
  onChange?: (value: string) => void
}) {
  const id = name ?? label.toLowerCase().replaceAll(" ", "-")
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        name={name}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        {...props}
      />
    </div>
  )
}

function SelectField({
  label,
  name,
  value,
  onChange,
  options,
  placeholder,
  required,
  disabled,
}: {
  label: string
  name?: string
  value?: string
  onChange?: (value: string) => void
  options: { value: string; label: string; disabled?: boolean }[]
  placeholder?: string
  required?: boolean
  disabled?: boolean
}) {
  const id = name ?? label.toLowerCase().replaceAll(" ", "-")
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        name={name}
        {...(value !== undefined ? { value } : {})}
        required={required}
        disabled={disabled}
        onChange={(event) => onChange?.(event.target.value)}
        className={selectClassName}
      >
        <option value="">{placeholder ?? "Selecione..."}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={option.disabled}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}
