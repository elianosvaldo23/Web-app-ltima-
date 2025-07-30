"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ExternalLink, Check } from "lucide-react"
import type { Task, UserTask } from "@/types"
import { formatDiamonds } from "@/lib/utils"
import { openTelegramLink, showAlert } from "@/lib/telegram"

interface TaskCardProps {
  task: Task
  userTask?: UserTask
  onComplete: (taskId: string) => void
}

export default function TaskCard({ task, userTask, onComplete }: TaskCardProps) {
  const [isCompleting, setIsCompleting] = useState(false)

  const handleComplete = async () => {
    setIsCompleting(true)
    try {
      // Abrir el enlace de la tarea
      if (task.url.includes("t.me")) {
        openTelegramLink(task.url)
      } else {
        window.open(task.url, "_blank")
      }

      // Marcar como completada después de un breve delay
      setTimeout(async () => {
        const response = await fetch("/api/tasks/complete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task_id: task._id }),
        })

        if (response.ok) {
          onComplete(task._id)
          showAlert(`¡Tarea completada! +${formatDiamonds(task.reward)} 💎`)
        } else {
          showAlert("Error al completar la tarea. Inténtalo de nuevo.")
        }
        setIsCompleting(false)
      }, 3000)
    } catch (error) {
      setIsCompleting(false)
      showAlert("Error al abrir el enlace.")
    }
  }

  const getStatusBadge = () => {
    if (!userTask) return null

    switch (userTask.status) {
      case "completed":
        return <Badge variant="secondary">Completada</Badge>
      case "verified":
        return <Badge className="bg-green-500">Verificada</Badge>
      case "pending":
        return <Badge variant="outline">Pendiente</Badge>
      default:
        return null
    }
  }

  const isCompleted = userTask?.status === "completed" || userTask?.status === "verified"

  return (
    <Card className="relative">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{task.title}</CardTitle>
            <CardDescription className="mt-1">{task.description}</CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">💎</span>
            <span className="text-xl font-bold text-yellow-500">{formatDiamonds(task.reward)}</span>
          </div>
          <Button
            onClick={handleComplete}
            disabled={isCompleting || isCompleted}
            variant={isCompleted ? "secondary" : "default"}
          >
            {isCompleting ? (
              "Completando..."
            ) : isCompleted ? (
              <>
                <Check className="w-4 h-4 mr-2" /> Completada
              </>
            ) : (
              <>
                Completar <ExternalLink className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
