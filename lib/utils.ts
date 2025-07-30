import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDiamonds(diamonds: number): string {
  return new Intl.NumberFormat().format(diamonds)
}

export function diamondsToTons(diamonds: number): number {
  return diamonds / 100000
}

export function tonsToDiamonds(tons: number): number {
  return tons * 100000
}
