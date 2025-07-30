"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import BottomNav from "@/components/bottom-nav"
import TaskCard from "@/components/task-card"
import WalletConnect from "@/components/wallet-connect"
import { formatDiamonds, diamondsToTons } from "@/lib/utils"
import { initTelegramWebApp, getTelegramUser } from "@/lib/telegram"
import type { User, Task, UserTask, Transaction } from "@/types"
import { Coins, Users, History, Gift } from "lucide-react"

export default function TelegramMiniApp() {
  const [activeTab, setActiveTab] = useState("tasks")
  const [user, setUser] = useState<User | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [userTasks, setUserTasks] = useState<UserTask[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initApp = async () => {
      // Inicializar Telegram WebApp
      const webApp = initTelegramWebApp()
      const telegramUser = getTelegramUser()

      if (telegramUser) {
        // Autenticar usuario
        const authResponse = await fetch("/api/auth/telegram", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user: telegramUser,
            start_param: webApp?.initDataUnsafe?.start_param,
          }),
        })

        if (authResponse.ok) {
          const { user: authenticatedUser } = await authResponse.json()
          setUser(authenticatedUser)

          // Cargar tareas
          const tasksResponse = await fetch(`/api/tasks?user_id=${telegramUser.id}`)
          if (tasksResponse.ok) {
            const { tasks, userTasks } = await tasksResponse.json()
            setTasks(tasks)
            setUserTasks(userTasks)
          }
        }
      }

      setLoading(false)
    }

    initApp()
  }, [])

  const handleTaskComplete = (taskId: string) => {
    setUserTasks((prev) => [
      ...prev,
      {
        user_id: user!.telegram_id,
        task_id: taskId,
        status: "completed",
        completed_at: new Date(),
      },
    ])

    // Actualizar diamonds del usuario
    const task = tasks.find((t) => t._id === taskId)
    if (task && user) {
      setUser((prev) => (prev ? { ...prev, diamonds: prev.diamonds + task.reward } : null))
    }
  }

  const handleExchange = async (type: "to_tons" | "to_diamonds") => {
    // Implementar lógica de intercambio
    console.log("Exchange:", type)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Cargando...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Error de Autenticación</CardTitle>
            <CardDescription>Esta aplicación debe abrirse desde Telegram</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const renderContent = () => {
    switch (activeTab) {
      case "tasks":
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gift className="h-5 w-5" />
                  Balance Actual
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">💎</span>
                    <span className="text-2xl font-bold text-yellow-500">{formatDiamonds(user.diamonds)}</span>
                  </div>
                  <Badge variant="outline">{diamondsToTons(user.diamonds).toFixed(4)} TON</Badge>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-3">
              <h3 className="text-lg font-semibold">Tareas Disponibles</h3>
              {tasks.map((task) => (
                <TaskCard
                  key={task._id}
                  task={task}
                  userTask={userTasks.find((ut) => ut.task_id === task._id)}
                  onComplete={handleTaskComplete}
                />
              ))}
            </div>
          </div>
        )

      case "missions":
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Misiones Especiales
                </CardTitle>
                <CardDescription>Completa misiones para obtener recompensas extra</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Las misiones estarán disponibles pronto...</p>
              </CardContent>
            </Card>
          </div>
        )

      case "interventions":
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Intervenciones</CardTitle>
                <CardDescription>Participa en intervenciones comunitarias</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">No hay intervenciones activas en este momento</p>
              </CardContent>
            </Card>
          </div>
        )

      case "exchange":
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Coins className="h-5 w-5" />
                  Intercambio de Monedas
                </CardTitle>
                <CardDescription>100,000 💎 = 1 TON</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">Tienes</p>
                    <p className="text-2xl font-bold text-yellow-500">{formatDiamonds(user.diamonds)} 💎</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">Equivale a</p>
                    <p className="text-2xl font-bold text-blue-500">{diamondsToTons(user.diamonds).toFixed(4)} TON</p>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <Button
                    className="w-full bg-transparent"
                    variant="outline"
                    onClick={() => handleExchange("to_tons")}
                    disabled={user.diamonds < 100000}
                  >
                    Convertir a TON
                  </Button>
                </div>
              </CardContent>
            </Card>

            <WalletConnect />

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Historial de Transacciones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-center py-4">No hay transacciones recientes</p>
              </CardContent>
            </Card>
          </div>
        )

      case "profile":
        return (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Perfil de Usuario</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Nombre</p>
                  <p className="font-medium">
                    {user.first_name} {user.last_name}
                  </p>
                </div>

                {user.username && (
                  <div>
                    <p className="text-sm text-muted-foreground">Usuario</p>
                    <p className="font-medium">@{user.username}</p>
                  </div>
                )}

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-500">{formatDiamonds(user.diamonds)}</p>
                    <p className="text-sm text-muted-foreground">💎 Diamantes</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-500">{user.referrals.length}</p>
                    <p className="text-sm text-muted-foreground">👥 Referidos</p>
                  </div>
                </div>

                <Separator />

                <div>
                  <p className="text-sm text-muted-foreground mb-2">Enlace de Referido</p>
                  <div className="bg-muted p-3 rounded-lg">
                    <p className="text-sm break-all">https://t.me/ZoolbotBot?start={user.telegram_id}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="container mx-auto p-4">{renderContent()}</div>

      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}
