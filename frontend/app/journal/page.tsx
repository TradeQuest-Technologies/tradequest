'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import UpgradeModal from '../../components/modals/UpgradeModal'
import { 
  PlusIcon, 
  ArrowUpTrayIcon, 
  ArrowDownTrayIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { formatCurrency, formatDateTime, getColorForValue } from '../../lib/utils'
import toast from 'react-hot-toast'

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
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [upgradeFeature, setUpgradeFeature] = useState('')
  const [userPlan, setUserPlan] = useState<string>('free')
  const [showExportMenu, setShowExportMenu] = useState(false)
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

    const fetchUserPlan = async () => {
      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        
        if (response.ok) {
          const data = await response.json()
          setUserPlan(data.plan || 'free')
        }
      } catch (error) {
        console.error('Failed to fetch user plan:', error)
      }
    }

    fetchTrades()
    fetchUserPlan()
  }, [router])

  const handleExport = async (format: 'csv' | 'json' | 'excel') => {
    // Check plan access for advanced formats
    if ((format === 'json' || format === 'excel') && (userPlan === 'free' || !userPlan)) {
      router.push(`/upgrade?feature=${format.toUpperCase()} Export`)
      return
    }

    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.tradequest.tech'}/api/v1/journal/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        const error = await response.json()
        toast.error(error.detail || 'Export failed')
        return
      }

      // Download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tradequest_trades_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success(`Trades exported as ${format.toUpperCase()}`)
      setShowExportMenu(false)
    } catch (error) {
      console.error('Export failed:', error)
      toast.error('Failed to export trades')
    }
  }

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
              <div className="relative">
                <Button 
                  variant="outline"
                  onClick={() => setShowExportMenu(!showExportMenu)}
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Export
                </Button>
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg"
                    >
                      CSV Format
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between"
                    >
                      JSON Format
                      {userPlan === 'free' && <span className="text-xs text-yellow-600">Plus</span>}
                    </button>
                    <button
                      onClick={() => handleExport('excel')}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-lg flex items-center justify-between"
                    >
                      Excel Format
                      {userPlan === 'free' && <span className="text-xs text-yellow-600">Plus</span>}
                    </button>
                  </div>
                )}
              </div>
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

          {/* History Retention Warning for Free Users */}
          {userPlan === 'free' && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    Limited History Access
                  </h3>
                  <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                    You're viewing the last 3 months of trades. Upgrade to Plus for unlimited trade history forever.
                  </p>
                  <div className="mt-2">
                    <button
                      onClick={() => router.push('/upgrade?feature=Unlimited Trade History')}
                      className="text-sm font-medium text-yellow-800 dark:text-yellow-200 hover:text-yellow-900 dark:hover:text-yellow-100 underline"
                    >
                      Upgrade Now →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

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

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        feature={upgradeFeature}
        currentPlan={userPlan}
      />
    </div>
  )
}