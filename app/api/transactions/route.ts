import { type NextRequest, NextResponse } from "next/server"
import { connectToDatabase } from "@/lib/mongodb"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id")
    const limit = Number.parseInt(searchParams.get("limit") || "10")

    if (!userId) {
      return NextResponse.json({ success: false, error: "User ID required" }, { status: 400 })
    }

    const { db } = await connectToDatabase()

    const transactions = await db
      .collection("transactions")
      .find({ user_id: Number.parseInt(userId) })
      .sort({ created_at: -1 })
      .limit(limit)
      .toArray()

    return NextResponse.json({
      success: true,
      transactions,
    })
  } catch (error) {
    console.error("Transactions error:", error)
    return NextResponse.json({ success: false, error: "Failed to fetch transactions" }, { status: 500 })
  }
}
