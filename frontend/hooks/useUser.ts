'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  email: string
  plan: string
  alias?: string
  legal_name?: string
  first_name?: string
}

export function useUser() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
        if (!token) {
          router.push('/auth')
          return
        }

        // Check if token is expired
        const expiresAt = localStorage.getItem('tq_expires_at') || sessionStorage.getItem('tq_expires_at')
        if (expiresAt && Date.now() > parseInt(expiresAt)) {
          // Clear expired tokens
          localStorage.removeItem('tq_session')
          localStorage.removeItem('tq_expires_at')
          sessionStorage.removeItem('tq_session')
          sessionStorage.removeItem('tq_expires_at')
          router.push('/auth')
          return
        }

        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
        } else {
          // Token might be invalid, redirect to auth
          router.push('/auth')
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error)
        router.push('/auth')
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [router])

  return { user, loading }
}
