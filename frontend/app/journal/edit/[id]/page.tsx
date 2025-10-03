'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Sidebar } from '../../../../components/layout/Sidebar'
import { Header } from '../../../../components/layout/Header'
import { Button } from '../../../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card'
import { 
  ArrowLeftIcon,
  PlusIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Trade {
  id: string
  user_id: string
  account?: string
  venue: string
  symbol: string
  side: 'buy' | 'sell'
  qty: number
  avg_price: number
  fees: number
  pnl: number
  submitted_at?: string
  filled_at: string
  order_ref?: string
  session_id?: string
  raw?: any
  chart_image?: string
}

export default function EditTrade() {
  const [loading, setLoading] = useState(false)
  const [trade, setTrade] = useState<Trade | null>(null)
  const [formData, setFormData] = useState({
    symbol: '',
    side: 'long' as 'long' | 'short',
    entry_time: '',
    exit_time: '',
    entry_price: '',
    exit_price: '',
    quantity: '',
    total_pnl: '',
    total_fees: '',
    is_dca: false,
    dca_entries: [] as Array<{time: string, price: string, reason: string}>,
    notes: '',
    tags: '',
    chart_image: null as File | null
  })
  const router = useRouter()
  const params = useParams()
  const tradeId = params.id as string

  useEffect(() => {
    const fetchTrade = async () => {
      try {
        const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
        if (!token) {
          router.push('/auth')
          return
        }

        const response = await fetch(`/api/v1/journal/trades/${tradeId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const tradeData = await response.json()
          setTrade(tradeData)
          
          // Populate form with existing data
          setFormData({
            symbol: tradeData.symbol,
            side: tradeData.side === 'buy' ? 'long' : 'short',
            entry_time: tradeData.filled_at ? new Date(tradeData.filled_at).toISOString().slice(0, 16) : '',
            exit_time: tradeData.submitted_at ? new Date(tradeData.submitted_at).toISOString().slice(0, 16) : '',
            entry_price: tradeData.avg_price?.toString() || '',
            exit_price: tradeData.raw?.exit_price || '',
            quantity: tradeData.qty?.toString() || '',
            total_pnl: tradeData.pnl?.toString() || '',
            total_fees: tradeData.fees?.toString() || '',
            is_dca: tradeData.raw?.is_dca || false,
            dca_entries: tradeData.raw?.dca_entries || [],
            notes: tradeData.raw?.notes || '',
            tags: tradeData.raw?.tags?.join(', ') || '',
            chart_image: null
          })
        } else {
          router.push('/journal')
        }
      } catch (error) {
        console.error('Error fetching trade:', error)
        router.push('/journal')
      }
    }

    if (tradeId) {
      fetchTrade()
    }
  }, [tradeId, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      
      // Create FormData for file upload
      const formDataToSend = new FormData()
      formDataToSend.append('venue', 'MANUAL')
      formDataToSend.append('symbol', formData.symbol)
      formDataToSend.append('side', formData.side === 'long' ? 'buy' : 'sell')
      formDataToSend.append('qty', formData.quantity)
      formDataToSend.append('avg_price', formData.entry_price)
      formDataToSend.append('fees', formData.total_fees || '0')
      formDataToSend.append('pnl', formData.total_pnl || '0')
      formDataToSend.append('filled_at', formData.entry_time)
      formDataToSend.append('submitted_at', formData.exit_time || formData.entry_time)
      formDataToSend.append('order_ref', trade?.order_ref || `manual_${Date.now()}`)
      formDataToSend.append('raw', JSON.stringify({
        entry_price: formData.entry_price,
        exit_price: formData.exit_price,
        is_dca: formData.is_dca,
        dca_entries: formData.dca_entries,
        notes: formData.notes,
        tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      }))
      
      // Add chart image if selected
      if (formData.chart_image) {
        formDataToSend.append('chart_image', formData.chart_image)
      }

      const response = await fetch(`/api/v1/journal/trades/${tradeId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formDataToSend
      })

      if (response.ok) {
        toast.success('Trade updated successfully!')
        router.push(`/journal/trade/${tradeId}`)
      } else {
        throw new Error('Failed to update trade')
      }
    } catch (error) {
      toast.error('Failed to update trade')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked
      setFormData(prev => ({
        ...prev,
        [name]: checked
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }))
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    setFormData({...formData, chart_image: file})
  }

  const addDCAEntry = () => {
    setFormData(prev => ({
      ...prev,
      dca_entries: [...prev.dca_entries, { time: '', price: '', reason: '' }]
    }))
  }

  const removeDCAEntry = (index: number) => {
    setFormData(prev => ({
      ...prev,
      dca_entries: prev.dca_entries.filter((_, i) => i !== index)
    }))
  }

  const updateDCAEntry = (index: number, field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      dca_entries: prev.dca_entries.map((entry, i) => 
        i === index ? { ...entry, [field]: value } : entry
      )
    }))
  }

  if (!trade) {
    return (
      <div className="min-h-screen bg-background flex">
        <Sidebar className="w-64" />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-foreground mb-4">Trade Not Found</h1>
              <p className="text-muted-foreground mb-4">The trade you're trying to edit doesn't exist.</p>
              <Button onClick={() => router.push('/journal')}>
                Back to Journal
              </Button>
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6">
          {/* Header */}
          <div className="flex items-center space-x-4 mb-6">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-foreground font-brand-display">
                Edit Trade
              </h1>
              <p className="text-muted-foreground mt-2">
                Update your trade details
              </p>
            </div>
          </div>

          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle>Trade Details</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Basic Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="symbol" className="block text-sm font-medium mb-2">
                        Symbol <span className="text-destructive">*</span>
                      </label>
                      <input
                        type="text"
                        id="symbol"
                        name="symbol"
                        value={formData.symbol}
                        onChange={handleInputChange}
                        placeholder="e.g., BTC/USDT, TSLA"
                        required
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>

                    <div>
                      <label htmlFor="side" className="block text-sm font-medium mb-2">
                        Side <span className="text-destructive">*</span>
                      </label>
                      <select
                        id="side"
                        name="side"
                        value={formData.side}
                        onChange={handleInputChange}
                        required
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      >
                        <option value="long">Long</option>
                        <option value="short">Short</option>
                      </select>
                    </div>
                  </div>

                  {/* Timing */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="entry_time" className="block text-sm font-medium mb-2">
                        Entry Time <span className="text-destructive">*</span>
                      </label>
                      <input
                        type="datetime-local"
                        id="entry_time"
                        name="entry_time"
                        value={formData.entry_time}
                        onChange={handleInputChange}
                        required
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>

                    <div>
                      <label htmlFor="exit_time" className="block text-sm font-medium mb-2">
                        Exit Time
                      </label>
                      <input
                        type="datetime-local"
                        id="exit_time"
                        name="exit_time"
                        value={formData.exit_time}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>
                  </div>

                  {/* Prices */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="entry_price" className="block text-sm font-medium mb-2">
                        Entry Price <span className="text-destructive">*</span>
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        id="entry_price"
                        name="entry_price"
                        value={formData.entry_price}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        required
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>

                    <div>
                      <label htmlFor="exit_price" className="block text-sm font-medium mb-2">
                        Exit Price
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        id="exit_price"
                        name="exit_price"
                        value={formData.exit_price}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>
                  </div>

                  {/* Quantity and P&L */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label htmlFor="quantity" className="block text-sm font-medium mb-2">
                        Quantity <span className="text-destructive">*</span>
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        id="quantity"
                        name="quantity"
                        value={formData.quantity}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        required
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>

                    <div>
                      <label htmlFor="total_pnl" className="block text-sm font-medium mb-2">
                        Total P&L
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        id="total_pnl"
                        name="total_pnl"
                        value={formData.total_pnl}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>

                    <div>
                      <label htmlFor="total_fees" className="block text-sm font-medium mb-2">
                        Total Fees
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        id="total_fees"
                        name="total_fees"
                        value={formData.total_fees}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        className="w-full px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring bg-background text-foreground"
                      />
                    </div>
                  </div>

                  {/* DCA Section */}
                  <div>
                    <div className="flex items-center space-x-2 mb-4">
                      <input
                        type="checkbox"
                        id="is_dca"
                        name="is_dca"
                        checked={formData.is_dca}
                        onChange={handleInputChange}
                        className="rounded border-input"
                      />
                      <label htmlFor="is_dca" className="text-sm font-medium">
                        I used Dollar Cost Averaging (DCA) during this trade
                      </label>
                    </div>

                    {formData.is_dca && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">DCA Entries</h4>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={addDCAEntry}
                          >
                            <PlusIcon className="h-4 w-4 mr-1" />
                            Add DCA Entry
                          </Button>
                        </div>

                        {formData.dca_entries.map((entry, index) => (
                          <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 border rounded-lg bg-muted/30">
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">Time</label>
                              <input
                                type="datetime-local"
                                value={entry.time}
                                onChange={(e) => updateDCAEntry(index, 'time', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-input rounded bg-background text-foreground"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">Price</label>
                              <input
                                type="number"
                                step="0.01"
                                value={entry.price}
                                onChange={(e) => updateDCAEntry(index, 'price', e.target.value)}
                                placeholder="0.00"
                                className="w-full px-2 py-1 text-sm border border-input rounded bg-background text-foreground"
                              />
                            </div>
                            <div>
                              <label className="text-xs font-medium text-muted-foreground">Reason</label>
                              <input
                                type="text"
                                value={entry.reason}
                                onChange={(e) => updateDCAEntry(index, 'reason', e.target.value)}
                                placeholder="Why this entry?"
                                className="w-full px-2 py-1 text-sm border border-input rounded bg-background text-foreground"
                              />
                            </div>
                            <div className="flex items-end">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => removeDCAEntry(index)}
                                className="text-danger-600 hover:text-danger-700"
                              >
                                Remove
                              </Button>
                            </div>
                          </div>
                        ))}
                        {formData.dca_entries.length === 0 && (
                          <p className="text-sm text-muted-foreground text-center py-4">
                            Click "Add DCA Entry" to add your first DCA entry
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Notes */}
                  <div>
                    <label htmlFor="notes" className="block text-sm font-medium mb-2">
                      Notes
                    </label>
                    <textarea
                      id="notes"
                      name="notes"
                      value={formData.notes}
                      onChange={handleInputChange}
                      placeholder="Add your trading notes, strategy, or observations..."
                      rows={4}
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    />
                  </div>

                  {/* Tags */}
                  <div>
                    <label htmlFor="tags" className="block text-sm font-medium mb-2">
                      Tags
                    </label>
                    <input
                      type="text"
                      id="tags"
                      name="tags"
                      value={formData.tags}
                      onChange={handleInputChange}
                      placeholder="breakout, btc, swing (comma-separated)"
                      className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Separate tags with commas
                    </p>
                  </div>

                  {/* Chart Image Upload */}
                  <div>
                    <label htmlFor="chart_image" className="block text-sm font-medium mb-2">
                      Chart Image (Optional)
                    </label>
                    <div className="space-y-2">
                      <input
                        type="file"
                        id="chart_image"
                        name="chart_image"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      />
                      {formData.chart_image && (
                        <div className="text-sm text-muted-foreground">
                          Selected: {formData.chart_image.name}
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground">
                        Upload a screenshot of your chart analysis for this trade (max 10MB)
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-4 pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => router.back()}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled={loading}
                      className="flex-1"
                    >
                      {loading ? 'Updating...' : 'Update Trade'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
