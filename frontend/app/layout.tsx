import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ToastProvider from '../components/Toaster'
import { ThemeProvider } from '../components/ThemeProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TradeQuest',
  description: 'Trading journal, analytics, and AI coaching platform for traders.',
  keywords: 'trading, journal, backtesting, analysis, crypto, stocks',
  icons: {
    icon: '/images/logos/Transparent/TradeQuest [Icon Only] [Colored] [Square].png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          {children}
          <ToastProvider />
        </ThemeProvider>
      </body>
    </html>
  )
}
