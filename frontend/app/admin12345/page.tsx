"use client";

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const ADMIN_PASSWORD = "TRADE!@#$%^";

export default function AdminDashboard() {
  const [password, setPassword] = useState('');
  const [storedPassword, setStoredPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [statsData, setStatsData] = useState<any>(null);
  const [insights, setInsights] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'users' | 'stats' | 'ai-posts' | 'bug-reports' | 'referrals' | 'analytics'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [userRole, setUserRole] = useState<'admin' | 'social_media_manager' | null>(null);
  const [searchEmail, setSearchEmail] = useState('');
  const [postTitle, setPostTitle] = useState('');
  const [postBody, setPostBody] = useState('');
  const [posting, setPosting] = useState(false);
  const [userPage, setUserPage] = useState(1);
  const [userTotal, setUserTotal] = useState(0);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [bugReports, setBugReports] = useState<any[]>([]);
  const [referralLinks, setReferralLinks] = useState<any[]>([]);
  const [selectedReferralLink, setSelectedReferralLink] = useState<any>(null);
  const [newReferralCode, setNewReferralCode] = useState('');
  const [newReferralName, setNewReferralName] = useState('');
  const [newReferralNotes, setNewReferralNotes] = useState('');
  const [analyticsData, setAnalyticsData] = useState<any>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Try to authenticate with the password
      const response = await fetch('/api/v1/admin12345/role', {
        headers: {
          'X-Admin-Password': password
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserRole(data.role);
        setStoredPassword(password); // Store password for API calls
        setIsAuthenticated(true);
        toast.success(`${data.role === 'admin' ? 'Admin' : 'Social Media Manager'} access granted`);
        
        // Load appropriate data based on role
        if (data.role === 'admin') {
          loadDashboard();
        } else if (data.role === 'social_media_manager') {
          // Social media managers see referrals and analytics by default
          setActiveTab('referrals');
          loadReferralLinks();
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Invalid password');
      }
    } catch (error) {
      toast.error('Failed to authenticate');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/dashboard', {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async (page: number = 1) => {
    setLoading(true);
    try {
      const skip = (page - 1) * 50;
      const url = searchEmail 
        ? `/api/v1/admin12345/users?search=${encodeURIComponent(searchEmail)}&skip=${skip}&limit=50`
        : `/api/v1/admin12345/users?skip=${skip}&limit=50`;
      
      const response = await fetch(url, {
        headers: {
          'X-Admin-Password': password
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
        setUserTotal(data.total || 0);
        setUserPage(page);
      }
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/stats', {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStatsData(data);
      }
    } catch (error) {
      toast.error('Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  const loadInsights = async () => {
    setLoading(true);
    try {
      // Get insights from the AI user
      const response = await fetch('/api/v1/admin12345/insights?user_id=ai@tradequest.tech&limit=50', {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setInsights(data.insights || []);
      }
    } catch (error) {
      toast.error('Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  const loadUserDetails = async (userId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/admin12345/users/${userId}`, {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedUser(data);
        setEditingUser({
          email: data.user.email,
          onboarding_completed: data.user.onboarding_completed
        });
      }
    } catch (error) {
      toast.error('Failed to load user details');
    } finally {
      setLoading(false);
    }
  };

  const updateSubscription = async (userId: string, plan: string, status: string) => {
    try {
      const response = await fetch(`/api/v1/admin12345/users/${userId}/subscription`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Password': storedPassword
        },
        body: JSON.stringify({ user_id: userId, plan, status })
      });
      
      if (response.ok) {
        toast.success('Subscription updated successfully');
        loadUserDetails(userId);
      } else {
        toast.error('Failed to update subscription');
      }
    } catch (error) {
      toast.error('Failed to update subscription');
    }
  };

  const updateUser = async (userId: string) => {
    if (!editingUser) return;
    
    try {
      const response = await fetch(`/api/v1/admin12345/users/${userId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Password': storedPassword
        },
        body: JSON.stringify({
          email: editingUser.email,
          onboarding_completed: editingUser.onboarding_completed
        })
      });
      
      if (response.ok) {
        toast.success('User updated successfully');
        loadUserDetails(userId);
        loadUsers(userPage);
      } else {
        toast.error('Failed to update user');
      }
    } catch (error) {
      toast.error('Failed to update user');
    }
  };

  const deleteUser = async (userId: string, email: string) => {
    if (!confirm(`Are you sure you want to delete user ${email}? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin12345/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      
      if (response.ok) {
        toast.success('User deleted successfully');
        setSelectedUser(null);
        loadUsers(userPage);
        loadDashboard();
      } else {
        toast.error('Failed to delete user');
      }
    } catch (error) {
      toast.error('Failed to delete user');
    }
  };

  const deleteInsight = async (insightId: string) => {
    if (!confirm('Are you sure you want to delete this insight?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin12345/insights/${insightId}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      
      if (response.ok) {
        toast.success('Insight deleted successfully');
        loadInsights();
      } else {
        toast.error('Failed to delete insight');
      }
    } catch (error) {
      toast.error('Failed to delete insight');
    }
  };

  const syncStripe = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/sync-stripe', {
        method: 'POST',
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(`Synced ${data.synced} subscriptions from Stripe`);
        loadDashboard();
        loadUsers(userPage);
      }
    } catch (error) {
      toast.error('Failed to sync Stripe');
    } finally {
      setLoading(false);
    }
  };

  const postDailyCompass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!postTitle.trim() || !postBody.trim()) {
      toast.error('Please fill in both title and body');
      return;
    }

    setPosting(true);
    try {
      // First ensure AI account exists
      const createResponse = await fetch('/api/v1/admin12345/create-ai-account', {
        method: 'POST',
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      
      if (!createResponse.ok) {
        throw new Error('Failed to create AI account');
      }

      // Then post the compass
      const postResponse = await fetch('/api/v1/admin12345/post-daily-compass', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Password': storedPassword
        },
        body: JSON.stringify({
          title: postTitle,
          body: postBody
        })
      });

      if (postResponse.ok) {
        const data = await postResponse.json();
        toast.success(`Posted successfully! Insight ID: ${data.insight_id}`);
        setPostTitle('');
        setPostBody('');
        loadInsights();
      } else {
        const error = await postResponse.json();
        throw new Error(error.detail || 'Failed to post');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to post daily compass');
    } finally {
      setPosting(false);
    }
  };

  const loadBugReports = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/bug-reports', {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBugReports(data.bug_reports || []);
      }
    } catch (error) {
      toast.error('Failed to load bug reports');
    } finally {
      setLoading(false);
    }
  };

  const updateBugReportStatus = async (reportId: string, status: string) => {
    try {
      const response = await fetch(`/api/v1/admin12345/bug-reports/${reportId}?status=${encodeURIComponent(status)}`, {
        method: 'PATCH',
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      
      if (response.ok) {
        toast.success('Bug report status updated');
        loadBugReports();
      } else {
        toast.error('Failed to update bug report status');
      }
    } catch (error) {
      toast.error('Failed to update bug report status');
    }
  };

  const loadReferralLinks = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/referral-links', {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setReferralLinks(data.referral_links || []);
      }
    } catch (error) {
      toast.error('Failed to load referral links');
    } finally {
      setLoading(false);
    }
  };

  const loadReferralLinkDetails = async (linkId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/admin12345/referral-links/${linkId}`, {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedReferralLink(data);
      }
    } catch (error) {
      toast.error('Failed to load referral link details');
    } finally {
      setLoading(false);
    }
  };

  const createReferralLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReferralCode.trim() || !newReferralName.trim()) {
      toast.error('Please fill in code and name');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/referral-links', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Password': storedPassword
        },
        body: JSON.stringify({
          code: newReferralCode.trim(),
          name: newReferralName.trim(),
          notes: newReferralNotes.trim() || undefined
        })
      });

      if (response.ok) {
        toast.success('Referral link created successfully');
        setNewReferralCode('');
        setNewReferralName('');
        setNewReferralNotes('');
        loadReferralLinks();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create referral link');
      }
    } catch (error) {
      toast.error('Failed to create referral link');
    } finally {
      setLoading(false);
    }
  };

  const toggleReferralLinkActive = async (linkId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/v1/admin12345/referral-links/${linkId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Password': storedPassword
        },
        body: JSON.stringify({
          is_active: !isActive
        })
      });

      if (response.ok) {
        toast.success('Referral link updated');
        loadReferralLinks();
        if (selectedReferralLink && selectedReferralLink.referral_link.id === linkId) {
          loadReferralLinkDetails(linkId);
        }
      } else {
        toast.error('Failed to update referral link');
      }
    } catch (error) {
      toast.error('Failed to update referral link');
    }
  };

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/analytics', {
        headers: {
          'X-Admin-Password': storedPassword
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (error) {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && activeTab === 'dashboard') {
      loadDashboard();
    } else if (isAuthenticated && activeTab === 'users') {
      loadUsers(1);
    } else if (isAuthenticated && activeTab === 'stats') {
      loadStats();
    } else if (isAuthenticated && activeTab === 'ai-posts') {
      loadInsights();
    } else if (isAuthenticated && activeTab === 'bug-reports') {
      loadBugReports();
    } else if (isAuthenticated && activeTab === 'referrals') {
      loadReferralLinks();
    } else if (isAuthenticated && activeTab === 'analytics') {
      loadAnalytics();
    }
  }, [isAuthenticated, activeTab]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800 rounded-2xl shadow-2xl p-8 max-w-md w-full border border-gray-700"
        >
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Admin Control Panel</h1>
            <p className="text-gray-400">Enter admin password to continue</p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Admin Password"
                autoFocus
              />
            </div>
            
            <button
              type="submit"
              className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-lg transition-colors"
            >
              Unlock Admin Panel
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-red-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold">TradeQuest Admin</h1>
                <p className="text-sm text-gray-400">Control Tower</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={syncStripe}
                disabled={loading}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                Sync Stripe
              </button>
              <button
                onClick={() => setIsAuthenticated(false)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition-colors"
              >
                Lock Panel
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {(
              userRole === 'admin' 
                ? ['dashboard', 'users', 'stats', 'ai-posts', 'bug-reports', 'referrals'] 
                : ['referrals', 'analytics']
            ).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`py-4 px-2 border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-red-500 text-white'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                {tab === 'ai-posts' ? 'AI Posts' : tab === 'bug-reports' ? 'Bug Reports' : tab === 'referrals' ? 'Referrals' : tab === 'analytics' ? 'Analytics' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto"></div>
          </div>
        )}

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboardData && !loading && (
          <div className="space-y-6">
            {/* Role Management (Admin Only) */}
            {userRole === 'admin' && (
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-xl font-bold mb-4">Role Management</h3>
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Social Media Manager Password</div>
                      <div className="text-lg font-mono font-bold">Check backend logs or environment variables</div>
                      <div className="text-xs text-gray-500 mt-2">
                        This password is randomly generated and stored in the backend configuration.
                        Check the server logs on startup or set SOCIAL_MEDIA_MANAGER_PASSWORD environment variable.
                      </div>
                    </div>
                    <button
                      onClick={async () => {
                        try {
                          // Try to get it from a new endpoint
                          const response = await fetch('/api/v1/admin12345/social-media-password', {
                            headers: {
                              'X-Admin-Password': storedPassword
                            }
                          });
                          if (response.ok) {
                            const data = await response.json();
                            navigator.clipboard.writeText(data.password);
                            toast.success('Password copied to clipboard!');
                          } else {
                            toast.error('Password not available via API. Check server logs.');
                          }
                        } catch (error) {
                          toast.error('Could not retrieve password. Check server logs.');
                        }
                      }}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium"
                    >
                      Get Password
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-400 text-sm font-medium">Total Users</h3>
                  <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl font-bold">{dashboardData.users.total}</div>
                <div className="text-sm text-green-400 mt-2">
                  +{dashboardData.users.today} today
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-400 text-sm font-medium">Active Subscriptions</h3>
                  <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl font-bold">{dashboardData.subscriptions.active}</div>
                <div className="text-sm text-gray-400 mt-2">
                  of {dashboardData.subscriptions.total} total
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-400 text-sm font-medium">MRR</h3>
                  <div className="w-10 h-10 bg-yellow-600 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl font-bold">${dashboardData.revenue.mrr}</div>
                <div className="text-sm text-gray-400 mt-2">
                  ${dashboardData.revenue.arr} ARR
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-400 text-sm font-medium">Total Trades</h3>
                  <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl font-bold">{dashboardData.trades.total}</div>
                <div className="text-sm text-green-400 mt-2">
                  +{dashboardData.trades.today} today
                </div>
              </div>
            </div>

            {/* Recent Users */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-4">Recent Users</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Email</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Created</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Onboarding</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.users.recent.map((user: any) => (
                      <tr key={user.id} className="border-b border-gray-700">
                        <td className="py-3 px-4">{user.email}</td>
                        <td className="py-3 px-4 text-gray-400">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4">
                          {user.onboarding_completed ? (
                            <span className="text-green-400">✓ Complete</span>
                          ) : (
                            <span className="text-yellow-400">Pending</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && !loading && (
          <div className="space-y-6">
            {/* Search */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={searchEmail}
                  onChange={(e) => setSearchEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadUsers(1)}
                  placeholder="Search by email..."
                  className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                />
                <button
                  onClick={() => loadUsers(1)}
                  className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
                >
                  Search
                </button>
              </div>
            </div>

            {/* Users Table */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-4">All Users ({userTotal})</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Email</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Plan</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Status</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Trades</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id} className="border-b border-gray-700">
                        <td className="py-3 px-4">{user.email}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            user.subscription.plan === 'plus_monthly' || user.subscription.plan === 'plus_yearly'
                              ? 'bg-green-600'
                              : 'bg-gray-600'
                          }`}>
                            {user.subscription.plan}
                          </span>
                        </td>
                        <td className="py-3 px-4">{user.subscription.status}</td>
                        <td className="py-3 px-4">{user.trade_count}</td>
                        <td className="py-3 px-4">
                          <button
                            onClick={() => loadUserDetails(user.id)}
                            className="text-red-400 hover:text-red-300 mr-3"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="flex justify-between items-center mt-4">
                <div className="text-sm text-gray-400">
                  Page {userPage} of {Math.ceil(userTotal / 50)}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => loadUsers(userPage - 1)}
                    disabled={userPage <= 1}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => loadUsers(userPage + 1)}
                    disabled={userPage >= Math.ceil(userTotal / 50)}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>

            {/* User Details Modal */}
            {selectedUser && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                <div className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto border border-gray-700">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h3 className="text-2xl font-bold">{selectedUser.user.email}</h3>
                      <p className="text-gray-400 text-sm">User ID: {selectedUser.user.id}</p>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedUser(null);
                        setEditingUser(null);
                      }}
                      className="text-gray-400 hover:text-white"
                    >
                      ✕
                    </button>
                  </div>

                  {/* User Details Edit */}
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold mb-3">User Details</h4>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Email</label>
                        <input
                          type="email"
                          value={editingUser?.email || ''}
                          onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Onboarding Completed</label>
                        <select
                          value={editingUser?.onboarding_completed ? 'true' : 'false'}
                          onChange={(e) => setEditingUser({ ...editingUser, onboarding_completed: e.target.value === 'true' })}
                          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                        >
                          <option value="false">No</option>
                          <option value="true">Yes</option>
                        </select>
                      </div>
                      <button
                        onClick={() => updateUser(selectedUser.user.id)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium"
                      >
                        Update User
                      </button>
                    </div>
                  </div>

                  {/* Subscription Management */}
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold mb-3">Subscription Management</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Plan</label>
                        <select
                          defaultValue={selectedUser.subscription?.plan || 'free'}
                          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                          onChange={(e) => {
                            const plan = e.target.value;
                            const status = selectedUser.subscription?.status || 'active';
                            updateSubscription(selectedUser.user.id, plan, status);
                          }}
                        >
                          <option value="free">Free</option>
                          <option value="plus_monthly">Plus Monthly</option>
                          <option value="plus_yearly">Plus Yearly</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Status</label>
                        <select
                          defaultValue={selectedUser.subscription?.status || 'active'}
                          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                          onChange={(e) => {
                            const status = e.target.value;
                            const plan = selectedUser.subscription?.plan || 'free';
                            updateSubscription(selectedUser.user.id, plan, status);
                          }}
                        >
                          <option value="active">Active</option>
                          <option value="canceled">Canceled</option>
                          <option value="past_due">Past Due</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Recent Trades */}
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold mb-3">Recent Trades ({selectedUser.trades.length})</h4>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {selectedUser.trades.map((trade: any) => (
                        <div key={trade.id} className="bg-gray-700 rounded-lg p-3 flex justify-between items-center">
                          <div>
                            <div className="font-medium">{trade.symbol}</div>
                            <div className="text-sm text-gray-400">
                              {trade.side} • {trade.filled_at ? new Date(trade.filled_at).toLocaleDateString() : 'N/A'}
                            </div>
                          </div>
                          <div className={`font-medium ${(trade.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {(trade.pnl || 0) >= 0 ? '+' : ''}{trade.pnl?.toFixed(2) || 'N/A'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Delete User */}
                  <div className="pt-4 border-t border-gray-700">
                    <button
                      onClick={() => deleteUser(selectedUser.user.id, selectedUser.user.email)}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium"
                    >
                      Delete User
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Stats Tab */}
        {activeTab === 'stats' && statsData && !loading && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-2xl font-bold mb-6">Platform Statistics</h3>
              
              {/* User Growth Chart */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-4">User Growth (Last 30 Days)</h4>
                <div className="h-64 flex items-end space-x-1">
                  {statsData.user_growth?.map((day: any, idx: number) => {
                    const maxUsers = Math.max(...statsData.user_growth.map((d: any) => d.total_users));
                    const height = (day.total_users / maxUsers) * 100;
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center">
                        <div
                          className="w-full bg-blue-600 rounded-t"
                          style={{ height: `${height}%` }}
                          title={`${day.date}: ${day.total_users} users`}
                        />
                        <div className="text-xs text-gray-400 mt-2 transform -rotate-45 origin-top-left">
                          {new Date(day.date).getDate()}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Subscription Breakdown */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-4">Subscription Breakdown</h4>
                <div className="space-y-2">
                  {statsData.subscription_breakdown?.map((sub: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center bg-gray-700 rounded-lg p-3">
                      <div>
                        <span className="font-medium">{sub.plan}</span>
                        <span className="text-gray-400 ml-2">({sub.status})</span>
                      </div>
                      <span className="text-lg font-bold">{sub.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Traders */}
              <div>
                <h4 className="text-lg font-semibold mb-4">Top Traders</h4>
                <div className="space-y-2">
                  {statsData.top_traders?.map((trader: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center bg-gray-700 rounded-lg p-3">
                      <span>{trader.email}</span>
                      <span className="font-bold">{trader.trade_count} trades</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Posts Tab */}
        {activeTab === 'ai-posts' && !loading && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold">Post Daily Market Compass</h3>
                  <p className="text-gray-400">Post as TradeQuest AI to the community insights section</p>
                </div>
              </div>

              <form onSubmit={postDailyCompass} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Title
                  </label>
                  <input
                    type="text"
                    value={postTitle}
                    onChange={(e) => setPostTitle(e.target.value)}
                    placeholder="e.g., 19 November 2025 Daily Market Compass"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Content
                  </label>
                  <textarea
                    value={postBody}
                    onChange={(e) => setPostBody(e.target.value)}
                    placeholder="Enter the daily market compass content here..."
                    rows={15}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
                    required
                  />
                  <p className="text-xs text-gray-400 mt-2">
                    {postBody.length} characters
                  </p>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                  <div className="text-sm text-gray-400">
                    <p>• Post will be published as TradeQuest AI</p>
                    <p>• Will appear in the community insights section</p>
                    <p>• Will be featured automatically</p>
                  </div>
                  <button
                    type="submit"
                    disabled={posting || !postTitle.trim() || !postBody.trim()}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
                  >
                    {posting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Posting...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        <span>Post Daily Compass</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Quick Template */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-lg font-semibold mb-4">Quick Template</h4>
              <button
                onClick={() => {
                  const today = new Date();
                  const dateStr = today.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });
                  setPostTitle(`${dateStr} Daily Market Compass`);
                  setPostBody(`In crypto markets, Bitcoin is trading around...\n\nIn forex pairs...\n\nThe bias...\n\nOn equities...\n\nIn commodities...\n\nShort-term actionable thesis: ...`);
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
              >
                Fill Template
              </button>
            </div>

            {/* Existing Insights */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-lg font-semibold mb-4">Existing Insights ({insights.length})</h4>
              <div className="space-y-3">
                {insights.map((insight: any) => (
                  <div key={insight.id} className="bg-gray-700 rounded-lg p-4 flex justify-between items-start">
                    <div className="flex-1">
                      <h5 className="font-semibold mb-1">{insight.title}</h5>
                      <p className="text-sm text-gray-400 line-clamp-2">{insight.description || insight.data?.content}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {insight.created_at ? new Date(insight.created_at).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteInsight(insight.id)}
                      className="ml-4 px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                    >
                      Delete
                    </button>
                  </div>
                ))}
                {insights.length === 0 && (
                  <p className="text-gray-400 text-center py-4">No insights found</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Bug Reports Tab */}
        {activeTab === 'bug-reports' && !loading && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-2xl font-bold mb-4">Bug Reports ({bugReports.length})</h3>
              <div className="space-y-4">
                {bugReports.map((report: any) => (
                  <div key={report.id} className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            report.status === 'open' ? 'bg-red-600' :
                            report.status === 'in_progress' ? 'bg-yellow-600' :
                            report.status === 'resolved' ? 'bg-green-600' : 'bg-gray-600'
                          }`}>
                            {report.status}
                          </span>
                          <span className="text-sm text-gray-400">{report.user_email}</span>
                          <span className="text-xs text-gray-500">
                            {report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'}
                          </span>
                        </div>
                        <h4 className="font-semibold text-white mb-2">{report.title}</h4>
                        <p className="text-sm text-gray-300 mb-3 whitespace-pre-wrap">{report.description}</p>
                        {report.url && (
                          <p className="text-xs text-gray-400 mb-2">
                            <strong>URL:</strong> {report.url}
                          </p>
                        )}
                        {report.screenshot_url && (
                          <div className="mb-3">
                            <img 
                              src={report.screenshot_url} 
                              alt="Screenshot" 
                              className="max-w-full h-48 object-contain border border-gray-600 rounded"
                            />
                          </div>
                        )}
                      </div>
                      <div className="ml-4 flex flex-col space-y-2">
                        <select
                          value={report.status}
                          onChange={(e) => updateBugReportStatus(report.id, e.target.value)}
                          className="px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm text-white"
                        >
                          <option value="open">Open</option>
                          <option value="in_progress">In Progress</option>
                          <option value="resolved">Resolved</option>
                          <option value="closed">Closed</option>
                        </select>
                      </div>
                    </div>
                  </div>
                ))}
                {bugReports.length === 0 && (
                  <p className="text-gray-400 text-center py-8">No bug reports found</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Referrals Tab */}
        {activeTab === 'referrals' && !loading && (
          <div className="space-y-6">
            {/* Create New Referral Link */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-2xl font-bold mb-6">Create Referral Link</h3>
              <form onSubmit={createReferralLink} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Referral Code *
                    </label>
                    <input
                      type="text"
                      value={newReferralCode}
                      onChange={(e) => setNewReferralCode(e.target.value)}
                      placeholder="e.g., INFLUENCER1"
                      className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Name/Description *
                    </label>
                    <input
                      type="text"
                      value={newReferralName}
                      onChange={(e) => setNewReferralName(e.target.value)}
                      placeholder="e.g., Influencer X Campaign"
                      className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Notes (Optional)
                  </label>
                  <textarea
                    value={newReferralNotes}
                    onChange={(e) => setNewReferralNotes(e.target.value)}
                    placeholder="Additional notes about this referral link..."
                    rows={3}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
                >
                  Create Referral Link
                </button>
              </form>
            </div>

            {/* Referral Links List */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-2xl font-bold mb-4">Referral Links ({referralLinks.length})</h3>
              <div className="space-y-4">
                {referralLinks.map((link) => (
                  <div key={link.id} className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            link.is_active ? 'bg-green-600' : 'bg-gray-600'
                          }`}>
                            {link.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <span className="font-semibold text-lg">{link.name}</span>
                          <span className="text-gray-400">({link.code})</span>
                        </div>
                        {link.notes && (
                          <p className="text-sm text-gray-400 mb-2">{link.notes}</p>
                        )}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <span className="text-xs text-gray-400">Signups</span>
                            <div className="text-lg font-bold">{link.signups_count}</div>
                          </div>
                          <div>
                            <span className="text-xs text-gray-400">Users</span>
                            <div className="text-lg font-bold">{link.user_count || 0}</div>
                          </div>
                          <div>
                            <span className="text-xs text-gray-400">First Signup</span>
                            <div className="text-sm">
                              {link.first_signup_at 
                                ? new Date(link.first_signup_at).toLocaleDateString()
                                : 'N/A'}
                            </div>
                          </div>
                          <div>
                            <span className="text-xs text-gray-400">Last Signup</span>
                            <div className="text-sm">
                              {link.last_signup_at
                                ? new Date(link.last_signup_at).toLocaleDateString()
                                : 'N/A'}
                            </div>
                          </div>
                        </div>
                        <div className="mt-3">
                          <span className="text-xs text-gray-400">Referral URL:</span>
                          <div className="mt-1 flex items-center space-x-2">
                            <code className="px-2 py-1 bg-gray-800 rounded text-sm text-blue-400">
                              {typeof window !== 'undefined' ? window.location.origin : ''}/auth?ref={link.code}
                            </code>
                            <button
                              onClick={() => {
                                const url = `${window.location.origin}/auth?ref=${link.code}`;
                                navigator.clipboard.writeText(url);
                                toast.success('Referral URL copied to clipboard');
                              }}
                              className="px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-xs"
                            >
                              Copy
                            </button>
                          </div>
                        </div>
                      </div>
                      <div className="ml-4 flex flex-col space-y-2">
                        <button
                          onClick={() => loadReferralLinkDetails(link.id)}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                        >
                          View Details
                        </button>
                        <button
                          onClick={() => toggleReferralLinkActive(link.id, link.is_active)}
                          className={`px-3 py-1 rounded text-sm ${
                            link.is_active
                              ? 'bg-yellow-600 hover:bg-yellow-700'
                              : 'bg-green-600 hover:bg-green-700'
                          }`}
                        >
                          {link.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                {referralLinks.length === 0 && (
                  <p className="text-gray-400 text-center py-8">No referral links created yet</p>
                )}
              </div>
            </div>

            {/* Referral Link Details Modal */}
            {selectedReferralLink && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                <div className="bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto border border-gray-700">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h3 className="text-2xl font-bold">{selectedReferralLink.referral_link.name}</h3>
                      <p className="text-gray-400">Code: {selectedReferralLink.referral_link.code}</p>
                    </div>
                    <button
                      onClick={() => setSelectedReferralLink(null)}
                      className="text-gray-400 hover:text-white text-2xl"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400">Total Signups</div>
                      <div className="text-2xl font-bold">{selectedReferralLink.referral_link.signups_count}</div>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400">Total Users</div>
                      <div className="text-2xl font-bold">{selectedReferralLink.total_users}</div>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400">First Signup</div>
                      <div className="text-sm">
                        {selectedReferralLink.referral_link.first_signup_at
                          ? new Date(selectedReferralLink.referral_link.first_signup_at).toLocaleString()
                          : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400">Last Signup</div>
                      <div className="text-sm">
                        {selectedReferralLink.referral_link.last_signup_at
                          ? new Date(selectedReferralLink.referral_link.last_signup_at).toLocaleString()
                          : 'N/A'}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold mb-3">Users ({selectedReferralLink.total_users})</h4>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {selectedReferralLink.users.map((user: any) => (
                        <div key={user.id} className="bg-gray-700 rounded-lg p-3 flex justify-between items-center">
                          <div>
                            <div className="font-medium">{user.email}</div>
                            <div className="text-sm text-gray-400">
                              Signed up: {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                            </div>
                          </div>
                          <div>
                            {user.onboarding_completed ? (
                              <span className="text-green-400 text-sm">✓ Onboarded</span>
                            ) : (
                              <span className="text-yellow-400 text-sm">Pending</span>
                            )}
                          </div>
                        </div>
                      ))}
                      {selectedReferralLink.users.length === 0 && (
                        <p className="text-gray-400 text-center py-4">No users signed up with this referral link yet</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && analyticsData && !loading && (
          <div className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Total Signups</div>
                <div className="text-3xl font-bold">{analyticsData.overview.total_signups}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Total Users</div>
                <div className="text-3xl font-bold">{analyticsData.overview.total_users}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Active Links</div>
                <div className="text-3xl font-bold">{analyticsData.overview.active_referral_links}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Conversion Rate</div>
                <div className="text-3xl font-bold">{analyticsData.overview.conversion_rate}%</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="text-gray-400 text-sm mb-2">Onboarded Users</div>
                <div className="text-3xl font-bold">{analyticsData.overview.onboarded_users}</div>
              </div>
            </div>

            {/* Signups Over Time Chart */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-2xl font-bold mb-6">Signups Over Time (Last 30 Days)</h3>
              <div className="h-64 flex items-end space-x-1">
                {analyticsData.signups_over_time?.map((day: any, idx: number) => {
                  const maxSignups = Math.max(...analyticsData.signups_over_time.map((d: any) => d.signups));
                  const height = maxSignups > 0 ? (day.signups / maxSignups) * 100 : 0;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-blue-600 rounded-t hover:bg-blue-500 transition-colors"
                        style={{ height: `${height}%` }}
                        title={`${day.date}: ${day.signups} signups`}
                      />
                      <div className="text-xs text-gray-400 mt-2 transform -rotate-45 origin-top-left whitespace-nowrap">
                        {new Date(day.date).getDate()}/{new Date(day.date).getMonth() + 1}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Top Performing Links */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-2xl font-bold mb-6">Top Performing Referral Links</h3>
              <div className="space-y-3">
                {analyticsData.top_performing_links?.map((link: any, idx: number) => (
                  <div key={idx} className="bg-gray-700 rounded-lg p-4 flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-2xl font-bold text-gray-400">#{idx + 1}</span>
                        <span className="font-semibold text-lg">{link.name}</span>
                        <span className="text-gray-400">({link.code})</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          link.is_active ? 'bg-green-600' : 'bg-gray-600'
                        }`}>
                          {link.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="text-sm text-gray-400">
                        First: {link.first_signup ? new Date(link.first_signup).toLocaleDateString() : 'N/A'} • 
                        Last: {link.last_signup ? new Date(link.last_signup).toLocaleDateString() : 'N/A'}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-blue-400">{link.signups}</div>
                      <div className="text-sm text-gray-400">signups</div>
                    </div>
                  </div>
                ))}
                {analyticsData.top_performing_links?.length === 0 && (
                  <p className="text-gray-400 text-center py-4">No referral links yet</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
