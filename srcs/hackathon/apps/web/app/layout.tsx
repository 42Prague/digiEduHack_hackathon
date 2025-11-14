import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./globals.css";
import React from "react";
import AppSidebar from "@/components/appSidebar";
import NavBar from "@/components/navBar";
import { ThemeProvider } from "@/components/providers/themeProvider";
import { SidebarProvider } from "@/components/ui/sidebar";

export const metadata: Metadata = {
  title: "Lazy form",
  description: "Test REST API",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const defaultOpen = cookieStore.get("sidebar_state")?.value === "true";

  return (
    <>
      <html lang="en" suppressHydrationWarning>
        <body>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <SidebarProvider defaultOpen={defaultOpen}>
              <AppSidebar />
              <main className="w-screen">
                <NavBar />
                <div>{children}</div>
              </main>
            </SidebarProvider>
          </ThemeProvider>
        </body>
      </html>
    </>
  );
}
