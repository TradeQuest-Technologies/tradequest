"use client";

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import toast from 'react-hot-toast';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [hasProcessed, setHasProcessed] = useState(false);

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('No token provided');
      return;
    }

    // Prevent double processing
    if (hasProcessed) {
      return;
    }
    setHasProcessed(true);

    const consumeToken = async () => {
      try {
        const response = await fetch('/api/v1/auth/consume', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });

        if (response.ok) {
          const data = await response.json();
          
          // Store the JWT token in sessionStorage for magic link (temporary)
          sessionStorage.setItem('tq_session', data.access_token);
          sessionStorage.setItem('tq_expires_at', (Date.now() + (24 * 60 * 60 * 1000)).toString());
          
          setStatus('success');
          setMessage('Successfully signed in!');
          
          // Check if user has completed onboarding
          // For now, always redirect to onboarding for new users
          setTimeout(() => {
            router.push('/onboarding');
          }, 1500);
          
        } else {
          const error = await response.json();
          // If token already used, treat as success since user is already authenticated
          if (response.status === 400 && error.detail?.includes('expired')) {
            setStatus('success');
            setMessage('Already signed in!');
            setTimeout(() => {
              router.push('/onboarding');
            }, 1500);
          } else {
            setStatus('error');
            setMessage(error.detail || 'Failed to sign in');
          }
        }
      } catch (error) {
        setStatus('error');
        setMessage('Network error occurred');
        console.error('Auth callback error:', error);
      }
    };

    consumeToken();
  }, [searchParams, router, hasProcessed]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            {status === 'loading' && (
              <>
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-dark-teal mx-auto"></div>
                <h2 className="mt-4 text-xl font-semibold text-gray-900">
                  Signing you in...
                </h2>
                <p className="mt-2 text-sm text-gray-600">
                  Please wait while we verify your magic link.
                </p>
              </>
            )}

            {status === 'success' && (
              <>
                <div className="rounded-full h-12 w-12 bg-green-100 mx-auto flex items-center justify-center">
                  <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h2 className="mt-4 text-xl font-semibold text-gray-900">
                  Welcome to TradeQuest!
                </h2>
                <p className="mt-2 text-sm text-gray-600">
                  {message}
                </p>
                <p className="mt-2 text-xs text-gray-500">
                  Redirecting to your dashboard...
                </p>
              </>
            )}

            {status === 'error' && (
              <>
                <div className="rounded-full h-12 w-12 bg-red-100 mx-auto flex items-center justify-center">
                  <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h2 className="mt-4 text-xl font-semibold text-gray-900">
                  Sign In Failed
                </h2>
                <p className="mt-2 text-sm text-gray-600">
                  {message}
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => router.push('/auth')}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-dark-teal hover:bg-brand-dark-teal/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-dark-teal"
                  >
                    Try Again
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
