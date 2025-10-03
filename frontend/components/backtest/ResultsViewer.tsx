'use client'

import { useState, useEffect } from 'react'
import { Card } from '../ui/Card'
import { ChartBarIcon } from '@heroicons/react/24/outline'
import { ClockIcon } from '@heroicons/react/24/outline'
import { CheckCircleIcon } from '@heroicons/react/24/outline'
import { XCircleIcon } from '@heroicons/react/24/outline'
import { DocumentTextIcon } from '@heroicons/react/24/outline'
import { ExclamationTriangleIcon } from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'

interface ResultsViewerProps {
  run: any
}

export default function ResultsViewer({ run }: ResultsViewerProps) {
  const [runs, setRuns] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [showModal, setShowModal] = useState(false)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    fetchRuns()
  }, [])

  useEffect(() => {
    if (run) {
      fetchRuns()
    }
  }, [run])

  const fetchRuns = async () => {
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/runs?limit=50`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setRuns(data)
      }
    } catch (error) {
      console.error('Failed to fetch runs:', error)
    }
  }

  const handleRunClick = (run: any) => {
    setSelectedRun(run)
    setNotes(run.notes || (run.diagnostics && run.diagnostics.notes) || '')
    setShowModal(true)
  }

  const handleSaveNotes = async () => {
    if (!selectedRun) return

    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/runs/${selectedRun.id}/notes`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ notes })
      })

      if (response.ok) {
        toast.success('Notes saved!')
        setSelectedRun({ ...selectedRun, notes })
        fetchRuns()
      } else {
        toast.error('Failed to save notes')
      }
    } catch (error) {
      toast.error('Failed to save notes')
    }
  }

  const getStatusIcon = (status: string) => {
    if (status === 'completed') {
      return <CheckCircleIcon className="h-5 w-5 text-success-600" />
    }
    if (status === 'failed') {
      return <XCircleIcon className="h-5 w-5 text-danger-600" />
    }
    if (status === 'running') {
      return <ClockIcon className="h-5 w-5 text-blue-600 animate-spin" />
    }
    return <ClockIcon className="h-5 w-5 text-muted-foreground" />
  }

  const getStatusColor = (status: string) => {
    if (status === 'completed') {
      return 'bg-success-500/10 text-success-600 border-success-500/20'
    }
    if (status === 'failed') {
      return 'bg-danger-500/10 text-danger-600 border-danger-500/20'
    }
    if (status === 'running') {
      return 'bg-blue-500/10 text-blue-600 border-blue-500/20'
    }
    return 'bg-gray-500/10 text-muted-foreground border-gray-500/20'
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border bg-gradient-to-r from-brand-dark-teal/5 to-brand-bright-yellow/5">
        <h2 className="text-xl font-bold">Backtest History</h2>
        <p className="text-sm text-muted-foreground">Click any run to view details and add notes</p>
      </div>

      {/* Runs List */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {runs.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <ChartBarIcon className="h-16 w-16 mx-auto text-muted-foreground opacity-50 mb-4" />
              <div className="text-lg font-medium mb-2">No Backtests Yet</div>
              <div className="text-sm text-muted-foreground">
                Run a backtest to see results here
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3 max-w-5xl mx-auto">
            {runs.map((r) => {
              const errorMessage = r.error_message || (r.diagnostics && r.diagnostics.error)
              const hasNotes = r.notes || (r.diagnostics && r.diagnostics.notes)
              
              return (
                <Card 
                  key={r.id}
                  className="p-4 hover:shadow-lg transition-all cursor-pointer border-l-4"
                  style={{ borderLeftColor: r.status === 'completed' ? '#10b981' : r.status === 'failed' ? '#ef4444' : '#6b7280' }}
                  onClick={() => handleRunClick(r)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(r.status)}
                        <div>
                          <div className="font-semibold">{r.config?.symbol || 'Unknown'} - {r.config?.timeframe || '?'}</div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(r.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      
                      {r.status === 'completed' && r.metrics ? (
                        <div className="flex items-center gap-4 text-sm mt-2">
                          <div className={`font-semibold ${r.metrics.total_return > 0 ? 'text-success-600' : 'text-danger-600'}`}>
                            {(r.metrics.total_return * 100).toFixed(2)}% Return
                          </div>
                          <div>Sharpe: {r.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</div>
                          <div>{r.metrics.total_trades} Trades</div>
                          <div>Win Rate: {(r.metrics.win_rate * 100).toFixed(0)}%</div>
                        </div>
                      ) : null}
                      
                      {r.status === 'failed' && errorMessage ? (
                        <div className="text-sm text-danger-600 mt-2">
                          {errorMessage.substring(0, 100)}{errorMessage.length > 100 ? '...' : ''}
                        </div>
                      ) : null}
                      
                      {hasNotes ? (
                        <div className="mt-2 text-sm text-muted-foreground italic flex items-center gap-2">
                          <DocumentTextIcon className="h-4 w-4" />
                          {(r.notes || r.diagnostics.notes).substring(0, 80)}{(r.notes || r.diagnostics.notes).length > 80 ? '...' : ''}
                        </div>
                      ) : null}
                    </div>
                    
                    <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(r.status)}`}>
                      {r.status}
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {/* Modal for Run Details */}
      {showModal && selectedRun ? (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
          <div className="bg-background rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="p-6 border-b border-border bg-gradient-to-r from-brand-dark-teal/5 to-brand-bright-yellow/5">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-2xl font-bold mb-1">
                    {selectedRun.config?.symbol || 'Unknown'} - {selectedRun.config?.timeframe || '?'}
                  </h3>
                  <div className="text-sm text-muted-foreground">
                    {new Date(selectedRun.created_at).toLocaleString()} • Run ID: {selectedRun.id?.substring(0, 8)}
                  </div>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-muted-foreground hover:text-foreground text-2xl leading-none"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)] custom-scrollbar">
              {/* Metrics for Successful Runs */}
              {selectedRun.status === 'completed' && selectedRun.metrics ? (
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <Card className="p-4">
                    <div className="text-sm text-muted-foreground mb-1">Total Return</div>
                    <div className={`text-2xl font-bold ${selectedRun.metrics.total_return > 0 ? 'text-success-600' : 'text-danger-600'}`}>
                      {(selectedRun.metrics.total_return * 100).toFixed(2)}%
                    </div>
                  </Card>
                  <Card className="p-4">
                    <div className="text-sm text-muted-foreground mb-1">Sharpe Ratio</div>
                    <div className="text-2xl font-bold">{selectedRun.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</div>
                  </Card>
                  <Card className="p-4">
                    <div className="text-sm text-muted-foreground mb-1">Total Trades</div>
                    <div className="text-2xl font-bold">{selectedRun.metrics.total_trades}</div>
                  </Card>
                  <Card className="p-4">
                    <div className="text-sm text-muted-foreground mb-1">Win Rate</div>
                    <div className="text-2xl font-bold">{(selectedRun.metrics.win_rate * 100).toFixed(0)}%</div>
                  </Card>
                </div>
              ) : null}

              {/* Error Display for Failed Runs */}
              {selectedRun.status === 'failed' ? (
                <div className="mb-6">
                  <div className="p-4 rounded-lg bg-danger-500/10 border border-danger-500/20">
                    <div className="flex items-start gap-3">
                      <ExclamationTriangleIcon className="h-6 w-6 text-danger-600 flex-shrink-0" />
                      <div>
                        <div className="font-semibold text-danger-600 mb-1">Backtest Failed</div>
                        <div className="text-sm text-muted-foreground">
                          {selectedRun.error_message || (selectedRun.diagnostics && selectedRun.diagnostics.error) || 'Unknown error'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Notes Section */}
              <div className="mt-6">
                <label className="block text-sm font-semibold mb-2">Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about this backtest run..."
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm min-h-[120px] resize-y"
                />
                <button
                  onClick={handleSaveNotes}
                  className="mt-3 px-4 py-2 bg-brand-dark-teal text-white rounded-lg hover:bg-brand-dark-teal/90 transition-colors"
                >
                  Save Notes
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
