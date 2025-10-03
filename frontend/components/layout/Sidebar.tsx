'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '../../lib/utils'
import { ThemeToggle } from '../ThemeToggle'
import { useUser } from '../../hooks/useUser'
import {
  HomeIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CogIcon,
  PlayIcon,
  BellIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  PlusIcon,
  ArrowUpTrayIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline'

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()
  const { user } = useUser()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Trading Journal', href: '/journal', icon: DocumentTextIcon },
    { name: 'Backtesting', href: '/backtest-v2', icon: PlayIcon },
    { name: 'AI Coach', href: '/coach', icon: ChatBubbleLeftRightIcon },
    // { name: 'Markets', href: '/markets', icon: ChartBarIcon },
    { name: 'Brokers', href: '/brokers', icon: CogIcon },
    { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
    { name: 'Settings', href: '/settings', icon: CogIcon },
  ]

  const quickActions = [
    { name: 'Add Trade', href: '/journal/add', icon: PlusIcon },
    { name: 'Import Data', href: '/journal/import', icon: ArrowUpTrayIcon },
  ]

  return (
    <div className={cn('flex flex-col h-full bg-card border-r', className)}>
      {/* Logo */}
      <div className="flex items-center justify-center h-16 px-4 border-b">
        <div className="flex items-center space-x-2">
          {/* Use rectangle wordmark; swap by theme */}
          <img
            src="/images/logos/Transparent/TradeQuest [Colored] [Rectangle].png"
            alt="TradeQuest"
            className="block dark:hidden h-12 w-auto"
          />
          <img
            src="/images/logos/Transparent/TradeQuest [White] [Rectangle].png"
            alt="TradeQuest"
            className="hidden dark:block h-12 w-auto"
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors hover-card',
                  isActive
                    ? 'bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow text-white brand-glow'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                )}
              >
                <item.icon className={cn(
                  'mr-3 h-5 w-5',
                  isActive ? 'text-white' : 'text-muted-foreground'
                )} />
                {item.name}
              </Link>
            )
          })}
        </div>

        {/* Quick Actions */}
        <div className="pt-6">
          <h3 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Quick Actions
          </h3>
          <div className="mt-2 space-y-1">
            {quickActions.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* User Section */}
      <div className="p-4 border-t">
        <div className="flex items-center space-x-3 mb-4">
          <img 
            src="/images/logos/Transparent/TradeQuest [Icon Only] [Colored] [Square].png" 
            alt="TradeQuest Logo" 
            className="w-8 h-8 rounded-full"
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {user?.first_name || user?.alias || user?.email?.split('@')[0] || 'Trader'}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {user?.email || 'No email'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <ThemeToggle />
          <button
            onClick={() => {
              if (confirm('Are you sure you want to sign out?')) {
                // Clear all authentication tokens
                try {
                  localStorage.removeItem('tq_session')
                  localStorage.removeItem('tq_expires_at')
                  localStorage.removeItem('tq_temp_token')
                  localStorage.removeItem('tq_user_data')
                } catch {}
                
                try {
                  sessionStorage.removeItem('tq_session')
                  sessionStorage.removeItem('tq_expires_at')
                  sessionStorage.removeItem('tq_temp_token')
                  sessionStorage.removeItem('tq_user_data')
                } catch {}
                
                // Clear any cookies (if any are set)
                document.cookie.split(";").forEach(function(c) { 
                  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
                });
                
                // Redirect to home page
                window.location.href = '/'
              }
            }}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors"
            title="Sign Out"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
