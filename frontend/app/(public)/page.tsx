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
  CheckIcon,
  StarIcon,
  PlayIcon,
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

  const features = [
    {
      icon: ChartBarIcon,
      title: "Advanced Analytics",
      description: "Deep insights into your trading performance with AI-powered analysis and visualizations.",
    },
    {
      icon: CpuChipIcon,
      title: "AI Trading Coach",
      description: "Get personalized coaching and actionable insights to improve your trading strategy.",
    },
    {
      icon: DocumentTextIcon,
      title: "Trade Journal",
      description: "Comprehensive trade tracking with detailed notes, tags, and performance metrics.",
    },
    {
      icon: ShieldCheckIcon,
      title: "Risk Management",
      description: "Built-in discipline tools and alerts to help you stick to your trading plan.",
    },
  ];

  const stats = [
    { label: "Active Traders", value: "10,000+" },
    { label: "Trades Analyzed", value: "2.5M+" },
    { label: "Average Win Rate Improvement", value: "23%" },
    { label: "Risk Reduction", value: "35%" },
  ];

  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Day Trader",
      content: "TradeQuest helped me identify my biggest weaknesses and improve my win rate by 40% in just 3 months.",
      rating: 5,
    },
    {
      name: "Mike Rodriguez",
      role: "Swing Trader",
      content: "The AI coach is incredible. It's like having a professional mentor available 24/7.",
      rating: 5,
    },
    {
      name: "Emily Watson",
      role: "Crypto Trader",
      content: "Finally, a platform that focuses on education and improvement rather than just execution.",
      rating: 5,
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
              The only trading platform that focuses on education, discipline, and continuous improvement. 
              Join thousands of traders who are finally turning profitable.
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
              <button className="bg-white/20 text-white hover:bg-white/30 text-lg font-semibold px-8 py-3 rounded-lg transition-colors duration-200 flex items-center">
                <PlayIcon className="mr-2 h-5 w-5" />
                Watch Demo
              </button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold text-brand-dark-teal mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Trade Better
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              TradeQuest combines advanced analytics, AI coaching, and discipline tools 
              to help you become a consistently profitable trader.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-center p-6 rounded-lg hover:shadow-lg transition-shadow duration-200"
              >
                <div className="bg-brand-bright-yellow/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="h-8 w-8 text-brand-dark-teal" />
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

      {/* Testimonials Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Trusted by Traders Worldwide
            </h2>
            <p className="text-xl text-gray-600">
              See what our community has to say about their transformation.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={testimonial.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white p-6 rounded-lg shadow-lg"
              >
                <div className="flex items-center mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <StarIcon key={i} className="h-5 w-5 text-brand-bright-yellow fill-current" />
                  ))}
                </div>
                <p className="text-gray-700 mb-4 italic">
                  "{testimonial.content}"
                </p>
                <div>
                  <div className="font-semibold text-gray-900">{testimonial.name}</div>
                  <div className="text-gray-600 text-sm">{testimonial.role}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Trading?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join thousands of traders who are finally turning profitable with TradeQuest.
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
