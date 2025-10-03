"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  UserIcon,
  CogIcon,
  BellIcon,
  CreditCardIcon,
  DocumentTextIcon,
  PlayIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import TOSModal from '../../components/TOSModal';
import PrivacyModal from '../../components/PrivacyModal';

interface OnboardingData {
        // Step 1: Legal
        age_confirm: boolean;
        accept_tos: boolean;
        accept_privacy: boolean;
        ai_data_consent: boolean;
        region: string;
  
  // Step 2: Account Basics
  first_name?: string;
  last_name?: string;
  birth_date?: string; // YYYY-MM-DD
  alias: string;
  timezone: string;
  display_currency: string;
  pnl_visibility_default: boolean;
  
  // Step 3: Security
  set_password: string;
  confirm_password: string;
  two_factor_method: string;
  phone_number: string;
  
  // Step 4: Trading Profile
  experience_level: string;
  markets: string[];
  style: string[];
  timeframes: string[];
  platforms: string[];
  days_active_per_week: number;
  session_pref: string[];
  
  // Step 5: Goals & Risk
  primary_goal: string;
  account_size_band: string;
  risk_per_trade_pct: number;
  max_monthly_drawdown_target_pct: number;
  target_winrate_hint: number;
}

const onboardingSteps = [
  {
    id: 1,
    title: "Legal & Age Verification",
    subtitle: "Let's start with the basics",
    icon: ShieldCheckIcon,
    color: "from-red-500 to-pink-500"
  },
  {
    id: 2,
    title: "Account Basics",
    subtitle: "Personalize your experience",
    icon: UserIcon,
    color: "from-blue-500 to-cyan-500"
  },
  {
    id: 3,
    title: "Security Setup",
    subtitle: "Protect your account",
    icon: ShieldCheckIcon,
    color: "from-green-500 to-emerald-500"
  },
  {
    id: 4,
    title: "Trading Profile",
    subtitle: "Tell us about your experience",
    icon: ChartBarIcon,
    color: "from-purple-500 to-violet-500"
  },
  {
    id: 5,
    title: "Goals & Risk",
    subtitle: "Define your objectives",
    icon: ChartBarIcon,
    color: "from-orange-500 to-red-500"
  }
];

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
        const [data, setData] = useState<OnboardingData>({
          // Initialize with defaults
          age_confirm: false,
          accept_tos: false,
          accept_privacy: false,
          ai_data_consent: false,
          region: '',
    alias: '',
    timezone: 'UTC',
    display_currency: 'USD',
    pnl_visibility_default: true,
    set_password: '',
    confirm_password: '',
    two_factor_method: 'email',
    phone_number: '',
    experience_level: '',
    markets: ['crypto'],
    style: [],
    timeframes: [],
    platforms: [],
    days_active_per_week: 3,
    session_pref: [],
    primary_goal: '',
    account_size_band: '',
    risk_per_trade_pct: 1.0,
    max_monthly_drawdown_target_pct: 10.0,
    target_winrate_hint: 50
  });
        const [isLoading, setIsLoading] = useState(false);
  const [showTOSModal, setShowTOSModal] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  
  // Verification states
  const [passwordVerified, setPasswordVerified] = useState(false);
  const [twoFactorVerified, setTwoFactorVerified] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [totpSecret, setTotpSecret] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verificationSent, setVerificationSent] = useState(false);
  const [emailResendCooldown, setEmailResendCooldown] = useState(0);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth');
      return;
    }
  }, [router]);

  // Verification functions
  const setupPasswordVerification = async () => {
    if (!data.set_password || data.set_password.length < 10) {
      toast.error('Password must be at least 10 characters');
      return;
    }
    if (data.set_password !== data.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    
    // Password verification passed
    setPasswordVerified(true);
    toast.success('Password verified ✓');
    
    // Auto-setup 2FA if method is selected
    if (data.two_factor_method && !twoFactorVerified) {
      await setupTwoFactorVerification();
    }
  };

  const setupTwoFactorVerification = async () => {
    if (!data.two_factor_method) {
      toast.error('Please select a 2FA method');
      return;
    }

    try {
      if (data.two_factor_method === 'totp') {
        // Setup TOTP
        const response = await fetch('/api/v1/2fa/setup/totp', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const result = await response.json();
          setTotpSecret(result.secret);
          setQrCode(result.qr_code);
          setBackupCodes(result.backup_codes);
          setVerificationSent(true);
          toast.success('TOTP setup initiated - scan QR code and enter verification code');
        } else {
          toast.error('Failed to setup TOTP');
        }
      } else if (data.two_factor_method === 'sms') {
        if (!data.phone_number) {
          toast.error('Phone number is required for SMS 2FA');
          return;
        }
        
        // Setup SMS
        const response = await fetch('/api/v1/2fa/setup/sms', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ phone_number: data.phone_number })
        });
        
        if (response.ok) {
          setVerificationSent(true);
          toast.success('SMS verification code sent to your phone');
        } else {
          toast.error('Failed to send SMS verification');
        }
      } else if (data.two_factor_method === 'email') {
        const response = await fetch('/api/v1/2fa/setup/email', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')}`,
          },
        });
        if (response.ok) {
          setVerificationSent(true);
          toast.success('Verification code sent to your email');
          setEmailResendCooldown(60);
        } else {
          const err = await response.json();
          toast.error(err.detail || 'Failed to send email verification');
        }
      }
    } catch (error) {
      console.error('2FA setup error:', error);
      toast.error('Failed to setup 2FA verification');
    }
  };

  const verifyTwoFactorCode = async () => {
    if (!verificationCode) {
      toast.error('Please enter verification code');
      return;
    }

    try {
      let response;
      
      if (data.two_factor_method === 'totp') {
        response = await fetch('/api/v1/2fa/verify/totp', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            secret: totpSecret,
            code: verificationCode,
            backup_codes: backupCodes
          })
        });
      } else if (data.two_factor_method === 'sms') {
        response = await fetch('/api/v1/2fa/verify/sms', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ code: verificationCode })
        });
      } else if (data.two_factor_method === 'email') {
        response = await fetch('/api/v1/2fa/verify/email', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ code: verificationCode })
        });
      }

      if (response && response.ok) {
        setTwoFactorVerified(true);
        toast.success('2FA verification completed ✓');
      } else if (response) {
        toast.error('Invalid verification code');
      }
    } catch (error) {
      console.error('2FA verification error:', error);
      toast.error('Failed to verify 2FA code');
    }
  };

  // Cooldown timer for email resend
  useEffect(() => {
    if (emailResendCooldown <= 0) return;
    const t = setInterval(() => setEmailResendCooldown((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, [emailResendCooldown]);

  const handleNext = async () => {
    setIsLoading(true);
    
    try {
      // Use the same token strategy as the dashboard/auth pages
      let token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session');
      if (!token) {
        toast.error('No authentication token found');
        return;
      }

      // Call backend API for current step
      let endpoint = '';
      let payload = {};

      switch (currentStep) {
        case 1: // Legal & Age Verification
          endpoint = '/api/v1/onboarding/step/1';
          payload = {
            age_confirm: data.age_confirm,
            accept_tos: data.accept_tos,
            accept_privacy: data.accept_privacy,
            region: data.region || 'US'
          };
          break;
        case 2: // Account Basics
          endpoint = '/api/v1/onboarding/step/2';
          payload = {
            first_name: data.first_name,
            last_name: data.last_name,
            birth_date: data.birth_date,
            alias: data.alias || 'trader',
            timezone: data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
            display_currency: data.display_currency || 'USD',
            pnl_visibility_default: data.pnl_visibility_default || 'hide'
          };
          break;
        case 3: // Security Setup
          endpoint = '/api/v1/onboarding/step/3';
          payload = {
            set_password: data.set_password,
            confirm_password: data.confirm_password,
            two_factor_method: data.two_factor_method,
            phone_number: data.phone_number
          };
          break;
        case 4: // Trading Profile
          endpoint = '/api/v1/onboarding/step/4';
          payload = {
            experience_level: data.experience_level || 'beginner',
            markets: data.markets || ['crypto'],
            style: data.style || ['swing'],
            timeframes: data.timeframes || ['1h', '4h', '1d'],
            platforms: data.platforms || ['binance'],
            days_active_per_week: data.days_active_per_week || 3,
            session_pref: data.session_pref || ['new_york']
          };
          break;
        case 5: // Goals & Risk
          endpoint = '/api/v1/onboarding/step/5';
          payload = {
            primary_goal: data.primary_goal || 'profitability',
            account_size_band: data.account_size_band || '$2k-$10k',
            risk_per_trade_pct: data.risk_per_trade_pct || 1.0,
            max_monthly_drawdown_target_pct: data.max_monthly_drawdown_target_pct || 10,
            target_winrate_hint: data.target_winrate_hint || 50
          };
          break;
        case 6: // Discipline Rules
          endpoint = '/api/v1/onboarding/step/6';
          payload = {
            daily_stop_type: 'percentage',
            daily_stop_value: 5,
            max_trades_per_day: 5,
            cooldown_minutes: 30,
            apply_rules_now: true
          };
          break;
        case 14: // Complete onboarding
          endpoint = '/api/v1/onboarding/complete';
          payload = {};
          break;
        default:
          // For other steps, just simulate
          await new Promise(resolve => setTimeout(resolve, 500));
          break;
      }

      if (endpoint) {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to save onboarding data');
        }
      }
      
      setCompletedSteps(prev => [...prev, currentStep]);
      
      if (currentStep < onboardingSteps.length) {
        setCurrentStep(currentStep + 1);
      } else {
        // Complete onboarding
        toast.success('Onboarding completed! Welcome to TradeQuest!');
        router.push('/dashboard');
      }
      
    } catch (error) {
      console.error('Onboarding step failed:', error);
      toast.error(`Failed to save step ${currentStep}: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    router.push('/dashboard');
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Legal Requirements
              </h3>
              <p className="text-gray-600">
                Please confirm your age and accept our terms
              </p>
            </div>
            
                  <div className="space-y-4">
                    <label className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="checkbox"
                        checked={data.age_confirm}
                        onChange={(e) => setData({...data, age_confirm: e.target.checked})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                      />
                      <span className="text-sm font-medium text-gray-900">
                        I am 16 years or older
                      </span>
                    </label>

                    <label className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="checkbox"
                        checked={data.accept_tos}
                        onChange={(e) => setData({...data, accept_tos: e.target.checked})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                      />
                      <span className="text-sm font-medium text-gray-900">
                        I agree to the{' '}
                        <button
                          type="button"
                          onClick={() => setShowTOSModal(true)}
                          className="text-brand-dark-teal hover:text-brand-dark-teal/80 underline font-medium"
                        >
                          Terms of Service
                        </button>
                      </span>
                    </label>

                    <label className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="checkbox"
                        checked={data.accept_privacy}
                        onChange={(e) => setData({...data, accept_privacy: e.target.checked})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                      />
                      <span className="text-sm font-medium text-gray-900">
                        I agree to the{' '}
                        <button
                          type="button"
                          onClick={() => setShowPrivacyModal(true)}
                          className="text-brand-dark-teal hover:text-brand-dark-teal/80 underline font-medium"
                        >
                          Privacy Policy
                        </button>
                      </span>
                    </label>

                    <label className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="checkbox"
                        checked={data.ai_data_consent}
                        onChange={(e) => setData({...data, ai_data_consent: e.target.checked})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                      />
                      <span className="text-sm font-medium text-gray-900">
                        I consent to TradeQuest using my anonymized data to improve our AI models and product features (optional)
                      </span>
                    </label>
                    
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-700">
                        <strong>Note:</strong> The AI data consent is completely optional. If you choose not to provide consent, 
                        we will still provide all our services to you. This only affects whether we can use your anonymized 
                        trading patterns to improve our AI coaching and analytics features.
                      </p>
                    </div>
                  </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Account Setup
              </h3>
              <p className="text-gray-600">
                Customize your trading experience
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">First name</label>
                  <input
                    type="text"
                    value={data.first_name || ''}
                    onChange={(e) => setData({...data, first_name: e.target.value})}
                    placeholder="First"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Last name</label>
                  <input
                    type="text"
                    value={data.last_name || ''}
                    onChange={(e) => setData({...data, last_name: e.target.value})}
                    placeholder="Last"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Birthday</label>
                  <input
                    type="date"
                    value={data.birth_date || ''}
                    onChange={(e) => setData({...data, birth_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Display Name
                </label>
                <input
                  type="text"
                  value={data.alias}
                  onChange={(e) => setData({...data, alias: e.target.value})}
                  placeholder="Enter your display name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Display Currency
                </label>
                <select
                  value={data.display_currency}
                  onChange={(e) => setData({...data, display_currency: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="USDT">USDT</option>
                </select>
              </div>
              
              <label className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <input
                  type="checkbox"
                  checked={data.pnl_visibility_default}
                  onChange={(e) => setData({...data, pnl_visibility_default: e.target.checked})}
                  className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                />
                <span className="text-sm font-medium text-gray-900">
                  Show PnL by default (recommended for learning)
                </span>
              </label>
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Security Setup
              </h3>
              <p className="text-gray-600">
                Password and 2FA are required for account security
              </p>
            </div>
            
            {/* Security Requirements Notice */}
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-amber-800">Security Requirements</h4>
                  <p className="text-sm text-amber-700 mt-1">
                    Both a password and 2FA method are required to secure your account and protect your trading data.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  value={data.set_password}
                  onChange={(e) => setData({...data, set_password: e.target.value})}
                  placeholder="Enter a strong password (min 10 characters)"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum 10 characters. Required for account security.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  value={data.confirm_password}
                  onChange={(e) => setData({...data, confirm_password: e.target.value})}
                  placeholder="Confirm your password"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Two-Factor Authentication <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-gray-500 mb-3">
                  Choose one 2FA method to secure your account (required)
                </p>
                <div className="grid grid-cols-1 gap-3">
                  {[
                    { value: 'email', label: 'Email Verification', icon: '📧', description: 'Receive codes via email' },
                    { value: 'sms', label: 'SMS Code', icon: '📱', description: 'Receive codes via text message' },
                    { value: 'totp', label: 'Authenticator App', icon: '🔑', description: 'Google Authenticator, Authy, etc.' }
                  ].map((method) => (
                    <label key={method.value} className={`flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors ${
                      data.two_factor_method === method.value 
                        ? 'border-brand-dark-teal bg-brand-dark-teal/5' 
                        : 'border-gray-200'
                    }`}>
                      <input
                        type="radio"
                        name="two_factor_method"
                        value={method.value}
                        checked={data.two_factor_method === method.value}
                        onChange={(e) => setData({...data, two_factor_method: e.target.value})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300"
                      />
                      <span className="text-2xl">{method.icon}</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">{method.label}</div>
                        <div className="text-xs text-gray-500">{method.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              
              {data.two_factor_method === 'sms' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    value={data.phone_number}
                    onChange={(e) => setData({...data, phone_number: e.target.value})}
                    placeholder="+1 (555) 123-4567"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Include country code (e.g., +1 for US, +44 for UK)
                  </p>
                </div>
              )}
              
              {/* Password Verification */}
              {data.set_password && data.confirm_password && !passwordVerified && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-blue-800">Verify Password</h4>
                      <p className="text-sm text-blue-700 mt-1">Click to verify your password</p>
                    </div>
                    <button
                      onClick={setupPasswordVerification}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Verify Password
                    </button>
                  </div>
                </div>
              )}

              {passwordVerified && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-green-700">Password verified ✓</span>
                  </div>
                </div>
              )}

              {/* 2FA Setup */}
              {passwordVerified && data.two_factor_method && !verificationSent && !twoFactorVerified && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-blue-800">Setup 2FA Verification</h4>
                      <p className="text-sm text-blue-700 mt-1">Click to setup your {data.two_factor_method} verification</p>
                    </div>
                    <button
                      onClick={setupTwoFactorVerification}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Setup 2FA
                    </button>
                  </div>
                </div>
              )}

              {/* TOTP QR Code */}
              {data.two_factor_method === 'totp' && qrCode && !twoFactorVerified && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-800 mb-3">Scan QR Code</h4>
                  <div className="text-center">
                    <img src={qrCode} alt="TOTP QR Code" className="mx-auto mb-3 w-48 h-48" />
                    <p className="text-xs text-gray-600 mb-3">
                      Scan with your authenticator app (Google Authenticator, Authy, etc.)
                    </p>
                    <p className="text-xs text-gray-500 mb-3">
                      After scanning, enter the 6-digit code from your app
                    </p>
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                        placeholder="Enter 6-digit code"
                        maxLength={6}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal text-center text-lg tracking-widest"
                      />
                      <button
                        onClick={verifyTwoFactorCode}
                        disabled={verificationCode.length !== 6}
                        className="px-4 py-2 bg-brand-dark-teal text-white rounded-md hover:bg-brand-dark-teal/80 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        Verify
                      </button>
                    </div>
                    {backupCodes.length > 0 && (
                      <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-xs text-yellow-700 font-medium">Backup Codes (save these!):</p>
                          <button
                            onClick={() => {
                              const codesText = backupCodes.join('\n');
                              const blob = new Blob([`TradeQuest Backup Codes\n\n${codesText}\n\nSave these codes in a secure location. Each code can only be used once.`], { type: 'text/plain' });
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = 'tradequest-backup-codes.txt';
                              document.body.appendChild(a);
                              a.click();
                              document.body.removeChild(a);
                              URL.revokeObjectURL(url);
                            }}
                            className="px-2 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
                          >
                            Download
                          </button>
                        </div>
                        <p className="text-xs text-yellow-600 font-mono">{backupCodes.slice(0, 3).join(' ')}</p>
                        <p className="text-xs text-yellow-500 mt-1">
                          {backupCodes.length > 3 && `... and ${backupCodes.length - 3} more codes`}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* SMS Verification */}
              {data.two_factor_method === 'sms' && verificationSent && !twoFactorVerified && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-800 mb-3">SMS Verification</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    We sent a verification code to {data.phone_number}
                  </p>
                  <p className="text-xs text-gray-500 mb-3">
                    Check your phone for a 6-digit code from TradeQuest
                  </p>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="Enter 6-digit code"
                      maxLength={6}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal"
                    />
                    <button
                      onClick={verifyTwoFactorCode}
                      disabled={verificationCode.length !== 6}
                      className="px-4 py-2 bg-brand-dark-teal text-white rounded-md hover:bg-brand-dark-teal/80 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      Verify
                    </button>
                  </div>
                  <button
                    onClick={() => {
                      setVerificationSent(false);
                      setupTwoFactorVerification();
                    }}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
                  >
                    Resend code
                  </button>
                </div>
              )}

              {/* Email Verification */}
              {data.two_factor_method === 'email' && verificationSent && !twoFactorVerified && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-800 mb-3">Email Verification</h4>
                  <p className="text-sm text-gray-600 mb-3">We sent a 6-digit code to your email.</p>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="Enter 6-digit code"
                      maxLength={6}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal text-center text-lg tracking-widest"
                    />
                    <button
                      onClick={verifyTwoFactorCode}
                      disabled={verificationCode.length !== 6}
                      className="px-4 py-2 bg-brand-dark-teal text-white rounded-md hover:bg-brand-dark-teal/80 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      Verify
                    </button>
                  </div>
                  <button
                    onClick={async () => {
                      const res = await fetch('/api/v1/2fa/setup/email', {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')}` },
                      });
                      if (res.ok) {
                        toast.success('Code resent');
                        setEmailResendCooldown(60);
                      } else {
                        toast.error('Failed to resend');
                      }
                    }}
                    disabled={emailResendCooldown > 0}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline disabled:text-gray-400"
                  >
                    {emailResendCooldown > 0 ? `Resend in ${emailResendCooldown}s` : 'Resend code'}
                  </button>
                </div>
              )}


              {/* 2FA Verified */}
              {twoFactorVerified && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-green-700">2FA verified ✓</span>
                  </div>
                </div>
              )}

              {/* Final Status */}
              {passwordVerified && twoFactorVerified && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-green-700">All security requirements completed ✓</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Trading Experience
              </h3>
              <p className="text-gray-600">
                Help us understand your trading background
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Experience Level
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {[
                    { value: 'beginner', label: 'Beginner', desc: 'New to trading' },
                    { value: 'intermediate', label: 'Intermediate', desc: 'Some trading experience' },
                    { value: 'advanced', label: 'Advanced', desc: 'Experienced trader' }
                  ].map((level) => (
                    <label key={level.value} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="radio"
                        name="experience_level"
                        value={level.value}
                        checked={data.experience_level === level.value}
                        onChange={(e) => setData({...data, experience_level: e.target.value})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300"
                      />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{level.label}</div>
                        <div className="text-xs text-gray-500">{level.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Trading Markets
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'crypto', label: 'Crypto', icon: '₿' },
                    { value: 'stocks', label: 'Stocks', icon: '📈' },
                    { value: 'forex', label: 'Forex', icon: '💱' },
                    { value: 'commodities', label: 'Commodities', icon: '🥇' }
                  ].map((market) => (
                    <label key={market.value} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="checkbox"
                        checked={data.markets.includes(market.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setData({...data, markets: [...data.markets, market.value]});
                          } else {
                            setData({...data, markets: data.markets.filter(m => m !== market.value)});
                          }
                        }}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300 rounded"
                      />
                      <span className="text-lg">{market.icon}</span>
                      <span className="text-sm font-medium text-gray-900">{market.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        );

      case 5:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Trading Goals
              </h3>
              <p className="text-gray-600">
                What do you want to achieve with trading?
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Goal
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {[
                    { value: 'profitability', label: 'Profitability', desc: 'Make consistent profits' },
                    { value: 'discipline', label: 'Discipline & Consistency', desc: 'Build good trading habits' },
                    { value: 'learning', label: 'Learn Strategy Development', desc: 'Master trading strategies' }
                  ].map((goal) => (
                    <label key={goal.value} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                      <input
                        type="radio"
                        name="primary_goal"
                        value={goal.value}
                        checked={data.primary_goal === goal.value}
                        onChange={(e) => setData({...data, primary_goal: e.target.value})}
                        className="h-4 w-4 text-brand-dark-teal focus:ring-brand-dark-teal border-gray-300"
                      />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{goal.label}</div>
                        <div className="text-xs text-gray-500">{goal.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Account Size
                </label>
                <select
                  value={data.account_size_band}
                  onChange={(e) => setData({...data, account_size_band: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-brand-dark-teal"
                >
                  <option value="">Select account size</option>
                  <option value="<500">Less than $500</option>
                  <option value="500-2k">$500 - $2,000</option>
                  <option value="2k-10k">$2,000 - $10,000</option>
                  <option value="10k-50k">$10,000 - $50,000</option>
                  <option value="50k+">$50,000+</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Risk per Trade: {data.risk_per_trade_pct}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="5"
                  step="0.1"
                  value={data.risk_per_trade_pct}
                  onChange={(e) => setData({...data, risk_per_trade_pct: parseFloat(e.target.value)})}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.1%</span>
                  <span>5%</span>
                </div>
              </div>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return data.age_confirm && data.accept_tos && data.accept_privacy;
      case 2:
        return (data.alias.trim() !== '' && (data.first_name || '').trim() !== '' && (data.last_name || '').trim() !== '' && (data.birth_date || '').trim() !== '');
      case 3:
        return passwordVerified && twoFactorVerified;
      case 4:
        return data.experience_level !== '';
      case 5:
        return data.primary_goal !== '' && data.account_size_band !== '';
      default:
        return false;
    }
  };

  const currentStepData = onboardingSteps[currentStep - 1];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">TQ</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">TradeQuest</h1>
            </div>
            
            <button
              onClick={handleSkip}
              className="flex items-center space-x-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
              <span className="text-sm">Skip</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Progress Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-lg p-6 sticky top-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Setup Progress
              </h2>
              
              <div className="space-y-4">
                {onboardingSteps.map((step, index) => (
                  <div key={step.id} className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                      completedSteps.includes(step.id)
                        ? 'bg-green-500 text-white'
                        : step.id === currentStep
                        ? `bg-gradient-to-r ${step.color} text-white`
                        : 'bg-gray-200 text-gray-500'
                    }`}>
                      {completedSteps.includes(step.id) ? (
                        <CheckIcon className="h-5 w-5" />
                      ) : (
                        <span className="text-sm font-medium">{step.id}</span>
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className={`text-sm font-medium transition-colors ${
                        step.id === currentStep ? 'text-gray-900' : 'text-gray-600'
                      }`}>
                        {step.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {step.subtitle}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Progress Bar */}
              <div className="mt-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Progress</span>
                  <span>{Math.round(((currentStep - 1) / onboardingSteps.length) * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${((currentStep - 1) / onboardingSteps.length) * 100}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              {/* Step Header */}
              <div className={`bg-gradient-to-r ${currentStepData.color} p-8 text-white`}>
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                    <currentStepData.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">{currentStepData.title}</h2>
                    <p className="text-white/80">{currentStepData.subtitle}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 text-white/60">
                  <span className="text-sm">Step {currentStep} of {onboardingSteps.length}</span>
                </div>
              </div>

              {/* Step Content */}
              <div className="p-8">
                <AnimatePresence mode="wait">
                  {renderStepContent()}
                </AnimatePresence>

                {/* Navigation */}
                <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
                  <button
                    onClick={handlePrevious}
                    disabled={currentStep === 1}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                      currentStep === 1
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <ArrowLeftIcon className="h-4 w-4" />
                    <span>Previous</span>
                  </button>

                  <button
                    onClick={handleNext}
                    disabled={!canProceed() || isLoading}
                    className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                      canProceed() && !isLoading
                        ? 'bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow text-white hover:shadow-lg transform hover:scale-105'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Processing...</span>
                      </>
                    ) : currentStep === onboardingSteps.length ? (
                      <>
                        <CheckIcon className="h-4 w-4" />
                        <span>Complete Setup</span>
                      </>
                    ) : (
                      <>
                        <span>Next</span>
                        <ArrowRightIcon className="h-4 w-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <TOSModal 
        isOpen={showTOSModal} 
        onClose={() => setShowTOSModal(false)} 
      />
      <PrivacyModal 
        isOpen={showPrivacyModal} 
        onClose={() => setShowPrivacyModal(false)} 
      />
    </div>
  );
}