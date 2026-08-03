"use client"

import { AlertCircle, BarChart3, Clock3, FlaskConical, Loader2, Percent, Users } from "lucide-react"

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
import { formatDateTime, useApiList } from "@/lib/api"

type TempoMedioEsperaRow = {
  id_unidade: number
  nome_unidade: string
  tempo_medio_espera_minutos: number
}

type PreceptorFlamenguistaRow = {
  preceptor: string
}

type UltimoAtendimentoRow = {
  paciente: string
  data_hora: string
  residente: string
  preceptor: string
  procedimentos: string[]
}

type PercentualAltoRiscoRow = {
  residente: string
  total_procedimentos: number
  total_alto_risco: number
  percentual_alto_risco: number
}

type ProcedimentoCatalogRow = {
  id_procedimento: number
  codigo: string
  nome: string
  tempo_medio_minutos: number
  nivel_risco: string
  media_tempo_procedimento: number | null
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

export function TempoMedioEsperaSection() {
  const { data, loading, error } = useApiList<TempoMedioEsperaRow>("/analytics/tempo-medio-espera")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock3 className="size-4 text-primary" /> Tempo médio de espera
        </CardTitle>
        <CardDescription>
          Resultado de <code>sp_calcular_tempo_medio_espera</code>: média, por unidade, entre a
          chegada do paciente e o início do primeiro procedimento.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ViewStatus
          loading={loading}
          error={error}
          empty={!data.length}
          loadingLabel="Calculando tempo médio de espera..."
          emptyLabel="Nenhum dado disponível."
        />
        {!loading && !error && data.length > 0 && (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Unidade</TableHead>
                  <TableHead>Tempo médio de espera</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id_unidade}>
                    <TableCell>{row.nome_unidade}</TableCell>
                    <TableCell>{row.tempo_medio_espera_minutos.toFixed(2)} min</TableCell>
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

export function ConsultasAvancadasSection() {
  const flamenguistas = useApiList<PreceptorFlamenguistaRow>("/analytics/preceptores-flamenguistas")
  const ultimos = useApiList<UltimoAtendimentoRow>("/analytics/ultimo-atendimento-por-paciente")
  const percentual = useApiList<PercentualAltoRiscoRow>("/analytics/percentual-alto-risco")

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="size-4 text-primary" /> Preceptores × pacientes flamenguistas
          </CardTitle>
          <CardDescription>
            Consulta ORM: preceptores que supervisionaram residentes que atenderam pacientes com{" "}
            <code>is_flamengo = TRUE</code>.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ViewStatus
            loading={flamenguistas.loading}
            error={flamenguistas.error}
            empty={!flamenguistas.data.length}
            loadingLabel="Carregando..."
            emptyLabel="Nenhum preceptor encontrado."
          />
          {!flamenguistas.loading && !flamenguistas.error && flamenguistas.data.length > 0 && (
            <ul className="list-inside list-disc text-sm">
              {flamenguistas.data.map((row) => (
                <li key={row.preceptor}>{row.preceptor}</li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="size-4 text-primary" /> Último atendimento por paciente
          </CardTitle>
          <CardDescription>
            Consulta ORM: atendimento mais recente de cada paciente, com residente, preceptor e
            procedimentos realizados.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ViewStatus
            loading={ultimos.loading}
            error={ultimos.error}
            empty={!ultimos.data.length}
            loadingLabel="Carregando..."
            emptyLabel="Nenhum atendimento encontrado."
          />
          {!ultimos.loading && !ultimos.error && ultimos.data.length > 0 && (
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Paciente</TableHead>
                    <TableHead>Data/hora</TableHead>
                    <TableHead>Residente</TableHead>
                    <TableHead>Preceptor</TableHead>
                    <TableHead>Procedimentos</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ultimos.data.map((row) => (
                    <TableRow key={row.paciente}>
                      <TableCell className="font-medium">{row.paciente}</TableCell>
                      <TableCell>{formatDateTime(row.data_hora)}</TableCell>
                      <TableCell>{row.residente}</TableCell>
                      <TableCell>{row.preceptor}</TableCell>
                      <TableCell className="whitespace-normal">
                        {row.procedimentos.length ? row.procedimentos.join(", ") : "—"}
                      </TableCell>
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
            <Percent className="size-4 text-primary" /> Percentual de risco ALTO por residente
          </CardTitle>
          <CardDescription>
            Consulta ORM: percentual de procedimentos ALTO sobre o total realizado por cada residente.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ViewStatus
            loading={percentual.loading}
            error={percentual.error}
            empty={!percentual.data.length}
            loadingLabel="Carregando..."
            emptyLabel="Nenhum residente com procedimentos realizados."
          />
          {!percentual.loading && !percentual.error && percentual.data.length > 0 && (
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Residente</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Alto risco</TableHead>
                    <TableHead>Percentual</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {percentual.data.map((row) => (
                    <TableRow key={row.residente}>
                      <TableCell className="font-medium">{row.residente}</TableCell>
                      <TableCell>{row.total_procedimentos}</TableCell>
                      <TableCell>{row.total_alto_risco}</TableCell>
                      <TableCell>{row.percentual_alto_risco.toFixed(1)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function MediaProcedimentosSection() {
  const { data, loading, error, reload } = useApiList<ProcedimentoCatalogRow>("/procedimentos")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FlaskConical className="size-4 text-primary" /> Média observada por procedimento
        </CardTitle>
        <CardDescription>
          Coluna <code>media_tempo_procedimento</code> mantida por{" "}
          <code>trg_atualiza_media_procedimentos</code>: é a média dos{" "}
          <strong>tempos reais</strong> registrados em atendimentos, não inclui o tempo
          cadastrado do catálogo. Cada novo atendimento completo com o procedimento entra no
          cálculo; clique em Atualizar para ver a média recalculada.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        <Button variant="outline" className="w-fit" onClick={() => void reload()}>
          Atualizar catálogo
        </Button>
        <ViewStatus
          loading={loading}
          error={error}
          empty={!data.length}
          loadingLabel="Carregando catálogo..."
          emptyLabel="Nenhum procedimento cadastrado."
        />
        {!loading && !error && data.length > 0 && (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Código</TableHead>
                  <TableHead>Nome</TableHead>
                  <TableHead>Risco</TableHead>
                  <TableHead>Tempo cadastrado</TableHead>
                  <TableHead>Média observada (trigger)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id_procedimento}>
                    <TableCell>{row.codigo}</TableCell>
                    <TableCell>{row.nome}</TableCell>
                    <TableCell>{row.nivel_risco}</TableCell>
                    <TableCell>{row.tempo_medio_minutos} min</TableCell>
                    <TableCell>
                      {row.media_tempo_procedimento != null
                        ? `${row.media_tempo_procedimento.toFixed(2)} min`
                        : "—"}
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
