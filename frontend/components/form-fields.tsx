"use client"

import * as React from "react"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export const selectClassName =
  "border-input bg-background ring-offset-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-xs transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"

export function Field({
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

export function SelectField({
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
