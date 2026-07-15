"use client"

import { FormEvent } from "react"
import { GraduationCap, UserCog, UserPlus, Users } from "lucide-react"

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

const selectClassName =
  "border-input bg-background ring-offset-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-xs transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"

export type CadastroMode = "novo" | "atualizar"

export type PacienteOption = {
  id_pessoa: number
  nome: string
  cpf: string
  data_nascimento: string
  is_flamengo: boolean
  telefone: string
  num_convenio: string | null
  alergias: string | null
  grupo_sanguineo: string | null
}

export type ResidenteOption = {
  id_profissional: number
  nome: string
  cpf: string
  data_nascimento: string
  is_flamengo: boolean
  telefone: string
  crm: string
  data_admissao: string
  especialidade: string
  ano_residencia: string
}

export type PreceptorOption = {
  id_profissional: number
  nome: string
  cpf: string
  data_nascimento: string
  is_flamengo: boolean
  telefone: string
  crm: string
  data_admissao: string
  especialidade: string
  titulacao: string
}

function toDateInput(value: string) {
  return value.slice(0, 10)
}

function readPessoaFromForm(form: FormData) {
  return {
    nome: String(form.get("nome")),
    cpf: String(form.get("cpf")),
    data_nascimento: String(form.get("data_nascimento")),
    is_flamengo: form.get("is_flamengo") === "on",
    telefone: String(form.get("telefone")),
  }
}

function readProfissionalFromForm(form: FormData) {
  return {
    ...readPessoaFromForm(form),
    crm: String(form.get("crm")),
    data_admissao: String(form.get("data_admissao")),
    especialidade: String(form.get("especialidade")),
  }
}

function ModeToggle({
  mode,
  onChange,
  disabled,
}: {
  mode: CadastroMode
  onChange: (mode: CadastroMode) => void
  disabled?: boolean
}) {
  return (
    <div className="flex gap-2">
      <Button
        type="button"
        size="sm"
        variant={mode === "novo" ? "default" : "outline"}
        disabled={disabled}
        onClick={() => onChange("novo")}
      >
        Novo cadastro
      </Button>
      <Button
        type="button"
        size="sm"
        variant={mode === "atualizar" ? "default" : "outline"}
        disabled={disabled}
        onClick={() => onChange("atualizar")}
      >
        Atualizar existente
      </Button>
    </div>
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
  options: { value: string; label: string }[]
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
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

function CheckboxField({
  label,
  name,
  checked,
  onChange,
}: {
  label: string
  name: string
  checked?: boolean
  onChange?: (checked: boolean) => void
}) {
  const id = name
  return (
    <div className="flex items-center gap-2 pt-6">
      <input
        id={id}
        name={name}
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange?.(event.target.checked)}
        className="size-4 rounded border"
      />
      <Label htmlFor={id}>{label}</Label>
    </div>
  )
}

function PessoaFieldsForm() {
  return (
    <>
      <Field label="Nome completo" name="nome" required />
      <Field label="CPF" name="cpf" placeholder="Somente números" minLength={11} maxLength={11} required />
      <Field label="Data de nascimento" name="data_nascimento" type="date" required />
      <Field label="Telefone" name="telefone" placeholder="Ex.: 83990000000" required />
      <CheckboxField label="Torcedor do Flamengo" name="is_flamengo" />
    </>
  )
}

function ProfissionalFieldsForm() {
  return (
    <>
      <PessoaFieldsForm />
      <Field label="CRM" name="crm" required />
      <Field label="Data de admissão" name="data_admissao" type="date" required />
      <Field label="Especialidade" name="especialidade" required />
    </>
  )
}

type SubmitHandler = (event: FormEvent<HTMLFormElement>) => void

export function PacientesSection({
  mode,
  onModeChange,
  catalogReady,
  pacientes,
  patientId,
  onSelectPatient,
  form,
  onCreate,
  onUpdate,
}: {
  mode: CadastroMode
  onModeChange: (mode: CadastroMode) => void
  catalogReady: boolean
  pacientes: PacienteOption[]
  patientId: string
  onSelectPatient: (id: string) => void
  form: {
    nome: string
    cpf: string
    dataNascimento: string
    telefone: string
    isFlamengo: boolean
    convenio: string
    alergias: string
    grupoSanguineo: string
    setNome: (v: string) => void
    setCpf: (v: string) => void
    setDataNascimento: (v: string) => void
    setTelefone: (v: string) => void
    setIsFlamengo: (v: boolean) => void
    setConvenio: (v: string) => void
    setAlergias: (v: string) => void
    setGrupoSanguineo: (v: string) => void
  }
  onCreate: SubmitHandler
  onUpdate: SubmitHandler
}) {
  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="size-4 text-primary" /> Pacientes
            </CardTitle>
            <CardDescription>
              Cadastre novos pacientes ou atualize dados de pacientes existentes.
            </CardDescription>
          </div>
          <ModeToggle mode={mode} onChange={onModeChange} disabled={!catalogReady && mode === "atualizar"} />
        </div>
      </CardHeader>
      <CardContent>
        {mode === "novo" ? (
          <form onSubmit={onCreate} className="grid gap-4 sm:grid-cols-2">
            <PessoaFieldsForm />
            <Field label="Número do convênio" name="num_convenio" />
            <Field label="Alergias" name="alergias" />
            <Field label="Grupo sanguíneo" name="grupo_sanguineo" placeholder="Ex.: O+" />
            <Button type="submit" disabled={!catalogReady} className="sm:col-span-2 sm:w-fit">
              <UserPlus className="mr-2 size-4" />
              Cadastrar paciente
            </Button>
          </form>
        ) : (
          <form onSubmit={onUpdate} className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Paciente"
              value={patientId}
              onChange={onSelectPatient}
              required
              disabled={!catalogReady}
              placeholder="Selecione o paciente"
              options={pacientes.map((item) => ({
                value: String(item.id_pessoa),
                label: item.nome,
              }))}
            />
            <Field label="Nome completo" value={form.nome} onChange={form.setNome} required />
            <Field label="CPF" value={form.cpf} onChange={form.setCpf} required />
            <Field label="Data de nascimento" value={form.dataNascimento} onChange={form.setDataNascimento} type="date" required />
            <Field label="Telefone" value={form.telefone} onChange={form.setTelefone} required />
            <CheckboxField label="Torcedor do Flamengo" name="is_flamengo_edit" checked={form.isFlamengo} onChange={form.setIsFlamengo} />
            <Field label="Número do convênio" value={form.convenio} onChange={form.setConvenio} />
            <Field label="Alergias" value={form.alergias} onChange={form.setAlergias} />
            <Field label="Grupo sanguíneo" value={form.grupoSanguineo} onChange={form.setGrupoSanguineo} placeholder="Ex.: O+" />
            <Button type="submit" disabled={!patientId || !catalogReady} className="sm:col-span-2 sm:w-fit">
              Salvar alterações
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

export function ResidentesSection({
  mode,
  onModeChange,
  catalogReady,
  residentes,
  residenteId,
  onSelectResidente,
  form,
  onCreate,
  onUpdate,
}: {
  mode: CadastroMode
  onModeChange: (mode: CadastroMode) => void
  catalogReady: boolean
  residentes: ResidenteOption[]
  residenteId: string
  onSelectResidente: (id: string) => void
  form: {
    nome: string
    cpf: string
    dataNascimento: string
    telefone: string
    isFlamengo: boolean
    crm: string
    dataAdmissao: string
    especialidade: string
    anoResidencia: string
    setNome: (v: string) => void
    setCpf: (v: string) => void
    setDataNascimento: (v: string) => void
    setTelefone: (v: string) => void
    setIsFlamengo: (v: boolean) => void
    setCrm: (v: string) => void
    setDataAdmissao: (v: string) => void
    setEspecialidade: (v: string) => void
    setAnoResidencia: (v: string) => void
  }
  onCreate: SubmitHandler
  onUpdate: SubmitHandler
}) {
  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GraduationCap className="size-4 text-primary" /> Residentes
            </CardTitle>
            <CardDescription>
              Cadastre médicos residentes ou atualize dados de residentes existentes.
            </CardDescription>
          </div>
          <ModeToggle mode={mode} onChange={onModeChange} disabled={!catalogReady && mode === "atualizar"} />
        </div>
      </CardHeader>
      <CardContent>
        {mode === "novo" ? (
          <form onSubmit={onCreate} className="grid gap-4 sm:grid-cols-2">
            <ProfissionalFieldsForm />
            <SelectField
              label="Ano de residência"
              name="ano_residencia"
              required
              placeholder="Selecione o ano"
              options={[
                { value: "R1", label: "R1" },
                { value: "R2", label: "R2" },
                { value: "R3", label: "R3" },
              ]}
            />
            <Button type="submit" disabled={!catalogReady} className="sm:col-span-2 sm:w-fit">
              <UserPlus className="mr-2 size-4" />
              Cadastrar residente
            </Button>
          </form>
        ) : (
          <form onSubmit={onUpdate} className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Residente"
              value={residenteId}
              onChange={onSelectResidente}
              required
              disabled={!catalogReady}
              placeholder="Selecione o residente"
              options={residentes.map((item) => ({
                value: String(item.id_profissional),
                label: `${item.nome} (${item.ano_residencia})`,
              }))}
            />
            <Field label="Nome completo" value={form.nome} onChange={form.setNome} required />
            <Field label="CPF" value={form.cpf} onChange={form.setCpf} required />
            <Field label="Data de nascimento" value={form.dataNascimento} onChange={form.setDataNascimento} type="date" required />
            <Field label="Telefone" value={form.telefone} onChange={form.setTelefone} required />
            <CheckboxField label="Torcedor do Flamengo" name="is_flamengo_res_edit" checked={form.isFlamengo} onChange={form.setIsFlamengo} />
            <Field label="CRM" value={form.crm} onChange={form.setCrm} required />
            <Field label="Data de admissão" value={form.dataAdmissao} onChange={form.setDataAdmissao} type="date" required />
            <Field label="Especialidade" value={form.especialidade} onChange={form.setEspecialidade} required />
            <SelectField
              label="Ano de residência"
              value={form.anoResidencia}
              onChange={form.setAnoResidencia}
              required
              placeholder="Selecione o ano"
              options={[
                { value: "R1", label: "R1" },
                { value: "R2", label: "R2" },
                { value: "R3", label: "R3" },
              ]}
            />
            <Button type="submit" disabled={!residenteId || !catalogReady} className="sm:col-span-2 sm:w-fit">
              Salvar alterações
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

export function PreceptoresSection({
  mode,
  onModeChange,
  catalogReady,
  preceptores,
  preceptorId,
  onSelectPreceptor,
  form,
  onCreate,
  onUpdate,
}: {
  mode: CadastroMode
  onModeChange: (mode: CadastroMode) => void
  catalogReady: boolean
  preceptores: PreceptorOption[]
  preceptorId: string
  onSelectPreceptor: (id: string) => void
  form: {
    nome: string
    cpf: string
    dataNascimento: string
    telefone: string
    isFlamengo: boolean
    crm: string
    dataAdmissao: string
    especialidade: string
    titulacao: string
    setNome: (v: string) => void
    setCpf: (v: string) => void
    setDataNascimento: (v: string) => void
    setTelefone: (v: string) => void
    setIsFlamengo: (v: boolean) => void
    setCrm: (v: string) => void
    setDataAdmissao: (v: string) => void
    setEspecialidade: (v: string) => void
    setTitulacao: (v: string) => void
  }
  onCreate: SubmitHandler
  onUpdate: SubmitHandler
}) {
  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <UserCog className="size-4 text-primary" /> Preceptores
            </CardTitle>
            <CardDescription>
              Cadastre preceptores ou atualize dados de preceptores existentes.
            </CardDescription>
          </div>
          <ModeToggle mode={mode} onChange={onModeChange} disabled={!catalogReady && mode === "atualizar"} />
        </div>
      </CardHeader>
      <CardContent>
        {mode === "novo" ? (
          <form onSubmit={onCreate} className="grid gap-4 sm:grid-cols-2">
            <ProfissionalFieldsForm />
            <Field label="Titulação" name="titulacao" placeholder="Ex.: Doutor, Mestre" required />
            <Button type="submit" disabled={!catalogReady} className="sm:col-span-2 sm:w-fit">
              <UserPlus className="mr-2 size-4" />
              Cadastrar preceptor
            </Button>
          </form>
        ) : (
          <form onSubmit={onUpdate} className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Preceptor"
              value={preceptorId}
              onChange={onSelectPreceptor}
              required
              disabled={!catalogReady}
              placeholder="Selecione o preceptor"
              options={preceptores.map((item) => ({
                value: String(item.id_profissional),
                label: `${item.nome} — ${item.titulacao}`,
              }))}
            />
            <Field label="Nome completo" value={form.nome} onChange={form.setNome} required />
            <Field label="CPF" value={form.cpf} onChange={form.setCpf} required />
            <Field label="Data de nascimento" value={form.dataNascimento} onChange={form.setDataNascimento} type="date" required />
            <Field label="Telefone" value={form.telefone} onChange={form.setTelefone} required />
            <CheckboxField label="Torcedor do Flamengo" name="is_flamengo_prec_edit" checked={form.isFlamengo} onChange={form.setIsFlamengo} />
            <Field label="CRM" value={form.crm} onChange={form.setCrm} required />
            <Field label="Data de admissão" value={form.dataAdmissao} onChange={form.setDataAdmissao} type="date" required />
            <Field label="Especialidade" value={form.especialidade} onChange={form.setEspecialidade} required />
            <Field label="Titulação" value={form.titulacao} onChange={form.setTitulacao} required />
            <Button type="submit" disabled={!preceptorId || !catalogReady} className="sm:col-span-2 sm:w-fit">
              Salvar alterações
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

export { readPessoaFromForm, readProfissionalFromForm, toDateInput }
