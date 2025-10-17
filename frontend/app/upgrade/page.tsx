'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { 
  CheckIcon, 
  XMarkIcon,
  SparklesIcon,
  ArrowRightIcon 
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function UpgradePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const feature = searchParams.get('feature') || 'This feature'
  const fromOnboarding = searchParams.get('from') === 'onboarding'
  const [userPlan, setUserPlan] = useState<string>('free')
  const [isUpgrading, setIsUpgrading] = useState(false)
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')

  useEffect(() => {
    const checkUserPlan = async () => {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      if (!token) {
        router.push('/auth')
        return
      }

      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        
        if (response.ok) {
          const data = await response.json()
          const plan = data.plan || 'free'
          setUserPlan(plan)
          
          // If already Plus user, redirect to dashboard
          if (plan !== 'free') {
            router.push('/dashboard')
          }
        }
      } catch (error) {
        console.error('Failed to fetch user plan:', error)
      }
    }

    checkUserPlan()
  }, [router])

  const handleUpgrade = async () => {
    setIsUpgrading(true)
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    
    try {
      const plan = billingCycle === 'monthly' ? 'plus_monthly' : 'plus_yearly'
      const response = await fetch('/api/v1/billing/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          plan: plan,
          success_url: `${window.location.origin}/dashboard?success=true`,
          cancel_url: `${window.location.origin}/upgrade?feature=${feature}&canceled=true`,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        // Redirect to Stripe Checkout
        window.location.href = data.checkout_url
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to create checkout session')
        setIsUpgrading(false)
      }
    } catch (error) {
      console.error('Upgrade failed:', error)
      toast.error('Failed to start upgrade process')
      setIsUpgrading(false)
    }
  }

  const plusFeatures = [
    "Unlimited trades",
    "Unlimited trade history (forever)",
    "Unlimited custom tags & categories",
    "Advanced trade journal with screenshots & attachments",
    "Unlimited notes (no character limit)",
    "Comprehensive performance metrics & analytics",
    "Unlimited AI trading coach sessions",
    "Advanced backtesting studio",
    "Paper trading simulator",
    "CSV/JSON/Excel import & export",
    "PDF reports with custom templates",
    "Advanced filters & search",
    "Priority email support"
  ]

  const freeFeatures = [
    "Up to 50 trades per month",
    "Last 3 months of trade history",
    "Up to 5 custom tags",
    "Basic trade journal (text notes only, max 500 chars)",
    "Manual trade entry only",
    "5 AI coaching sessions per month",
    "Basic analytics"
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-brand-dark-teal/20 to-gray-900">
      {/* Header */}
      <nav className="bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/dashboard">
              <img
                src="/images/logos/Transparent/TradeQuest%20%5BColored%5D%20%5BRectangle%5D.png"
                alt="TradeQuest"
                className="h-10 w-auto"
              />
            </Link>
            <button
              onClick={() => router.push('/dashboard')}
              className="text-gray-300 hover:text-white"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Welcome Banner - Only show for onboarding */}
        {fromOnboarding ? (
          <div className="bg-gradient-to-r from-brand-dark-teal/20 to-brand-bright-yellow/20 border-2 border-brand-bright-yellow rounded-2xl p-8 mb-12 text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow rounded-full p-4">
                <SparklesIcon className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Welcome to TradeQuest! 🎉
            </h1>
            <p className="text-gray-200 text-xl mb-6">
              You've successfully completed onboarding! Now choose your plan:
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="bg-gray-700 hover:bg-gray-600 text-white px-8 py-3 rounded-xl font-semibold transition-colors"
              >
                Continue on Free Plan
              </button>
              <span className="text-gray-400">or</span>
              <button
                onClick={handleUpgrade}
                disabled={isUpgrading}
                className="bg-brand-bright-yellow hover:bg-brand-bright-yellow/90 text-gray-900 px-8 py-3 rounded-xl font-bold transition-colors disabled:opacity-50"
              >
                Upgrade to Plus
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Upgrade to TradeQuest Plus
            </h1>
            <p className="text-xl text-gray-300 mb-6">
              Unlock {feature} and all premium features
            </p>
          </div>
        )}

        {/* Pricing Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Free Plan */}
          <div className="bg-gray-800/50 border-2 border-gray-700 rounded-2xl p-8">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-400 mb-2">Free Plan</h3>
              <div className="text-4xl font-bold text-gray-500 mb-2">$0</div>
              <p className="text-gray-500">Your Current Plan</p>
            </div>
            <ul className="space-y-3">
              {freeFeatures.map((feature, index) => (
                <li key={index} className="flex items-start">
                  <CheckIcon className="h-5 w-5 text-gray-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-400 text-sm">{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Plus Plan */}
          <div className="bg-gradient-to-br from-brand-teal to-brand-dark-teal border-2 border-brand-bright-yellow rounded-2xl p-8 relative transform scale-105 shadow-2xl">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <div className="bg-brand-bright-yellow text-gray-900 px-6 py-1.5 rounded-full text-sm font-bold">
                RECOMMENDED
              </div>
            </div>
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">Plus Plan</h3>
              
              {/* Billing Toggle */}
              <div className="flex items-center justify-center mb-4">
                <span className={`mr-3 text-sm font-medium ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-400'}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                  className="relative inline-flex h-6 w-12 items-center rounded-full bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-bright-yellow focus:ring-offset-2 focus:ring-offset-gray-900"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-brand-bright-yellow transition-transform ${
                      billingCycle === 'yearly' ? 'translate-x-7' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`ml-3 text-sm font-medium ${billingCycle === 'yearly' ? 'text-white' : 'text-gray-400'}`}>
                  Yearly
                </span>
                {billingCycle === 'yearly' && (
                  <span className="ml-2 bg-brand-bright-yellow/20 text-brand-bright-yellow px-2 py-0.5 rounded-full text-xs font-semibold">
                    Save $58
                  </span>
                )}
              </div>
              
              <div className="text-5xl font-bold text-white mb-2">
                ${billingCycle === 'monthly' ? '29' : '24'}
              </div>
              <p className="text-gray-200">per month</p>
              {billingCycle === 'yearly' && (
                <p className="text-sm text-gray-300 mt-2">Billed annually ($290/year)</p>
              )}
            </div>
            <ul className="space-y-3 mb-8">
              {plusFeatures.map((feature, index) => (
                <li key={index} className="flex items-start">
                  <CheckIcon className="h-5 w-5 text-brand-bright-yellow mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-white text-sm font-medium">{feature}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={handleUpgrade}
              disabled={isUpgrading}
              className="w-full bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 text-center text-lg font-bold px-8 py-4 rounded-xl shadow-2xl transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUpgrading ? 'Redirecting to Checkout...' : 'Upgrade to Plus'}
              {!isUpgrading && <ArrowRightIcon className="inline-block ml-2 h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center">
          <p className="text-gray-400 mb-4">
            Not ready to upgrade?{' '}
            <button
              onClick={() => router.push('/dashboard')}
              className="text-brand-bright-yellow hover:text-brand-bright-yellow/80 underline"
            >
              Return to Dashboard
            </button>
          </p>
          <p className="text-sm text-gray-500">
            Questions? <Link href="/contact" className="text-brand-teal hover:text-brand-light-teal underline">Contact us</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
