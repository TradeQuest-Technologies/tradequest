'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { 
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  CogIcon,
  KeyIcon,
  GlobeAltIcon,
  CreditCardIcon,
  TrashIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  ChartBarIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'
import { formatDateTime } from '../../lib/utils'
import toast from 'react-hot-toast'

interface ProfileSettings {
  first_name: string
  last_name: string
  alias: string
  email: string
  timezone: string
  display_currency: string
  birth_date: string
}

interface SecuritySettings {
  two_factor_enabled: boolean
  last_password_change: string | null
  active_sessions: number
}

interface NotificationSettings {
  email_enabled: boolean
  push_enabled: boolean
  sms_enabled: boolean
  in_app_enabled: boolean
  quiet_hours_start: string | null
  quiet_hours_end: string | null
  email_frequency_limit: string
  sms_frequency_limit: string
}

interface TradingPreferences {
  default_symbol: string
  default_timeframe: string
  fees_bps_default: number
  slip_bps_default: number
  mc_runs_default: number
}

interface CoachPreferences {
  tone: string
  data_window_days: number
  action_items_per_session: number
  anonymized_optin: boolean
}

interface ApiKey {
  id: string
  venue: string
  created_at: string
  masked_key: string
}

interface Session {
  id: string
  created_at: string
  last_used: string
  ip_address: string
  user_agent: string
  is_current: boolean
}

export default function Settings() {
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('profile')
  const [editing, setEditing] = useState<string | null>(null)
  const router = useRouter()

  // State for each settings section
  const [profile, setProfile] = useState<ProfileSettings | null>(null)
  const [security, setSecurity] = useState<SecuritySettings | null>(null)
  const [notifications, setNotifications] = useState<NotificationSettings | null>(null)
  const [trading, setTrading] = useState<TradingPreferences | null>(null)
  const [coach, setCoach] = useState<CoachPreferences | null>(null)
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [sessions, setSessions] = useState<Session[]>([])

  // 2FA setup state
  const [show2FASetup, setShow2FASetup] = useState(false)
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [verificationCode, setVerificationCode] = useState('')

  // API key add modal
  const [showAddKeyModal, setShowAddKeyModal] = useState(false)
  const [newKeyVenue, setNewKeyVenue] = useState('kraken')
  const [newApiKey, setNewApiKey] = useState('')
  const [newApiSecret, setNewApiSecret] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('tq_session')
    if (!token) {
      router.push('/auth')
      return
    }

    // Add a small delay to ensure backend is ready
    const timer = setTimeout(() => {
      fetchAllSettings()
    }, 500)

    return () => clearTimeout(timer)
  }, [router])

  const fetchAllSettings = async () => {
    const token = localStorage.getItem('tq_session')
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    try {
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }

      // Fetch all settings in parallel with better error handling
      const requests = [
        { url: `${apiUrl}/api/v1/settings/profile`, setter: setProfile },
        { url: `${apiUrl}/api/v1/settings/security`, setter: setSecurity },
        { url: `${apiUrl}/api/v1/settings/notifications`, setter: setNotifications },
        { url: `${apiUrl}/api/v1/settings/trading`, setter: setTrading },
        { url: `${apiUrl}/api/v1/settings/coach`, setter: setCoach },
        { url: `${apiUrl}/api/v1/settings/api-keys`, setter: null, isArray: true },
        { url: `${apiUrl}/api/v1/settings/sessions`, setter: null, isArray: true }
      ]

      const responses = await Promise.allSettled(
        requests.map(req => fetch(req.url, { headers }))
      )

      responses.forEach((result, index) => {
        const request = requests[index]
        if (result.status === 'fulfilled' && result.value.ok) {
          result.value.json().then(data => {
            if (request.isArray) {
              if (index === 5) { // api-keys
                setApiKeys(data.api_keys || [])
              } else if (index === 6) { // sessions
                setSessions(data.sessions || [])
              }
            } else if (request.setter) {
              request.setter(data)
            }
          }).catch(err => {
            console.error(`Failed to parse response for ${request.url}:`, err)
          })
        } else {
          console.error(`Failed to fetch ${request.url}:`, 
            result.status === 'rejected' ? result.reason : 'HTTP error')
        }
      })

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch settings:', error)
      toast.error('Failed to load settings - please check if backend is running')
      setLoading(false)
    }
  }

  const handleSaveProfile = async () => {
    if (!profile) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profile)
      })

      if (response.ok) {
        toast.success('Profile updated successfully!')
        setEditing(null)
      } else {
        throw new Error('Update failed')
      }
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleSaveNotifications = async () => {
    if (!notifications) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/notifications`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(notifications)
      })

      if (response.ok) {
        toast.success('Notification settings updated!')
      } else {
        throw new Error('Update failed')
      }
    } catch (error) {
      toast.error('Failed to update notifications')
    }
  }

  const handleSaveTrading = async () => {
    if (!trading) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/trading`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(trading)
      })

      if (response.ok) {
        toast.success('Trading preferences updated!')
        setEditing(null)
      } else {
        throw new Error('Update failed')
      }
    } catch (error) {
      toast.error('Failed to update trading preferences')
    }
  }

  const handleSaveCoach = async () => {
    if (!coach) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/coach`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(coach)
      })

      if (response.ok) {
        toast.success('Coach preferences updated!')
        setEditing(null)
      } else {
        throw new Error('Update failed')
      }
    } catch (error) {
      toast.error('Failed to update coach preferences')
    }
  }

  const handleEnable2FA = async () => {
    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/2fa/enable`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setQrCodeUrl(data.qr_code_url)
        setBackupCodes(data.backup_codes)
        setShow2FASetup(true)
      } else {
        throw new Error('2FA enable failed')
      }
    } catch (error) {
      toast.error('Failed to enable 2FA')
    }
  }

  const handleDisable2FA = async () => {
    if (!confirm('Are you sure you want to disable two-factor authentication?')) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/2fa/disable`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('2FA disabled successfully!')
        if (security) {
          setSecurity({ ...security, two_factor_enabled: false })
        }
      } else {
        throw new Error('2FA disable failed')
      }
    } catch (error) {
      toast.error('Failed to disable 2FA')
    }
  }

  const handleAddApiKey = async () => {
    if (!newApiKey || !newApiSecret) {
      toast.error('Please fill in all fields')
      return
    }

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/broker/connect/${newKeyVenue}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          api_key: newApiKey,
          api_secret: newApiSecret,
          meta: null
        })
      })

      if (response.ok) {
        toast.success(`Connected to ${newKeyVenue} successfully!`)
        setShowAddKeyModal(false)
        setNewApiKey('')
        setNewApiSecret('')
        // Refresh API keys
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const keysRes = await fetch(`${apiUrl}/api/v1/settings/api-keys`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (keysRes.ok) {
          const data = await keysRes.json()
          setApiKeys(data.api_keys || [])
        }
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to add API key')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to add API key')
    }
  }

  const handleDeleteApiKey = async (keyId: string, venue: string) => {
    if (!confirm(`Are you sure you want to remove the ${venue} API key?`)) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('API key removed successfully!')
        setApiKeys(apiKeys.filter(k => k.id !== keyId))
      } else {
        throw new Error('Delete failed')
      }
    } catch (error) {
      toast.error('Failed to delete API key')
    }
  }

  const handleRevokeSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to revoke this session?')) return

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('Session revoked successfully!')
        setSessions(sessions.filter(s => s.id !== sessionId))
      } else {
        throw new Error('Revoke failed')
      }
    } catch (error) {
      toast.error('Failed to revoke session')
    }
  }

  const handleDeleteAccount = async () => {
    const confirmText = prompt('Type DELETE to confirm account deletion:')
    if (confirmText !== 'DELETE') {
      toast.error('Account deletion cancelled')
      return
    }

    try {
      const token = localStorage.getItem('tq_session')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/account`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('Account deleted successfully!')
        localStorage.removeItem('tq_session')
        router.push('/')
      } else {
        throw new Error('Delete failed')
      }
    } catch (error) {
      toast.error('Failed to delete account')
    }
  }

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'api-keys', name: 'API Keys', icon: KeyIcon },
    { id: 'trading', name: 'Trading', icon: ChartBarIcon },
    { id: 'coach', name: 'AI Coach', icon: CodeBracketIcon },
    { id: 'sessions', name: 'Sessions', icon: CogIcon },
    { id: 'billing', name: 'Billing', icon: CreditCardIcon }
  ]

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground">Settings</h1>
              <p className="text-muted-foreground mt-2">
                Manage your account settings and preferences
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Sidebar */}
              <div className="lg:col-span-1">
                <Card>
                  <CardContent className="p-4">
                    <nav className="space-y-2">
                      {tabs.map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                            activeTab === tab.id
                              ? 'bg-primary text-primary-foreground'
                              : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                          }`}
                        >
                          <tab.icon className="h-5 w-5" />
                          <span>{tab.name}</span>
                        </button>
                      ))}
                    </nav>
                  </CardContent>
                </Card>
              </div>

              {/* Content */}
              <div className="lg:col-span-3">
                {/* Profile Tab */}
                {activeTab === 'profile' && profile && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle>Profile Settings</CardTitle>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditing(editing === 'profile' ? null : 'profile')}
                        >
                          <PencilIcon className="h-4 w-4 mr-2" />
                          {editing === 'profile' ? 'Cancel' : 'Edit'}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">First Name</label>
                          <input
                            type="text"
                            value={profile.first_name || ''}
                            onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                            disabled={editing !== 'profile'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Last Name</label>
                          <input
                            type="text"
                            value={profile.last_name || ''}
                            onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                            disabled={editing !== 'profile'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Alias/Username</label>
                          <input
                            type="text"
                            value={profile.alias || ''}
                            onChange={(e) => setProfile({ ...profile, alias: e.target.value })}
                            disabled={editing !== 'profile'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Email</label>
                          <input
                            type="email"
                            value={profile.email}
                            disabled
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Timezone</label>
                          <select
                            value={profile.timezone}
                            onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                            disabled={editing !== 'profile'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          >
                            <option value="UTC">UTC</option>
                            <option value="America/New_York">Eastern Time</option>
                            <option value="America/Chicago">Central Time</option>
                            <option value="America/Denver">Mountain Time</option>
                            <option value="America/Los_Angeles">Pacific Time</option>
                            <option value="Europe/London">London</option>
                            <option value="Europe/Paris">Paris</option>
                            <option value="Asia/Tokyo">Tokyo</option>
                            <option value="Asia/Hong_Kong">Hong Kong</option>
                            <option value="Australia/Sydney">Sydney</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Display Currency</label>
                          <select
                            value={profile.display_currency}
                            onChange={(e) => setProfile({ ...profile, display_currency: e.target.value })}
                            disabled={editing !== 'profile'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          >
                            <option value="USD">USD</option>
                            <option value="EUR">EUR</option>
                            <option value="GBP">GBP</option>
                            <option value="JPY">JPY</option>
                            <option value="AUD">AUD</option>
                            <option value="CAD">CAD</option>
                          </select>
                        </div>
                      </div>
                      {editing === 'profile' && (
                        <div className="flex space-x-2">
                          <Button onClick={handleSaveProfile}>
                            <CheckIcon className="h-4 w-4 mr-2" />
                            Save Changes
                          </Button>
                          <Button variant="outline" onClick={() => setEditing(null)}>
                            <XMarkIcon className="h-4 w-4 mr-2" />
                            Cancel
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Security Tab */}
                {activeTab === 'security' && security && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Security Settings</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Two-Factor Authentication</h3>
                          <p className="text-sm text-muted-foreground">
                            {security.two_factor_enabled ? 'Extra layer of security enabled' : 'Not enabled'}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge variant={security.two_factor_enabled ? 'success' : 'outline'}>
                            {security.two_factor_enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={security.two_factor_enabled ? handleDisable2FA : handleEnable2FA}
                          >
                            {security.two_factor_enabled ? 'Disable' : 'Enable'}
                          </Button>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Password</h3>
                          <p className="text-sm text-muted-foreground">
                            {security.last_password_change 
                              ? `Last changed: ${formatDateTime(security.last_password_change)}`
                              : 'Never changed'}
                          </p>
                        </div>
                        <Button variant="outline" size="sm">
                          <KeyIcon className="h-4 w-4 mr-2" />
                          Change Password
                        </Button>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Active Sessions</h3>
                          <p className="text-sm text-muted-foreground">
                            {security.active_sessions} active session{security.active_sessions !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setActiveTab('sessions')}
                        >
                          View Sessions
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Notifications Tab */}
                {activeTab === 'notifications' && notifications && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Notification Preferences</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <h3 className="font-medium">Email Notifications</h3>
                            <p className="text-sm text-muted-foreground">
                              Receive notifications via email
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.email_enabled}
                              onChange={(e) => {
                                const updated = { ...notifications, email_enabled: e.target.checked }
                                setNotifications(updated)
                                handleSaveNotifications()
                              }}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                          </label>
                        </div>

                        <div className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <h3 className="font-medium">Push Notifications</h3>
                            <p className="text-sm text-muted-foreground">
                              Receive push notifications in browser
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.push_enabled}
                              onChange={(e) => {
                                const updated = { ...notifications, push_enabled: e.target.checked }
                                setNotifications(updated)
                                handleSaveNotifications()
                              }}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                          </label>
                        </div>

                        <div className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <h3 className="font-medium">SMS Notifications</h3>
                            <p className="text-sm text-muted-foreground">
                              Receive critical alerts via SMS
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.sms_enabled}
                              onChange={(e) => {
                                const updated = { ...notifications, sms_enabled: e.target.checked }
                                setNotifications(updated)
                                handleSaveNotifications()
                              }}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                          </label>
                        </div>

                        <div className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <h3 className="font-medium">In-App Notifications</h3>
                            <p className="text-sm text-muted-foreground">
                              Show notifications within the app
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.in_app_enabled}
                              onChange={(e) => {
                                const updated = { ...notifications, in_app_enabled: e.target.checked }
                                setNotifications(updated)
                                handleSaveNotifications()
                              }}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                          </label>
                        </div>
                      </div>

                      <div className="border-t pt-4">
                        <h3 className="font-medium mb-4">Quiet Hours</h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-2">Start Time</label>
                            <input
                              type="time"
                              value={notifications.quiet_hours_start || ''}
                              onChange={(e) => {
                                const updated = { ...notifications, quiet_hours_start: e.target.value }
                                setNotifications(updated)
                                handleSaveNotifications()
                              }}
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-2">End Time</label>
                            <input
                              type="time"
                              value={notifications.quiet_hours_end || ''}
                              onChange={(e) => {
                                const updated = { ...notifications, quiet_hours_end: e.target.value }
                                setNotifications(updated)
                                handleSaveNotifications()
                              }}
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                            />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* API Keys Tab */}
                {activeTab === 'api-keys' && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle>Exchange API Keys</CardTitle>
                        <Button size="sm" onClick={() => setShowAddKeyModal(true)}>
                          <KeyIcon className="h-4 w-4 mr-2" />
                          Add API Key
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {apiKeys.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          <KeyIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
                          <p>No API keys configured</p>
                          <p className="text-sm mt-1">Add an exchange API key to sync your trades automatically</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {apiKeys.map((key) => (
                            <div key={key.id} className="flex items-center justify-between p-4 border rounded-lg">
                              <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                                  <KeyIcon className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                  <h3 className="font-medium capitalize">{key.venue}</h3>
                                  <p className="text-sm text-muted-foreground">
                                    {key.masked_key} • Added {formatDateTime(key.created_at)}
                                  </p>
                                </div>
                              </div>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDeleteApiKey(key.id, key.venue)}
                              >
                                <TrashIcon className="h-4 w-4 mr-2" />
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Trading Tab */}
                {activeTab === 'trading' && trading && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle>Trading Preferences</CardTitle>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditing(editing === 'trading' ? null : 'trading')}
                        >
                          <PencilIcon className="h-4 w-4 mr-2" />
                          {editing === 'trading' ? 'Cancel' : 'Edit'}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Default Symbol</label>
                          <input
                            type="text"
                            value={trading.default_symbol}
                            onChange={(e) => setTrading({ ...trading, default_symbol: e.target.value })}
                            disabled={editing !== 'trading'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                            placeholder="BTC/USDT"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Default Timeframe</label>
                          <select
                            value={trading.default_timeframe}
                            onChange={(e) => setTrading({ ...trading, default_timeframe: e.target.value })}
                            disabled={editing !== 'trading'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          >
                            <option value="1m">1 minute</option>
                            <option value="5m">5 minutes</option>
                            <option value="15m">15 minutes</option>
                            <option value="1h">1 hour</option>
                            <option value="4h">4 hours</option>
                            <option value="1d">1 day</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Fees (bps)</label>
                          <input
                            type="number"
                            step="0.1"
                            value={trading.fees_bps_default}
                            onChange={(e) => setTrading({ ...trading, fees_bps_default: parseFloat(e.target.value) })}
                            disabled={editing !== 'trading'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Slippage (bps)</label>
                          <input
                            type="number"
                            step="0.1"
                            value={trading.slip_bps_default}
                            onChange={(e) => setTrading({ ...trading, slip_bps_default: parseFloat(e.target.value) })}
                            disabled={editing !== 'trading'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Monte Carlo Runs</label>
                          <input
                            type="number"
                            value={trading.mc_runs_default}
                            onChange={(e) => setTrading({ ...trading, mc_runs_default: parseInt(e.target.value) })}
                            disabled={editing !== 'trading'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                      </div>
                      {editing === 'trading' && (
                        <div className="flex space-x-2">
                          <Button onClick={handleSaveTrading}>
                            <CheckIcon className="h-4 w-4 mr-2" />
                            Save Changes
                          </Button>
                          <Button variant="outline" onClick={() => setEditing(null)}>
                            <XMarkIcon className="h-4 w-4 mr-2" />
                            Cancel
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Coach Tab */}
                {activeTab === 'coach' && coach && (
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle>AI Coach Preferences</CardTitle>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditing(editing === 'coach' ? null : 'coach')}
                        >
                          <PencilIcon className="h-4 w-4 mr-2" />
                          {editing === 'coach' ? 'Cancel' : 'Edit'}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Coach Tone</label>
                          <select
                            value={coach.tone}
                            onChange={(e) => setCoach({ ...coach, tone: e.target.value })}
                            disabled={editing !== 'coach'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          >
                            <option value="succinct">Succinct</option>
                            <option value="detailed">Detailed</option>
                            <option value="encouraging">Encouraging</option>
                            <option value="direct">Direct</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Data Window (days)</label>
                          <input
                            type="number"
                            value={coach.data_window_days}
                            onChange={(e) => setCoach({ ...coach, data_window_days: parseInt(e.target.value) })}
                            disabled={editing !== 'coach'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Action Items Per Session</label>
                          <input
                            type="number"
                            value={coach.action_items_per_session}
                            onChange={(e) => setCoach({ ...coach, action_items_per_session: parseInt(e.target.value) })}
                            disabled={editing !== 'coach'}
                            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground disabled:opacity-50"
                          />
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Anonymized Data Opt-In</h3>
                          <p className="text-sm text-muted-foreground">
                            Help improve the AI coach by sharing anonymized performance data
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={coach.anonymized_optin}
                            onChange={(e) => setCoach({ ...coach, anonymized_optin: e.target.checked })}
                            disabled={editing !== 'coach'}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      {editing === 'coach' && (
                        <div className="flex space-x-2">
                          <Button onClick={handleSaveCoach}>
                            <CheckIcon className="h-4 w-4 mr-2" />
                            Save Changes
                          </Button>
                          <Button variant="outline" onClick={() => setEditing(null)}>
                            <XMarkIcon className="h-4 w-4 mr-2" />
                            Cancel
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Sessions Tab */}
                {activeTab === 'sessions' && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Active Sessions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {sessions.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          <p>No active sessions</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {sessions.map((session) => (
                            <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h3 className="font-medium">{session.user_agent.substring(0, 50)}...</h3>
                                  {session.is_current && (
                                    <Badge variant="success">Current</Badge>
                                  )}
                                </div>
                                <p className="text-sm text-muted-foreground mt-1">
                                  {session.ip_address} • Created {formatDateTime(session.created_at)} • Last used {formatDateTime(session.last_used)}
                                </p>
                              </div>
                              {!session.is_current && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRevokeSession(session.id)}
                                >
                                  Revoke
                                </Button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Billing Tab */}
                {activeTab === 'billing' && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Billing & Subscription</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Current Plan</h3>
                          <p className="text-sm text-muted-foreground">Free Plan - Unlimited access to all features</p>
                        </div>
                        <Button variant="outline" size="sm">
                          Upgrade to Pro
                        </Button>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Payment Method</h3>
                          <p className="text-sm text-muted-foreground">No payment method on file</p>
                        </div>
                        <Button variant="outline" size="sm">
                          <CreditCardIcon className="h-4 w-4 mr-2" />
                          Add Payment Method
                        </Button>
                      </div>
                      
                      <div className="p-4 border border-danger-200 bg-danger-50 dark:bg-danger-950 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-danger-800 dark:text-danger-200">Danger Zone</h3>
                            <p className="text-sm text-danger-600 dark:text-danger-400">
                              Permanently delete your account and all data
                            </p>
                          </div>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={handleDeleteAccount}
                          >
                            <TrashIcon className="h-4 w-4 mr-2" />
                            Delete Account
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Add API Key Modal */}
      {showAddKeyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Exchange API Key</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Exchange</label>
                <select
                  value={newKeyVenue}
                  onChange={(e) => setNewKeyVenue(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                >
                  <option value="kraken">Kraken</option>
                  <option value="coinbase">Coinbase</option>
                  <option value="binance">Binance</option>
                  <option value="bybit">Bybit</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <input
                  type="text"
                  value={newApiKey}
                  onChange={(e) => setNewApiKey(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                  placeholder="Your API key"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">API Secret</label>
                <input
                  type="password"
                  value={newApiSecret}
                  onChange={(e) => setNewApiSecret(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                  placeholder="Your API secret"
                />
              </div>
              <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  ⚠️ Make sure your API key has read-only permissions. Never give withdrawal permissions.
                </p>
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleAddApiKey} className="flex-1">
                  Add API Key
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowAddKeyModal(false)
                    setNewApiKey('')
                    setNewApiSecret('')
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 2FA Setup Modal */}
      {show2FASetup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md max-h-[90vh] overflow-auto">
            <CardHeader>
              <CardTitle>Enable Two-Factor Authentication</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-4">
                  Scan this QR code with your authenticator app:
                </p>
                {qrCodeUrl && (
                  <img 
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrCodeUrl)}`}
                    alt="QR Code"
                    className="mx-auto border rounded-lg"
                  />
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Verification Code</label>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground text-center text-2xl tracking-widest"
                  placeholder="000000"
                  maxLength={6}
                />
              </div>

              {backupCodes.length > 0 && (
                <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                  <h4 className="font-medium text-amber-800 dark:text-amber-200 mb-2">Backup Codes</h4>
                  <p className="text-xs text-amber-700 dark:text-amber-300 mb-2">
                    Save these codes in a safe place. Each can be used once if you lose access to your authenticator.
                  </p>
                  <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                    {backupCodes.map((code, i) => (
                      <div key={i} className="text-amber-900 dark:text-amber-100">{code}</div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex space-x-2">
                <Button 
                  onClick={() => {
                    toast.success('2FA enabled successfully!')
                    setShow2FASetup(false)
                    if (security) {
                      setSecurity({ ...security, two_factor_enabled: true })
                    }
                  }}
                  className="flex-1"
                  disabled={verificationCode.length !== 6}
                >
                  Verify & Enable
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setShow2FASetup(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
