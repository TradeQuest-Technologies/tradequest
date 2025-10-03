'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { 
  PlusIcon,
  BellIcon,
  BellSlashIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { formatDateTime } from '../../lib/utils'
import toast from 'react-hot-toast'

interface Alert {
  id: string
  name: string
  type: 'price' | 'volume' | 'indicator' | 'risk' | 'news'
  symbol?: string
  condition: string
  value: number
  isActive: boolean
  lastTriggered?: string
  triggerCount: number
  createdAt: string
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Mock data for demonstration
  const mockAlerts: Alert[] = [
    {
      id: '1',
      name: 'BTC Price Alert',
      type: 'price',
      symbol: 'BTC/USDT',
      condition: 'above',
      value: 50000,
      isActive: true,
      lastTriggered: '2024-01-07T10:30:00Z',
      triggerCount: 3,
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: '2',
      name: 'High Volume Alert',
      type: 'volume',
      symbol: 'ETH/USDT',
      condition: 'above',
      value: 1000000000,
      isActive: true,
      triggerCount: 1,
      createdAt: '2024-01-02T00:00:00Z'
    },
    {
      id: '3',
      name: 'RSI Oversold',
      type: 'indicator',
      symbol: 'SOL/USDT',
      condition: 'below',
      value: 30,
      isActive: false,
      lastTriggered: '2024-01-06T15:20:00Z',
      triggerCount: 5,
      createdAt: '2024-01-03T00:00:00Z'
    },
    {
      id: '4',
      name: 'Daily Loss Limit',
      type: 'risk',
      condition: 'below',
      value: -1000,
      isActive: true,
      triggerCount: 0,
      createdAt: '2024-01-04T00:00:00Z'
    }
  ]

  useEffect(() => {
    const token = localStorage.getItem('tq_session')
    if (!token) {
      router.push('/auth')
      return
    }

    // Simulate API call
    setTimeout(() => {
      setAlerts(mockAlerts)
      setLoading(false)
    }, 1000)
  }, [router])

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'price':
        return <InformationCircleIcon className="h-5 w-5 text-blue-600" />
      case 'volume':
        return <BellIcon className="h-5 w-5 text-green-600" />
      case 'indicator':
        return <BellIcon className="h-5 w-5 text-purple-600" />
      case 'risk':
        return <XCircleIcon className="h-5 w-5 text-red-600" />
      case 'news':
        return <InformationCircleIcon className="h-5 w-5 text-orange-600" />
      default:
        return <BellIcon className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'price':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'volume':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'indicator':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'risk':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'news':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const handleToggleActive = async (alertId: string) => {
    try {
      const token = localStorage.getItem('tq_session')
      const alert = alerts.find(a => a.id === alertId)
      const response = await fetch(`/api/v1/alerts/${alertId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ isActive: !alert?.isActive })
      })

      if (response.ok) {
        toast.success('Alert status updated!')
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, isActive: !alert.isActive }
            : alert
        ))
      } else {
        throw new Error('Update failed')
      }
    } catch (error) {
      toast.error('Failed to update alert')
    }
  }

  const handleDelete = async (alertId: string) => {
    if (!confirm('Are you sure you want to delete this alert?')) return

    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('Alert deleted successfully!')
        setAlerts(prev => prev.filter(alert => alert.id !== alertId))
      } else {
        throw new Error('Delete failed')
      }
    } catch (error) {
      toast.error('Failed to delete alert')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading alerts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Alerts & Notifications</h1>
              <p className="text-muted-foreground mt-2">
                Set up alerts for price movements, indicators, and risk management
              </p>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline">
                <BellSlashIcon className="h-4 w-4 mr-2" />
                Disable All
              </Button>
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                New Alert
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <BellIcon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Alerts</p>
                    <p className="text-2xl font-bold">{alerts.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-success/10 rounded-lg">
                    <CheckCircleIcon className="h-6 w-6 text-success-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Active Alerts</p>
                    <p className="text-2xl font-bold text-success-600">
                      {alerts.filter(a => a.isActive).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-warning/10 rounded-lg">
                    <InformationCircleIcon className="h-6 w-6 text-warning-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Triggered Today</p>
                    <p className="text-2xl font-bold text-warning-600">
                      {alerts.filter(a => a.lastTriggered && new Date(a.lastTriggered).toDateString() === new Date().toDateString()).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-info/10 rounded-lg">
                    <InformationCircleIcon className="h-6 w-6 text-info-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Triggers</p>
                    <p className="text-2xl font-bold">
                      {alerts.reduce((sum, alert) => sum + alert.triggerCount, 0)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Alerts List */}
          <Card>
            <CardHeader>
              <CardTitle>Your Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-muted-foreground mb-4">
                    <BellIcon className="h-12 w-12 mx-auto mb-2" />
                    <p className="text-lg font-medium">No alerts set up</p>
                    <p className="text-sm">Create your first alert to get notified about market movements</p>
                  </div>
                  <Button>
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create Your First Alert
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center space-x-4">
                        {getAlertIcon(alert.type)}
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="font-medium">{alert.name}</h3>
                            <Badge className={getAlertColor(alert.type)}>
                              {alert.type}
                            </Badge>
                            {!alert.isActive && (
                              <Badge variant="outline">Inactive</Badge>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {alert.symbol && `${alert.symbol} `}
                            {alert.condition} {alert.value}
                            {alert.type === 'price' && ' USD'}
                            {alert.type === 'volume' && ' USD'}
                            {alert.type === 'indicator' && ' RSI'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Created: {formatDateTime(alert.createdAt)}
                            {alert.lastTriggered && (
                              <span className="ml-4">
                                Last triggered: {formatDateTime(alert.lastTriggered)}
                              </span>
                            )}
                            <span className="ml-4">
                              Triggered {alert.triggerCount} times
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleToggleActive(alert.id)}
                        >
                          {alert.isActive ? (
                            <BellIcon className="h-4 w-4" />
                          ) : (
                            <BellSlashIcon className="h-4 w-4" />
                          )}
                        </Button>
                        
                        <Button variant="ghost" size="icon">
                          <PencilIcon className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(alert.id)}
                        >
                          <TrashIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}