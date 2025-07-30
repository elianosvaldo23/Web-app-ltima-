import { MongoClient, type Db } from "mongodb"

const uri =
  process.env.MONGODB_URI ||
  "mongodb+srv://zoobot:zoobot@zoolbot.6avd6qf.mongodb.net/zoolbot?retryWrites=true&w=majority&appName=Zoolbot"
const dbName = "zoolbot"

let cachedClient: MongoClient | null = null
let cachedDb: Db | null = null

export async function connectToDatabase() {
  // En producción, usar conexión cacheada
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb }
  }

  try {
    const client = new MongoClient(uri, {
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
      bufferMaxEntries: 0,
      useNewUrlParser: true,
      useUnifiedTopology: true,
    })

    await client.connect()
    const db = client.db(dbName)

    // Verificar conexión
    await db.command({ ping: 1 })
    console.log("✅ Connected to MongoDB")

    cachedClient = client
    cachedDb = db

    return { client, db }
  } catch (error) {
    console.error("❌ MongoDB connection error:", error)
    throw error
  }
}
