"use client";

import { motion } from 'framer-motion';
import { EnvelopeIcon, CheckCircleIcon, ArrowRightIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

export default function ThankYouPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="bg-white rounded-xl shadow-xl p-8 text-center"
        >
          {/* Success Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
          >
            <CheckCircleIcon className="h-12 w-12 text-green-600" />
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-2xl font-bold text-gray-900 mb-4"
          >
            Check Your Email!
          </motion.h1>

          {/* Message */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-gray-600 mb-8"
          >
            We've sent you a magic link to sign in. Click the link in your email to complete your account setup.
          </motion.p>

          {/* Email Icon */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex items-center justify-center space-x-3 p-4 bg-blue-50 rounded-lg mb-6"
          >
            <EnvelopeIcon className="h-8 w-8 text-blue-600" />
            <div className="text-left">
              <div className="text-sm font-medium text-blue-900">Magic Link Sent</div>
              <div className="text-xs text-blue-700">Check your inbox and spam folder</div>
            </div>
          </motion.div>

          {/* Instructions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="text-sm text-gray-500 mb-8 space-y-2"
          >
            <p>• Click the link in your email</p>
            <p>• Complete the onboarding process</p>
            <p>• Start your trading journey!</p>
          </motion.div>

          {/* Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="space-y-4"
          >
            <button
              onClick={() => window.close()}
              className="w-full flex justify-center items-center space-x-2 py-3 px-4 bg-brand-dark-teal text-white rounded-lg hover:bg-brand-dark-teal/90 transition-colors"
            >
              <span>Close This Page</span>
              <ArrowRightIcon className="h-4 w-4" />
            </button>

            <Link
              href="/"
              className="block w-full text-center py-2 px-4 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Back to Homepage
            </Link>
          </motion.div>

          {/* Footer Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-8 pt-6 border-t border-gray-200"
          >
            <p className="text-xs text-gray-500">
              Didn't receive the email? Check your spam folder or try signing up again.
            </p>
          </motion.div>
        </motion.div>

        {/* Background Decoration */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 0.1, scale: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
        >
          <div className="w-96 h-96 bg-white rounded-full blur-3xl" />
        </motion.div>
      </div>
    </div>
  );
}
