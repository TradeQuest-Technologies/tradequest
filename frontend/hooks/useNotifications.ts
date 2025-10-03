'use client'

import { useState, useEffect, useCallback } from 'react'

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

interface NotificationStats {
  total_notifications: number
  unread_notifications: number
  notifications_by_type: Record<string, number>
  notifications_by_priority: Record<string, number>
  recent_activity: Notification[]
}

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [stats, setStats] = useState<NotificationStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = () => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  const fetchNotifications = useCallback(async (
    page: number = 1,
    pageSize: number = 20,
    unreadOnly: boolean = false,
    notificationType?: string
  ) => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      params.append('page', page.toString())
      params.append('page_size', pageSize.toString())
      if (unreadOnly) params.append('unread_only', 'true')
      if (notificationType) params.append('notification_type', notificationType)

      const response = await fetch(`/api/v1/notifications?${params}`, {
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.status}`)
      }

      const data = await response.json()
      setNotifications(data.notifications)
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/notifications/stats', {
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('Failed to fetch notification stats')
      }

      const data = await response.json()
      setStats(data)
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    }
  }, [])

  const markAsRead = useCallback(async (notificationIds: string[]) => {
    try {
      const response = await fetch('/api/v1/notifications/mark-read', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ notification_ids: notificationIds })
      })

      if (!response.ok) {
        throw new Error('Failed to mark notifications as read')
      }

      // Update local state
      setNotifications(prev => 
        prev.map(notif => 
          notificationIds.includes(notif.id) 
            ? { ...notif, is_read: true, read_at: new Date().toISOString() }
            : notif
        )
      )

      // Update stats
      if (stats) {
        setStats(prev => prev ? {
          ...prev,
          unread_notifications: Math.max(0, prev.unread_notifications - notificationIds.length)
        } : null)
      }

      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return false
    }
  }, [stats])

  const markAllAsRead = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/notifications/mark-all-read', {
        method: 'POST',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('Failed to mark all notifications as read')
      }

      // Update local state
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, is_read: true, read_at: new Date().toISOString() }))
      )

      // Update stats
      if (stats) {
        setStats(prev => prev ? { ...prev, unread_notifications: 0 } : null)
      }

      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return false
    }
  }, [stats])

  const createNotification = useCallback(async (
    title: string,
    message: string,
    notificationType: string,
    priority: 'low' | 'medium' | 'high' | 'urgent' = 'medium',
    channels: string[] = ['in_app'],
    metadata?: any
  ) => {
    try {
      const response = await fetch('/api/v1/notifications/create', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title,
          message,
          notification_type: notificationType,
          priority,
          channels,
          metadata
        })
      })

      if (!response.ok) {
        throw new Error('Failed to create notification')
      }

      const data = await response.json()
      
      // Add to local state
      setNotifications(prev => [data, ...prev])

      // Update stats
      if (stats) {
        setStats(prev => prev ? {
          ...prev,
          total_notifications: prev.total_notifications + 1,
          unread_notifications: prev.unread_notifications + 1,
          notifications_by_type: {
            ...prev.notifications_by_type,
            [notificationType]: (prev.notifications_by_type[notificationType] || 0) + 1
          },
          notifications_by_priority: {
            ...prev.notifications_by_priority,
            [priority]: (prev.notifications_by_priority[priority] || 0) + 1
          },
          recent_activity: [data, ...prev.recent_activity.slice(0, 4)]
        } : null)
      }

      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    }
  }, [stats])

  const getUnreadCount = useCallback(() => {
    return stats?.unread_notifications || 0
  }, [stats])

  const getNotificationsByType = useCallback((type: string) => {
    return notifications.filter(notif => notif.notification_type === type)
  }, [notifications])

  const getNotificationsByPriority = useCallback((priority: string) => {
    return notifications.filter(notif => notif.priority === priority)
  }, [notifications])

  const getUnreadNotifications = useCallback(() => {
    return notifications.filter(notif => !notif.is_read)
  }, [notifications])

  // Auto-refresh notifications every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStats()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchStats])

  return {
    notifications,
    stats,
    loading,
    error,
    fetchNotifications,
    fetchStats,
    markAsRead,
    markAllAsRead,
    createNotification,
    getUnreadCount,
    getNotificationsByType,
    getNotificationsByPriority,
    getUnreadNotifications
  }
}
