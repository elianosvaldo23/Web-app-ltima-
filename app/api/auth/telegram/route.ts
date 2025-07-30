import { type NextRequest, NextResponse } from "next/server"
import { connectToDatabase } from "@/lib/mongodb"

export async function POST(request: NextRequest) {
  try {
    const { user, start_param } = await request.json()
    const { db } = await connectToDatabase()

    // Verificar si el usuario ya existe
    let existingUser = await db.collection("users").findOne({
      telegram_id: user.id,
    })

    if (!existingUser) {
      // Crear nuevo usuario
      const referrerId = start_param ? Number.parseInt(start_param) : null

      const newUser = {
        telegram_id: user.id,
        username: user.username,
        first_name: user.first_name,
        last_name: user.last_name,
        diamonds: 0,
        tons: 0,
        referrer_id: referrerId,
        referrals: [],
        is_banned: false,
        created_at: new Date(),
        last_active: new Date(),
      }

      await db.collection("users").insertOne(newUser)

      // Si tiene referidor, agregarlo a la lista de referidos
      if (referrerId) {
        await db.collection("users").updateOne({ telegram_id: referrerId }, { $push: { referrals: user.id } })
      }

      existingUser = newUser
    } else {
      // Actualizar última actividad
      await db.collection("users").updateOne({ telegram_id: user.id }, { $set: { last_active: new Date() } })
    }

    return NextResponse.json({
      success: true,
      user: existingUser,
    })
  } catch (error) {
    console.error("Auth error:", error)
    return NextResponse.json({ success: false, error: "Authentication failed" }, { status: 500 })
  }
}
