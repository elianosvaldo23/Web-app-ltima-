"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Wallet, ExternalLink } from "lucide-react"

export default function WalletConnect() {
  const [isConnecting, setIsConnecting] = useState(false)
  const [walletAddress, setWalletAddress] = useState<string | null>(null)

  const connectWallet = async () => {
    setIsConnecting(true)
    try {
      // Simular conexión con TonKeeper
      if (typeof window !== "undefined" && window.tonkeeper) {
        const accounts = await window.tonkeeper.send("ton_requestAccounts")
        if (accounts.length > 0) {
          setWalletAddress(accounts[0])
          // Aquí guardarías la dirección en la base de datos
          await fetch("/api/user/wallet", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ wallet_address: accounts[0] }),
          })
        }
      } else {
        // Fallback para cuando TonKeeper no está disponible
        window.open("https://tonkeeper.com/", "_blank")
      }
    } catch (error) {
      console.error("Error connecting wallet:", error)
    } finally {
      setIsConnecting(false)
    }
  }

  if (walletAddress) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            Billetera Conectada
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            {walletAddress.slice(0, 6)}...{walletAddress.slice(-6)}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              Depositar TON
            </Button>
            <Button variant="outline" size="sm">
              Retirar TON
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-5 w-5" />
          Conectar Billetera
        </CardTitle>
        <CardDescription>Conecta tu billetera TonKeeper para depositar y retirar TON</CardDescription>
      </CardHeader>
      <CardContent>
        <Button onClick={connectWallet} disabled={isConnecting} className="w-full">
          {isConnecting ? "Conectando..." : "Conectar TonKeeper"}
          <ExternalLink className="ml-2 h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  )
}
