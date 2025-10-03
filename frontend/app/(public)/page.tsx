"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ChartBarIcon,
  CpuChipIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";

export default function PublicLandingPage() {
  const [isLoading, setIsLoading] = useState(false);
  
  // If already signed in, send to dashboard
  useEffect(() => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session');
    const expiresAt = localStorage.getItem('tq_expires_at') || sessionStorage.getItem('tq_expires_at');
    const isValid = token && (!expiresAt || Date.now() <= parseInt(expiresAt));
    if (isValid) {
      window.location.replace('/dashboard');
    }
  }, []);

  const handleGetStarted = () => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session');
    const expiresAt = localStorage.getItem('tq_expires_at') || sessionStorage.getItem('tq_expires_at');
    const isValid = token && (!expiresAt || Date.now() <= parseInt(expiresAt));
    window.location.href = isValid ? '/dashboard' : '/auth';
  };

  const handleSignIn = () => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session');
    const expiresAt = localStorage.getItem('tq_expires_at') || sessionStorage.getItem('tq_expires_at');
    const isValid = token && (!expiresAt || Date.now() <= parseInt(expiresAt));
    window.location.href = isValid ? '/dashboard' : '/auth';
  };


  const coreFeatures = [
    { 
      icon: ChartBarIcon,
      title: "Performance Analytics", 
      description: "Track every metric that matters - win rate, profit factor, drawdown, and more with beautiful visualizations." 
    },
    { 
      icon: CpuChipIcon,
      title: "AI Trading Coach", 
      description: "Get personalized insights and coaching on your trades to identify patterns and improve decision-making." 
    },
    { 
      icon: DocumentTextIcon,
      title: "Trade Journal", 
      description: "Detailed journaling with screenshots, notes, tags, and session tracking to learn from every trade." 
    },
    { 
      icon: ShieldCheckIcon,
      title: "Risk Management", 
      description: "Set daily limits, stop-loss alerts, and trading rules to protect your capital and maintain discipline." 
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gradient">TradeQuest</h1>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link href="/features" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Features
                </Link>
                <Link href="/pricing" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Pricing
                </Link>
                <Link href="/docs" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Docs
                </Link>
                <Link href="/contact" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Contact
                </Link>
                <button
                  onClick={handleSignIn}
                  className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium"
                >
                  Sign In
                </button>
                <button
                  onClick={handleGetStarted}
                  className="bg-brand-bright-yellow text-brand-dark-teal hover:bg-brand-bright-yellow/90 px-4 py-2 rounded-md text-sm font-medium"
                >
                  Get Started
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-4xl md:text-6xl font-bold text-white mb-6"
            >
              Stop Losing. Start Learning.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-xl md:text-2xl text-white/90 mb-8 max-w-3xl mx-auto"
            >
              A trading platform that focuses on education, discipline, and continuous improvement. 
              Master your trading psychology and build consistent strategies.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            >
              <button
                onClick={handleGetStarted}
                disabled={isLoading}
                className="bg-white text-brand-dark-teal hover:bg-gray-50 text-lg font-semibold px-8 py-3 rounded-lg shadow-lg transition-colors duration-200 flex items-center"
              >
                {isLoading ? 'Loading...' : 'Start Free Trial'}
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </button>
              <Link href="/features" className="bg-white/20 text-white hover:bg-white/30 text-lg font-semibold px-8 py-3 rounded-lg transition-colors duration-200 inline-flex items-center">
                Explore Features
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Feature Highlights */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Powerful Features for Serious Traders
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Everything you need to analyze, improve, and master your trading performance
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {coreFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow"
              >
                <feature.icon className="h-12 w-12 text-brand-dark-teal mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How TradeQuest Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              A simple three-step process to start improving your trading
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="bg-brand-teal/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-brand-dark-teal">1</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Track Your Trades</h3>
              <p className="text-gray-600">
                Import trades via CSV or enter them manually. Add notes, screenshots, and tags to capture your thought process.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-brand-teal/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-brand-dark-teal">2</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Analyze Performance</h3>
              <p className="text-gray-600">
                Review detailed analytics, identify patterns, and get AI-powered insights on what's working and what's not.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-brand-teal/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-brand-dark-teal">3</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Improve & Repeat</h3>
              <p className="text-gray-600">
                Apply insights from your AI coach, refine your strategy, and watch your consistency improve over time.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Elevate Your Trading?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Start tracking, analyzing, and improving your trades today with TradeQuest.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGetStarted}
              disabled={isLoading}
              className="bg-white text-brand-dark-teal hover:bg-gray-50 text-lg font-semibold px-8 py-3 rounded-lg shadow-lg transition-colors duration-200"
            >
              {isLoading ? 'Loading...' : 'Start Your Free Trial'}
            </button>
            <Link href="/pricing" className="bg-white/20 text-white hover:bg-white/30 text-lg font-semibold px-8 py-3 rounded-lg transition-colors duration-200">
              View Pricing Plans
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
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/risk-disclaimer" className="hover:text-white">Risk Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 TradeQuest. All rights reserved.</p>
          </div>
        </div>
      </footer>

    </div>
  );
}
