'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Sidebar } from '../../../../components/layout/Sidebar'
import { Header } from '../../../../components/layout/Header'
import { Button } from '../../../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card'
import { Badge } from '../../../../components/ui/Badge'
import { 
  ArrowLeftIcon,
  PencilIcon,
  TrashIcon,
  ChartBarIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  TagIcon
} from '@heroicons/react/24/outline'
import { formatCurrency, formatDateTime, getColorForValue } from '../../../../lib/utils'

interface Trade {
  id: string
  user_id: string
  account?: string
  venue: string
  symbol: string
  side: 'buy' | 'sell'
  qty: number
  avg_price: number
  fees: number
  pnl: number
  submitted_at?: string
  filled_at: string
  order_ref?: string
  session_id?: string
  raw?: any
  chart_image?: string
}

export default function ViewTrade() {
  const [trade, setTrade] = useState<Trade | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const params = useParams()
  const tradeId = params.id as string

  useEffect(() => {
    const fetchTrade = async () => {
      try {
        const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
        if (!token) {
          router.push('/auth')
          return
        }

        const response = await fetch(`/api/v1/journal/trades/${tradeId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const tradeData = await response.json()
          setTrade(tradeData)
        } else {
          router.push('/journal')
        }
      } catch (error) {
        console.error('Error fetching trade:', error)
        router.push('/journal')
      } finally {
        setLoading(false)
      }
    }

    if (tradeId) {
      fetchTrade()
    }
  }, [tradeId, router])

  const handleEdit = () => {
    router.push(`/journal/edit/${tradeId}`)
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this trade? This action cannot be undone.')) {
      return
    }

    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/journal/trades/${tradeId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        router.push('/journal')
        alert('Trade deleted successfully!')
      } else {
        throw new Error('Failed to delete trade')
      }
    } catch (error) {
      console.error('Error deleting trade:', error)
      alert('Failed to delete trade. Please try again.')
    }
  }

  const getSideLabel = (side: 'buy' | 'sell') => {
    return side === 'buy' ? 'LONG' : 'SHORT'
  }

  const getSideColor = (side: 'buy' | 'sell') => {
    return side === 'buy' ? 'text-success-600 dark:text-success-400' : 'text-danger-600 dark:text-danger-400'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex">
        <Sidebar className="w-64" />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          </main>
        </div>
      </div>
    )
  }

  if (!trade) {
    return (
      <div className="min-h-screen bg-background flex">
        <Sidebar className="w-64" />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-foreground mb-4">Trade Not Found</h1>
              <p className="text-muted-foreground mb-4">The trade you're looking for doesn't exist.</p>
              <Button onClick={() => router.push('/journal')}>
                Back to Journal
              </Button>
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6">
          {/* Header */}
          <div className="flex items-center space-x-4 mb-6">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-foreground font-brand-display">
                Trade Details
              </h1>
              <p className="text-muted-foreground mt-2">
                {trade.symbol} • {getSideLabel(trade.side)} • {formatDateTime(trade.filled_at)}
              </p>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" onClick={handleEdit}>
                <PencilIcon className="h-4 w-4 mr-2" />
                Edit
              </Button>
              <Button 
                variant="outline" 
                onClick={handleDelete}
                className="text-danger-600 hover:text-danger-700 hover:bg-danger-50"
              >
                <TrashIcon className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Trade Info */}
            <div className="lg:col-span-2 space-y-6">
              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <ChartBarIcon className="h-5 w-5" />
                    <span>Trade Information</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Symbol</label>
                      <p className="text-lg font-semibold">{trade.symbol}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Side</label>
                      <p className={`text-lg font-semibold ${getSideColor(trade.side)}`}>
                        {getSideLabel(trade.side)}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Quantity</label>
                      <p className="text-lg font-semibold">{trade.qty}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Price</label>
                      <p className="text-lg font-semibold">{formatCurrency(trade.avg_price)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Fees</label>
                      <p className="text-lg font-semibold">{formatCurrency(trade.fees)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">P&L</label>
                      <p className={`text-lg font-semibold ${getColorForValue(trade.pnl)}`}>
                        {trade.pnl > 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Timing */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CalendarIcon className="h-5 w-5" />
                    <span>Timing</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Entry Time</label>
                      <p className="text-lg font-semibold">{formatDateTime(trade.filled_at)}</p>
                    </div>
                    {trade.submitted_at && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Exit Time</label>
                        <p className="text-lg font-semibold">{formatDateTime(trade.submitted_at)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Chart Image */}
              {trade.chart_image && (
                <Card>
                  <CardHeader>
                    <CardTitle>Chart Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <img 
                        src={`/${trade.chart_image}`}
                        alt="Trade Chart"
                        className="w-full h-auto rounded-lg border"
                        onError={(e) => {
                          console.error('Image failed to load:', trade.chart_image);
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Additional Data */}
              {trade.raw && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <TagIcon className="h-5 w-5" />
                      <span>Additional Information</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {trade.raw.notes && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Notes</label>
                          <p className="mt-1 text-sm">{trade.raw.notes}</p>
                        </div>
                      )}
                      {trade.raw.tags && trade.raw.tags.length > 0 && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Tags</label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {trade.raw.tags.map((tag: string, index: number) => (
                              <Badge key={index} variant="secondary">{tag}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {trade.raw.is_dca && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">DCA Trade</label>
                          <p className="mt-1 text-sm">This was a Dollar Cost Averaging trade</p>
                          {trade.raw.dca_entries && trade.raw.dca_entries.length > 0 && (
                            <div className="mt-2 space-y-2">
                              {trade.raw.dca_entries.map((entry: any, index: number) => (
                                <div key={index} className="p-2 bg-muted rounded text-sm">
                                  <div className="font-medium">{formatDateTime(entry.time)}</div>
                                  <div>Price: {formatCurrency(entry.price)}</div>
                                  {entry.reason && <div>Reason: {entry.reason}</div>}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Trade Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Trade Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className={`text-3xl font-bold ${getColorForValue(trade.pnl)}`}>
                      {trade.pnl > 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                    </div>
                    <p className="text-sm text-muted-foreground">Total P&L</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Venue:</span>
                      <span className="text-sm font-medium">{trade.venue}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Order Ref:</span>
                      <span className="text-sm font-medium">{trade.order_ref || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Session ID:</span>
                      <span className="text-sm font-medium">{trade.session_id || 'N/A'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
