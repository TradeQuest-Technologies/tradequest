'use client'

import { useState, useEffect } from 'react'
import { Card } from '../ui/Card'
import { ChartBarIcon, ClockIcon, CheckCircleIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import { XCircleIcon } from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'
import BacktestResultsModal from './BacktestResultsModal'

interface ResultsViewerProps {
  run: any
  strategyGraphId?: string  // Filter runs by strategy
  onNewRun?: (run: any) => void  // Callback for when a new completed run is detected
}

export default function ResultsViewer({ run, strategyGraphId, onNewRun }: ResultsViewerProps) {
  const [runs, setRuns] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [showModal, setShowModal] = useState(false)
  const [selectedRunDetails, setSelectedRunDetails] = useState<any>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [lastCompletedRunId, setLastCompletedRunId] = useState<string | null>(null)

  useEffect(() => {
    if (strategyGraphId) {
      fetchRuns()
    }
  }, [strategyGraphId])

  useEffect(() => {
    if (run && run.id) {
      // Only refetch if run ID changed
      fetchRuns()
      
      // Auto-popup when a run completes
      if (run.status === 'completed' && run.id !== lastCompletedRunId) {
        setLastCompletedRunId(run.id)
        handleRunClick(run)
        
        // Notify parent
        if (onNewRun) {
          onNewRun(run)
        }
      }
    }
  }, [run?.id, run?.status])

  const fetchRuns = async () => {
    if (!strategyGraphId) {
      console.log('[ResultsViewer] No strategy selected, skipping fetch')
      return
    }
    
    console.log('[ResultsViewer] Fetching runs for strategy:', strategyGraphId)
    try {
      const token = localStorage.getItem('tq_session')
      const url = `/api/v1/backtest/v2/runs?limit=50&strategy_graph_id=${strategyGraphId}`
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        console.log('[ResultsViewer] Fetched', data.length, 'runs for this strategy')
        setRuns(data)
      }
    } catch (error) {
      console.error('Failed to fetch runs:', error)
    }
  }

  const handleRunClick = async (run: any) => {
    setSelectedRun(run)
    setShowModal(true)
    setLoadingDetails(true)
    
    // Fetch full run details including trades and equity curve
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/backtest/v2/runs/${run.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const fullRun = await response.json()
        setSelectedRunDetails(fullRun)
      } else {
        toast.error('Failed to load run details')
      }
    } catch (error) {
      console.error('Failed to fetch run details:', error)
      toast.error('Failed to load run details')
    } finally {
      setLoadingDetails(false)
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
                          <div className="font-semibold">
                            Run #{runs.length - runs.indexOf(r)} • {r.strategy_name || 'Unnamed Strategy'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {r.config?.symbol || 'N/A'} • {r.config?.timeframe || 'N/A'} • {new Date(r.created_at).toLocaleString()}
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

      {/* Comprehensive Results Modal */}
      <BacktestResultsModal
        run={selectedRunDetails || selectedRun}
        isOpen={showModal}
        onClose={() => {
          setShowModal(false)
          setSelectedRun(null)
          setSelectedRunDetails(null)
        }}
      />
      
      {/* Loading overlay while fetching details */}
      {showModal && loadingDetails && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-dark-teal mx-auto mb-4" />
            <p className="text-center text-gray-700 dark:text-gray-300">Loading backtest details...</p>
          </div>
        </div>
      )}
    </div>
  )
}
