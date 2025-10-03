"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ChartBarIcon,
  CpuChipIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  CheckIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  EyeIcon,
  CogIcon,
  BellIcon,
} from "@heroicons/react/24/outline";

export default function FeaturesPage() {
  const mainFeatures = [
    {
      icon: ChartBarIcon,
      title: "Advanced Analytics",
      description: "Deep insights into your trading performance with comprehensive metrics and visualizations.",
      features: [
        "Real-time performance tracking",
        "Win rate and profit factor analysis",
        "Drawdown monitoring",
        "Risk-adjusted returns",
        "Trade heatmaps by symbol and time",
        "Consistency scoring"
      ]
    },
    {
      icon: CpuChipIcon,
      title: "AI Trading Coach",
      description: "Get personalized coaching and actionable insights powered by advanced AI.",
      features: [
        "Trade-by-trade analysis",
        "Session coaching and feedback",
        "Pattern recognition",
        "Risk management suggestions",
        "Entry and exit timing analysis",
        "Performance improvement recommendations"
      ]
    },
    {
      icon: DocumentTextIcon,
      title: "Comprehensive Trade Journal",
      description: "Track every trade with detailed notes, tags, and performance metrics.",
      features: [
        "Automatic trade import from brokers",
        "Manual trade entry with CSV upload",
        "Rich text notes and attachments",
        "Custom tags and categorization",
        "Trade session grouping",
        "Export capabilities (PDF, CSV, JSON)"
      ]
    },
    {
      icon: ShieldCheckIcon,
      title: "Discipline & Risk Management",
      description: "Built-in tools to help you stick to your trading plan and manage risk.",
      features: [
        "Daily stop-loss limits",
        "Maximum trades per day",
        "Cooldown periods",
        "Quiet hours enforcement",
        "Real-time alerts and notifications",
        "Streak tracking and achievements"
      ]
    }
  ];

  const additionalFeatures = [
    {
      icon: ArrowTrendingUpIcon,
      title: "Backtesting Studio",
      description: "Test your strategies with historical data and advanced backtesting tools."
    },
    {
      icon: EyeIcon,
      title: "Market Explorer",
      description: "Analyze market data with interactive charts and technical indicators."
    },
    {
      icon: BellIcon,
      title: "Smart Alerts",
      description: "Get notified about important market events and trading opportunities."
    },
    {
      icon: CogIcon,
      title: "Broker Integrations",
      description: "Connect with Kraken, Coinbase Advanced, and other major brokers."
    },
    {
      icon: ClockIcon,
      title: "Real-time Sync",
      description: "Automatically sync your trades and positions in real-time."
    },
    {
      icon: CurrencyDollarIcon,
      title: "Multi-asset Support",
      description: "Trade stocks, crypto, forex, and other assets from one platform."
    }
  ];

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
                <Link href="/features" className="text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Features
                </Link>
                <Link href="/pricing" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
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
            Powerful Features for Serious Traders
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl md:text-2xl text-white/90 mb-8 max-w-3xl mx-auto"
          >
            Everything you need to analyze, improve, and optimize your trading performance. 
            From AI coaching to advanced analytics, we've got you covered.
          </motion.p>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-20">
            {mainFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex flex-col ${index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'} items-center gap-12`}
              >
                <div className="flex-1">
                  <div className="bg-brand-bright-yellow/20 w-20 h-20 rounded-full flex items-center justify-center mb-6">
                    <feature.icon className="h-10 w-10 text-brand-dark-teal" />
                  </div>
                  <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                    {feature.title}
                  </h2>
                  <p className="text-xl text-gray-600 mb-6">
                    {feature.description}
                  </p>
                  <ul className="space-y-3">
                    {feature.features.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-center">
                        <CheckIcon className="h-5 w-5 text-brand-bright-yellow mr-3 flex-shrink-0" />
                        <span className="text-gray-700">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex-1">
                  <div className="bg-gray-100 rounded-lg p-8 h-80 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <feature.icon className="h-24 w-24 mx-auto mb-4" />
                      <p>Feature Preview</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Additional Features */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              And Much More
            </h2>
            <p className="text-xl text-gray-600">
              Additional tools and features to enhance your trading experience.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {additionalFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-200"
              >
                <div className="bg-brand-bright-yellow/20 w-12 h-12 rounded-full flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-brand-dark-teal" />
                </div>
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

      {/* Integration Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Seamless Integrations
            </h2>
            <p className="text-xl text-gray-600">
              Connect with your favorite brokers and tools.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center">
            {["Kraken", "Coinbase Advanced", "Binance", "Interactive Brokers"].map((broker, index) => (
              <motion.div
                key={broker}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-100 rounded-lg p-8 text-center hover:shadow-lg transition-shadow duration-200"
              >
                <div className="text-2xl font-bold text-gray-700">{broker}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Experience These Features?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Start your free trial today and see how TradeQuest can transform your trading.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth" className="bg-white text-brand-dark-teal hover:bg-gray-50 text-lg font-semibold px-8 py-3 rounded-lg shadow-lg transition-colors duration-200 inline-flex items-center justify-center">
              Start Free Trial
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
            <Link href="/pricing" className="bg-white/20 text-white hover:bg-white/30 text-lg font-semibold px-8 py-3 rounded-lg transition-colors duration-200">
              View Pricing
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
