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
  ArrowUpTrayIcon, 
  FunnelIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { formatCurrency, formatDateTime, getColorForValue } from '../../lib/utils'

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
}

export default function TradingJournal() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterSymbol, setFilterSymbol] = useState<string>('all')
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    if (!token) {
      router.push('/auth')
      return
    }

    // Fetch real trades from API
    const fetchTrades = async () => {
      try {
        const response = await fetch('/api/v1/journal/trades', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          setTrades(data)
        } else {
          console.error('Failed to fetch trades')
        }
      } catch (error) {
        console.error('Error fetching trades:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTrades()
  }, [router])

  const filteredTrades = trades.filter(trade => {
    const matchesSearch = trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trade.venue.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSymbol = filterSymbol === 'all' || trade.symbol === filterSymbol

    return matchesSearch && matchesSymbol
  })

  const getSideColor = (side: 'buy' | 'sell') => {
    return side === 'buy' ? 'text-success-600 dark:text-success-400' : 'text-danger-600 dark:text-danger-400'
  }

  const getSideLabel = (side: 'buy' | 'sell') => {
    return side === 'buy' ? 'LONG' : 'SHORT'
  }

  const handleViewTrade = (tradeId: string) => {
    router.push(`/journal/trade/${tradeId}`)
  }

  const handleEditTrade = (tradeId: string) => {
    router.push(`/journal/edit/${tradeId}`)
  }

  const handleDeleteTrade = async (tradeId: string) => {
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
        // Remove the trade from the local state
        setTrades(trades.filter(trade => trade.id !== tradeId))
        // Show success message
        alert('Trade deleted successfully!')
      } else {
        throw new Error('Failed to delete trade')
      }
    } catch (error) {
      console.error('Error deleting trade:', error)
      alert('Failed to delete trade. Please try again.')
    }
  }

  const uniqueSymbols = Array.from(new Set(trades.map(trade => trade.symbol)))

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading trading journal...</p>
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
              <h1 className="text-3xl font-bold text-foreground">Trading Journal</h1>
              <p className="text-muted-foreground mt-2">
                Track and analyze your trading performance
              </p>
            </div>
            <div className="flex space-x-3">
              <Button 
                variant="outline"
                onClick={() => router.push('/journal/import')}
              >
                <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                Import
              </Button>
              <Button onClick={() => router.push('/journal/add')}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Trade
              </Button>
            </div>
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-4">
                {/* Search */}
                <div className="flex-1 min-w-64">
                  <div className="relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search trades, symbols, notes..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    />
                  </div>
                </div>


                {/* Symbol Filter */}
                <select
                  value={filterSymbol}
                  onChange={(e) => setFilterSymbol(e.target.value)}
                  className="px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="all">All Symbols</option>
                  {uniqueSymbols.map(symbol => (
                    <option key={symbol} value={symbol}>{symbol}</option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Trades Table */}
          <Card>
            <CardHeader>
              <CardTitle>Your Trades ({filteredTrades.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {filteredTrades.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-muted-foreground mb-4">
                    <PlusIcon className="h-12 w-12 mx-auto mb-2" />
                    <p className="text-lg font-medium">No trades found</p>
                    <p className="text-sm">Start by adding your first trade or importing data</p>
                  </div>
                  <Button onClick={() => router.push('/journal/add')}>
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Your First Trade
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredTrades.map((trade) => (
                    <div key={trade.id} className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                      <div className="flex items-center space-x-4">
                        <div className="flex flex-col">
                          <span className="font-medium text-lg">{trade.symbol}</span>
                          <span className="text-sm text-muted-foreground">
                            {formatDateTime(trade.filled_at)}
                          </span>
                        </div>
                        
                        <div className="flex flex-col">
                          <span className={`font-medium ${getSideColor(trade.side)}`}>
                            {getSideLabel(trade.side)}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            {trade.qty} @ {formatCurrency(trade.avg_price)}
                          </span>
                        </div>

                        <div className="flex flex-col">
                          <span className="text-sm font-medium">Venue</span>
                          <span className="text-sm text-muted-foreground">
                            {trade.venue}
                          </span>
                        </div>

                        {trade.fees > 0 && (
                          <div className="flex flex-col">
                            <span className="text-sm font-medium">Fees</span>
                            <span className="text-sm text-muted-foreground">
                              {formatCurrency(trade.fees)}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        {trade.pnl !== 0 && (
                          <div className="text-right">
                            <div className={`font-medium text-lg ${getColorForValue(trade.pnl)}`}>
                              {trade.pnl > 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                            </div>
                          </div>
                        )}
                        
                        <div className="flex space-x-2">
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleViewTrade(trade.id)}
                            title="View Trade Details"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleEditTrade(trade.id)}
                            title="Edit Trade"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleDeleteTrade(trade.id)}
                            title="Delete Trade"
                            className="text-danger-600 hover:text-danger-700 hover:bg-danger-50"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </Button>
                        </div>
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