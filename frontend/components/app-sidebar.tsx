"use client"

import * as React from "react"
import {
  Activity,
  CalendarPlus,
  GraduationCap,
  Search,
  Stethoscope,
  Trash2,
  UserCog,
  Users,
} from "lucide-react"

import { NavMain, type NavItem } from "@/components/nav-main"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

export const atendimentosItems: NavItem[] = [
  { id: "novo", title: "Novo atendimento", icon: <CalendarPlus /> },
  { id: "consultas", title: "Consultas", icon: <Search /> },
]

export const cadastrosItems: NavItem[] = [
  { id: "pacientes", title: "Pacientes", icon: <Users /> },
  { id: "residentes", title: "Residentes", icon: <GraduationCap /> },
  { id: "preceptores", title: "Preceptores", icon: <UserCog /> },
  { id: "procedimentos", title: "Procedimentos", icon: <Trash2 /> },
]

export const relatoriosItems: NavItem[] = [
  { id: "relatorios", title: "Painel analítico", icon: <Activity /> },
]

export function AppSidebar({
  activeId,
  onSelect,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  activeId: string
  onSelect: (id: string) => void
}) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="hover:bg-transparent active:bg-transparent">
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <Stethoscope className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">Dra. Yuska</span>
                <span className="truncate text-xs text-sidebar-foreground/60">
                  Sistema hospitalar
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain
          label="Atendimentos"
          items={atendimentosItems}
          activeId={activeId}
          onSelect={onSelect}
        />
        <NavMain
          label="Cadastros"
          items={cadastrosItems}
          activeId={activeId}
          onSelect={onSelect}
        />
        <NavMain
          label="Relatórios"
          items={relatoriosItems}
          activeId={activeId}
          onSelect={onSelect}
        />
      </SidebarContent>
      <SidebarFooter>
        <div className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden">
          <span className="relative flex size-2">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
          </span>
          Conectado ao servidor
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
