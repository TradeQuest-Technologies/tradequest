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
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Link href="/" className="text-2xl font-bold text-gradient">TradeQuest</Link>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link href="/features" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Features
                </Link>
                <Link href="/pricing" className="text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Pricing
                </Link>
                <Link href="/docs" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Docs
                </Link>
                <Link href="/auth" className="bg-brand-bright-yellow text-brand-dark-teal hover:bg-brand-bright-yellow/90 px-4 py-2 rounded-md text-sm font-medium">
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow">
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
            className="text-xl md:text-2xl text-white/90 mb-8 max-w-3xl mx-auto"
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
            <span className={`mr-3 ${billingCycle === 'monthly' ? 'text-white' : 'text-white/70'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
              className="relative inline-flex h-6 w-11 items-center rounded-full bg-white/20 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  billingCycle === 'yearly' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`ml-3 ${billingCycle === 'yearly' ? 'text-white' : 'text-white/70'}`}>
              Yearly
            </span>
            {billingCycle === 'yearly' && (
              <span className="ml-2 bg-white/20 text-white px-2 py-1 rounded-full text-sm">
                Save 2 months
              </span>
            )}
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-20 -mt-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`relative bg-white rounded-2xl shadow-lg p-8 ${
                  plan.popular ? 'ring-2 ring-brand-bright-yellow' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-brand-bright-yellow text-brand-dark-teal px-4 py-1 rounded-full text-sm font-medium flex items-center">
                      <StarIcon className="h-4 w-4 mr-1" />
                      Most Popular
                    </div>
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <p className="text-gray-600 mb-4">{plan.description}</p>
                  <div className="mb-4">
                    <span className="text-4xl font-bold text-gray-900">
                      ${billingCycle === 'monthly' ? plan.price.monthly : Math.floor(plan.price.yearly / 12)}
                    </span>
                    <span className="text-gray-600 ml-1">
                      /{billingCycle === 'monthly' ? 'month' : 'month'}
                    </span>
                  </div>
                  {billingCycle === 'yearly' && plan.price.yearly > 0 && (
                    <div className="text-sm text-gray-500">
                      Billed annually (${plan.price.yearly}/year)
                    </div>
                  )}
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-brand-bright-yellow mr-3 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                {plan.limitations.length > 0 && (
                  <div className="mb-8">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Limitations:</h4>
                    <ul className="space-y-1">
                      {plan.limitations.map((limitation, limitationIndex) => (
                        <li key={limitationIndex} className="flex items-start text-sm text-gray-500">
                          <XMarkIcon className="h-4 w-4 mr-2 flex-shrink-0 mt-0.5" />
                          {limitation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Link
                  href={plan.ctaLink}
                  className={`w-full block text-center py-3 px-4 rounded-lg font-semibold transition-colors duration-200 ${
                    plan.popular
                      ? 'bg-brand-bright-yellow text-brand-dark-teal hover:bg-brand-bright-yellow/90'
                      : 'bg-brand-dark-teal text-white hover:bg-brand-dark-teal/90'
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
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600">
              Everything you need to know about TradeQuest pricing and plans.
            </p>
          </div>
          <div className="space-y-8">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-lg p-6 shadow-lg"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {faq.question}
                </h3>
                <p className="text-gray-600">
                  {faq.answer}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Start Your Trading Journey?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join thousands of traders who are improving their performance with TradeQuest.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth" className="bg-white text-brand-dark-teal hover:bg-gray-50 text-lg font-semibold px-8 py-3 rounded-lg shadow-lg transition-colors duration-200 inline-flex items-center justify-center">
              Start Free Trial
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
            <Link href="/features" className="bg-white/20 text-white hover:bg-white/30 text-lg font-semibold px-8 py-3 rounded-lg transition-colors duration-200">
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
