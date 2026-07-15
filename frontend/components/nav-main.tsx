"use client"

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export type NavItem = {
  id: string
  title: string
  icon: React.ReactNode
}

export function NavMain({
  label,
  items,
  activeId,
  onSelect,
}: {
  label: string
  items: NavItem[]
  activeId: string
  onSelect: (id: string) => void
}) {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton
              tooltip={item.title}
              isActive={activeId === item.id}
              onClick={() => onSelect(item.id)}
            >
              {item.icon}
              <span>{item.title}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}
