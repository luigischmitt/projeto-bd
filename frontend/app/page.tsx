"use client"

import { FormEvent, useState } from "react"
import {
  Activity,
  AlertCircle,
  CalendarPlus,
  CheckCircle2,
  Loader2,
  Search,
  Trash2,
  Users,
} from "lucide-react"

import { AppSidebar } from "@/components/app-sidebar"
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

const VIEWS = {
  novo: { group: "Atendimentos", title: "Novo atendimento", description: "Cadastre um atendimento com os IDs existentes." },
  consultas: { group: "Atendimentos", title: "Consultas", description: "Use os IDs para listar atendimentos e procedimentos." },
  pacientes: { group: "Cadastros", title: "Pacientes", description: "Informe o ID e os campos que devem ser alterados." },
  procedimentos: { group: "Cadastros", title: "Procedimentos", description: "A remoção só é permitida para procedimentos ainda não faturados." },
  relatorios: { group: "Relatórios", title: "Painel analítico", description: "Indicadores operacionais do hospital." },
} as const

type ViewId = keyof typeof VIEWS

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
          <TableRow>{columns.map((column) => <TableHead key={column} className="whitespace-nowrap">{column.replaceAll("_", " ")}</TableHead>)}</TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={index}>
              {columns.map((column) => <TableCell key={column} className="whitespace-nowrap">{String(row[column] ?? "—")}</TableCell>)}
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
  const [patientId, setPatientId] = useState("")
  const [attendanceId, setAttendanceId] = useState("")
  const [procedureCode, setProcedureCode] = useState("")
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7))

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

  function updatePatient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    request(`/pacientes/${patientId}`, {
      method: "PUT",
      body: JSON.stringify({
        num_convenio: form.get("num_convenio") || null,
        alergias: form.get("alergias") || null,
        grupo_sanguineo: form.get("grupo_sanguineo") || null,
      }),
    })
  }

  const view_ = VIEWS[view]

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

          {view === "novo" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><CalendarPlus className="size-4 text-primary" /> Novo atendimento</CardTitle>
                <CardDescription>Cadastre um atendimento com os IDs existentes.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={createAttendance} className="grid gap-4 sm:grid-cols-2">
                  <Field label="Data e hora" name="data_hora" type="datetime-local" required />
                  <Field label="Duração (minutos)" name="duracao_minutos" type="number" min="1" required />
                  <Field label="ID do paciente" name="id_paciente" type="number" min="1" required />
                  <Field label="ID do residente" name="id_residente" type="number" min="1" required />
                  <Field label="ID do preceptor" name="id_preceptor" type="number" min="1" required />
                  <Button className="mt-auto" type="submit">Cadastrar atendimento</Button>
                </form>
              </CardContent>
            </Card>
          )}

          {view === "consultas" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Search className="size-4 text-primary" /> Consultas operacionais</CardTitle>
                <CardDescription>Use os IDs para listar atendimentos e procedimentos.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Input value={patientId} onChange={(event) => setPatientId(event.target.value)} type="number" min="1" placeholder="ID do paciente" />
                  <Button variant="outline" onClick={() => request(`/pacientes/${patientId}/atendimentos`)} disabled={!patientId}>Ver atendimentos</Button>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Input value={attendanceId} onChange={(event) => setAttendanceId(event.target.value)} type="number" min="1" placeholder="ID do atendimento" />
                  <Button variant="outline" onClick={() => request(`/atendimentos/${attendanceId}/procedimentos`)} disabled={!attendanceId}>Ver procedimentos</Button>
                </div>
                <Separator />
                <Button variant="outline" onClick={() => request("/residentes/tempo-medio")}>Tempo médio por residente</Button>
              </CardContent>
            </Card>
          )}

          {view === "pacientes" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Users className="size-4 text-primary" /> Atualizar paciente</CardTitle>
                <CardDescription>Informe o ID e os campos que devem ser alterados.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={updatePatient} className="grid gap-4 sm:grid-cols-2">
                  <Field label="ID do paciente" value={patientId} onChange={setPatientId} type="number" required />
                  <Field label="Número do convênio" name="num_convenio" />
                  <Field label="Alergias" name="alergias" />
                  <Field label="Grupo sanguíneo" name="grupo_sanguineo" placeholder="Ex.: O+" />
                  <Button type="submit">Salvar alterações</Button>
                </form>
              </CardContent>
            </Card>
          )}

          {view === "procedimentos" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Trash2 className="size-4 text-destructive" /> Remover procedimento</CardTitle>
                <CardDescription>A remoção só é permitida para procedimentos ainda não faturados.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 sm:flex-row">
                <Input value={attendanceId} onChange={(event) => setAttendanceId(event.target.value)} type="number" min="1" placeholder="ID do atendimento" />
                <Input value={procedureCode} onChange={(event) => setProcedureCode(event.target.value)} placeholder="Código do procedimento" />
                <Button
                  variant="destructive"
                  className="sm:w-auto"
                  disabled={!attendanceId || !procedureCode}
                  onClick={() => request(`/atendimentos/${attendanceId}/procedimentos/${procedureCode}`, { method: "DELETE" })}
                >
                  Remover
                </Button>
              </CardContent>
            </Card>
          )}

          {view === "relatorios" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Activity className="size-4 text-primary" /> Painel analítico</CardTitle>
                <CardDescription>Indicadores operacionais do hospital.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <Button variant="outline" className="h-auto min-h-16 justify-start text-left" onClick={() => request("/analytics/ranking-residentes")}>Ranking de residentes</Button>
                  <Button variant="outline" className="h-auto min-h-16 justify-start text-left" onClick={() => request("/analytics/plantoes-por-unidade")}>Plantões por unidade</Button>
                  <Button variant="outline" className="h-auto min-h-16 justify-start text-left" onClick={() => request("/analytics/pacientes-sem-risco-alto")}>Pacientes sem risco alto</Button>
                  <Button variant="outline" className="h-auto min-h-16 justify-start text-left" onClick={() => request(`/analytics/preceptores-supervisao?mes=${month}`)}>Supervisões em {month}</Button>
                </div>
                <div className="max-w-xs">
                  <Label htmlFor="month">Mês das supervisões</Label>
                  <Input id="month" value={month} onChange={(event) => setMonth(event.target.value)} type="month" className="mt-2" />
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
      <Input id={id} name={name} value={value} onChange={(event) => onChange?.(event.target.value)} {...props} />
    </div>
  )
}
