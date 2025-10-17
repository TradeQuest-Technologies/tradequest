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
  ShieldCheckIcon,
  CogIcon,
  KeyIcon,
  GlobeAltIcon,
  CreditCardIcon,
  TrashIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'
import { formatDateTime } from '../../lib/utils'
import { getAuthToken } from '../../lib/auth'
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
  two_factor_method: string | null  // "totp", "email", "sms", or null
  last_password_change: string | null
  active_sessions: number
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

interface BillingInfo {
  plan: string
  status: string
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  current_period_end: number | null
  cancel_at_period_end: boolean
  payment_method: {
    brand: string
    last4: string
    exp_month: number
    exp_year: number
  } | null
}

export default function Settings() {
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('profile')
  const [editing, setEditing] = useState<string | null>(null)
  const router = useRouter()

  // State for each settings section
  const [profile, setProfile] = useState<ProfileSettings | null>(null)
  const [security, setSecurity] = useState<SecuritySettings | null>(null)
  const [coach, setCoach] = useState<CoachPreferences | null>(null)
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [billing, setBilling] = useState<BillingInfo | null>(null)

  // 2FA setup state
  const [show2FASetup, setShow2FASetup] = useState(false)
  const [show2FAMethodSelect, setShow2FAMethodSelect] = useState(false)
  const [selected2FAMethod, setSelected2FAMethod] = useState<'totp' | 'email' | null>(null)
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [verificationCode, setVerificationCode] = useState('')
  const [setupStep, setSetupStep] = useState<'qr' | 'verify'>('qr')

  // Password change state
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordChange2FACode, setPasswordChange2FACode] = useState('')

  // Disable 2FA state
  const [showDisable2FA, setShowDisable2FA] = useState(false)
  const [disable2FACode, setDisable2FACode] = useState('')

  // Email 2FA code sending state
  const [emailCodeSent, setEmailCodeSent] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)

  useEffect(() => {
    const token = getAuthToken()
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
    const token = getAuthToken()
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
        { url: `${apiUrl}/api/v1/settings/coach`, setter: setCoach },
        { url: `${apiUrl}/api/v1/settings/api-keys`, setter: null, isArray: true },
        { url: `${apiUrl}/api/v1/settings/sessions`, setter: null, isArray: true },
        { url: `${apiUrl}/api/v1/settings/billing`, setter: setBilling }
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
      const token = getAuthToken()
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

  const handleSaveCoach = async () => {
    if (!coach) return

    try {
      const token = getAuthToken()
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

  const handleEnable2FA = () => {
    setShow2FAMethodSelect(true)
  }

  const handle2FAMethodSelect = async (method: 'totp' | 'email') => {
    setSelected2FAMethod(method)
    setShow2FAMethodSelect(false)
    
    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/2fa/enable`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ method })
      })

      if (response.ok) {
        const data = await response.json()
        if (method === 'totp') {
          setQrCodeUrl(data.qr_code_url)
          setBackupCodes(data.backup_codes)
          setSelected2FAMethod('totp')
          setSetupStep('qr')
          setShow2FASetup(true)
        } else {
          // Email 2FA - show verification step
          setSelected2FAMethod('email')
          setSetupStep('verify')
          setShow2FASetup(true)
          toast.success('Verification code sent to your email!')
        }
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to enable 2FA')
        // Refresh security settings to show current state
        const secResponse = await fetch(`${apiUrl}/api/v1/settings/security`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (secResponse.ok) {
          const secData = await secResponse.json()
          setSecurity(secData)
        }
      }
    } catch (error) {
      toast.error('Failed to enable 2FA')
    }
  }

  const handle2FAVerification = async () => {
    if (!verificationCode) {
      toast.error('Please enter the verification code')
      return
    }

    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/2fa/verify-setup`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ verification_code: verificationCode })
      })

      if (response.ok) {
        const data = await response.json()
        toast.success(data.message)
        setShow2FASetup(false)
        setVerificationCode('')
        setSetupStep('qr')
        setSelected2FAMethod(null)
        fetchSecuritySettings()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Verification failed')
      }
    } catch (error) {
      toast.error('Failed to verify 2FA')
    }
  }

  const handleDisable2FA = async () => {
    if (!disable2FACode) {
      toast.error('Please enter your 2FA code')
      return
    }

    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/2fa/disable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          two_factor_code: disable2FACode
        })
      })

      if (response.ok) {
        toast.success('2FA disabled successfully!')
        setShowDisable2FA(false)
        setDisable2FACode('')
        if (security) {
          setSecurity({ ...security, two_factor_enabled: false })
        }
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to disable 2FA')
      }
    } catch (error) {
      toast.error('Failed to disable 2FA')
    }
  }

  const handleSendEmailCode = async () => {
    setSendingCode(true)
    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/2fa/send-code`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('Verification code sent to your email')
        setEmailCodeSent(true)
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to send code')
      }
    } catch (error) {
      toast.error('Failed to send verification code')
    } finally {
      setSendingCode(false)
    }
  }

  const handleChangePassword = async () => {
    // Validate inputs
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Please fill in all password fields')
      return
    }

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match')
      return
    }

    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters long')
      return
    }

    // Check 2FA if enabled
    if (security?.two_factor_enabled && !passwordChange2FACode) {
      toast.error('Please enter your 2FA code')
      return
    }

    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/password/change`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          two_factor_code: passwordChange2FACode || null
        })
      })

      if (response.ok) {
        toast.success('Password changed successfully!')
        setShowPasswordChange(false)
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
        setPasswordChange2FACode('')
        
        // Refresh security settings
        const secResponse = await fetch(`${apiUrl}/api/v1/settings/security`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (secResponse.ok) {
          const secData = await secResponse.json()
          setSecurity(secData)
        }
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to change password')
      }
    } catch (error) {
      toast.error('Failed to change password')
    }
  }

  const handleAddApiKey = async () => {
    if (!newApiKey || !newApiSecret) {
      toast.error('Please fill in all fields')
      return
    }

    try {
      const token = getAuthToken()
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
      const token = getAuthToken()
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
      const token = getAuthToken()
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

  const handleOpenBillingPortal = async () => {
    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/billing/portal`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        window.location.href = data.url
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to open billing portal')
      }
    } catch (error) {
      toast.error('Failed to open billing portal')
    }
  }

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will continue to have access until the end of your billing period.')) {
      return
    }

    try {
      const token = getAuthToken()
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/settings/billing/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        toast.success(data.message)
        // Refresh billing info
        const billingResponse = await fetch(`${apiUrl}/api/v1/settings/billing`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (billingResponse.ok) {
          const billingData = await billingResponse.json()
          setBilling(billingData)
        }
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to cancel subscription')
      }
    } catch (error) {
      toast.error('Failed to cancel subscription')
    }
  }

  const handleDeleteAccount = async () => {
    const confirmText = prompt('Type DELETE to confirm account deletion:')
    if (confirmText !== 'DELETE') {
      toast.error('Account deletion cancelled')
      return
    }

    try {
      const token = getAuthToken()
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
                            onClick={security.two_factor_enabled ? () => setShowDisable2FA(true) : handleEnable2FA}
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
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setShowPasswordChange(true)}
                        >
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
                {activeTab === 'billing' && billing && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Billing & Subscription</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Current Plan</h3>
                          <p className="text-sm text-muted-foreground">
                            {billing.plan === 'plus_monthly' || billing.plan === 'plus_yearly' ? 'Plus' : billing.plan.charAt(0).toUpperCase() + billing.plan.slice(1)} Plan
                            {billing.cancel_at_period_end && ' (Cancels at period end)'}
                          </p>
                          {billing.current_period_end && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {billing.cancel_at_period_end ? 'Access until' : 'Renews on'}: {new Date(billing.current_period_end * 1000).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                        {billing.plan === 'free' ? (
                          <Button variant="outline" size="sm" onClick={() => router.push('/pricing')}>
                            Upgrade to Pro
                          </Button>
                        ) : !billing.cancel_at_period_end && billing.stripe_customer_id && (
                          <Button variant="outline" size="sm" onClick={handleCancelSubscription}>
                            Cancel Plan
                          </Button>
                        )}
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h3 className="font-medium">Payment Method</h3>
                          {billing.payment_method ? (
                            <p className="text-sm text-muted-foreground">
                              {billing.payment_method.brand.toUpperCase()} •••• {billing.payment_method.last4}
                              <span className="ml-2 text-xs">
                                Expires {billing.payment_method.exp_month}/{billing.payment_method.exp_year}
                              </span>
                            </p>
                          ) : (
                            <p className="text-sm text-muted-foreground">No payment method on file</p>
                          )}
                        </div>
                        {billing.stripe_customer_id && (
                          <Button variant="outline" size="sm" onClick={handleOpenBillingPortal}>
                            <CreditCardIcon className="h-4 w-4 mr-2" />
                            Manage Billing
                          </Button>
                        )}
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

      {/* Password Change Modal */}
      {showPasswordChange && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                  placeholder="Enter current password"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                  placeholder="Enter new password (min 8 characters)"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                  placeholder="Confirm new password"
                />
              </div>
              {security?.two_factor_enabled && (
                <div>
                  <label className="block text-sm font-medium mb-2">
                    2FA Code {security.two_factor_method === 'email' && '(Check your email)'}
                  </label>
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={passwordChange2FACode}
                      onChange={(e) => setPasswordChange2FACode(e.target.value)}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground"
                      placeholder={security.two_factor_method === 'totp' ? 'Enter code from authenticator app' : 'Enter code from email'}
                      maxLength={6}
                    />
                    {security.two_factor_method === 'email' && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleSendEmailCode}
                        disabled={sendingCode}
                        className="w-full"
                      >
                        {sendingCode ? 'Sending...' : emailCodeSent ? 'Resend Code' : 'Send Code'}
                      </Button>
                    )}
                  </div>
                </div>
              )}
              <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  💡 Password must be at least 8 characters long and cannot be one of your last 5 passwords.
                </p>
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleChangePassword} className="flex-1">
                  Change Password
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowPasswordChange(false)
                    setCurrentPassword('')
                    setNewPassword('')
                    setConfirmPassword('')
                    setPasswordChange2FACode('')
                    setEmailCodeSent(false)
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

      {/* 2FA Method Selection Modal */}
      {show2FAMethodSelect && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Choose Two-Factor Authentication Method</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Select how you'd like to receive your verification codes:
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => handle2FAMethodSelect('totp')}
                  className="w-full p-4 border border-input rounded-lg hover:bg-accent transition-colors text-left"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <ShieldCheckIcon className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-medium">Authenticator App</h3>
                      <p className="text-sm text-muted-foreground">
                        Use Google Authenticator, Authy, or similar apps
                      </p>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={() => handle2FAMethodSelect('email')}
                  className="w-full p-4 border border-input rounded-lg hover:bg-accent transition-colors text-left"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <EnvelopeIcon className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-medium">Email</h3>
                      <p className="text-sm text-muted-foreground">
                        Receive verification codes via email
                      </p>
                    </div>
                  </div>
                </button>
              </div>
              
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShow2FAMethodSelect(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Disable 2FA Modal */}
      {showDisable2FA && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Disable Two-Factor Authentication</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  ⚠️ To confirm you still have access to your 2FA {security?.two_factor_method === 'email' ? 'email' : 'device'}, please enter your current 2FA code.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  2FA Code {security?.two_factor_method === 'email' && '(Check your email)'}
                </label>
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={disable2FACode}
                        onChange={(e) => setDisable2FACode(e.target.value)}
                        className="flex-1 px-3 py-2 border border-input rounded-lg bg-background text-foreground text-center text-2xl tracking-widest"
                        placeholder="000000"
                        maxLength={6}
                      />
                    </div>
                    {security?.two_factor_method === 'email' && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleSendEmailCode}
                        disabled={sendingCode}
                        className="w-full"
                      >
                        {sendingCode ? 'Sending...' : emailCodeSent ? 'Resend Code' : 'Send Code'}
                      </Button>
                    )}
                  </div>
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleDisable2FA} variant="destructive" className="flex-1">
                  Disable 2FA
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowDisable2FA(false)
                    setDisable2FACode('')
                    setEmailCodeSent(false)
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
              <CardTitle>
                {selected2FAMethod === 'totp' ? 'Setup Authenticator App' : 'Setup Email 2FA'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {setupStep === 'qr' && selected2FAMethod === 'totp' && (
                <>
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
                </>
              )}

              {setupStep === 'verify' && (
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-4">
                    {selected2FAMethod === 'totp' 
                      ? 'Enter the 6-digit code from your authenticator app to verify setup:'
                      : 'Enter the 6-digit verification code sent to your email:'
                    }
                  </p>
                </div>
              )}

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

              <div className="flex space-x-2">
                <Button 
                  onClick={selected2FAMethod === 'totp' && setupStep === 'qr' 
                    ? () => setSetupStep('verify')
                    : handle2FAVerification
                  }
                  className="flex-1"
                  disabled={verificationCode.length !== 6}
                >
                  {selected2FAMethod === 'totp' && setupStep === 'qr' 
                    ? 'Next: Verify Code'
                    : 'Verify & Enable'
                  }
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShow2FASetup(false)
                    setVerificationCode('')
                    setSetupStep('qr')
                    setSelected2FAMethod(null)
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
    </div>
  )
}
