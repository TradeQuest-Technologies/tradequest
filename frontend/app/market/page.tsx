'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  ChartBarIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  CurrencyDollarIcon,
  EyeIcon,
  CogIcon
} from '@heroicons/react/24/outline'
import AppShell from '../../components/AppShell'
import toast from 'react-hot-toast'

interface MarketData {
  symbol: string
  price: number
  change_24h: number
  change_percent_24h: number
  volume_24h: number
  market_cap?: number
  high_24h: number
  low_24h: number
  last_updated: string
}

interface OHLCVData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface IndicatorData {
  sma_20: number
  sma_50: number
  rsi: number
  atr: number
  macd: number
  macd_signal: number
}

export default function MarketExplorerPage() {
  const [marketData, setMarketData] = useState<MarketData[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USD')
  const [ohlcvData, setOhlcvData] = useState<OHLCVData[]>([])
  const [indicatorData, setIndicatorData] = useState<IndicatorData | null>(null)
  const [timeframe, setTimeframe] = useState('1h')
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showIndicators, setShowIndicators] = useState(true)

  useEffect(() => {
    fetchMarketData()
  }, [])

  useEffect(() => {
    if (selectedSymbol) {
      fetchOHLCVData()
      fetchIndicatorData()
    }
  }, [selectedSymbol, timeframe])

  const fetchMarketData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/market/symbols', {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        const data = await response.json()
        setMarketData(data)
      } else {
        // Mock data for demo
        setMarketData([
          {
            symbol: 'BTC/USD',
            price: 43250.50,
            change_24h: 1250.30,
            change_percent_24h: 2.98,
            volume_24h: 28500000000,
            high_24h: 44100.00,
            low_24h: 42000.00,
            last_updated: new Date().toISOString()
          },
          {
            symbol: 'ETH/USD',
            price: 2650.75,
            change_24h: -45.25,
            change_percent_24h: -1.68,
            volume_24h: 15200000000,
            high_24h: 2750.00,
            low_24h: 2600.00,
            last_updated: new Date().toISOString()
          },
          {
            symbol: 'SOL/USD',
            price: 98.45,
            change_24h: 3.20,
            change_percent_24h: 3.36,
            volume_24h: 2100000000,
            high_24h: 102.00,
            low_24h: 95.00,
            last_updated: new Date().toISOString()
          }
        ])
      }
    } catch (error) {
      toast.error('Failed to load market data')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchOHLCVData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/market/ohlcv/${selectedSymbol}?timeframe=${timeframe}&limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        const data = await response.json()
        setOhlcvData(data)
      } else {
        // Mock data for demo
        const mockData: OHLCVData[] = []
        const basePrice = marketData.find(m => m.symbol === selectedSymbol)?.price || 100
        let currentPrice = basePrice

        for (let i = 0; i < 100; i++) {
          const change = (Math.random() - 0.5) * 0.02
          currentPrice = currentPrice * (1 + change)
          
          mockData.push({
            timestamp: new Date(Date.now() - (100 - i) * 3600000).toISOString(),
            open: currentPrice * (1 + (Math.random() - 0.5) * 0.001),
            high: currentPrice * (1 + Math.random() * 0.01),
            low: currentPrice * (1 - Math.random() * 0.01),
            close: currentPrice,
            volume: Math.random() * 1000000
          })
        }
        setOhlcvData(mockData)
      }
    } catch (error) {
      toast.error('Failed to load OHLCV data')
    }
  }

  const fetchIndicatorData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/market/indicators/${selectedSymbol}?timeframe=${timeframe}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        const data = await response.json()
        setIndicatorData(data)
      } else {
        // Mock data for demo
        const currentPrice = marketData.find(m => m.symbol === selectedSymbol)?.price || 100
        setIndicatorData({
          sma_20: currentPrice * 0.98,
          sma_50: currentPrice * 1.02,
          rsi: 45 + Math.random() * 20,
          atr: currentPrice * 0.02,
          macd: currentPrice * 0.001,
          macd_signal: currentPrice * 0.0008
        })
      }
    } catch (error) {
      toast.error('Failed to load indicator data')
    }
  }

  const filteredMarketData = marketData.filter(market =>
    market.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const timeframes = [
    { value: '1m', label: '1 Minute' },
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' }
  ]

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Market Explorer</h1>
            <p className="text-gray-600 mt-1">
              Real-time market data and technical analysis
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowIndicators(!showIndicators)}
              className={`btn-secondary ${showIndicators ? 'bg-brand-dark-teal text-white' : ''}`}
            >
              <CogIcon className="h-4 w-4 mr-2" />
              Indicators
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Market List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search symbols..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 input text-sm"
                  />
                </div>
              </div>
              
              <div className="max-h-96 overflow-y-auto">
                {filteredMarketData.map((market) => (
                  <div
                    key={market.symbol}
                    onClick={() => setSelectedSymbol(market.symbol)}
                    className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                      selectedSymbol === market.symbol ? 'bg-brand-dark-teal/10 border-brand-dark-teal/20' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">{market.symbol}</div>
                        <div className="text-sm text-gray-500">
                          Vol: ${(market.volume_24h / 1000000000).toFixed(1)}B
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">
                          ${market.price.toFixed(2)}
                        </div>
                        <div className={`text-sm ${
                          market.change_percent_24h >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {market.change_percent_24h >= 0 ? '+' : ''}{market.change_percent_24h.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Chart Area */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {/* Chart Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{selectedSymbol}</h2>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Price: ${marketData.find(m => m.symbol === selectedSymbol)?.price.toFixed(2)}</span>
                      <span className={`${
                        (marketData.find(m => m.symbol === selectedSymbol)?.change_percent_24h || 0) >= 0 
                          ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {(marketData.find(m => m.symbol === selectedSymbol)?.change_percent_24h || 0) >= 0 ? '+' : ''}
                        {(marketData.find(m => m.symbol === selectedSymbol)?.change_percent_24h || 0).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {timeframes.map((tf) => (
                      <button
                        key={tf.value}
                        onClick={() => setTimeframe(tf.value)}
                        className={`px-3 py-1 text-sm rounded-md ${
                          timeframe === tf.value
                            ? 'bg-brand-dark-teal text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {tf.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Chart Placeholder */}
              <div className="p-6">
                <div className="bg-gray-50 rounded-lg h-96 flex items-center justify-center">
                  <div className="text-center">
                    <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Chart View</h3>
                    <p className="text-gray-500">
                      Interactive candlestick chart with technical indicators
                    </p>
                    <div className="mt-4 text-sm text-gray-400">
                      <p>• OHLCV data visualization</p>
                      <p>• Moving averages overlay</p>
                      <p>• RSI, MACD, ATR indicators</p>
                      <p>• Volume analysis</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Technical Indicators */}
              {showIndicators && indicatorData && (
                <div className="border-t border-gray-200 p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Technical Indicators</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">SMA 20</div>
                      <div className="font-semibold text-gray-900">${indicatorData.sma_20.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">SMA 50</div>
                      <div className="font-semibold text-gray-900">${indicatorData.sma_50.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">RSI</div>
                      <div className={`font-semibold ${
                        indicatorData.rsi > 70 ? 'text-red-600' :
                        indicatorData.rsi < 30 ? 'text-green-600' : 'text-gray-900'
                      }`}>
                        {indicatorData.rsi.toFixed(1)}
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">ATR</div>
                      <div className="font-semibold text-gray-900">${indicatorData.atr.toFixed(2)}</div>
                    </div>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">MACD</div>
                      <div className="font-semibold text-gray-900">${indicatorData.macd.toFixed(4)}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">MACD Signal</div>
                      <div className="font-semibold text-gray-900">${indicatorData.macd_signal.toFixed(4)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Market Overview */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Market Overview</h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      24h Change
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Volume
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      High/Low
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {marketData.map((market) => (
                    <tr key={market.symbol} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900">{market.symbol}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${market.price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center">
                          {market.change_percent_24h >= 0 ? (
                            <ArrowTrendingUpIcon className="h-4 w-4 text-green-500 mr-1" />
                          ) : (
                            <ArrowTrendingDownIcon className="h-4 w-4 text-red-500 mr-1" />
                          )}
                          <span className={`font-medium ${
                            market.change_percent_24h >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {market.change_percent_24h >= 0 ? '+' : ''}{market.change_percent_24h.toFixed(2)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${(market.volume_24h / 1000000000).toFixed(1)}B
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${market.high_24h.toFixed(0)} / ${market.low_24h.toFixed(0)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          onClick={() => setSelectedSymbol(market.symbol)}
                          className="text-brand-dark-teal hover:text-brand-bright-yellow"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
