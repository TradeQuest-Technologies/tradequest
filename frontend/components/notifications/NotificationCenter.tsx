'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BellIcon, 
  XMarkIcon, 
  CheckIcon,
  ExclaimationTriangleIcon,
  InformationCircleIcon,
  ShieldExclamationIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ClockIcon,
  EnvelopeIcon,
  PhoneIcon,
  ComputerDesktopIcon
} from '@heroicons/react/24/outline'
import { useTheme } from '../ThemeProvider'

interface Notification {
  id: string
  user_id: string
  title: string
  message: string
  notification_type: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  channels: string[]
  is_read: boolean
  is_delivered: boolean
  metadata?: any
  created_at: string
  read_at?: string
  delivered_at?: string
}

interface NotificationCenterProps {
  isOpen: boolean
  onClose: () => void
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [unreadCount, setUnreadCount] = useState(0)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const { theme } = useTheme()

  useEffect(() => {
    if (isOpen) {
      fetchNotifications()
    }
  }, [isOpen, filter])

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      if (!token) return

      const params = new URLSearchParams()
      if (filter === 'unread') params.append('unread_only', 'true')
      params.append('page', '1')
      params.append('page_size', '50')

      const response = await fetch(`/api/v1/notifications?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setNotifications(data.notifications)
        setUnreadCount(data.unread_count)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async (notificationIds: string[]) => {
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      if (!token) return

      const response = await fetch('/api/v1/notifications/mark-read', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ notification_ids: notificationIds })
      })

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(notif => 
            notificationIds.includes(notif.id) 
              ? { ...notif, is_read: true, read_at: new Date().toISOString() }
              : notif
          )
        )
        setUnreadCount(prev => Math.max(0, prev - notificationIds.length))
      }
    } catch (error) {
      console.error('Failed to mark notifications as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      if (!token) return

      const response = await fetch('/api/v1/notifications/mark-all-read', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(notif => ({ ...notif, is_read: true, read_at: new Date().toISOString() }))
        )
        setUnreadCount(0)
      }
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error)
    }
  }

  const getNotificationIcon = (type: string, priority: string) => {
    const iconClass = `w-5 h-5 ${
      priority === 'urgent' ? 'text-red-500' :
      priority === 'high' ? 'text-orange-500' :
      priority === 'medium' ? 'text-blue-500' :
      'text-gray-500'
    }`

    switch (type) {
      case 'trade_alert':
        return <CurrencyDollarIcon className={iconClass} />
      case 'price_alert':
        return <ChartBarIcon className={iconClass} />
      case 'security_alert':
        return <ShieldExclamationIcon className={iconClass} />
      case 'system_update':
        return <InformationCircleIcon className={iconClass} />
    case 'account_update':
      return <ExclaimationTriangleIcon className={iconClass} />
      case 'journal_reminder':
        return <ClockIcon className={iconClass} />
      default:
        return <BellIcon className={iconClass} />
    }
  }

  const getChannelIcon = (channel: string) => {
    const iconClass = "w-4 h-4 text-muted-foreground"
    
    switch (channel) {
      case 'email':
        return <EnvelopeIcon className={iconClass} />
      case 'sms':
        return <PhoneIcon className={iconClass} />
      case 'in_app':
        return <ComputerDesktopIcon className={iconClass} />
      default:
        return <BellIcon className={iconClass} />
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/20'
      case 'high':
        return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/20'
      case 'medium':
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20'
      case 'low':
        return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20'
      default:
        return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20'
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 overflow-hidden"
      >
        {/* Backdrop */}
        <div 
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />
        
        {/* Notification Panel */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="absolute right-0 top-0 h-full w-full max-w-md bg-background border-l border-border shadow-xl flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <div className="flex items-center space-x-2">
              <BellIcon className="w-6 h-6 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Notifications</h2>
              {unreadCount > 0 && (
                <span className="px-2 py-1 text-xs font-medium text-white bg-primary rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-muted rounded-md transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-2 p-4 border-b border-border">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                filter === 'all' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                filter === 'unread' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              Unread ({unreadCount})
            </button>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="ml-auto px-3 py-1 text-sm text-primary hover:bg-primary/10 rounded-md transition-colors"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <BellIcon className="w-12 h-12 mb-2 opacity-50" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="p-4 space-y-3">
                {notifications.map((notification) => (
                  <motion.div
                    key={notification.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-4 rounded-lg border-l-4 ${getPriorityColor(notification.priority)} ${
                      !notification.is_read ? 'bg-background' : 'bg-muted/30'
                    } hover:bg-muted/50 transition-colors cursor-pointer`}
                    onClick={() => {
                      if (!notification.is_read) {
                        markAsRead([notification.id])
                      }
                    }}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getNotificationIcon(notification.notification_type, notification.priority)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h3 className={`text-sm font-medium ${
                            !notification.is_read ? 'text-foreground' : 'text-muted-foreground'
                          }`}>
                            {notification.title}
                          </h3>
                          <span className="text-xs text-muted-foreground">
                            {formatTime(notification.created_at)}
                          </span>
                        </div>
                        
                        <p className={`text-sm mt-1 ${
                          !notification.is_read ? 'text-foreground' : 'text-muted-foreground'
                        }`}>
                          {notification.message}
                        </p>
                        
                        {/* Channels */}
                        <div className="flex items-center space-x-2 mt-2">
                          {notification.channels.map((channel) => (
                            <div key={channel} className="flex items-center space-x-1">
                              {getChannelIcon(channel)}
                              <span className="text-xs text-muted-foreground capitalize">
                                {channel.replace('_', ' ')}
                              </span>
                            </div>
                          ))}
                        </div>
                        
                        {!notification.is_read && (
                          <div className="mt-2">
                            <span className="inline-block w-2 h-2 bg-primary rounded-full"></span>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default NotificationCenter
