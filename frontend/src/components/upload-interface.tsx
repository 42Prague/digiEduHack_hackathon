"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, FileText, Music, Table, X, Loader2, ActivitySquare } from "lucide-react"

export function UploadInterface() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setSelectedFiles((prev) => [...prev, ...files])
  }

  const removeFile = (index: number) => {
    setSelectedFiles((files) => files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadStatus({
        type: "error",
        message: "Vyberte prosím alespoň jeden soubor k nahrání.",
      })
      return
    }

    setIsUploading(true)
    setUploadStatus(null)

    try {
      const formData = new FormData()
      selectedFiles.forEach((file) => {
        formData.append("files", file)
      })

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

      const response = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Nahrání se nezdařilo: ${response.statusText}`)
      }

      setUploadStatus({
        type: "success",
        message: `Úspěšně nahráno ${selectedFiles.length} soubor(y)`,
      })

      setSelectedFiles([])

      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Během nahrávání došlo k chybě",
      })
    } finally {
      setIsUploading(false)
    }
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split(".").pop()?.toLowerCase()
    switch (extension) {
      case "pdf":
        return <FileText className="size-4 text-primary" />
      case "mp3":
        return <Music className="size-4 text-accent" />
      case "csv":
        return <Table className="size-4 text-primary" />
      default:
        return <FileText className="size-4 text-muted-foreground" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="border-2 border-primary/20 shadow-lg bg-card">
        <CardHeader>
          <CardTitle className="text-foreground">Nahrát soubory</CardTitle>
          <CardDescription className="text-muted-foreground">
            Vyberte soubory k nahrání
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Drop Zone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="relative border-2 border-dashed border-primary/40 hover:border-primary/60 rounded-xl p-12 text-center cursor-pointer transition-all bg-secondary/50 hover:bg-secondary group"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />

            <div className="flex flex-col items-center gap-3">
              <div className="p-4 rounded-full bg-primary group-hover:scale-110 transition-transform">
                <Upload className="size-8 text-primary-foreground" />
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground mb-1">Vyberte soubory</p>
                <p className="text-sm text-muted-foreground">Příklady formátů: PDF, MP3, CSV</p>
              </div>
            </div>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-foreground">Vybrané soubory ({selectedFiles.length})</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedFiles([])}
                  className="text-destructive hover:text-destructive hover:bg-destructive/10"
                >
                  Vymazat vše
                </Button>
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2 rounded-lg bg-secondary/50 p-3 border border-border">
                {selectedFiles.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between p-3 rounded-lg bg-card border border-border hover:border-primary/40 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {getFileIcon(file.name)}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate text-foreground">{file.name}</p>
                        <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                      className="shrink-0 hover:text-destructive hover:bg-destructive/10"
                    >
                      <X className="size-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {uploadStatus && (
            <div
              className={`p-4 rounded-lg border ${uploadStatus.type === "success"
                ? "bg-success/10 border-success/30 text-success"
                : "bg-destructive/10 border-destructive/30 text-destructive"
                }`}
            >
              <p className="text-sm font-medium">{uploadStatus.message}</p>
            </div>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={isUploading || selectedFiles.length === 0}
            className="w-full h-12 text-lg bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 size-5 animate-spin" />
                Nahrávání {selectedFiles.length} file(s)...
              </>
            ) : (
              <>
                <Upload className="mr-2 size-5" />
                Nahrát {selectedFiles.length > 0 ? `${selectedFiles.length} file(s)` : "Files"}
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
