'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  WrenchScrewdriverIcon,
  PlusIcon,
  CheckCircleIcon,
  XMarkIcon,
  KeyIcon,
  ArrowPathIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  ClockIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'
import AppShell from '../../components/AppShell'
import toast from 'react-hot-toast'

interface BrokerConnection {
  id: string
  venue: 'kraken' | 'coinbase'
  name: string
  description: string
  status: 'connected' | 'disconnected' | 'error' | 'testing'
  api_key_masked: string
  permissions: string[]
  last_sync: string
  trade_count: number
  created_at: string
  error_message?: string
}

interface APICredentials {
  api_key: string
  api_secret: string
  passphrase?: string
}

export default function IntegrationsPage() {
  const [connections, setConnections] = useState<BrokerConnection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [selectedBroker, setSelectedBroker] = useState<'kraken' | 'coinbase' | null>(null)
  const [credentials, setCredentials] = useState<APICredentials>({
    api_key: '',
    api_secret: '',
    passphrase: ''
  })
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({})
  const [isConnecting, setIsConnecting] = useState(false)

  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/broker/connections', {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        const data = await response.json()
        setConnections(data)
      } else {
        // Mock data for demo
        setConnections([
          {
            id: '1',
            venue: 'kraken',
            name: 'Kraken Pro',
            description: 'Kraken cryptocurrency exchange',
            status: 'connected',
            api_key_masked: 'kraken_****_abc123',
            permissions: ['read_trades', 'read_balances'],
            last_sync: '2024-12-15T14:30:00Z',
            trade_count: 156,
            created_at: '2024-11-01T10:00:00Z'
          },
          {
            id: '2',
            venue: 'coinbase',
            name: 'Coinbase Advanced',
            description: 'Coinbase Advanced Trading',
            status: 'error',
            api_key_masked: 'coinbase_****_def456',
            permissions: ['read_trades'],
            last_sync: '2024-12-14T09:15:00Z',
            trade_count: 89,
            created_at: '2024-11-15T14:30:00Z',
            error_message: 'API key expired'
          }
        ])
      }
    } catch (error) {
      toast.error('Failed to load connections')
    } finally {
      setIsLoading(false)
    }
  }

  const handleConnect = async () => {
    if (!selectedBroker || !credentials.api_key || !credentials.api_secret) {
      toast.error('Please fill in all required fields')
      return
    }

    setIsConnecting(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/broker/connect/${selectedBroker}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(credentials)
      })

      if (response.ok) {
        toast.success('Broker connected successfully!')
        setShowConnectModal(false)
        setCredentials({ api_key: '', api_secret: '', passphrase: '' })
        fetchConnections()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to connect broker')
      }
    } catch (error) {
      toast.error('Network error')
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async (connectionId: string) => {
    if (!confirm('Are you sure you want to disconnect this broker?')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/broker/connections/${connectionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success('Broker disconnected')
        fetchConnections()
      } else {
        toast.error('Failed to disconnect broker')
      }
    } catch (error) {
      toast.error('Network error')
    }
  }

  const handleSync = async (connectionId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/broker/sync/${connectionId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success('Sync started successfully')
        fetchConnections()
      } else {
        toast.error('Failed to start sync')
      }
    } catch (error) {
      toast.error('Network error')
    }
  }

  const brokers = [
    {
      id: 'kraken',
      name: 'Kraken',
      description: 'Connect to Kraken cryptocurrency exchange',
      logo: '🦑',
      features: ['Real-time trade sync', 'Balance tracking', 'Order history'],
      required_fields: ['API Key', 'API Secret'],
      optional_fields: []
    },
    {
      id: 'coinbase',
      name: 'Coinbase Advanced',
      description: 'Connect to Coinbase Advanced Trading',
      logo: '🪙',
      features: ['Advanced trading data', 'Portfolio tracking', 'Fee analysis'],
      required_fields: ['API Key', 'API Secret', 'Passphrase'],
      optional_fields: []
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100'
      case 'disconnected': return 'text-gray-600 bg-gray-100'
      case 'error': return 'text-red-600 bg-red-100'
      case 'testing': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircleIcon className="h-5 w-5" />
      case 'disconnected': return <XMarkIcon className="h-5 w-5" />
      case 'error': return <XMarkIcon className="h-5 w-5" />
      case 'testing': return <ClockIcon className="h-5 w-5" />
      default: return <XMarkIcon className="h-5 w-5" />
    }
  }

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
            <p className="text-gray-600 mt-1">
              Connect your brokers and manage API access
            </p>
          </div>
          <button
            onClick={() => setShowConnectModal(true)}
            className="btn-primary"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Connect Broker
          </button>
        </div>

        {/* Security Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <div className="flex">
            <ShieldCheckIcon className="h-5 w-5 text-blue-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Security & Privacy</h3>
              <div className="mt-1 text-sm text-blue-700">
                <p>• All API keys are encrypted and stored securely</p>
                <p>• We only request read-only permissions</p>
                <p>• Your credentials are never used for trading</p>
                <p>• You can revoke access at any time</p>
              </div>
            </div>
          </div>
        </div>

        {/* Available Brokers */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Brokers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {brokers.map((broker) => (
              <div key={broker.id} className="card">
                <div className="flex items-center mb-3">
                  <div className="text-2xl mr-3">{broker.logo}</div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{broker.name}</h3>
                    <p className="text-sm text-gray-600">{broker.description}</p>
                  </div>
                </div>
                
                <div className="space-y-2 mb-4">
                  <div className="text-xs text-gray-500">Features:</div>
                  {broker.features.map((feature, index) => (
                    <div key={index} className="text-xs text-gray-600">• {feature}</div>
                  ))}
                </div>
                
                <button
                  onClick={() => {
                    setSelectedBroker(broker.id as 'kraken' | 'coinbase')
                    setShowConnectModal(true)
                  }}
                  className="btn-secondary w-full"
                >
                  Connect {broker.name}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Connected Brokers */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Connected Brokers</h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Broker
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      API Key
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Permissions
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Sync
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trades
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {connections.map((connection) => (
                    <tr key={connection.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{connection.name}</div>
                          <div className="text-sm text-gray-500">{connection.description}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(connection.status)}`}>
                            {getStatusIcon(connection.status)}
                            <span className="ml-1 capitalize">{connection.status}</span>
                          </span>
                        </div>
                        {connection.error_message && (
                          <div className="text-xs text-red-600 mt-1">{connection.error_message}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center">
                          <KeyIcon className="h-4 w-4 mr-1" />
                          {connection.api_key_masked}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="space-y-1">
                          {connection.permissions.map((permission, index) => (
                            <div key={index} className="text-xs bg-gray-100 px-2 py-1 rounded">
                              {permission.replace('_', ' ')}
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>{new Date(connection.last_sync).toLocaleDateString()}</div>
                        <div className="text-xs">{new Date(connection.last_sync).toLocaleTimeString()}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {connection.trade_count.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleSync(connection.id)}
                            className="text-brand-dark-teal hover:text-brand-bright-yellow"
                            title="Sync Trades"
                          >
                            <ArrowPathIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDisconnect(connection.id)}
                            className="text-red-400 hover:text-red-600"
                            title="Disconnect"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {connections.length === 0 && (
              <div className="text-center py-12">
                <WrenchScrewdriverIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No brokers connected</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Connect your first broker to start syncing trades automatically
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Connect Modal */}
        {showConnectModal && selectedBroker && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-screen items-center justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowConnectModal(false)} />
              
              <div className="inline-block w-full max-w-md transform overflow-hidden rounded-lg bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:align-middle">
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Connect {brokers.find(b => b.id === selectedBroker)?.name}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="label">API Key</label>
                      <div className="relative">
                        <input
                          type={showSecrets.api_key ? 'text' : 'password'}
                          value={credentials.api_key}
                          onChange={(e) => setCredentials(prev => ({ ...prev, api_key: e.target.value }))}
                          className="input pr-10"
                          placeholder="Enter your API key"
                        />
                        <button
                          onClick={() => setShowSecrets(prev => ({ ...prev, api_key: !prev.api_key }))}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showSecrets.api_key ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                    
                    <div>
                      <label className="label">API Secret</label>
                      <div className="relative">
                        <input
                          type={showSecrets.api_secret ? 'text' : 'password'}
                          value={credentials.api_secret}
                          onChange={(e) => setCredentials(prev => ({ ...prev, api_secret: e.target.value }))}
                          className="input pr-10"
                          placeholder="Enter your API secret"
                        />
                        <button
                          onClick={() => setShowSecrets(prev => ({ ...prev, api_secret: !prev.api_secret }))}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showSecrets.api_secret ? <EyeSlashIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    {selectedBroker === 'coinbase' && (
                      <div>
                        <label className="label">Passphrase</label>
                        <input
                          type="password"
                          value={credentials.passphrase || ''}
                          onChange={(e) => setCredentials(prev => ({ ...prev, passphrase: e.target.value }))}
                          className="input"
                          placeholder="Enter your passphrase"
                        />
                      </div>
                    )}

                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="text-sm text-yellow-800">
                        <strong>Important:</strong> Make sure your API key has read-only permissions. 
                        We will never use your credentials for trading.
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    onClick={handleConnect}
                    disabled={isConnecting}
                    className="btn-primary"
                  >
                    {isConnecting ? 'Connecting...' : 'Connect'}
                  </button>
                  <button
                    onClick={() => setShowConnectModal(false)}
                    className="btn-secondary mr-3"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
