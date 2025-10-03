"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  CheckIcon,
  StarIcon,
  ArrowRightIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

export default function PublicPricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const plans = [
    {
      name: "Free",
      price: { monthly: 0, yearly: 0 },
      description: "Perfect for getting started with trading analysis",
      features: [
        "Up to 50 trades per month",
        "Basic trade journal with notes and tags",
        "Core performance metrics (Win rate, P&L, Profit factor)",
        "Paper trading simulator",
        "CSV import/export",
        "Basic charts and visualizations",
        "Email support"
      ],
      limitations: [
        "Limited to 50 trades per month",
        "5 AI coaching sessions per month",
        "Basic analytics only"
      ],
      cta: "Get Started Free",
      ctaLink: "/auth",
      popular: false
    },
    {
      name: "Plus",
      price: { monthly: 29, yearly: 290 },
      description: "For serious traders who want unlimited analysis",
      features: [
        "Unlimited trades",
        "Advanced trade journal with screenshots",
        "Comprehensive performance metrics & analytics",
        "Unlimited AI trading coach sessions",
        "Advanced backtesting studio",
        "Custom strategy builder",
        "Advanced charts with technical indicators",
        "Risk management & discipline alerts",
        "PDF reports and analytics export",
        "Priority support",
        "Custom tags and categories",
        "Trade session analysis with heatmaps"
      ],
      limitations: [],
      cta: "Start Plus Trial",
      ctaLink: "/auth?plan=plus",
      popular: true
    }
  ];

  const faqs = [
    {
      question: "Can I change plans anytime?",
      answer: "Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and we'll prorate any differences."
    },
    {
      question: "What happens to my data if I cancel?",
      answer: "Your data remains accessible for 30 days after cancellation. You can export all your data in various formats before the account is deactivated."
    },
    {
      question: "Do you offer refunds?",
      answer: "We offer a 30-day money-back guarantee for all paid plans. If you're not satisfied, contact us for a full refund."
    },
    {
      question: "Can I use TradeQuest for paper trading?",
      answer: "Absolutely! TradeQuest is perfect for paper trading and backtesting. Many users start with paper trading to learn the platform before going live."
    },
    {
      question: "Is my trading data secure?",
      answer: "Yes, we use bank-level encryption and security measures. Your data is encrypted at rest and in transit, and we follow industry best practices for security."
    },
    {
      question: "Do you support international traders?",
      answer: "Yes, TradeQuest is available worldwide. We support multiple currencies and time zones."
    }
  ];

  const savings = {
    monthly: 0,
    yearly: 2 // 2 months free with yearly billing
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navigation */}
      <nav className="bg-gray-900/95 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Link href="/" className="text-2xl font-bold text-white">TradeQuest</Link>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link href="/features" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Features
                </Link>
                <Link href="/pricing" className="text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium">
                  Pricing
                </Link>
                <Link href="/docs" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Docs
                </Link>
                <Link href="/contact" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Contact
                </Link>
                <Link href="/auth" className="bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 px-6 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg hover:shadow-xl">
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-24 bg-gradient-to-br from-gray-900 via-brand-dark-teal/20 to-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-6xl font-bold text-white mb-6"
          >
            Simple, Transparent Pricing
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto"
          >
            Choose the plan that fits your trading needs. Start free, upgrade when you're ready.
          </motion.p>
          
          {/* Billing Toggle */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex items-center justify-center mb-8"
          >
            <span className={`mr-3 font-medium ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
              className="relative inline-flex h-7 w-14 items-center rounded-full bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-teal focus:ring-offset-2 focus:ring-offset-gray-900"
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-brand-bright-yellow transition-transform ${
                  billingCycle === 'yearly' ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`ml-3 font-medium ${billingCycle === 'yearly' ? 'text-white' : 'text-gray-500'}`}>
              Yearly
            </span>
            {billingCycle === 'yearly' && (
              <span className="ml-3 bg-brand-bright-yellow/20 text-brand-bright-yellow px-3 py-1 rounded-full text-sm font-semibold">
                Save 2 months
              </span>
            )}
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`relative bg-gray-800/50 backdrop-blur-sm border-2 rounded-2xl p-8 hover:scale-105 transition-all duration-300 ${
                  plan.popular ? 'border-brand-bright-yellow shadow-2xl shadow-brand-bright-yellow/20' : 'border-gray-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-brand-bright-yellow to-brand-teal text-gray-900 px-6 py-1.5 rounded-full text-sm font-bold flex items-center shadow-lg">
                      <StarIcon className="h-4 w-4 mr-1" />
                      Most Popular
                    </div>
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-3xl font-bold text-white mb-3">{plan.name}</h3>
                  <p className="text-gray-400 mb-6">{plan.description}</p>
                  <div className="mb-4">
                    <span className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-brand-teal to-brand-bright-yellow">
                      ${billingCycle === 'monthly' ? plan.price.monthly : Math.floor(plan.price.yearly / 12)}
                    </span>
                    <span className="text-gray-400 ml-2 text-lg">
                      /{billingCycle === 'monthly' ? 'month' : 'month'}
                    </span>
                  </div>
                  {billingCycle === 'yearly' && plan.price.yearly > 0 && (
                    <div className="text-sm text-gray-500">
                      Billed annually (${plan.price.yearly}/year)
                    </div>
                  )}
                </div>

                <ul className="space-y-4 mb-10">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <CheckIcon className="h-6 w-6 text-brand-bright-yellow mr-3 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                {plan.limitations.length > 0 && (
                  <div className="mb-8 pt-6 border-t border-gray-700">
                    <h4 className="text-sm font-semibold text-gray-400 mb-3">Limitations:</h4>
                    <ul className="space-y-2">
                      {plan.limitations.map((limitation, limitationIndex) => (
                        <li key={limitationIndex} className="flex items-start text-sm text-gray-500">
                          <XMarkIcon className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5 text-gray-600" />
                          {limitation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Link
                  href={plan.ctaLink}
                  className={`w-full block text-center py-4 px-6 rounded-xl font-bold transition-all duration-200 shadow-lg ${
                    plan.popular
                      ? 'bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 hover:shadow-xl hover:shadow-brand-bright-yellow/50'
                      : 'bg-gray-700 text-white hover:bg-gray-600 border border-gray-600 hover:border-brand-teal'
                  }`}
                >
                  {plan.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-gray-800/30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-400">
              Everything you need to know about TradeQuest pricing and plans.
            </p>
          </div>
          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-8 hover:border-brand-teal transition-all duration-300"
              >
                <h3 className="text-xl font-bold text-white mb-3">
                  {faq.question}
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  {faq.answer}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-brand-teal via-brand-dark-teal to-gray-900">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Start Your Trading Journey?
          </h2>
          <p className="text-xl text-gray-200 mb-10">
            Start improving your trading performance with TradeQuest today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth" className="bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 text-lg font-bold px-10 py-4 rounded-xl shadow-2xl transition-all duration-200 hover:scale-105 inline-flex items-center justify-center">
              Start Free Trial
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
            <Link href="/features" className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 text-white hover:bg-gray-900 hover:border-brand-bright-yellow text-lg font-semibold px-10 py-4 rounded-xl transition-all duration-200">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold text-gradient mb-4">TradeQuest</h3>
              <p className="text-gray-400">
                The trading platform that focuses on education, discipline, and continuous improvement.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/features" className="hover:text-white">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-white">Pricing</Link></li>
                <li><Link href="/docs" className="hover:text-white">Documentation</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                <li><Link href="/careers" className="hover:text-white">Careers</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/disclaimer" className="hover:text-white">Risk Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 TradeQuest. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
