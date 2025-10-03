'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  CogIcon,
  ChartPieIcon,
  BellIcon,
  ShieldCheckIcon,
  WrenchScrewdriverIcon,
  QuestionMarkCircleIcon,
  Bars3Icon,
  XMarkIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  CommandLineIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import toast from 'react-hot-toast'

interface User {
  id: string
  email: string
  plan: string
}

interface AppShellProps {
  children: React.ReactNode
}

export default function AppShell({ children }: AppShellProps) {
  const [user, setUser] = useState<User | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    fetchUserData()
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        if (e.key === 'k') {
          e.preventDefault()
          setCommandPaletteOpen(true)
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/auth')
        return
      }

      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      }
    } catch (error) {
      console.error('Failed to fetch user data:', error)
    }
  }

  const handleSignOut = () => {
    localStorage.removeItem('access_token')
    router.push('/')
  }

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: ChartBarIcon },
    { name: 'AI Coach', href: '/chat', icon: ChatBubbleLeftRightIcon },
    { name: 'Journal', href: '/journal', icon: DocumentTextIcon },
    { name: 'Backtesting', href: '/backtesting', icon: CogIcon },
    { name: 'Market Explorer', href: '/market', icon: ChartPieIcon },
    { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
    { name: 'Alerts & Discipline', href: '/alerts', icon: BellIcon },
    { name: 'Integrations', href: '/integrations', icon: WrenchScrewdriverIcon },
    { name: 'Settings', href: '/settings', icon: ShieldCheckIcon },
    { name: 'Help', href: '/help', icon: QuestionMarkCircleIcon },
  ]

  const quickActions = [
    { name: 'Import CSV', action: () => router.push('/journal?import=true') },
    { name: 'Connect Broker', action: () => router.push('/integrations') },
    { name: 'Run Backtest', action: () => router.push('/backtesting?new=true') },
    { name: 'Ask AI Coach', action: () => router.push('/chat') },
  ]

  const filteredActions = quickActions.filter(action =>
    action.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
            <Link href="/dashboard" className="text-xl font-bold text-gradient">
              TradeQuest
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-brand-dark-teal text-white'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* User info */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center">
              <UserCircleIcon className="h-8 w-8 text-gray-400" />
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {user?.email}
                </p>
                <p className="text-xs text-gray-500">
                  {user?.plan?.toUpperCase()} Plan
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            {/* Left side */}
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500"
              >
                <Bars3Icon className="h-6 w-6" />
              </button>
              
              {/* Search */}
              <div className="relative ml-4">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search trades, strategies..."
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-brand-dark-teal focus:border-brand-dark-teal sm:text-sm"
                />
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center space-x-4">
              {/* Command palette trigger */}
              <button
                onClick={() => setCommandPaletteOpen(true)}
                className="hidden sm:flex items-center px-3 py-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md"
              >
                <CommandLineIcon className="h-4 w-4 mr-2" />
                ⌘K
              </button>

              {/* Notifications */}
              <button className="p-2 text-gray-400 hover:text-gray-500">
                <BellIcon className="h-6 w-6" />
              </button>

              {/* Account menu */}
              <div className="relative">
                <button className="flex items-center text-sm text-gray-700 hover:text-gray-900">
                  <span className="mr-2">{user?.email}</span>
                  <div className={`w-2 h-2 rounded-full ${
                    user?.plan === 'pro' ? 'bg-brand-bright-yellow' :
                    user?.plan === 'plus' ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1">
          {children}
        </main>
      </div>

      {/* Command Palette */}
      {commandPaletteOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-start justify-center px-4 pt-16 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setCommandPaletteOpen(false)} />
            
            <div className="relative inline-block w-full max-w-md transform overflow-hidden rounded-lg bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:align-middle">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center mb-4">
                  <CommandLineIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium text-gray-900">Command Palette</h3>
                </div>
                
                <div className="relative mb-4">
                  <input
                    type="text"
                    placeholder="Search commands..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-brand-dark-teal focus:border-brand-dark-teal sm:text-sm"
                    autoFocus
                  />
                  <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                </div>

                <div className="space-y-1">
                  {filteredActions.map((action, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        action.action()
                        setCommandPaletteOpen(false)
                        setSearchQuery('')
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                    >
                      {action.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
