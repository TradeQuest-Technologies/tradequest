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
        "Manual trade entry",
        "CSV import for bulk uploads",
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
      icon: ClockIcon,
      title: "Session Tracking",
      description: "Group trades by session and analyze your performance over time."
    },
    {
      icon: CurrencyDollarIcon,
      title: "Multi-asset Support",
      description: "Trade stocks, crypto, forex, and other assets from one platform."
    }
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
                <Link href="/features" className="text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium">
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
            Powerful Features for Serious Traders
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed"
          >
            Everything you need to analyze, improve, and optimize your trading performance. 
            From AI coaching to advanced analytics, we've got you covered.
          </motion.p>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-24">
            {mainFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex flex-col ${index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'} items-center gap-16`}
              >
                <div className="flex-1">
                  <div className="bg-gradient-to-br from-brand-teal to-brand-bright-yellow w-20 h-20 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-brand-teal/50">
                    <feature.icon className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                    {feature.title}
                  </h2>
                  <p className="text-xl text-gray-400 mb-8 leading-relaxed">
                    {feature.description}
                  </p>
                  <ul className="space-y-4">
                    {feature.features.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-center">
                        <CheckIcon className="h-6 w-6 text-brand-bright-yellow mr-4 flex-shrink-0" />
                        <span className="text-gray-300 text-lg">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex-1">
                  <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-12 h-96 flex items-center justify-center hover:border-brand-teal transition-all duration-300">
                    <div className="text-center">
                      <feature.icon className="h-32 w-32 mx-auto mb-6 text-brand-teal" />
                      <p className="text-gray-500 text-lg">Feature Preview</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Additional Features */}
      <section className="py-20 bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              And Much More
            </h2>
            <p className="text-xl text-gray-400">
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
                className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 p-8 rounded-2xl hover:border-brand-teal hover:shadow-xl hover:shadow-brand-teal/20 transition-all duration-300"
              >
                <div className="bg-brand-teal/10 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                  <feature.icon className="h-8 w-8 text-brand-teal" />
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

      {/* Integration Section - Removed (broker integrations not implemented yet) */}

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-brand-teal via-brand-dark-teal to-gray-900">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Experience These Features?
          </h2>
          <p className="text-xl text-gray-200 mb-10">
            Start your free trial today and see how TradeQuest can transform your trading.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth" className="bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 text-lg font-bold px-10 py-4 rounded-xl shadow-2xl transition-all duration-200 hover:scale-105 inline-flex items-center justify-center">
              Start Free Trial
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
            <Link href="/pricing" className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 text-white hover:bg-gray-900 hover:border-brand-bright-yellow text-lg font-semibold px-10 py-4 rounded-xl transition-all duration-200">
              View Pricing
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
