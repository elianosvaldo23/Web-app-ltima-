export interface User {
  telegram_id: number
  username?: string
  first_name: string
  last_name?: string
  diamonds: number
  tons: number
  referrer_id?: number
  referrals: number[]
  is_banned: boolean
  wallet_address?: string
  created_at: Date
  last_active: Date
}

export interface Task {
  _id: string
  title: string
  description: string
  reward: number
  url: string
  verification_type: "url_visit" | "telegram_join" | "manual"
  verification_data?: any
  is_active: boolean
  created_at: Date
}

export interface Mission {
  _id: string
  title: string
  description: string
  reward: number
  requirements: string[]
  is_active: boolean
  created_at: Date
}

export interface Transaction {
  _id: string
  user_id: number
  type: "deposit" | "withdraw" | "task_reward" | "referral_bonus"
  amount: number
  currency: "diamonds" | "tons"
  status: "pending" | "completed" | "failed"
  transaction_hash?: string
  created_at: Date
}

export interface UserTask {
  user_id: number
  task_id: string
  status: "pending" | "completed" | "verified"
  completed_at?: Date
  verified_at?: Date
}
