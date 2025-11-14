"use client"

import { useState, useEffect } from "react"
import { LoginForm } from "@/components/login-form"
import { UploadInterface } from "@/components/upload-interface"
import { Header } from "@/components/header"

export default function HomePage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const authStatus = localStorage.getItem("isUploadAuthenticated")
    if (authStatus === "true") {
      setIsAuthenticated(true)
    }
  }, [])

  const handleLoginSuccess = () => {
    localStorage.setItem("isUploadAuthenticated", "true")
    setIsAuthenticated(true)
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      {!isAuthenticated ? (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="w-full max-w-md">
            <LoginForm onSuccess={handleLoginSuccess} />
          </div>
        </div>
      ) : (
        <div className="min-h-screen p-8">
          <div className="max-w-4xl mx-auto space-y-6">
            <UploadInterface />
          </div>
        </div>
      )}
    </div>
  )
}
