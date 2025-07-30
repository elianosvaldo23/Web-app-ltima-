import { type NextRequest, NextResponse } from "next/server"
import { connectToDatabase } from "@/lib/mongodb"

export async function POST(request: NextRequest) {
  try {
    const { wallet_address, telegram_id } = await request.json()

    if (!wallet_address || !telegram_id) {
      return NextResponse.json({ success: false, error: "Missing required fields" }, { status: 400 })
    }

    const { db } = await connectToDatabase()

    const result = await db.collection("users").updateOne(
      { telegram_id: telegram_id },
      {
        $set: {
          wallet_address: wallet_address,
          wallet_connected_at: new Date(),
        },
      },
    )

    if (result.matchedCount === 0) {
      return NextResponse.json({ success: false, error: "User not found" }, { status: 404 })
    }

    return NextResponse.json({
      success: true,
      message: "Wallet connected successfully",
    })
  } catch (error) {
    console.error("Wallet connect error:", error)
    return NextResponse.json({ success: false, error: "Failed to connect wallet" }, { status: 500 })
  }
}
