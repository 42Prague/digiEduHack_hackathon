"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Home, FileText } from "lucide-react"
import Image from "next/image"

export function Header() {
  const pathname = usePathname()

  const isLogsPage = pathname === "/logs"

  return (
    <header className="border-b border-border/40 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Image
            src="/eduzmena.png"
            alt="Eduzměna logo"
            width={24}
            height={24}
            className="object-contain"
          />
          <h1 className="text-lg font-bold text-foreground">Eduzměna</h1>
        </div>


        {isLogsPage ? (
          <Link href="/">
            <Button variant="outline" className="gap-2 bg-transparent">
              <Home className="size-4" />
              Zpět domů
            </Button>
          </Link>
        ) : (
          <Link href="/logs">
            <Button variant="outline" className="gap-2 bg-transparent">
              <FileText className="size-4" />
              Zobrazit záznamy
            </Button>
          </Link>
        )}
      </div>
    </header>
  )
}
