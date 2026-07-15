import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { TooltipProvider } from "@/components/ui/tooltip";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Gestão Hospitalar Dra. Yuska",
  description: "Painel de atendimentos e indicadores hospitalares.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={inter.variable}>
      <body>
        <TooltipProvider delay={200}>{children}</TooltipProvider>
      </body>
    </html>
  );
}
