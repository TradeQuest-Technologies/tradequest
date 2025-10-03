'use client'

import { useState, useEffect } from 'react'
import { Button } from './ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { 
  PlusIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface CustomVenue {
  id: string
  user_id: string
  venue_name: string
  venue_code: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface VenueSelectorProps {
  selectedVenue: string
  onVenueChange: (venue: string) => void
  className?: string
}

export function VenueSelector({ selectedVenue, onVenueChange, className }: VenueSelectorProps) {
  const [customVenues, setCustomVenues] = useState<CustomVenue[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [newVenueName, setNewVenueName] = useState('')
  const [newVenueCode, setNewVenueCode] = useState('')
  const [loading, setLoading] = useState(false)

  // Standard venues
  const standardVenues = [
    { value: 'MANUAL', label: 'Manual Entry' },
    { value: 'INTERACTIVE_BROKERS', label: 'Interactive Brokers' },
    { value: 'TD_AMERITRADE', label: 'TD Ameritrade' },
    { value: 'SCHWAB', label: 'Charles Schwab' },
    { value: 'ETRADE', label: 'E*TRADE' },
    { value: 'ROBINHOOD', label: 'Robinhood' },
    { value: 'WEBULL', label: 'Webull' },
    { value: 'ALPACA', label: 'Alpaca' },
    { value: 'BINANCE', label: 'Binance' },
    { value: 'KRAKEN', label: 'Kraken' },
    { value: 'COINBASE', label: 'Coinbase' }
  ]

  useEffect(() => {
    fetchCustomVenues()
  }, [])

  const fetchCustomVenues = async () => {
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch('/api/v1/venues/venues', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setCustomVenues(data.custom_venues || [])
      }
    } catch (error) {
      console.error('Failed to fetch custom venues:', error)
    }
  }

  const handleAddVenue = async () => {
    if (!newVenueName.trim() || !newVenueCode.trim()) {
      toast.error('Please enter both venue name and code')
      return
    }

    setLoading(true)
    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch('/api/v1/venues/venues', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          venue_name: newVenueName.trim(),
          venue_code: newVenueCode.trim().toUpperCase()
        })
      })

      if (response.ok) {
        const newVenue = await response.json()
        setCustomVenues([...customVenues, newVenue])
        setNewVenueName('')
        setNewVenueCode('')
        setShowAddForm(false)
        toast.success('Custom venue added successfully!')
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to add custom venue')
      }
    } catch (error) {
      toast.error('Failed to add custom venue')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteVenue = async (venueId: string) => {
    if (!confirm('Are you sure you want to delete this custom venue?')) {
      return
    }

    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/venues/venues/${venueId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setCustomVenues(customVenues.filter(v => v.id !== venueId))
        // If the deleted venue was selected, reset to first standard venue
        if (selectedVenue === customVenues.find(v => v.id === venueId)?.venue_code) {
          onVenueChange('MANUAL')
        }
        toast.success('Custom venue deleted successfully!')
      } else {
        toast.error('Failed to delete custom venue')
      }
    } catch (error) {
      toast.error('Failed to delete custom venue')
    }
  }

  const generateVenueCode = (name: string) => {
    return name
      .replace(/[^a-zA-Z0-9\s]/g, '') // Remove special characters
      .replace(/\s+/g, '_') // Replace spaces with underscores
      .toUpperCase()
      .substring(0, 20) // Limit length
  }

  return (
    <div className={className}>
      <label htmlFor="venue" className="block text-sm font-medium mb-2">
        Select Venue/Broker *
      </label>
      
      <div className="space-y-2">
        {/* Venue Selector */}
        <select
          id="venue"
          value={selectedVenue}
          onChange={(e) => onVenueChange(e.target.value)}
          className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          {/* Standard Venues */}
          {standardVenues.map(venue => (
            <option key={venue.value} value={venue.value}>
              {venue.label}
            </option>
          ))}
          
          {/* Custom Venues */}
          {customVenues.map(venue => (
            <option key={venue.id} value={venue.venue_code}>
              {venue.venue_name}
            </option>
          ))}
        </select>

        {/* Add Custom Venue Button */}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setShowAddForm(true)}
          className="w-full"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Custom Broker
        </Button>

        {/* Add Custom Venue Form */}
        {showAddForm && (
          <Card className="mt-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Add Custom Broker</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddForm(false)}
                >
                  <XMarkIcon className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="block text-xs font-medium mb-1">
                  Broker Name
                </label>
                <input
                  type="text"
                  value={newVenueName}
                  onChange={(e) => {
                    setNewVenueName(e.target.value)
                    setNewVenueCode(generateVenueCode(e.target.value))
                  }}
                  placeholder="e.g., My Custom Broker"
                  className="w-full px-2 py-1 text-sm border border-input rounded bg-background text-foreground"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">
                  Broker Code
                </label>
                <input
                  type="text"
                  value={newVenueCode}
                  onChange={(e) => setNewVenueCode(e.target.value.toUpperCase())}
                  placeholder="e.g., MY_CUSTOM_BROKER"
                  className="w-full px-2 py-1 text-sm border border-input rounded bg-background text-foreground"
                />
              </div>
              <div className="flex space-x-2">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleAddVenue}
                  disabled={loading || !newVenueName.trim() || !newVenueCode.trim()}
                  className="flex-1"
                >
                  {loading ? 'Adding...' : 'Add Broker'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Custom Venues List */}
        {customVenues.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Your Custom Brokers:
            </p>
            <div className="space-y-1">
              {customVenues.map(venue => (
                <div key={venue.id} className="flex items-center justify-between p-2 bg-muted/30 rounded text-sm">
                  <span>{venue.venue_name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteVenue(venue.id)}
                    className="text-danger-600 hover:text-danger-700 h-6 w-6 p-0"
                  >
                    <TrashIcon className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-muted-foreground mt-1">
          Select the broker/exchange where these trades were executed
        </p>
      </div>
    </div>
  )
}
