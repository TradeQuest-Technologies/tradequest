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
    <div className="min-h-screen bg-gray-900">
      {/* Navigation */}
      <nav className="bg-gray-900/95 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Link href="/">
                  <img
                    src="/images/logos/Transparent/TradeQuest [Colored] [Rectangle].png"
                    alt="TradeQuest"
                    className="h-10 w-auto"
                  />
                </Link>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link href="/features" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Features
                </Link>
                <Link href="/pricing" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Pricing
                </Link>
                <Link href="/docs" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Docs
                </Link>
                <Link href="/contact" className="text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Contact
                </Link>
                <button
                  onClick={handleSignIn}
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={handleGetStarted}
                  className="bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 px-6 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg hover:shadow-xl"
                >
                  Get Started
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-gray-900 via-brand-dark-teal/20 to-gray-900 py-32 overflow-hidden">
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-brand-teal/10 to-brand-bright-yellow/10 opacity-30"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-5xl md:text-7xl font-bold mb-6"
            >
              <span className="text-white">Stop Losing.</span>{" "}
              <span className="text-brand-bright-yellow">
                Start Learning.
              </span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed"
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
                className="bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 text-lg font-bold px-10 py-4 rounded-xl shadow-2xl transition-all duration-200 flex items-center hover:scale-105"
              >
                {isLoading ? 'Loading...' : 'Start Free Trial'}
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </button>
              <Link href="/features" className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 text-white hover:bg-gray-800 hover:border-brand-teal text-lg font-semibold px-10 py-4 rounded-xl transition-all duration-200 inline-flex items-center">
                Explore Features
                <ArrowRightIcon className="ml-2 h-5 w-5" />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Feature Highlights */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Powerful Features for Serious Traders
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
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
                className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 p-8 rounded-2xl hover:border-brand-teal hover:shadow-xl hover:shadow-brand-teal/20 transition-all duration-300 group"
              >
                <div className="bg-brand-teal/10 p-4 rounded-xl inline-block mb-6 group-hover:bg-brand-teal/20 transition-colors">
                  <feature.icon className="h-10 w-10 text-brand-teal" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              How TradeQuest Works
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              A simple three-step process to start improving your trading
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center group">
              <div className="bg-gradient-to-br from-brand-teal to-brand-dark-teal w-24 h-24 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-brand-teal/30 group-hover:scale-110 transition-transform">
                <span className="text-4xl font-bold text-white">1</span>
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Track Your Trades</h3>
              <p className="text-gray-400 leading-relaxed">
                Import trades via CSV or enter them manually. Add notes, screenshots, and tags to capture your thought process.
              </p>
            </div>
            <div className="text-center group">
              <div className="bg-gradient-to-br from-brand-bright-yellow to-brand-teal w-24 h-24 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-brand-bright-yellow/30 group-hover:scale-110 transition-transform">
                <span className="text-4xl font-bold text-gray-900">2</span>
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Analyze Performance</h3>
              <p className="text-gray-400 leading-relaxed">
                Review detailed analytics, identify patterns, and get AI-powered insights on what's working and what's not.
              </p>
            </div>
            <div className="text-center group">
              <div className="bg-gradient-to-br from-brand-dark-teal to-brand-teal w-24 h-24 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-brand-teal/30 group-hover:scale-110 transition-transform">
                <span className="text-4xl font-bold text-white">3</span>
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Improve & Repeat</h3>
              <p className="text-gray-400 leading-relaxed">
                Apply insights from your AI coach, refine your strategy, and watch your consistency improve over time.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-brand-teal via-brand-dark-teal to-gray-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-white/5"></div>
        <div className="relative max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Elevate Your Trading?
          </h2>
          <p className="text-xl text-gray-200 mb-10 max-w-2xl mx-auto leading-relaxed">
            Start tracking, analyzing, and improving your trades today with TradeQuest.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGetStarted}
              disabled={isLoading}
              className="bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 text-lg font-bold px-10 py-4 rounded-xl shadow-2xl transition-all duration-200 hover:scale-105"
            >
              {isLoading ? 'Loading...' : 'Start Your Free Trial'}
            </button>
            <Link href="/pricing" className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 text-white hover:bg-gray-900 hover:border-brand-bright-yellow text-lg font-semibold px-10 py-4 rounded-xl transition-all duration-200">
              View Pricing Plans
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black border-t border-gray-800 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-8">
            <div>
              <img
                src="/images/logos/Transparent/TradeQuest [Colored] [Rectangle].png"
                alt="TradeQuest"
                className="h-10 w-auto mb-4"
              />
              <p className="text-gray-400 leading-relaxed">
                The trading platform that focuses on education, discipline, and continuous improvement.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Product</h4>
              <ul className="space-y-3 text-gray-400">
                <li><Link href="/features" className="hover:text-brand-bright-yellow transition-colors">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-brand-bright-yellow transition-colors">Pricing</Link></li>
                <li><Link href="/docs" className="hover:text-brand-bright-yellow transition-colors">Documentation</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Company</h4>
              <ul className="space-y-3 text-gray-400">
                <li><Link href="/contact" className="hover:text-brand-bright-yellow transition-colors">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Legal</h4>
              <ul className="space-y-3 text-gray-400">
                <li><Link href="/terms" className="hover:text-brand-bright-yellow transition-colors">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-brand-bright-yellow transition-colors">Privacy Policy</Link></li>
                <li><Link href="/risk-disclaimer" className="hover:text-brand-bright-yellow transition-colors">Risk Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center">
            <p className="text-gray-500">&copy; 2025 TradeQuest. All rights reserved.</p>
          </div>
        </div>
      </footer>

    </div>
  );
}
