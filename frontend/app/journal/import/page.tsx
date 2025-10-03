'use client'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../../components/layout/Sidebar'
import { Header } from '../../../components/layout/Header'
import { Button } from '../../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card'
import { Badge } from '../../../components/ui/Badge'
import { VenueSelector } from '../../../components/VenueSelector'
import { 
  ArrowLeftIcon, 
  ArrowUpTrayIcon, 
  DocumentIcon,
  CheckCircleIcon,
  TrashIcon,
  PencilIcon,
  PhotoIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface ImportedTrade {
  id: string
  symbol: string
  side: 'buy' | 'sell' | 'long' | 'short'
  qty: number
  avg_price: number
  entry_price?: number
  exit_price?: number
  filled_at: string
  fees?: number
  pnl?: number
  venue?: string
  account?: string
  chart_image?: string
}

export default function ImportTrades() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [importedTrades, setImportedTrades] = useState<ImportedTrade[]>([])
  const [importStatus, setImportStatus] = useState<'idle' | 'parsing' | 'success' | 'error'>('idle')
  const [error, setError] = useState<string>('')
  const [selectedVenue, setSelectedVenue] = useState<string>('MANUAL')
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [importType, setImportType] = useState<'trades' | 'positions'>('positions')
  const [editingTrade, setEditingTrade] = useState<ImportedTrade | null>(null)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const chartImageInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setImportStatus('parsing')
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('venue', selectedVenue)
      formData.append('import_type', importType)

      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/journal/ai_convert_csv_preview', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setImportedTrades(data.trades || [])
        setImportStatus('success')
        setShowPreviewModal(true)
        toast.success(`AI analyzed ${data.total_positions || 0} trades from ${data.broker_detected || 'Unknown Broker'}`)
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'AI conversion failed')
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'AI conversion failed')
      setImportStatus('error')
      toast.error('Failed to convert CSV with AI')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmImport = async () => {
    if (importedTrades.length === 0) return

    setLoading(true)
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/journal/confirm_import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(importedTrades)
      })

      if (response.ok) {
        const data = await response.json()
        toast.success(data.message || 'Trades imported successfully!')
        router.push('/journal')
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save trades')
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to save trades')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteTrade = (index: number) => {
    setImportedTrades(prev => prev.filter((_, i) => i !== index))
    toast.success('Trade removed from import')
  }

  const handleCloseModal = () => {
    setShowPreviewModal(false)
    setImportedTrades([])
    setImportStatus('idle')
    setError('')
  }

  const handleEditTrade = (trade: ImportedTrade, index: number) => {
    setEditingTrade({...trade})
    setEditingIndex(index)
  }

  const handleSaveEdit = () => {
    if (editingTrade && editingIndex !== null) {
      setImportedTrades(prev => prev.map((t, i) => i === editingIndex ? editingTrade : t))
      setEditingTrade(null)
      setEditingIndex(null)
      toast.success('Trade updated')
    }
  }

  const handleCancelEdit = () => {
    setEditingTrade(null)
    setEditingIndex(null)
  }

  const handleChartImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && editingTrade) {
      // Convert to base64 or handle file upload
      const reader = new FileReader()
      reader.onloadend = () => {
        setEditingTrade({
          ...editingTrade,
          chart_image: reader.result as string
        })
        toast.success('Chart image uploaded')
      }
      reader.readAsDataURL(file)
    }
  }

  const getStatusIcon = () => {
    switch (importStatus) {
      case 'parsing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-success-600" />
      case 'error':
        return <TrashIcon className="h-5 w-5 text-danger-600" />
      default:
        return <DocumentIcon className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getStatusColor = () => {
    switch (importStatus) {
      case 'success':
        return 'border-success-200 bg-success-50'
      case 'error':
        return 'border-danger-200 bg-danger-50'
      default:
        return 'border-border bg-card'
    }
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
              <h1 className="text-3xl font-bold text-foreground">Import Trades</h1>
              <p className="text-muted-foreground mt-2">
                Upload a CSV file to import your trading history
              </p>
            </div>
          </div>

          <div className="max-w-4xl mx-auto space-y-6">
            {/* Upload Section */}
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered CSV Import</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* File Upload */}
                  <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${getStatusColor()}`}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <div className="flex flex-col items-center space-y-4">
                      {getStatusIcon()}
                      <div>
                        <p className="text-lg font-medium">
                          {importStatus === 'idle' && 'Click to upload or drag and drop'}
                          {importStatus === 'parsing' && 'AI is analyzing your CSV...'}
                          {importStatus === 'success' && 'AI conversion successful!'}
                          {importStatus === 'error' && 'AI conversion failed'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          CSV or Excel files (.csv, .xlsx, .xls) - max 10MB
                        </p>
                      </div>
                      <Button variant="outline">
                        <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                        Choose File
                      </Button>
                    </div>
                  </div>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileUpload}
                    className="hidden"
                  />

                  {/* Import Type Selection */}
                  <div className="space-y-3">
                    <label className="text-sm font-medium">What are you uploading?</label>
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setImportType('positions')}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          importType === 'positions'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <div className="text-left">
                          <div className="font-semibold mb-1">Complete Positions</div>
                          <div className="text-xs opacity-75">
                            Each row is a complete trade cycle (entry + exit already grouped)
                          </div>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => setImportType('trades')}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          importType === 'trades'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <div className="text-left">
                          <div className="font-semibold mb-1">Raw Trades</div>
                          <div className="text-xs opacity-75">
                            Individual buy/sell orders that need to be grouped into positions
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>

                  {/* Venue Selection */}
                  <VenueSelector
                    selectedVenue={selectedVenue}
                    onVenueChange={setSelectedVenue}
                  />

                  {/* Error Message */}
                  {error && (
                    <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg">
                      <p className="text-danger-800 text-sm">{error}</p>
                    </div>
                  )}

                  {/* CSV Format Help */}
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">CSV Format Requirements:</h4>
                    <div className="text-sm text-muted-foreground space-y-2">
                      <p><strong>Our AI technology will automatically parse your CSV!</strong> No specific format required.</p>
                      <p>However, your CSV should include these data points (column names can vary):</p>
                      <ul className="list-disc list-inside ml-4 space-y-1">
                        <li><strong>Symbol</strong> - Trading pair (e.g., BTC/USDT, AAPL, EUR/USD, GOLD)</li>
                        <li><strong>Side</strong> - Buy/Sell or Long/Short</li>
                        <li><strong>Quantity</strong> - Amount traded</li>
                        <li><strong>Price</strong> - Entry/exit price</li>
                        <li><strong>Timestamp</strong> - When the trade occurred</li>
                        <li><strong>Fees</strong> - Trading fees (optional, will be calculated if missing)</li>
                        <li><strong>PnL</strong> - Profit/Loss (optional, will be calculated if missing)</li>
                      </ul>
                      <p className="text-xs mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border-l-4 border-blue-500">
                        💡 <strong>Tip:</strong> The AI will automatically split positions, calculate fees, and determine PnL based on your data structure.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Preview Modal */}
            {showPreviewModal && importedTrades.length > 0 && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                <div className="bg-background rounded-lg shadow-2xl w-full max-w-7xl max-h-[90vh] overflow-hidden mx-4">
                  {/* Modal Header */}
                  <div className="flex items-center justify-between p-6 border-b bg-muted/30">
                    <div>
                      <h2 className="text-2xl font-bold">Review & Confirm Import</h2>
                      <p className="text-sm text-muted-foreground mt-1">
                        {importedTrades.length} trades ready to import
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleCloseModal}
                    >
                      <span className="text-2xl">&times;</span>
                    </Button>
                  </div>

                  {/* Modal Content */}
                  <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                    <div className="space-y-4">
                      {/* Summary */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-muted/50 rounded-lg">
                        <div>
                          <p className="text-sm text-muted-foreground">Total Trades</p>
                          <p className="text-2xl font-bold">{importedTrades.length}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Long/Buy</p>
                          <p className="text-2xl font-bold text-success-600">
                            {importedTrades.filter(t => t.side === 'buy' || t.side === 'long').length}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Short/Sell</p>
                          <p className="text-2xl font-bold text-danger-600">
                            {importedTrades.filter(t => t.side === 'sell' || t.side === 'short').length}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Total P&L</p>
                          <p className={`text-2xl font-bold ${importedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                            ${importedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0).toFixed(2)}
                          </p>
                        </div>
                      </div>

                      {/* Trades Table */}
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full">
                          <thead className="bg-muted sticky top-0">
                            <tr>
                              <th className="text-left p-3 text-sm font-medium">Symbol</th>
                              <th className="text-left p-3 text-sm font-medium">Side</th>
                              <th className="text-right p-3 text-sm font-medium">Qty</th>
                              <th className="text-right p-3 text-sm font-medium">Entry</th>
                              <th className="text-right p-3 text-sm font-medium">Exit</th>
                              <th className="text-right p-3 text-sm font-medium">P&L</th>
                              <th className="text-left p-3 text-sm font-medium">Date</th>
                              <th className="text-center p-3 text-sm font-medium">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {importedTrades.map((trade, index) => (
                              <tr 
                                key={trade.id} 
                                className="border-t hover:bg-muted/50 cursor-pointer"
                                onDoubleClick={() => handleEditTrade(trade, index)}
                              >
                                <td className="p-3 font-medium">{trade.symbol}</td>
                                <td className="p-3">
                                  <Badge variant={(trade.side === 'buy' || trade.side === 'long') ? 'success' : 'destructive'}>
                                    {trade.side.toUpperCase()}
                                  </Badge>
                                </td>
                                <td className="p-3 text-right">{trade.qty.toFixed(2)}</td>
                                <td className="p-3 text-right">
                                  {trade.entry_price && trade.entry_price > 0 ? `$${trade.entry_price.toFixed(2)}` : '-'}
                                </td>
                                <td className="p-3 text-right">
                                  {trade.exit_price && trade.exit_price > 0 ? `$${trade.exit_price.toFixed(2)}` : '-'}
                                </td>
                                <td className={`p-3 text-right font-medium ${(trade.pnl || 0) >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                                  ${(trade.pnl || 0).toFixed(2)}
                                </td>
                                <td className="p-3 text-sm text-muted-foreground">
                                  {new Date(trade.filled_at).toLocaleDateString()}
                                </td>
                                <td className="p-3 text-center">
                                  <div className="flex items-center justify-center gap-1">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleEditTrade(trade, index)
                                      }}
                                      className="text-primary hover:text-primary/80"
                                    >
                                      <PencilIcon className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleDeleteTrade(index)
                                      }}
                                      className="text-danger-600 hover:text-danger-700"
                                    >
                                      <TrashIcon className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* Modal Footer */}
                  <div className="flex items-center justify-between p-6 border-t bg-muted/30">
                    <Button
                      variant="outline"
                      onClick={handleCloseModal}
                      disabled={loading}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleConfirmImport}
                      disabled={loading}
                      size="lg"
                    >
                      {loading ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      ) : (
                        <CheckCircleIcon className="h-4 w-4 mr-2" />
                      )}
                      Confirm and Add {importedTrades.length} Trades
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Edit Trade Modal */}
            {editingTrade && (
              <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
                <div className="bg-background rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden mx-4">
                  {/* Modal Header */}
                  <div className="flex items-center justify-between p-6 border-b">
                    <h2 className="text-2xl font-bold">Edit Trade</h2>
                    <Button variant="ghost" size="icon" onClick={handleCancelEdit}>
                      <span className="text-2xl">&times;</span>
                    </Button>
                  </div>

                  {/* Modal Content */}
                  <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
                    <div className="space-y-4">
                      {/* Symbol */}
                      <div>
                        <label className="block text-sm font-medium mb-2">Symbol</label>
                        <input
                          type="text"
                          value={editingTrade.symbol}
                          onChange={(e) => setEditingTrade({...editingTrade, symbol: e.target.value})}
                          className="w-full p-2 border rounded-lg bg-background"
                        />
                      </div>

                      {/* Side */}
                      <div>
                        <label className="block text-sm font-medium mb-2">Side</label>
                        <select
                          value={editingTrade.side}
                          onChange={(e) => setEditingTrade({...editingTrade, side: e.target.value as any})}
                          className="w-full p-2 border rounded-lg bg-background"
                        >
                          <option value="long">Long</option>
                          <option value="short">Short</option>
                        </select>
                      </div>

                      {/* Quantity, Entry, Exit in a row */}
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Quantity</label>
                          <input
                            type="number"
                            step="0.01"
                            value={editingTrade.qty}
                            onChange={(e) => setEditingTrade({...editingTrade, qty: parseFloat(e.target.value) || 0})}
                            className="w-full p-2 border rounded-lg bg-background"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Entry Price</label>
                          <input
                            type="number"
                            step="0.01"
                            value={editingTrade.entry_price || 0}
                            onChange={(e) => setEditingTrade({...editingTrade, entry_price: parseFloat(e.target.value) || 0})}
                            className="w-full p-2 border rounded-lg bg-background"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Exit Price</label>
                          <input
                            type="number"
                            step="0.01"
                            value={editingTrade.exit_price || 0}
                            onChange={(e) => setEditingTrade({...editingTrade, exit_price: parseFloat(e.target.value) || 0})}
                            className="w-full p-2 border rounded-lg bg-background"
                          />
                        </div>
                      </div>

                      {/* Fees and PnL */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Fees</label>
                          <input
                            type="number"
                            step="0.01"
                            value={editingTrade.fees || 0}
                            onChange={(e) => setEditingTrade({...editingTrade, fees: parseFloat(e.target.value) || 0})}
                            className="w-full p-2 border rounded-lg bg-background"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">P&L</label>
                          <input
                            type="number"
                            step="0.01"
                            value={editingTrade.pnl || 0}
                            onChange={(e) => setEditingTrade({...editingTrade, pnl: parseFloat(e.target.value) || 0})}
                            className="w-full p-2 border rounded-lg bg-background"
                          />
                        </div>
                      </div>

                      {/* Date */}
                      <div>
                        <label className="block text-sm font-medium mb-2">Date</label>
                        <input
                          type="datetime-local"
                          value={editingTrade.filled_at ? new Date(editingTrade.filled_at).toISOString().slice(0, 16) : ''}
                          onChange={(e) => setEditingTrade({...editingTrade, filled_at: new Date(e.target.value).toISOString()})}
                          className="w-full p-2 border rounded-lg bg-background"
                        />
                      </div>

                      {/* Chart Image Upload */}
                      <div>
                        <label className="block text-sm font-medium mb-2">Chart Image</label>
                        <div className="space-y-2">
                          {editingTrade.chart_image && (
                            <div className="relative">
                              <img 
                                src={editingTrade.chart_image} 
                                alt="Chart" 
                                className="w-full h-48 object-cover rounded-lg border"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setEditingTrade({...editingTrade, chart_image: undefined})}
                                className="absolute top-2 right-2 bg-danger-600 text-white hover:bg-danger-700"
                              >
                                Remove
                              </Button>
                            </div>
                          )}
                          <Button
                            variant="outline"
                            onClick={() => chartImageInputRef.current?.click()}
                            className="w-full"
                          >
                            <PhotoIcon className="h-4 w-4 mr-2" />
                            {editingTrade.chart_image ? 'Change Chart Image' : 'Upload Chart Image'}
                          </Button>
                          <input
                            ref={chartImageInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleChartImageUpload}
                            className="hidden"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Modal Footer */}
                  <div className="flex items-center justify-end gap-3 p-6 border-t">
                    <Button variant="outline" onClick={handleCancelEdit}>
                      Cancel
                    </Button>
                    <Button onClick={handleSaveEdit}>
                      Save Changes
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
