'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'

interface PublicHeaderProps {
  currentPage?: 'home' | 'features' | 'pricing' | 'contact'
  className?: string
}

export default function PublicHeader({ currentPage, className }: PublicHeaderProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleGetStarted = () => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    const expiresAt = localStorage.getItem('tq_expires_at') || sessionStorage.getItem('tq_expires_at')
    const isValid = token && (!expiresAt || Date.now() <= parseInt(expiresAt))
    window.location.href = isValid ? '/dashboard' : '/auth'
  }

  const handleSignIn = () => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    const expiresAt = localStorage.getItem('tq_expires_at') || sessionStorage.getItem('tq_expires_at')
    const isValid = token && (!expiresAt || Date.now() <= parseInt(expiresAt))
    window.location.href = isValid ? '/dashboard' : '/auth'
  }

  const getNavLinkClass = (page: string) => {
    const baseClass = "text-gray-300 hover:text-brand-bright-yellow px-3 py-2 rounded-md text-sm font-medium transition-colors"
    const activeClass = "text-brand-bright-yellow"
    return currentPage === page ? `${activeClass} px-3 py-2 rounded-md text-sm font-medium` : baseClass
  }

  return (
    <nav className={`bg-gray-900/95 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Link href="/">
                <img
                  src="/images/logos/Transparent/TradeQuest%20%5BColored%5D%20%5BRectangle%5D.png"
                  alt="TradeQuest"
                  className="h-10 w-auto"
                />
              </Link>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <Link href="/features" className={getNavLinkClass('features')}>
                Features
              </Link>
              <Link href="/pricing" className={getNavLinkClass('pricing')}>
                Pricing
              </Link>
              <Link href="/contact" className={getNavLinkClass('contact')}>
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
  )
}
