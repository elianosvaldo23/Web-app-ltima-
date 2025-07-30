export function initTelegramWebApp() {
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    const webApp = window.Telegram.WebApp
    webApp.ready()
    webApp.expand()
    return webApp
  }
  return null
}

export function getTelegramUser() {
  if (typeof window !== "undefined" && window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user
  }
  return null
}

export function showAlert(message: string) {
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    window.Telegram.WebApp.showAlert(message)
  } else {
    alert(message)
  }
}

export function openTelegramLink(url: string) {
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    window.Telegram.WebApp.openTelegramLink(url)
  } else {
    window.open(url, "_blank")
  }
}
