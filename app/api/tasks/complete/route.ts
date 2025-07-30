import { type NextRequest, NextResponse } from "next/server"
import { connectToDatabase } from "@/lib/mongodb"

export async function POST(request: NextRequest) {
  try {
    const { task_id, user_id } = await request.json()
    const { db } = await connectToDatabase()

    // Verificar que la tarea existe y está activa
    const task = await db.collection("tasks").findOne({
      _id: task_id,
      is_active: true,
    })

    if (!task) {
      return NextResponse.json({ success: false, error: "Task not found" }, { status: 404 })
    }

    // Verificar si el usuario ya completó esta tarea
    const existingUserTask = await db.collection("user_tasks").findOne({
      user_id: user_id,
      task_id: task_id,
    })

    if (existingUserTask) {
      return NextResponse.json({ success: false, error: "Task already completed" }, { status: 400 })
    }

    // Marcar tarea como completada
    await db.collection("user_tasks").insertOne({
      user_id: user_id,
      task_id: task_id,
      status: "completed",
      completed_at: new Date(),
    })

    // Dar recompensa al usuario
    await db.collection("users").updateOne({ telegram_id: user_id }, { $inc: { diamonds: task.reward } })

    // Dar bonificación de referido (10%)
    const user = await db.collection("users").findOne({ telegram_id: user_id })
    if (user && user.referrer_id) {
      const referralBonus = Math.floor(task.reward * 0.1)
      await db.collection("users").updateOne({ telegram_id: user.referrer_id }, { $inc: { diamonds: referralBonus } })

      // Registrar transacción de bonificación
      await db.collection("transactions").insertOne({
        user_id: user.referrer_id,
        type: "referral_bonus",
        amount: referralBonus,
        currency: "diamonds",
        status: "completed",
        created_at: new Date(),
      })
    }

    // Registrar transacción de recompensa
    await db.collection("transactions").insertOne({
      user_id: user_id,
      type: "task_reward",
      amount: task.reward,
      currency: "diamonds",
      status: "completed",
      created_at: new Date(),
    })

    return NextResponse.json({
      success: true,
      reward: task.reward,
    })
  } catch (error) {
    console.error("Complete task error:", error)
    return NextResponse.json({ success: false, error: "Failed to complete task" }, { status: 500 })
  }
}
