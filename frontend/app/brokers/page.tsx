'use client'

import { useState, useEffect } from 'react'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { 
  PlusIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowPathIcon,
  TrashIcon,
  BanknotesIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface BrokerConnection {
  id: string
  venue: string
  wallet_address?: string
  api_key_masked?: string
  status: string
  last_sync?: string
  trade_count: number
  created_at: string
  meta?: any
}

interface SyncResult {
  venue: string
  synced_count: number
  trades_added: number
  skipped_count: number
  error_count: number
  message: string
}

export default function BrokersPage() {
  const [connections, setConnections] = useState<BrokerConnection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [selectedVenue, setSelectedVenue] = useState<string>('')
  
  // Hyperliquid connection form
  const [walletAddress, setWalletAddress] = useState('')
  const [privateKey, setPrivateKey] = useState('')
  const [includePrivateKey, setIncludePrivateKey] = useState(false)
  
  // Kraken connection form
  const [krakenApiKey, setKrakenApiKey] = useState('')
  const [krakenApiSecret, setKrakenApiSecret] = useState('')
  
  // Coinbase OAuth
  const [isConnectingCoinbase, setIsConnectingCoinbase] = useState(false)
  
  // Sync modal
  const [showSyncModal, setShowSyncModal] = useState(false)
  const [syncVenue, setSyncVenue] = useState<string>('')
  const [syncStartDate, setSyncStartDate] = useState('')
  const [syncEndDate, setSyncEndDate] = useState('')
  const [syncSymbols, setSyncSymbols] = useState('')
  const [syncLimit, setSyncLimit] = useState(1000)
  const [isSyncing, setIsSyncing] = useState(false)

  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch('/api/v1/broker/list', {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        const data = await response.json()
        setConnections(data)
      } else {
        toast.error('Failed to load broker connections')
      }
    } catch (error) {
      console.error('Failed to fetch connections:', error)
      toast.error('Network error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleConnect = async () => {
    if (!selectedVenue) {
      toast.error('Please select a broker')
      return
    }

    // Coinbase uses OAuth2
    if (selectedVenue === 'coinbase') {
      handleCoinbaseOAuth()
      return
    }

    // Validate fields
    if (selectedVenue === 'hyperliquid' && !walletAddress) {
      toast.error('Please enter your wallet address')
      return
    }
    
    if (selectedVenue === 'kraken' && (!krakenApiKey || !krakenApiSecret)) {
      toast.error('Please enter your API key and secret')
      return
    }

    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      
      const requestBody: any = {
        venue: selectedVenue,
        auto_sync: true,
        sync_interval_minutes: 15
      }
      
      if (selectedVenue === 'hyperliquid') {
        requestBody.wallet_address = walletAddress
        requestBody.private_key = includePrivateKey ? privateKey : undefined
      } else if (selectedVenue === 'kraken') {
        requestBody.api_key = krakenApiKey
        requestBody.api_secret = krakenApiSecret
      }
      
      const response = await fetch('/api/v1/broker/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const result = await response.json()
        toast.success(result.message)
        setShowConnectModal(false)
        resetForm()
        fetchConnections()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to connect broker')
      }
    } catch (error) {
      toast.error('Network error')
    }
  }
  
  const handleCoinbaseOAuth = async () => {
    setIsConnectingCoinbase(true)
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch('/api/v1/broker/oauth/coinbase/authorize', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        // Open OAuth popup
        const width = 600
        const height = 700
        const left = window.screen.width / 2 - width / 2
        const top = window.screen.height / 2 - height / 2
        
        window.open(
          data.authorization_url,
          'Coinbase OAuth',
          `width=${width},height=${height},left=${left},top=${top}`
        )
        
        // Close modal and wait for callback
        setShowConnectModal(false)
        toast.success('Complete authorization in the popup window')
      } else {
        toast.error('Failed to initiate OAuth')
      }
    } catch (error) {
      toast.error('Network error')
    } finally {
      setIsConnectingCoinbase(false)
    }
  }
  
  const resetForm = () => {
    setWalletAddress('')
    setPrivateKey('')
    setIncludePrivateKey(false)
    setKrakenApiKey('')
    setKrakenApiSecret('')
    setSelectedVenue('')
  }

  const handleDisconnect = async (connectionId: string, venue: string) => {
    if (!confirm(`Disconnect from ${venue}? This will not delete your imported trades.`)) {
      return
    }

    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/broker/connections/${connectionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success(`Disconnected from ${venue}`)
        fetchConnections()
      } else {
        toast.error('Failed to disconnect broker')
      }
    } catch (error) {
      toast.error('Network error')
    }
  }

  const handleSync = async (venue?: string) => {
    setIsSyncing(true)
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      
      const symbols_list = syncSymbols ? syncSymbols.split(',').map(s => s.trim()) : undefined
      
      const response = await fetch('/api/v1/broker/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          venue: venue || syncVenue || undefined,
          symbols: symbols_list,
          start_date: syncStartDate || undefined,
          end_date: syncEndDate || undefined,
          limit: syncLimit
        })
      })

      if (response.ok) {
        const results: SyncResult[] = await response.json()
        const totalAdded = results.reduce((sum, r) => sum + r.trades_added, 0)
        const totalSkipped = results.reduce((sum, r) => sum + r.skipped_count, 0)
        
        toast.success(`Synced ${totalAdded} new trades (${totalSkipped} already imported)`)
        setShowSyncModal(false)
        setSyncStartDate('')
        setSyncEndDate('')
        setSyncSymbols('')
        fetchConnections()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to sync trades')
      }
    } catch (error) {
      toast.error('Network error')
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-3xl font-bold text-foreground">Broker Integrations</h1>
                <p className="text-muted-foreground mt-2">
                  Connect your exchange accounts for automated trade sync
                </p>
              </div>
              <button
                onClick={() => setShowConnectModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
              >
                <PlusIcon className="h-5 w-5" />
                <span>Connect Broker</span>
              </button>
            </div>

            {/* Connected Brokers */}
            {isLoading ? (
              <div className="text-center py-12">
                <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              </div>
            ) : connections.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <BanknotesIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium text-foreground mb-2">No Brokers Connected</h3>
                  <p className="text-muted-foreground mb-6">
                    Connect your first exchange to start importing trades
                  </p>
                  <button
                    onClick={() => setShowConnectModal(true)}
                    className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                  >
                    Connect Your First Broker
                  </button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {connections.map((conn) => (
                  <Card key={conn.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-xl capitalize">{conn.venue}</CardTitle>
                          <p className="text-sm text-muted-foreground mt-1">
                            {conn.wallet_address ? `Wallet: ${conn.wallet_address.substring(0, 6)}...${conn.wallet_address.substring(conn.wallet_address.length - 4)}` : conn.api_key_masked}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircleIcon className="h-5 w-5 text-green-500" />
                          <button
                            onClick={() => handleDisconnect(conn.id, conn.venue)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Total Trades</p>
                          <p className="text-xl font-semibold">{conn.trade_count}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Last Sync</p>
                          <p className="text-sm">
                            {conn.last_sync ? new Date(conn.last_sync).toLocaleString() : 'Never'}
                          </p>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => {
                          setSyncVenue(conn.venue)
                          setShowSyncModal(true)
                        }}
                        className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-accent hover:bg-accent/80 rounded-lg"
                      >
                        <ArrowPathIcon className="h-4 w-4" />
                        <span>Sync Trades</span>
                      </button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Connect Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Connect Broker</CardTitle>
                <button onClick={() => setShowConnectModal(false)}>
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Venue Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Select Exchange</label>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => setSelectedVenue('hyperliquid')}
                    className={`p-4 border-2 rounded-lg ${
                      selectedVenue === 'hyperliquid'
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <div className="font-semibold">Hyperliquid</div>
                    <div className="text-xs text-muted-foreground mt-1">Perps DEX</div>
                  </button>
                  <button
                    onClick={() => setSelectedVenue('kraken')}
                    className={`p-4 border-2 rounded-lg ${
                      selectedVenue === 'kraken'
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <div className="font-semibold">Kraken</div>
                    <div className="text-xs text-muted-foreground mt-1">CEX</div>
                  </button>
                  <button
                    onClick={() => setSelectedVenue('coinbase')}
                    className={`p-4 border-2 rounded-lg ${
                      selectedVenue === 'coinbase'
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <div className="font-semibold">Coinbase</div>
                    <div className="text-xs text-muted-foreground mt-1">CEX</div>
                  </button>
                </div>
              </div>

              {/* Hyperliquid Form */}
              {selectedVenue === 'hyperliquid' && (
                <div className="space-y-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Hyperliquid Connection</h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      Enter your wallet address for read-only access (view trades, positions). 
                      Optionally add your private key for trading capabilities (stored encrypted).
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Wallet Address <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={walletAddress}
                      onChange={(e) => setWalletAddress(e.target.value)}
                      placeholder="0x..."
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="includePrivateKey"
                      checked={includePrivateKey}
                      onChange={(e) => setIncludePrivateKey(e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="includePrivateKey" className="text-sm">
                      Include private key (enables trading features)
                    </label>
                  </div>
                  
                  {includePrivateKey && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Private Key <span className="text-xs text-muted-foreground">(optional, for trading)</span>
                      </label>
                      <input
                        type="password"
                        value={privateKey}
                        onChange={(e) => setPrivateKey(e.target.value)}
                        placeholder="0x..."
                        className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                        🔒 Your private key is encrypted before storage and never leaves our secure servers.
                      </p>
                    </div>
                  )}
                </div>
              )}
              
              {/* Kraken Form */}
              {selectedVenue === 'kraken' && (
                <div className="space-y-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Kraken Connection</h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      Create an API key at Settings → API → Generate New Key. 
                      Required permissions: Query Funds, Query Open Orders & Trades, Query Closed Orders & Trades
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      API Key <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={krakenApiKey}
                      onChange={(e) => setKrakenApiKey(e.target.value)}
                      placeholder="Your Kraken API Key"
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      API Secret <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      value={krakenApiSecret}
                      onChange={(e) => setKrakenApiSecret(e.target.value)}
                      placeholder="Your Kraken API Secret"
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                    <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                      🔒 Your API credentials are encrypted before storage and never shared.
                    </p>
                  </div>
                </div>
              )}
              
              {/* Coinbase OAuth Form */}
              {selectedVenue === 'coinbase' && (
                <div className="space-y-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Coinbase Connection</h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      Click Connect to authorize TradeQuest via Coinbase's secure OAuth2 flow. 
                      You'll be redirected to Coinbase to approve access.
                    </p>
                  </div>
                  
                  <div className="bg-accent/30 rounded-lg p-4">
                    <h5 className="font-medium mb-2">What we'll access:</h5>
                    <ul className="text-sm space-y-1 text-muted-foreground">
                      <li>✓ View your account balances</li>
                      <li>✓ Read your trade history</li>
                      <li>✓ View your transaction history</li>
                    </ul>
                    <p className="text-xs text-muted-foreground mt-3">
                      We will NOT be able to trade or withdraw funds from your account.
                    </p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  onClick={() => setShowConnectModal(false)}
                  className="px-4 py-2 border border-border rounded-lg hover:bg-accent"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConnect}
                  disabled={
                    !selectedVenue || 
                    (selectedVenue === 'hyperliquid' && !walletAddress) ||
                    (selectedVenue === 'kraken' && (!krakenApiKey || !krakenApiSecret)) ||
                    (selectedVenue === 'coinbase' && isConnectingCoinbase)
                  }
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {selectedVenue === 'coinbase' ? (isConnectingCoinbase ? 'Opening OAuth...' : 'Authorize with Coinbase') : 'Connect'}
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sync Modal */}
      {showSyncModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Sync Trades from {syncVenue.toUpperCase()}</CardTitle>
                <button onClick={() => setShowSyncModal(false)}>
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Date</label>
                  <input
                    type="date"
                    value={syncStartDate}
                    onChange={(e) => setSyncStartDate(e.target.value)}
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Date</label>
                  <input
                    type="date"
                    value={syncEndDate}
                    onChange={(e) => setSyncEndDate(e.target.value)}
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  Filter by Symbols <span className="text-xs text-muted-foreground">(optional, comma-separated)</span>
                </label>
                <input
                  type="text"
                  value={syncSymbols}
                  onChange={(e) => setSyncSymbols(e.target.value)}
                  placeholder="BTC, ETH, SOL"
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Leave empty to import all symbols
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Maximum Trades to Import</label>
                <input
                  type="number"
                  value={syncLimit}
                  onChange={(e) => setSyncLimit(Number(e.target.value))}
                  min={1}
                  max={10000}
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  onClick={() => setShowSyncModal(false)}
                  className="px-4 py-2 border border-border rounded-lg hover:bg-accent"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleSync()}
                  disabled={isSyncing}
                  className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  {isSyncing && <ArrowPathIcon className="h-4 w-4 animate-spin" />}
                  <span>{isSyncing ? 'Syncing...' : 'Start Sync'}</span>
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
