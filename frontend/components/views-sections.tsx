"use client"

import { AlertCircle, BarChart3, BedDouble, Loader2, ShieldAlert } from "lucide-react"

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
import { formatDateTime, formatDuration, formatMonth, useApiList } from "@/lib/api"

export type PacienteInternadoRow = {
  id_internacao: number
  id_paciente: number
  nome_paciente: string
  id_unidade: number
  nome_unidade: string
  data_hora_entrada: string
  tempo_internado: string
}

export type ResidenteSemSupervisorRow = {
  id_escala: number
  id_residente: number
  nome_residente: string
  id_unidade: number
  nome_unidade: string
  dia_semana: string
  turno: string
  id_preceptor: number
  nome_preceptor: string
  titulacao_preceptor: string
}

export type ProcedimentoFrequenteItem = {
  procedimento: string
  quantidade: number
}

export type EstatisticaMensalRow = {
  mes: string
  id_unidade: number
  nome_unidade: string
  total_atendimentos: number
  duracao_media_minutos: number
  procedimentos_mais_frequentes: ProcedimentoFrequenteItem[]
}

function ViewStatus({
  loading,
  error,
  empty,
  loadingLabel,
  emptyLabel,
}: {
  loading: boolean
  error: string | null
  empty: boolean
  loadingLabel: string
  emptyLabel: string
}) {
  if (loading) {
    return (
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> {loadingLabel}
      </p>
    )
  }
  if (error) {
    return (
      <p className="flex items-center gap-2 text-sm text-destructive">
        <AlertCircle className="size-4" /> {error}
      </p>
    )
  }
  if (empty) {
    return <p className="py-6 text-center text-sm text-muted-foreground">{emptyLabel}</p>
  }
  return null
}

export function PacientesInternadosSection() {
  const { data, loading, error } = useApiList<PacienteInternadoRow>("/views/pacientes-internados")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BedDouble className="size-4 text-primary" /> Pacientes internados
        </CardTitle>
        <CardDescription>
          Pacientes cuja internação mais recente ainda está em curso (vw_pacientes_internados).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ViewStatus
          loading={loading}
          error={error}
          empty={!data.length}
          loadingLabel="Carregando pacientes internados..."
          emptyLabel="Nenhum paciente internado no momento."
        />
        {!loading && !error && data.length > 0 && (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Paciente</TableHead>
                  <TableHead>Unidade</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Tempo internado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id_internacao}>
                    <TableCell className="font-medium">{row.nome_paciente}</TableCell>
                    <TableCell>{row.nome_unidade}</TableCell>
                    <TableCell>{formatDateTime(row.data_hora_entrada)}</TableCell>
                    <TableCell>{formatDuration(row.tempo_internado)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function ResidentesSemSupervisorSection() {
  const { data, loading, error } = useApiList<ResidenteSemSupervisorRow>(
    "/views/residentes-sem-supervisor"
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldAlert className="size-4 text-destructive" /> Residentes sem supervisor
        </CardTitle>
        <CardDescription>
          Escalas de residentes sem supervisão de preceptor doutor (vw_residentes_sem_supervisor).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ViewStatus
          loading={loading}
          error={error}
          empty={!data.length}
          loadingLabel="Carregando residentes sem supervisor..."
          emptyLabel="Todos os residentes escalados têm supervisão de um preceptor doutor."
        />
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
                  <TableHead>Titulação</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id_escala}>
                    <TableCell className="font-medium">{row.nome_residente}</TableCell>
                    <TableCell>{row.nome_unidade}</TableCell>
                    <TableCell>{row.dia_semana}</TableCell>
                    <TableCell>{row.turno}</TableCell>
                    <TableCell>{row.nome_preceptor}</TableCell>
                    <TableCell>{row.titulacao_preceptor}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function EstatisticasMensaisSection() {
  const { data, loading, error } = useApiList<EstatisticaMensalRow>("/views/estatisticas-mensais")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="size-4 text-primary" /> Estatísticas mensais
        </CardTitle>
        <CardDescription>
          Total de atendimentos, duração média e procedimentos mais frequentes por unidade e mês
          (vw_estatisticas_atendimentos_mensal).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ViewStatus
          loading={loading}
          error={error}
          empty={!data.length}
          loadingLabel="Carregando estatísticas mensais..."
          emptyLabel="Nenhuma estatística disponível ainda."
        />
        {!loading && !error && data.length > 0 && (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Mês</TableHead>
                  <TableHead>Unidade</TableHead>
                  <TableHead>Atendimentos</TableHead>
                  <TableHead>Duração média</TableHead>
                  <TableHead>Procedimentos mais frequentes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={`${row.mes}-${row.id_unidade}`}>
                    <TableCell className="capitalize">{formatMonth(row.mes)}</TableCell>
                    <TableCell>{row.nome_unidade}</TableCell>
                    <TableCell>{row.total_atendimentos}</TableCell>
                    <TableCell>{row.duracao_media_minutos.toFixed(1)} min</TableCell>
                    <TableCell className="whitespace-normal">
                      {row.procedimentos_mais_frequentes
                        .map((item) => `${item.procedimento} (${item.quantidade})`)
                        .join(", ")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
