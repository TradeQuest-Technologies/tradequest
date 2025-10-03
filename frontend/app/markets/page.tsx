'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { 
  TrendingUpIcon,
  TrendingDownIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  StarIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { formatCurrency, formatPercentage, getColorForValue } from '../../lib/utils'

interface MarketData {
  symbol: string
  name: string
  price: number
  change24h: number
  changePercent24h: number
  volume24h: number
  marketCap?: number
  isFavorite?: boolean
}

type MarketType = 'stocks' | 'crypto' | 'forex'

export default function Markets() {
  const [markets, setMarkets] = useState<MarketData[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'price' | 'change' | 'volume'>('change')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [marketType, setMarketType] = useState<MarketType>('stocks')
  const router = useRouter()

  // Mock data for demonstration
  const mockMarkets: MarketData[] = [
    {
      symbol: 'BTC/USDT',
      name: 'Bitcoin',
      price: 43250.50,
      change24h: 1250.75,
      changePercent24h: 0.029,
      volume24h: 28500000000,
      marketCap: 850000000000,
      isFavorite: true
    },
    {
      symbol: 'ETH/USDT',
      name: 'Ethereum',
      price: 2650.25,
      change24h: -85.50,
      changePercent24h: -0.031,
      volume24h: 15200000000,
      marketCap: 320000000000,
      isFavorite: true
    },
    {
      symbol: 'SOL/USDT',
      name: 'Solana',
      price: 98.75,
      change24h: 5.25,
      changePercent24h: 0.056,
      volume24h: 2800000000,
      marketCap: 45000000000,
      isFavorite: false
    },
    {
      symbol: 'ADA/USDT',
      name: 'Cardano',
      price: 0.485,
      change24h: 0.025,
      changePercent24h: 0.054,
      volume24h: 850000000,
      marketCap: 17000000000,
      isFavorite: false
    },
    {
      symbol: 'DOT/USDT',
      name: 'Polkadot',
      price: 7.85,
      change24h: -0.35,
      changePercent24h: -0.043,
      volume24h: 450000000,
      marketCap: 11000000000,
      isFavorite: false
    },
    {
      symbol: 'MATIC/USDT',
      name: 'Polygon',
      price: 0.95,
      change24h: 0.08,
      changePercent24h: 0.092,
      volume24h: 680000000,
      marketCap: 9000000000,
      isFavorite: false
    }
  ]

  useEffect(() => {
    const fetchMarkets = async () => {
      const token = localStorage.getItem('tq_session')
      if (!token) {
        router.push('/auth')
        return
      }

      setLoading(true)
      try {
        const response = await fetch(`/api/v1/market/tickers?market_type=${marketType}&limit=50`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          setMarkets(data.tickers || [])
        } else {
          console.warn('Failed to fetch market data')
          setMarkets([])
        }
      } catch (error) {
        console.error('Failed to fetch markets:', error)
        setMarkets([])
      } finally {
        setLoading(false)
      }
    }

    fetchMarkets()
  }, [router, marketType])

  // Search functionality with debounce
  useEffect(() => {
    if (!searchTerm || searchTerm.length < 2) return

    const searchTimeout = setTimeout(async () => {
      const token = localStorage.getItem('tq_session')
      if (!token) return

      setLoading(true)
      try {
        // Search for both stocks and crypto
        const searchResponse = await fetch(`/api/v1/market/search?query=${searchTerm}&market_type=${marketType}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (searchResponse.ok) {
          const data = await searchResponse.json()
          
          if (marketType === 'stocks') {
            // Fetch ticker data for stock search results
            const tickerPromises = (data.results || []).slice(0, 10).map(async (result: any) => {
              const resp = await fetch(`/api/v1/market/ticker/${result.ticker || result.symbol}?market_type=stocks`, {
                headers: { 'Authorization': `Bearer ${token}` }
              })
              if (resp.ok) {
                return await resp.json()
              }
              return null
            })

            const tickers = (await Promise.all(tickerPromises)).filter(t => t !== null)
            setMarkets(tickers)
          } else if (marketType === 'crypto') {
            // For crypto, fetch details for search results from CoinGecko
            const cryptoResponse = await fetch(`/api/v1/market/tickers?market_type=crypto&limit=100`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
            
            if (cryptoResponse.ok) {
              const cryptoData = await cryptoResponse.json()
              // Filter by search term
              const filtered = (cryptoData.tickers || []).filter((t: any) => 
                t.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                t.name.toLowerCase().includes(searchTerm.toLowerCase())
              )
              setMarkets(filtered)
            }
          }
        }
      } catch (error) {
        console.error('Failed to search:', error)
      } finally {
        setLoading(false)
      }
    }, 400) // 400ms debounce

    return () => clearTimeout(searchTimeout)
  }, [searchTerm, marketType])

  const filteredMarkets = markets.filter(market =>
    market.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    market.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const sortedMarkets = [...filteredMarkets].sort((a, b) => {
    let aValue: number, bValue: number
    
    switch (sortBy) {
      case 'price':
        aValue = a.price
        bValue = b.price
        break
      case 'change':
        aValue = a.changePercent24h
        bValue = b.changePercent24h
        break
      case 'volume':
        aValue = a.volume24h
        bValue = b.volume24h
        break
      default:
        return 0
    }
    
    return sortOrder === 'asc' ? aValue - bValue : bValue - aValue
  })

  const toggleFavorite = (symbol: string) => {
    setMarkets(prev => prev.map(market => 
      market.symbol === symbol 
        ? { ...market, isFavorite: !market.isFavorite }
        : market
    ))
  }

  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading market data...</p>
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
              <h1 className="text-3xl font-bold text-foreground">Markets</h1>
              <p className="text-muted-foreground mt-2">
                Real-time market data powered by Polygon.io
              </p>
            </div>
          </div>

          {/* Market Type Tabs */}
          <div className="flex gap-2 border-b">
            <button
              onClick={() => setMarketType('stocks')}
              className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                marketType === 'stocks'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              📈 Stocks
            </button>
            <button
              onClick={() => setMarketType('crypto')}
              className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                marketType === 'crypto'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              ₿ Crypto
            </button>
            <button
              onClick={() => setMarketType('forex')}
              className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                marketType === 'forex'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              💱 Forex
            </button>
          </div>

          {/* Search and Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-4">
                {/* Search */}
                <div className="flex-1 min-w-64">
                  <div className="relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search markets..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    />
                  </div>
                </div>

                {/* Sort Options */}
                <div className="flex space-x-2">
                  <Button
                    variant={sortBy === 'price' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleSort('price')}
                  >
                    Price
                    {sortBy === 'price' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </Button>
                  <Button
                    variant={sortBy === 'change' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleSort('change')}
                  >
                    24h Change
                    {sortBy === 'change' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </Button>
                  <Button
                    variant={sortBy === 'volume' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleSort('volume')}
                  >
                    Volume
                    {sortBy === 'volume' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Markets Table */}
          <Card>
            <CardHeader>
              <CardTitle>
                {marketType === 'crypto' ? 'Cryptocurrency' : marketType === 'stocks' ? 'Stock' : 'Forex'} Markets ({sortedMarkets.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              
              <div className="space-y-4">
                {sortedMarkets.map((market) => (
                  <div
                    key={market.symbol}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      {/* Favorite */}
                      <button
                        onClick={() => toggleFavorite(market.symbol)}
                        className="p-1 hover:bg-accent rounded"
                      >
                        <StarIcon
                          className={`h-5 w-5 ${
                            market.isFavorite
                              ? 'text-yellow-500 fill-current'
                              : 'text-muted-foreground'
                          }`}
                        />
                      </button>

                      {/* Symbol and Name */}
                      <div className="flex flex-col">
                        <span className="font-medium text-lg">{market.symbol}</span>
                        <span className="text-sm text-muted-foreground">{market.name}</span>
                      </div>
                    </div>

                    {/* Price */}
                    <div className="text-right">
                      <div className="font-bold text-lg">
                        {formatCurrency(market.price)}
                      </div>
                    </div>

                    {/* 24h Change */}
                    <div className="text-right">
                      <div className={`font-medium ${getColorForValue(market.change24h)}`}>
                        {market.change24h > 0 ? '+' : ''}{formatCurrency(market.change24h)}
                      </div>
                      <div className={`text-sm ${getColorForValue(market.changePercent24h)}`}>
                        {market.changePercent24h > 0 ? '+' : ''}{formatPercentage(market.changePercent24h)}
                      </div>
                    </div>

                    {/* Volume */}
                    <div className="text-right">
                      <div className="font-medium">
                        {formatCurrency(market.volume24h, 'USD')}
                      </div>
                      <div className="text-sm text-muted-foreground">24h Volume</div>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline">
                        Trade
                      </Button>
                      <Button size="sm" variant="outline">
                        <ChartBarIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}
