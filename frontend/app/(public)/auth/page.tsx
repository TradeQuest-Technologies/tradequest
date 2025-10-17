"use client";

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeftIcon, EnvelopeIcon, ChartBarIcon, ShieldCheckIcon, LockClosedIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function PublicAuthPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [authMode, setAuthMode] = useState<'signup' | 'signin' | 'forgot-password'>('signup');
  const [showPasswordField, setShowPasswordField] = useState(false);
  const [show2FAField, setShow2FAField] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [twoFactorMethod, setTwoFactorMethod] = useState<string | null>(null);
  const router = useRouter();

  const handleSendMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/magic-link', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email,
          is_signup: authMode === 'signup'
        }),
      });

      if (response.ok) {
        // Always redirect to thank you page for magic link
        router.push('/auth/thank-you');
      } else {
        const error = await response.json();
        // If user exists during signup, show specific message with confirm dialog
        if (error.detail && error.detail.includes('already exists')) {
          // Show a custom error message
          const shouldSignIn = window.confirm(
            'An account with this email already exists.\n\nWould you like to sign in instead?'
          );
          
          if (shouldSignIn) {
            setAuthMode('signin');
            toast.success('Switched to sign in mode');
          }
        } else {
          toast.error(error.detail || 'Failed to send magic link');
        }
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/password-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, remember_me: rememberMe }),
      });

      const data = await response.json();

      if (response.ok) {
        if (data.requires_2fa) {
          setTempToken(data.temp_token);
          setTwoFactorMethod(data.two_factor_method || null);
          setShow2FAField(true);
          const method = data.two_factor_method || '2FA';
          toast.success(method === 'email' ? 'We emailed you a verification code.' : 'Password verified. Please enter your 2FA code.');
          if (method === 'email') {
            setResendCooldown(60);
          }
        } else {
          // Store token and redirect
          if (rememberMe) {
            localStorage.setItem('tq_session', data.access_token);
            localStorage.setItem('tq_expires_at', (Date.now() + (30 * 24 * 60 * 60 * 1000)).toString());
          } else {
            sessionStorage.setItem('tq_session', data.access_token);
            sessionStorage.setItem('tq_expires_at', (Date.now() + (24 * 60 * 60 * 1000)).toString());
          }
          toast.success('Login successful!');
          router.push('/dashboard');
        }
      } else {
        toast.error(data.detail || 'Login failed');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handle2FAVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!twoFactorCode) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/verify-2fa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ temp_token: tempToken, code: twoFactorCode, remember_me: rememberMe }),
      });

      const data = await response.json();

      if (response.ok) {
        if (rememberMe) {
          localStorage.setItem('tq_session', data.access_token);
          localStorage.setItem('tq_expires_at', (Date.now() + (30 * 24 * 60 * 60 * 1000)).toString());
        } else {
          sessionStorage.setItem('tq_session', data.access_token);
          sessionStorage.setItem('tq_expires_at', (Date.now() + (24 * 60 * 60 * 1000)).toString());
        }
        toast.success('2FA verified! Login successful.');
        router.push('/dashboard');
      } else {
        toast.error(data.detail || '2FA verification failed');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Resend code for email 2FA
  const handleResendCode = async () => {
    if (!tempToken || resendCooldown > 0) return;
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/auth/resend-2fa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_token: tempToken }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success('Verification code resent');
        setResendCooldown(60);
      } else {
        toast.error(data.detail || 'Failed to resend code');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setInterval(() => setResendCooldown((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, [resendCooldown]);

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    // If 2FA is required but code not provided, show error
    if (show2FAField && !twoFactorCode) {
      toast.error('Please enter your verification code');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email,
          two_factor_code: twoFactorCode || undefined
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Check if 2FA is required
        if (data.requires_2fa) {
          setShow2FAField(true);
          setTwoFactorMethod(data.two_factor_method || null);
          if (data.two_factor_method === 'email') {
            toast.success('Verification code sent to your email');
            setResendCooldown(60);
          } else if (data.two_factor_method === 'totp') {
            toast.success('Enter the code from your authenticator app');
          } else {
            toast.success('2FA verification required');
          }
        } else {
          // Success - reset link sent
          toast.success('Password reset instructions sent to your email');
          // Switch back to signin mode after a delay
          setTimeout(() => {
            setAuthMode('signin');
            setShow2FAField(false);
            setTwoFactorCode('');
          }, 2000);
        }
      } else {
        toast.error(data.detail || 'Failed to send reset instructions');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend2FAForForgotPassword = async () => {
    if (!email || resendCooldown > 0) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        toast.success('Verification code resent');
        setResendCooldown(60);
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to resend code');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="flex min-h-screen">
        {/* Left Side - Form */}
        <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-900">
          <div className="mx-auto w-full max-w-md">
            {/* Header */}
            <div className="mb-8">
              <Link href="/" className="inline-flex items-center text-white/80 hover:text-white mb-6 transition-colors">
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Back to Home
              </Link>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="text-center"
              >
                <div className="text-3xl font-bold text-white mb-2">
                  TradeQuest
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  {authMode === 'signup' ? 'Create your account' : authMode === 'forgot-password' ? 'Reset your password' : 'Welcome back'}
                </h2>
                <p className="text-white/80">
                  {authMode === 'forgot-password' 
                    ? 'Enter your email to receive reset instructions'
                    : 'Enter your email to get a magic link'
                  }
                </p>
              </motion.div>
            </div>

            {/* Auth Mode Toggle */}
            {authMode !== 'forgot-password' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="mb-8"
              >
                <div className="bg-white/20 rounded-lg p-1 flex">
                  <button
                    onClick={() => setAuthMode('signup')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                      authMode === 'signup'
                        ? 'bg-white text-brand-dark-teal shadow-sm'
                        : 'text-white/80 hover:text-white'
                    }`}
                  >
                    Sign Up
                  </button>
                  <button
                    onClick={() => setAuthMode('signin')}
                    className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                      authMode === 'signin'
                        ? 'bg-white text-brand-dark-teal shadow-sm'
                        : 'text-white/80 hover:text-white'
                    }`}
                  >
                    Sign In
                  </button>
                </div>
              </motion.div>
            )}

            {/* Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-white rounded-lg shadow-xl p-8"
            >
              <AnimatePresence mode="wait">
                {show2FAField ? (
                  <motion.form
                    key="2fa"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -50 }}
                    onSubmit={authMode === 'forgot-password' ? handleForgotPassword : handle2FAVerification}
                    className="space-y-6"
                  >
                    <div className="text-center mb-6">
                      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Two-Factor Authentication
                      </h3>
                      <p className="text-gray-600">
                        {twoFactorMethod === 'email' && 'Enter the 6-digit code sent to your email'}
                        {twoFactorMethod === 'sms' && 'Enter the 6-digit code sent via SMS'}
                        {!twoFactorMethod || twoFactorMethod === 'totp' ? 'Enter the 6-digit code from your authenticator app' : ''}
                      </p>
                    </div>

                    <div>
                      <label htmlFor="twoFactorCode" className="block text-sm font-medium text-gray-700 mb-2">
                        {twoFactorMethod === 'email' && 'Email verification code'}
                        {twoFactorMethod === 'sms' && 'SMS verification code'}
                        {!twoFactorMethod || twoFactorMethod === 'totp' ? 'Authenticator app code' : ''}
                      </label>
                      <input
                        id="twoFactorCode"
                        name="twoFactorCode"
                        type="text"
                        maxLength={6}
                        value={twoFactorCode}
                        onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                        className="block w-full px-4 py-3 border border-gray-300 rounded-md text-center text-lg font-mono text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                        placeholder="000000"
                      />
                    </div>

                    {twoFactorMethod === 'email' && (
                      <button
                        type="button"
                        onClick={authMode === 'forgot-password' ? handleResend2FAForForgotPassword : handleResendCode}
                        disabled={resendCooldown > 0 || isLoading}
                        className="w-full text-sm text-brand-dark-teal hover:text-brand-dark-teal/80 disabled:text-gray-400"
                      >
                        {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : 'Resend code'}
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={isLoading || twoFactorCode.length !== 6}
                      className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-dark-teal hover:bg-brand-dark-teal/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-dark-teal disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isLoading 
                        ? 'Verifying...' 
                        : authMode === 'forgot-password'
                          ? 'Verify & Send Reset Link'
                          : 'Verify & Sign In'
                      }
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setShow2FAField(false);
                        setTwoFactorCode('');
                      }}
                      className="w-full text-sm text-gray-600 hover:text-gray-800 transition-colors"
                    >
                      {authMode === 'forgot-password' ? 'Back to forgot password' : 'Back to login'}
                    </button>
                  </motion.form>
                ) : (
                  <motion.form
                    key="login"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -50 }}
                    onSubmit={
                      authMode === 'forgot-password' 
                        ? handleForgotPassword 
                        : authMode === 'signin' 
                          ? handlePasswordLogin 
                          : handleSendMagicLink
                    }
                    className="space-y-6"
                  >
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                        Email address
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                          id="email"
                          name="email"
                          type="email"
                          autoComplete="email"
                          required
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md leading-5 bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                          placeholder="Enter your email"
                        />
                      </div>
                    </div>

                    {authMode === 'signin' && (
                      <>
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                            Password
                          </label>
                          <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                              <LockClosedIcon className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                              id="password"
                              name="password"
                              type={showPassword ? 'text' : 'password'}
                              autoComplete="current-password"
                              required
                              value={password}
                              onChange={(e) => setPassword(e.target.value)}
                              className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-md leading-5 bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                              placeholder="Enter your password"
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            >
                              {showPassword ? (
                                <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                              ) : (
                                <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                              )}
                            </button>
                          </div>
                        </motion.div>
                        <div className="flex items-center justify-end">
                          <button
                            type="button"
                            onClick={() => setAuthMode('forgot-password')}
                            className="text-sm text-brand-dark-teal hover:text-brand-dark-teal/80 font-medium"
                          >
                            Forgot password?
                          </button>
                        </div>
                      </>
                    )}

                    {authMode === 'signin' && (
                      <div className="flex items-center">
                        <input
                          id="remember-me"
                          name="remember-me"
                          type="checkbox"
                          checked={rememberMe}
                          onChange={(e) => setRememberMe(e.target.checked)}
                          className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                        />
                        <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                          Stay logged in for 30 days
                        </label>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={isLoading || !email || (authMode === 'signin' && !password)}
                      className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-dark-teal hover:bg-brand-dark-teal/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-dark-teal disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isLoading 
                        ? 'Processing...' 
                        : authMode === 'forgot-password' 
                          ? 'Send Reset Link'
                          : authMode === 'signin' 
                            ? 'Sign In' 
                            : 'Send Magic Link'
                      }
                    </button>

                    {authMode === 'forgot-password' && (
                      <button
                        type="button"
                        onClick={() => setAuthMode('signin')}
                        className="w-full text-sm text-gray-600 hover:text-gray-800 transition-colors"
                      >
                        Back to sign in
                      </button>
                    )}
                  </motion.form>
                )}
              </AnimatePresence>
              
              {!show2FAField && (
                <div className="mt-6 p-4 bg-blue-50 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <EnvelopeIcon className="h-5 w-5 text-blue-400" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-blue-800">
                        {authMode === 'forgot-password' 
                          ? 'Reset Your Password' 
                          : authMode === 'signin' 
                            ? 'Password Authentication' 
                            : 'Magic Link Signup'
                        }
                      </h3>
                      <div className="mt-2 text-sm text-blue-700">
                        <p>
                          {authMode === 'forgot-password'
                            ? "We'll send you a link to reset your password. The link expires in 1 hour."
                            : authMode === 'signin' 
                              ? 'Sign in with your email and password. 2FA will be required if enabled.'
                              : "We'll send you a magic link to create your account. No password required!"
                          }
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Footer */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-8 text-center text-sm text-white/80"
            >
              <p>
                By {authMode === 'signup' ? 'creating an account' : 'signing in'}, you agree to our{' '}
                <Link href="/terms" className="text-white hover:text-white/80 font-medium">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link href="/privacy" className="text-white hover:text-white/80 font-medium">
                  Privacy Policy
                </Link>
              </p>
              <p className="mt-2">
                Educational only. Not financial advice. 16+ only.
              </p>
            </motion.div>
          </div>
        </div>

        {/* Right Side - Visual Design */}
        <div className="hidden lg:flex lg:flex-1 lg:flex-col lg:justify-center lg:items-center lg:px-8 bg-gradient-to-br from-brand-dark-teal via-brand-teal to-gray-900 relative overflow-hidden">
          {/* Animated background elements */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-20 left-20 w-72 h-72 bg-brand-bright-yellow rounded-full mix-blend-multiply filter blur-3xl animate-pulse"></div>
            <div className="absolute bottom-20 right-20 w-72 h-72 bg-brand-teal rounded-full mix-blend-multiply filter blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
          </div>
          
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="relative z-10 text-center max-w-lg"
          >
            {/* Main visual card */}
            <div className="relative mb-12">
              <div className="bg-white/10 backdrop-blur-md rounded-3xl p-12 border border-white/20 shadow-2xl">
                <div className="space-y-6">
                  {/* Icon grid */}
                  <div className="grid grid-cols-2 gap-6 mb-8">
                    <div className="bg-white/10 rounded-2xl p-6 backdrop-blur-sm">
                      <ChartBarIcon className="h-12 w-12 text-brand-bright-yellow mx-auto" />
                      <p className="text-white text-sm mt-2 font-medium">Analytics</p>
                    </div>
                    <div className="bg-white/10 rounded-2xl p-6 backdrop-blur-sm">
                      <ShieldCheckIcon className="h-12 w-12 text-brand-bright-yellow mx-auto" />
                      <p className="text-white text-sm mt-2 font-medium">Secure</p>
                    </div>
                  </div>
                  
                  <h3 className="text-3xl font-bold text-white">
                    Your Trading Journey Starts Here
                  </h3>
                  <p className="text-white/90 text-lg leading-relaxed">
                    Join traders who are improving their performance with AI-powered insights and comprehensive analytics.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Features list */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4 text-left">
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
                  <div className="text-brand-bright-yellow font-bold mb-1">50+</div>
                  <div className="text-white/80 text-sm">Free Trades/Month</div>
                </div>
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
                  <div className="text-brand-bright-yellow font-bold mb-1">AI Coach</div>
                  <div className="text-white/80 text-sm">Personalized Insights</div>
                </div>
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
                  <div className="text-brand-bright-yellow font-bold mb-1">Analytics</div>
                  <div className="text-white/80 text-sm">Real-time Metrics</div>
                </div>
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
                  <div className="text-brand-bright-yellow font-bold mb-1">Backtest</div>
                  <div className="text-white/80 text-sm">Strategy Testing</div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
