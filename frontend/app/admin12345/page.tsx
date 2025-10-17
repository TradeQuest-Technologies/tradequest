"use client";

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const ADMIN_PASSWORD = "TRADE!@#$%^";

export default function AdminDashboard() {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'users' | 'stats'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [searchEmail, setSearchEmail] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === ADMIN_PASSWORD) {
      setIsAuthenticated(true);
      toast.success('Admin access granted');
      loadDashboard();
    } else {
      toast.error('Invalid admin password');
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/dashboard', {
        headers: {
          'X-Admin-Password': ADMIN_PASSWORD
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

  const loadUsers = async () => {
    setLoading(true);
    try {
      const url = searchEmail 
        ? `/api/v1/admin12345/users?search=${searchEmail}`
        : '/api/v1/admin12345/users';
      
      const response = await fetch(url, {
        headers: {
          'X-Admin-Password': ADMIN_PASSWORD
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadUserDetails = async (userId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/admin12345/users/${userId}`, {
        headers: {
          'X-Admin-Password': ADMIN_PASSWORD
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedUser(data);
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
          'X-Admin-Password': ADMIN_PASSWORD
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

  const syncStripe = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin12345/sync-stripe', {
        method: 'POST',
        headers: {
          'X-Admin-Password': ADMIN_PASSWORD
        }
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(`Synced ${data.synced} subscriptions from Stripe`);
        loadDashboard();
      }
    } catch (error) {
      toast.error('Failed to sync Stripe');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && activeTab === 'dashboard') {
      loadDashboard();
    } else if (isAuthenticated && activeTab === 'users') {
      loadUsers();
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
            {(['dashboard', 'users', 'stats'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-2 border-b-2 transition-colors capitalize ${
                  activeTab === tab
                    ? 'border-red-500 text-white'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                {tab}
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
                  placeholder="Search by email..."
                  className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                />
                <button
                  onClick={loadUsers}
                  className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
                >
                  Search
                </button>
              </div>
            </div>

            {/* Users Table */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-4">All Users ({users.length})</h3>
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
                            className="text-red-400 hover:text-red-300"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
                      onClick={() => setSelectedUser(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      ✕
                    </button>
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
                  <div>
                    <h4 className="text-lg font-semibold mb-3">Recent Trades ({selectedUser.trades.length})</h4>
                    <div className="space-y-2">
                      {selectedUser.trades.map((trade: any) => (
                        <div key={trade.id} className="bg-gray-700 rounded-lg p-3 flex justify-between items-center">
                          <div>
                            <div className="font-medium">{trade.symbol}</div>
                            <div className="text-sm text-gray-400">{trade.side} • {trade.entry_date}</div>
                          </div>
                          <div className={`font-medium ${trade.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.profit_loss >= 0 ? '+' : ''}{trade.profit_loss?.toFixed(2) || 'N/A'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

