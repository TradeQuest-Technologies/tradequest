"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  DocumentTextIcon,
  ArrowRightIcon,
  CodeBracketIcon,
  ChartBarIcon,
  CogIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";

export default function DocsPage() {
  const sections = [
    {
      icon: DocumentTextIcon,
      title: "Getting Started",
      description: "Learn how to set up your TradeQuest account and start trading analysis.",
      topics: [
        "Account Setup",
        "Broker Integration",
        "First Trade Import",
        "Basic Navigation"
      ]
    },
    {
      icon: CodeBracketIcon,
      title: "CSV Import Guide",
      description: "Import your trading data from various brokers and platforms.",
      topics: [
        "Supported Brokers",
        "CSV Format Requirements",
        "Column Mapping",
        "Data Validation"
      ]
    },
    {
      icon: ChartBarIcon,
      title: "API Documentation",
      description: "Integrate TradeQuest with your own applications and tools.",
      topics: [
        "Authentication",
        "Rate Limits",
        "Endpoints Reference",
        "Webhooks"
      ]
    },
    {
      icon: CogIcon,
      title: "Broker Scopes",
      description: "Understand what permissions are required for each broker integration.",
      topics: [
        "Kraken API Scopes",
        "Coinbase Advanced Scopes",
        "Read-Only Access",
        "Security Best Practices"
      ]
    },
    {
      icon: ShieldCheckIcon,
      title: "Security & Privacy",
      description: "Learn about our security measures and data protection policies.",
      topics: [
        "Data Encryption",
        "API Key Security",
        "Privacy Policy",
        "GDPR Compliance"
      ]
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
                <Link href="/features" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Features
                </Link>
                <Link href="/pricing" className="text-gray-700 hover:text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
                  Pricing
                </Link>
                <Link href="/docs" className="text-brand-dark-teal px-3 py-2 rounded-md text-sm font-medium">
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
            Documentation
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl md:text-2xl text-white/90 mb-8 max-w-3xl mx-auto"
          >
            Everything you need to know to get the most out of TradeQuest.
          </motion.p>
        </div>
      </section>

      {/* Documentation Sections */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {sections.map((section, index) => (
              <motion.div
                key={section.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow duration-200"
              >
                <div className="bg-brand-bright-yellow/20 w-12 h-12 rounded-full flex items-center justify-center mb-4">
                  <section.icon className="h-6 w-6 text-brand-dark-teal" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {section.title}
                </h3>
                <p className="text-gray-600 mb-4">
                  {section.description}
                </p>
                <ul className="space-y-1">
                  {section.topics.map((topic, topicIndex) => (
                    <li key={topicIndex} className="text-sm text-gray-500 flex items-center">
                      <ArrowRightIcon className="h-3 w-3 mr-2 text-brand-bright-yellow" />
                      {topic}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join thousands of traders improving their skills with TradeQuest.
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