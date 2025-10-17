"use client";

import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, StarIcon, CheckIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
  feature: string
  currentPlan?: string
}

export default function UpgradeModal({ isOpen, onClose, feature, currentPlan = "Free" }: UpgradeModalProps) {
  const features = [
    "Unlimited trades",
    "CSV import/export",
    "Trade screenshots",
    "Advanced trade journal",
    "Comprehensive performance metrics & analytics",
    "Unlimited AI trading coach sessions",
    "Advanced backtesting studio",
    "PDF reports and analytics export",
    "Priority support"
  ]

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-gray-900 border border-gray-700 p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center">
                    <div className="bg-gradient-to-r from-brand-bright-yellow to-brand-teal p-2 rounded-xl mr-3">
                      <StarIcon className="h-6 w-6 text-white" />
                    </div>
                    <Dialog.Title as="h3" className="text-xl font-bold text-white">
                      Upgrade to Plus
                    </Dialog.Title>
                  </div>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="mb-6">
                  <p className="text-gray-300 mb-4">
                    <span className="font-semibold text-brand-bright-yellow">{feature}</span> is available in our Plus plan.
                  </p>
                  
                  <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xl font-bold text-white">$29</span>
                      <span className="text-gray-400">/month</span>
                    </div>
                    <div className="text-sm text-gray-500">or $290/year (save $58)</div>
                  </div>

                  <div className="space-y-3">
                    {features.map((featureItem, index) => (
                      <div key={index} className="flex items-center">
                        <CheckIcon className="h-5 w-5 text-brand-bright-yellow mr-3 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">{featureItem}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3">
                  <Link
                    href="/pricing"
                    className="flex-1 bg-brand-bright-yellow text-gray-900 hover:bg-brand-bright-yellow/90 font-semibold py-3 px-4 rounded-xl text-center transition-colors"
                    onClick={onClose}
                  >
                    View Pricing
                  </Link>
                  <button
                    onClick={onClose}
                    className="px-4 py-3 text-gray-400 hover:text-white transition-colors"
                  >
                    Maybe Later
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
