"use client"

import type React from "react"
import { useEffect, useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Activity, Home, Pause, Play, Trash2, Loader2 } from "lucide-react"
import Link from "next/link"
import { Header } from "@/components/header"

interface LogEntry {
  id: string
  timestamp: string
  level: "INFO" | "ERROR" | "WARNING" | "SUCCESS"
  message: string
  component?: string
}

export default function LogsPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [authError, setAuthError] = useState("")
  const [isLoggingIn, setIsLoggingIn] = useState(false)

  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [logLimit, setLogLimit] = useState(50)

  const logsEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [isLoadingOlder, setIsLoadingOlder] = useState(false)
  const [hasMoreOlder, setHasMoreOlder] = useState(true)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const [lastTimestamp, setLastTimestamp] = useState<string>(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem("lastTimestamp") : null
    return stored ?? new Date().toISOString()
  })

  useEffect(() => {
    if (lastTimestamp) localStorage.setItem("lastTimestamp", lastTimestamp)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // --- AUTH ---
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoggingIn(true)
    setAuthError("")

    try {
      const formData = new URLSearchParams()
      formData.append("username", username)
      formData.append("password", password)

      const res = await fetch(`${apiUrl}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || "Login failed")
      }

      const data = await res.json()
      localStorage.setItem("accessToken", data.access_token)
      setIsAuthenticated(true)

    } catch (err: any) {
      setAuthError(err.message || "Login failed")
    } finally {
      setIsLoggingIn(false)
    }
  }

  // --- FETCH LOGS ---
  const fetchLogs = async () => {
    try {
      const url = lastTimestamp ? `${apiUrl}/logs?from_date=${lastTimestamp}` : `${apiUrl}/logs?from_date=0`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Failed to fetch logs: ${res.statusText}`)
      const data = await res.json()

      if (data.logs && data.logs.length > 0) {
        const sortedLogs = data.logs
          .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .map((log: any) => ({
            id: log.ts,
            timestamp: log.ts,
            level: log.level,
            message: log.message,
            component: log.component,
          }))
          .filter((log: LogEntry) => !lastTimestamp || new Date(log.timestamp) > new Date(lastTimestamp));

        if (sortedLogs.length === 0) return; // nothing new, do nothing

        setLogs(prev => {
          const combined = [...sortedLogs, ...prev];
          return combined.slice(0, logLimit);
        });

        const newestTimestamp = sortedLogs[0].timestamp;
        setLastTimestamp(newestTimestamp);
        localStorage.setItem("lastTimestamp", newestTimestamp);
      }

    } catch (err) {
      console.error("Fetch logs error:", err)
    }
  }

  // --- POLLING ---
  useEffect(() => {
    if (!isAuthenticated) return

    fetchLogs()

    const interval = setInterval(() => {
      if (!isPaused) fetchLogs()
    }, 5000)

    return () => clearInterval(interval)
  }, [isAuthenticated, isPaused, logLimit, lastTimestamp])

  const clearLogs = () => {
    setLogs([])
    // reset older-loading state so user can load from scratch
    setHasMoreOlder(true)
    // reset timestamp to now so polling won't pull historical logs immediately
    const now = new Date().toISOString()
    setLastTimestamp(now)
    localStorage.setItem("lastTimestamp", now)
  }

  const togglePause = () => setIsPaused(!isPaused)

  const loadLast10Logs = async () => {
    try {
      const url = `${apiUrl}/logs?from_date=0&limit=10`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Failed to fetch last logs: ${res.statusText}`)
      const data = await res.json()

      if (data.logs && data.logs.length > 0) {
        const sortedLogs = data.logs
          .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .map((log: any) => ({
            id: log.ts,
            timestamp: log.ts,
            level: log.level,
            message: log.message,
            component: log.component,
          }))
          .slice(0, 10)

        setLogs(sortedLogs)

        const newestTimestamp = sortedLogs[0].timestamp
        setLastTimestamp(newestTimestamp)
        localStorage.setItem("lastTimestamp", newestTimestamp)
      }
    } catch (err) {
      console.error("Load last logs error:", err)
    }
  }

  // Load older logs (for upward infinite scroll). Appends older logs to the end of
  // the `logs` array (which stores newest->oldest). We request a larger window and
  // filter client-side for entries older than the current oldest timestamp.
  const loadOlderLogs = async (pageSize = 10) => {
    if (isLoadingOlder || !hasMoreOlder) return

    setIsLoadingOlder(true)
    try {
      // If there are no logs currently displayed, treat this as an initial "load older"
      // which should load the most recent `pageSize` entries (same as loadLast10Logs behavior).
      if (logs.length === 0) {
        const url = `${apiUrl}/logs?from_date=0&limit=${pageSize}`
        const res = await fetch(url)
        if (!res.ok) throw new Error(`Failed to fetch logs: ${res.statusText}`)
        const data = await res.json()
        if (!data.logs || data.logs.length === 0) {
          setHasMoreOlder(false)
          return
        }

        const sortedLogs = data.logs
          .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .map((log: any) => ({
            id: log.ts,
            timestamp: log.ts,
            level: log.level,
            message: log.message,
            component: log.component,
          }))

        setLogs(sortedLogs.slice(0, pageSize))
        // update lastTimestamp to newest so polling continues from newest
        const newest = sortedLogs[0].timestamp
        setLastTimestamp(newest)
        localStorage.setItem("lastTimestamp", newest)
        // If fewer than pageSize returned, no more older logs
        if (data.logs.length < pageSize) setHasMoreOlder(false)
        return
      }

      // Normal case: we have some logs and want entries older than the current oldest
      const oldest = logs[logs.length - 1].timestamp
      // If backend supports a 'before' param, replace this with a lighter call.
      const url = `${apiUrl}/logs?from_date=0&limit=200`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Failed to fetch older logs: ${res.statusText}`)
      const data = await res.json()

      if (!data.logs || data.logs.length === 0) {
        setHasMoreOlder(false)
        return
      }

      // Keep only logs strictly older than current oldest
      const older = data.logs
        .map((log: any) => ({
          id: log.ts,
          timestamp: log.ts,
          level: log.level,
          message: log.message,
          component: log.component,
        }))
        .filter((l: LogEntry) => new Date(l.timestamp) < new Date(oldest))
        // sort newest->oldest so appending preserves order
        .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        // remove ones we already have
        .filter((l: LogEntry) => !logs.find(existing => existing.id === l.id))
        .slice(0, pageSize)

      if (older.length === 0) {
        setHasMoreOlder(false)
        return
      }

      setLogs(prev => {
        const combined = [...prev, ...older]
        return combined.slice(0, Math.max(combined.length, logLimit))
      })
    } catch (err) {
      console.error("Load older logs error:", err)
    } finally {
      setIsLoadingOlder(false)
    }
  }

  const getLevelColor = (level: LogEntry["level"]) => {
    switch (level) {
      case "ERROR":
        return "bg-destructive/20 text-destructive border-destructive/30"
      case "WARNING":
        return "bg-yellow-500/20 text-yellow-700 border-yellow-500/30"
      case "SUCCESS":
        return "bg-success/20 text-success border-success/30"
      default:
        return "bg-primary/20 text-primary border-primary/30"
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString("cs-CZ", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour12: false,
      timeZone: "Europe/Prague",
    })
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-2 border-primary/20 shadow-lg bg-card">
          <CardHeader>
            <CardTitle className="text-foreground">Vyžadován přístup správce</CardTitle>
            <CardDescription className="text-muted-foreground">Přihlaste se pro zobrazení záznamů</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="admin-username" className="text-foreground">Uživatelské jméno</Label>
                <Input
                  id="admin-username"
                  type="text"
                  placeholder="admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="border-input focus:border-primary focus:ring-primary"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="admin-password" className="text-foreground">Heslo</Label>
                <Input
                  id="admin-password"
                  type="password"
                  placeholder="admin"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="border-input focus:border-primary focus:ring-primary"
                />
              </div>

              {authError && <p className="text-sm text-destructive">{authError}</p>}

              <Button type="submit" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground" disabled={isLoggingIn}>
                {isLoggingIn ? <>
                  <Loader2 className="mr-2 size-4 animate-spin" /> Ověřování...
                </> : "Login as Admin"}
              </Button>

              <Link href="/">
                <Button variant="outline" className="w-full bg-transparent">
                  <Home className="size-4 mr-2" /> Zpět na nahrávání
                </Button>
              </Link>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="relative">
        <Header />

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-7xl mx-auto">
            <Card className="border-primary/20 shadow-lg h-[calc(90vh-4rem)] flex flex-col">

              <CardHeader className="pb-2">
                <div className="flex items-center justify-between flex-wrap gap-3 relative">
                  {/* Controls on the left */}
                  <div className="flex items-center gap-2 flex-wrap">

                    <Button
                      onClick={togglePause}
                      variant="outline"
                      size="sm"
                      className="gap-2 bg-transparent"
                    >
                      {isPaused ? (
                        <>
                          <Play className="size-4" /> Pokračovat
                        </>
                      ) : (
                        <>
                          <Pause className="size-4" /> Pauza
                        </>
                      )}
                    </Button>

                    <Button
                      onClick={clearLogs}
                      variant="outline"
                      size="sm"
                      className="gap-2 text-destructive hover:bg-destructive"
                    >
                      <Trash2 className="size-4" /> Vymazat
                    </Button>

                    <Button
                      onClick={() => {
                        fetchLogs()
                      }}

                      variant="ghost"
                      size="sm"
                      className="px-2 py-1 hover:bg-primary/10 rounded-md flex items-center gap-1"
                    >
                      <span className="text-lg">🔄</span>
                      {/* obhovit */}
                    </Button>

                    {/* Title in the exact centre */}
                    <CardTitle className="absolute left-1/2 -translate-x-1/2 text-xl font-semibold text-center w-1/2 px-4 flex items-center justify-center gap-2">
                      <Activity className="size-5 text-primary" /> Záznamy
                    </CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Zobrazit</span>
                    <select
                      value={logLimit}
                      onChange={(e) => setLogLimit(Number(e.target.value))}
                      className="border rounded px-2 py-1 text-sm bg-transparent"
                    >
                      {[5, 10, 25, 50].map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                    <span className="text-sm text-muted-foreground">záznamů</span>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {/* Column headers */}
                <div className="grid grid-cols-[110px_1fr_200px_240px] font-semibold text-xs text-muted-foreground mb-2 text-center">
                  <div>Úroveň</div>
                  <div>Zpráva</div>
                  <div>Komponenta</div>
                  <div>Čas</div>
                </div>

                <div className="rounded-lg bg-secondary/30 border border-border/50 overflow-hidden">
                  <div
                    ref={containerRef}
                    onScroll={(e) => {
                      const el = e.currentTarget as HTMLDivElement
                      // when scrolled to very top (oldest visible), load older logs
                      if (el.scrollTop <= 50) {
                        void loadOlderLogs(10)
                      }
                    }}
                    className="overflow-y-auto p-4 font-mono text-sm h-[calc(70vh-4rem)] flex flex-col-reverse space-y-reverse space-y-2 scroll-smooth"
                  >

                    {logs.length === 0 ? (
                      <div className="h-full flex items-center justify-center text-muted-foreground">
                        <div className="text-center">
                              <Activity className="size-12 mx-auto mb-3 opacity-50" />
                              <p>Čekání na záznamy...</p>
                              <Button
                                onClick={loadLast10Logs}
                                variant="ghost"
                                size="sm"
                                className="mt-3 bg-transparent text-sm text-muted-foreground/70 underline"
                              >
                                Načíst posledních 10.
                              </Button>
                            </div>
                      </div>
                    ) : (
                      <>
                        {/* Log rows */}
                        {logs.map((log) => (
                          <div
                            key={log.id}
                            className="grid grid-cols-[150px_1fr_200px_200px] items-start gap-2 p-3 rounded-lg bg-card/40 border border-border/60 hover:border-primary/30 hover:bg-card/60 transition-colors text-center shadow-sm"
                          >
                            <Badge className={`justify-center ${getLevelColor(log.level)}`} variant="outline">
                              {log.level.toUpperCase()}
                            </Badge>

                            <span className="text-foreground break-words text-left">
                              {log.message}
                            </span>

                            <span className="text-foreground/70 truncate">
                              {log.component}
                            </span>

                            <span className="text-muted-foreground text-xs">
                              {formatTimestamp(log.timestamp)}
                            </span>
                          </div>
                        ))}

                        <div ref={logsEndRef} />
                      </>
                    )}
                  </div>
                </div>
              </CardContent>

            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
