import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'FinPulse Analytics - Groww Weekly Review',
  description: 'Internal Review Tool for Groww weekly review pulses.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
