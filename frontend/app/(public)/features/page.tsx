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
import PublicHeader from "@/components/layout/PublicHeader";
import PublicFooter from "@/components/layout/PublicFooter";

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
      ],
      image: null
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
      ],
      image: null
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
      ],
      image: null
    },
    {
      icon: ArrowTrendingUpIcon,
      title: "Advanced Backtesting Studio",
      description: "Test and validate your trading strategies with historical data before risking real capital.",
      features: [
        "Visual strategy builder",
        "Historical data backtesting",
        "Performance metrics and reports",
        "Multiple timeframe analysis",
        "Strategy optimization tools",
        "Paper trading integration"
      ],
      image: "/images/features/backtest.png"
    }
  ];

  const additionalFeatures = [
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
      <PublicHeader currentPage="features" />

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
                  <div className="relative bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm border-2 border-gray-700 rounded-2xl p-12 h-96 flex items-center justify-center hover:border-brand-teal hover:shadow-2xl hover:shadow-brand-teal/20 transition-all duration-300 group overflow-hidden">
                    {/* Animated background pattern */}
                    <div className="absolute inset-0 opacity-10">
                      <div className="absolute inset-0" style={{
                        backgroundImage: 'radial-gradient(circle at 2px 2px, rgb(20 184 166) 1px, transparent 0)',
                        backgroundSize: '40px 40px'
                      }}></div>
                    </div>
                    
                    {/* Large icon with glow */}
                    <div className="relative">
                      <div className="absolute inset-0 bg-brand-teal/30 blur-3xl group-hover:bg-brand-teal/50 transition-all duration-300"></div>
                      <feature.icon className="relative h-48 w-48 text-brand-teal group-hover:text-brand-bright-yellow transition-colors duration-300" />
                    </div>
                    
                    {/* Corner accent */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-brand-bright-yellow/20 to-transparent rounded-bl-full"></div>
                    <div className="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-brand-teal/20 to-transparent rounded-tr-full"></div>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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

      <PublicFooter />
    </div>
  );
}
