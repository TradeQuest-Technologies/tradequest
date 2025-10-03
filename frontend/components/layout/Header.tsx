'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import NotificationCenter from '../notifications/NotificationCenter'
import { useNotifications } from '../../hooks/useNotifications'
import { useUser } from '../../hooks/useUser'
import { 
  BellIcon, 
  MagnifyingGlassIcon,
  PlusIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline'

interface HeaderProps {
  className?: string
}

export function Header({ className }: HeaderProps) {
  const [isNotificationCenterOpen, setIsNotificationCenterOpen] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const { getUnreadCount, fetchStats } = useNotifications()
  const { user } = useUser()
  const router = useRouter()
  
  const unreadCount = getUnreadCount()

  // Fetch notification stats when component mounts
  React.useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return (
    <>
      <header className={`flex items-center justify-between px-6 py-4 bg-background border-b ${className}`}>
        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search trades, symbols, strategies..."
              className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-4">
          <Button 
            size="sm"
            onClick={() => setShowImportModal(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Trade
          </Button>

          {/* Notifications */}
          <div className="relative">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => setIsNotificationCenterOpen(true)}
            >
              <BellIcon className="h-5 w-5" />
            </Button>
            {unreadCount > 0 && (
              <Badge 
                variant="destructive" 
                className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
              >
                {unreadCount}
              </Badge>
            )}
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-2">
            <img 
              src="/images/logos/Transparent/TradeQuest [Icon Only] [Colored] [Square].png" 
              alt="TradeQuest Logo" 
              className="w-8 h-8 rounded-full"
            />
            <div className="text-sm">
              <div className="font-medium text-foreground font-brand">{user?.first_name || user?.alias || user?.email?.split('@')[0] || 'Trader'}</div>
              <div className="text-muted-foreground capitalize">{user?.plan || 'Free'} Plan</div>
            </div>
          </div>
        </div>
      </header>

      {/* Notification Center */}
      <NotificationCenter 
        isOpen={isNotificationCenterOpen}
        onClose={() => setIsNotificationCenterOpen(false)}
      />

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Import Trades</h3>
            <p className="text-muted-foreground mb-6">
              Choose how you'd like to add trades to your journal
            </p>
            
            <div className="space-y-3">
              <Button 
                className="w-full justify-start"
                onClick={() => {
                  setShowImportModal(false)
                  router.push('/journal/add')
                }}
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Single Trade
              </Button>
              
              <Button 
                variant="outline"
                className="w-full justify-start"
                onClick={() => {
                  setShowImportModal(false)
                  router.push('/journal/import')
                }}
              >
                <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                Upload CSV File
              </Button>
            </div>
            
            <Button 
              variant="ghost"
              className="w-full mt-4"
              onClick={() => setShowImportModal(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </>
  )
}
