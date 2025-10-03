'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { StatsCard } from '../../components/dashboard/StatsCard'
import { PortfolioChart } from '../../components/dashboard/PortfolioChart'
import { RecentTrades } from '../../components/dashboard/RecentTrades'
import { QuickActions } from '../../components/dashboard/QuickActions'
import { PerformanceMetrics } from '../../components/dashboard/PerformanceMetrics'
import { useUser } from '../../hooks/useUser'
import { 
  CurrencyDollarIcon, 
  ChartBarIcon, 
  ArrowTrendingUpIcon,
  ClockIcon,
  DocumentTextIcon,
  PlusIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline'
import { Button } from '../../components/ui/Button'
import { useNotificationManager } from '../../services/NotificationManager'

type TimePeriod = 'day' | 'week' | 'month' | 'year' | 'custom' | 'all'

export default function Dashboard() {
  const [showImportModal, setShowImportModal] = useState(false)
  const [trades, setTrades] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('all')
  const [customStartDate, setCustomStartDate] = useState('')
  const [customEndDate, setCustomEndDate] = useState('')
  const [chartMode, setChartMode] = useState<'pnl' | 'portfolio'>('pnl')
  const router = useRouter()
  const notificationManager = useNotificationManager()
  const { user } = useUser()

  // Fetch trades data
  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
        if (!token) return

        const response = await fetch('/api/v1/journal/trades', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const tradesData = await response.json()
          setTrades(tradesData)
        }
      } catch (error) {
        console.error('Failed to fetch trades:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTrades()
  }, [])

  // Filter trades by time period
  const getFilteredTrades = () => {
    if (timePeriod === 'all') return trades

    const now = new Date()
    let startDate: Date

    switch (timePeriod) {
      case 'day':
        startDate = new Date(now.setDate(now.getDate() - 1))
        break
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7))
        break
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1))
        break
      case 'year':
        startDate = new Date(now.setFullYear(now.getFullYear() - 1))
        break
      case 'custom':
        if (!customStartDate) return trades
        startDate = new Date(customStartDate)
        const endDate = customEndDate ? new Date(customEndDate) : new Date()
        return trades.filter(trade => {
          const tradeDate = new Date(trade.filled_at)
          return tradeDate >= startDate && tradeDate <= endDate
        })
      default:
        return trades
    }

    return trades.filter(trade => {
      const tradeDate = new Date(trade.filled_at)
      return tradeDate >= startDate
    })
  }

  const filteredTrades = getFilteredTrades()

  // Calculate portfolio metrics
  const totalPnL = filteredTrades.reduce((sum, trade) => sum + (parseFloat(trade.pnl) || 0), 0)
  const winningTrades = filteredTrades.filter(trade => parseFloat(trade.pnl) > 0).length
  const totalTrades = filteredTrades.length
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) : 0  // Keep as decimal (0-1) for proper formatting
  const avgTrade = totalTrades > 0 ? totalPnL / totalTrades : 0
  const recentTrades = filteredTrades.slice(0, 5) // Last 5 trades

  const getPeriodLabel = () => {
    switch (timePeriod) {
      case 'day': return 'past day'
      case 'week': return 'past week'
      case 'month': return 'past month'
      case 'year': return 'past year'
      case 'custom': return 'custom period'
      case 'all': return 'all time'
      default: return 'selected period'
    }
  }


  return (
    <div className="min-h-screen bg-background flex">
        <Sidebar className="w-64" />
        
        <div className="flex-1 flex flex-col">
          <Header />
        
        <main className="flex-1 p-6 space-y-6">
          {/* Welcome Section with Period Selector */}
          <div className="mb-8 flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground font-brand-display">
                Welcome back, {user?.first_name || user?.alias || user?.email?.split('@')[0] || 'Trader'}!
              </h1>
              <p className="text-muted-foreground mt-2">
                Ready to analyze your trading performance?
              </p>
            </div>

            {/* Time Period Selector */}
            <div className="flex items-center gap-3">
              <select
                value={timePeriod}
                onChange={(e) => setTimePeriod(e.target.value as TimePeriod)}
                className="px-4 py-2 border rounded-lg bg-background text-foreground font-medium"
              >
                <option value="all">All Time</option>
                <option value="day">Past Day</option>
                <option value="week">Past Week</option>
                <option value="month">Past Month</option>
                <option value="year">Past Year</option>
                <option value="custom">Custom Period</option>
              </select>
              
              {timePeriod === 'custom' && (
                <div className="flex items-center gap-2">
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="px-3 py-2 border rounded-lg bg-background"
                  />
                  <span className="text-muted-foreground">to</span>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="px-3 py-2 border rounded-lg bg-background"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
              title="Total P&L"
              value={totalPnL}
              changeType="currency"
              trend={totalPnL > 0 ? "up" : totalPnL < 0 ? "down" : "neutral"}
              icon={<CurrencyDollarIcon />}
              description={totalTrades > 0 ? `From ${totalTrades} trades (${getPeriodLabel()})` : "Start trading to see your P&L"}
              periodLabel={getPeriodLabel()}
            />
            <StatsCard
              title="Win Rate"
              value={winRate}
              changeType="percentage"
              trend={winRate > 0.5 ? "up" : winRate < 0.5 ? "down" : "neutral"}
              icon={<ChartBarIcon />}
              description={totalTrades > 0 ? `${winningTrades} winning trades (${getPeriodLabel()})` : "No trades yet"}
              periodLabel={getPeriodLabel()}
            />
            <StatsCard
              title="Total Trades"
              value={totalTrades}
              changeType="number"
              trend="neutral"
              icon={<ArrowTrendingUpIcon />}
              description={`Executed in ${getPeriodLabel()}`}
              periodLabel={getPeriodLabel()}
            />
            <StatsCard
              title="Avg Trade"
              value={avgTrade}
              changeType="currency"
              trend="neutral"
              icon={<ClockIcon />}
              description={`Average P&L per trade (${getPeriodLabel()})`}
              periodLabel={getPeriodLabel()}
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Performance Chart */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Performance Chart</CardTitle>
                  <select
                    value={chartMode}
                    onChange={(e) => setChartMode(e.target.value as 'pnl' | 'portfolio')}
                    className="px-3 py-1.5 border rounded-lg bg-background text-sm"
                  >
                    <option value="pnl">Cumulative P&L</option>
                    <option value="portfolio" disabled>Portfolio Value (Connect Broker)</option>
                  </select>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex items-center justify-center h-80">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : filteredTrades.length === 0 ? (
                    <div className="text-center py-16">
                      <ChartBarIcon className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-foreground mb-2">No Trading Data</h3>
                      <p className="text-muted-foreground mb-4">
                        Import your trades to see your performance chart.
                      </p>
                      <Button 
                        variant="outline"
                        onClick={() => router.push('/journal/import')}
                      >
                        <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                        Import Trades
                      </Button>
                    </div>
                  ) : (
                    <PortfolioChart trades={filteredTrades} mode={chartMode} />
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div>
              <QuickActions />
            </div>
          </div>

          {/* Bottom Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Trades */}
            <div className="lg:col-span-2">
              {loading ? (
                <div className="bg-card rounded-lg p-8 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                  <p className="text-muted-foreground">Loading trades...</p>
                </div>
              ) : recentTrades.length > 0 ? (
                <RecentTrades trades={recentTrades} />
              ) : (
                <div className="bg-card rounded-lg p-8 text-center">
                  <DocumentTextIcon className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-foreground mb-2">No Trades Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Start tracking your trades to see your performance analytics.
                  </p>
                  <Button 
                    variant="outline"
                    onClick={() => router.push('/journal/add')}
                  >
                    Add Your First Trade
                  </Button>
                </div>
              )}
            </div>

            {/* Performance Metrics */}
            <div>
              <PerformanceMetrics />
            </div>
          </div>
        </main>
      </div>

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
    </div>
  )
}