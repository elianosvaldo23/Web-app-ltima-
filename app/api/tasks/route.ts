import { type NextRequest, NextResponse } from "next/server"
import { connectToDatabase } from "@/lib/mongodb"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id")

    const { db } = await connectToDatabase()

    // Obtener todas las tareas activas
    const tasks = await db.collection("tasks").find({ is_active: true }).toArray()

    // Si hay user_id, obtener el estado de las tareas del usuario
    let userTasks = []
    if (userId) {
      userTasks = await db
        .collection("user_tasks")
        .find({
          user_id: Number.parseInt(userId),
        })
        .toArray()
    }

    return NextResponse.json({
      success: true,
      tasks,
      userTasks,
    })
  } catch (error) {
    console.error("Tasks error:", error)
    return NextResponse.json({ success: false, error: "Failed to fetch tasks" }, { status: 500 })
  }
}
