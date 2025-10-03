'use client'

import { useState, useEffect } from 'react'
import { Button } from '../ui/Button'
import {
  FolderIcon,
  PlusIcon,
  ChartBarIcon,
  RectangleStackIcon,
  BeakerIcon,
  DocumentTextIcon,
  ClockIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface NavigatorSidebarProps {
  currentGraph: any
  onGraphSelect: (graph: any) => void
  onClose: () => void
}

const DEMO_STRATEGIES = [
  {
    id: 'demo_rsi_mean_reversion',
    name: 'RSI Mean Reversion',
    description: 'Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought)',
    nodes: [
      { id: 'data1', type: 'data.loader', params: { symbol: 'BTC/USDT', timeframe: '1m', start_date: '2024-01-01', end_date: '2024-03-31' }, inputs: [] },
      { id: 'rsi1', type: 'feature.rsi', params: { period: 14, output_name: 'rsi' }, inputs: ['data1'] },
      { id: 'atr1', type: 'feature.atr', params: { period: 14, output_name: 'atr' }, inputs: ['data1'] },
      { id: 'sig1', type: 'signal.threshold', params: { feature: 'rsi', upper_threshold: 70, lower_threshold: 30 }, inputs: ['rsi1'] },
      { id: 'size1', type: 'sizing.vol_target', params: { target_vol: 0.15, lookback: 30 }, inputs: ['sig1'] },
      { id: 'risk1', type: 'risk.stop_take', params: { stop_atr_mult: 2.0, take_atr_mult: 3.0 }, inputs: ['size1', 'atr1'] },
      { id: 'exec1', type: 'exec.market', params: { slippage_bps: 5, fee_bps: 2 }, inputs: ['risk1'] }
    ],
    outputs: ['exec1'],
    version: 1,
    tags: ['demo', 'mean-reversion', 'rsi'],
    is_demo: true
  },
  {
    id: 'demo_sma_crossover',
    name: 'SMA Crossover (Trend)',
    description: 'Buy when fast SMA crosses above slow SMA, sell on opposite crossover',
    nodes: [
      { id: 'data1', type: 'data.loader', params: { symbol: 'ETH/USDT', timeframe: '1h', start_date: '2024-01-01', end_date: '2024-12-31' }, inputs: [] },
      { id: 'ema_fast', type: 'feature.ema', params: { period: 10, source: 'close', output_name: 'ema_fast' }, inputs: ['data1'] },
      { id: 'ema_slow', type: 'feature.ema', params: { period: 30, source: 'close', output_name: 'ema_slow' }, inputs: ['data1'] },
      { id: 'sig1', type: 'signal.crossover', params: { fast_feature: 'ema_fast', slow_feature: 'ema_slow' }, inputs: ['ema_fast', 'ema_slow'] },
      { id: 'size1', type: 'sizing.fixed', params: { position_size: 1.0 }, inputs: ['sig1'] },
      { id: 'exec1', type: 'exec.market', params: { slippage_bps: 5, fee_bps: 2 }, inputs: ['size1'] }
    ],
    outputs: ['exec1'],
    version: 1,
    tags: ['demo', 'trend-following', 'sma'],
    is_demo: true
  },
  {
    id: 'demo_volatility_breakout',
    name: 'Volatility Breakout',
    description: 'Advanced strategy with ATR-based stops and volatility targeting',
    nodes: [
      { id: 'data1', type: 'data.loader', params: { symbol: 'BTC/USDT', timeframe: '15m', start_date: '2024-06-01', end_date: '2024-09-30' }, inputs: [] },
      { id: 'atr1', type: 'feature.atr', params: { period: 14, output_name: 'atr' }, inputs: ['data1'] },
      { id: 'rsi1', type: 'feature.rsi', params: { period: 14, output_name: 'rsi' }, inputs: ['data1'] },
      { id: 'macd1', type: 'feature.macd', params: { fast_period: 12, slow_period: 26, signal_period: 9 }, inputs: ['data1'] },
      { id: 'sig1', type: 'signal.rule', params: { rule: 'rsi < 40 and macd_hist > 0 -> long; rsi > 60 and macd_hist < 0 -> short' }, inputs: ['rsi1', 'macd1'] },
      { id: 'size1', type: 'sizing.vol_target', params: { target_vol: 0.20, lookback: 20, max_position: 1.5 }, inputs: ['sig1'] },
      { id: 'risk1', type: 'risk.stop_take', params: { stop_atr_mult: 2.5, take_atr_mult: 4.0 }, inputs: ['size1', 'atr1'] },
      { id: 'exec1', type: 'exec.market', params: { slippage_bps: 8, fee_bps: 3 }, inputs: ['risk1'] }
    ],
    outputs: ['exec1'],
    version: 1,
    tags: ['demo', 'advanced', 'multi-indicator'],
    is_demo: true
  }
]

export default function NavigatorSidebar({ currentGraph, onGraphSelect, onClose }: NavigatorSidebarProps) {
  const [graphs, setGraphs] = useState<any[]>([])
  const [runs, setRuns] = useState<any[]>([])
  const [activeSection, setActiveSection] = useState<'projects' | 'strategies' | 'runs'>('strategies')
  const [showDemos, setShowDemos] = useState(true)
  const [showNewStrategyModal, setShowNewStrategyModal] = useState(false)
  const [newStrategyName, setNewStrategyName] = useState('')
  const [newStrategyDescription, setNewStrategyDescription] = useState('')

  useEffect(() => {
    fetchGraphs()
    fetchRuns()
    
    // Listen for refresh events from save operations
    const handleRefresh = () => {
      fetchGraphs()
    }
    
    window.addEventListener('refreshNavigator', handleRefresh)
    return () => window.removeEventListener('refreshNavigator', handleRefresh)
  }, [])

  const fetchGraphs = async () => {
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/graphs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setGraphs(data)
      }
    } catch (error) {
      console.error('Failed to fetch graphs:', error)
    }
  }

  const fetchRuns = async () => {
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/runs?limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setRuns(data)
      }
    } catch (error) {
      console.error('Failed to fetch runs:', error)
    }
  }

  const handleDeleteGraph = async (graphId: string, graphName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm(`Delete strategy "${graphName}"?\n\nThis action cannot be undone.`)) {
      return
    }

    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/graphs/${graphId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        toast.success(`Deleted "${graphName}"`)
        fetchGraphs() // Refresh list
        if (currentGraph?.id === graphId) {
          onGraphSelect(null) // Clear selection
        }
      } else {
        throw new Error('Delete failed')
      }
    } catch (error) {
      console.error('Failed to delete graph:', error)
      toast.error('Failed to delete strategy')
    }
  }

  const handleCreateStrategy = async () => {
    if (!newStrategyName.trim()) {
      toast.error('Please enter a strategy name')
      return
    }

    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/graphs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newStrategyName,
          description: newStrategyDescription,
          nodes: [
            {
              id: 'data1',
              type: 'data.loader',
              params: { symbol: 'BTC/USDT', timeframe: '1m', start_date: '2024-01-01', end_date: '2024-03-31' },
              inputs: [],
              position: { x: 100, y: 100 }
            }
          ],
          edges: [],
          outputs: ['data1'],
          tags: ['user-created']
        })
      })

      if (response.ok) {
        const newGraph = await response.json()
        toast.success(`Strategy "${newStrategyName}" created!`)
        setShowNewStrategyModal(false)
        setNewStrategyName('')
        setNewStrategyDescription('')
        fetchGraphs()
        onGraphSelect(newGraph)
      } else {
        throw new Error('Failed to create strategy')
      }
    } catch (error) {
      console.error('Failed to create strategy:', error)
      toast.error('Failed to create strategy')
    }
  }

  return (
    <div className="w-64 border-r border-border bg-card flex flex-col" style={{ height: '100%' }}>
      {/* Header */}
      <div className="p-4 border-b border-border flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Navigator</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            ×
          </button>
        </div>
        
        <Button size="sm" className="w-full" onClick={() => setShowNewStrategyModal(true)}>
          <PlusIcon className="h-4 w-4 mr-2" />
          New Strategy
        </Button>
      </div>

      {/* New Strategy Modal */}
      {showNewStrategyModal && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowNewStrategyModal(false)}>
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Create New Strategy</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Strategy Name *</label>
                <input
                  type="text"
                  value={newStrategyName}
                  onChange={(e) => setNewStrategyName(e.target.value)}
                  placeholder="My Trading Strategy"
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-brand-dark-teal"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description (optional)</label>
                <textarea
                  value={newStrategyDescription}
                  onChange={(e) => setNewStrategyDescription(e.target.value)}
                  placeholder="Describe your strategy..."
                  rows={3}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-brand-dark-teal resize-none"
                />
              </div>

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => {
                  setShowNewStrategyModal(false)
                  setNewStrategyName('')
                  setNewStrategyDescription('')
                }}>
                  Cancel
                </Button>
                <Button onClick={handleCreateStrategy} disabled={!newStrategyName.trim()}>
                  Create Strategy
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section Tabs */}
      <div className="flex border-b border-border flex-shrink-0">
        {[
          { id: 'strategies' as const, label: 'Strategies', icon: RectangleStackIcon },
          { id: 'runs' as const, label: 'Runs', icon: BeakerIcon }
        ].map(section => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`
              flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium transition-colors
              ${activeSection === section.id 
                ? 'text-brand-dark-teal border-b-2 border-brand-dark-teal' 
                : 'text-muted-foreground hover:text-foreground'
              }
            `}
          >
            <section.icon className="h-4 w-4" />
            {section.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2 custom-scrollbar">
        {activeSection === 'strategies' && (
          <div className="space-y-3">
            {/* Demo Strategies */}
            {showDemos && (
              <div>
                <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase flex items-center justify-between">
                  <span>Demo Strategies</span>
                  <button 
                    onClick={() => setShowDemos(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Hide
                  </button>
                </div>
                <div className="space-y-1">
                  {DEMO_STRATEGIES.map(demo => (
                    <button
                      key={demo.id}
                      onClick={() => onGraphSelect(demo)}
                      className={`
                        w-full text-left p-3 rounded-lg transition-colors border
                        ${currentGraph?.id === demo.id 
                          ? 'bg-brand-bright-yellow/10 border-brand-bright-yellow/40' 
                          : 'border-dashed border-border/50 hover:bg-muted/50 hover:border-border'
                        }
                      `}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="font-medium truncate">{demo.name}</div>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-brand-bright-yellow/20 text-brand-bright-yellow">
                              DEMO
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground truncate mt-1">
                            {demo.description}
                          </div>
                          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                            <span>{demo.nodes?.length || 0} blocks</span>
                            {demo.tags && demo.tags.slice(1).map(tag => (
                              <span key={tag}>• {tag}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* User Strategies */}
            {graphs.length > 0 && (
              <div>
                <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">
                  Your Strategies
                </div>
                <div className="space-y-1">
                  {graphs.map(graph => (
                <div
                  key={graph.id}
                  className={`
                    group relative w-full text-left p-3 rounded-lg transition-colors cursor-pointer
                    ${currentGraph?.id === graph.id 
                      ? 'bg-brand-dark-teal/10 border border-brand-dark-teal/20' 
                      : 'hover:bg-muted/50'
                    }
                  `}
                  onClick={() => onGraphSelect(graph)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{graph.name}</div>
                      {graph.description && (
                        <div className="text-xs text-muted-foreground truncate mt-1">
                          {graph.description}
                        </div>
                      )}
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                        <span>{graph.nodes?.length || 0} blocks</span>
                        <span>•</span>
                        <span>v{graph.version}</span>
                      </div>
                    </div>
                    
                    {/* Delete button */}
                    <button
                      onClick={(e) => handleDeleteGraph(graph.id, graph.name, e)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-danger-500/10 rounded"
                      title="Delete strategy"
                    >
                      <TrashIcon className="h-4 w-4 text-danger-600" />
                    </button>
                  </div>
                </div>
              ))}
                </div>
              </div>
            )}

            {graphs.length === 0 && !showDemos && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                <RectangleStackIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <div>No strategies yet</div>
                <button 
                  onClick={() => setShowDemos(true)}
                  className="text-brand-dark-teal hover:underline text-xs mt-2"
                >
                  Show demo strategies
                </button>
              </div>
            )}
          </div>
        )}

        {activeSection === 'runs' && (
          <div className="space-y-1">
            {runs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                <BeakerIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                No runs yet
              </div>
            ) : (
              runs.map(run => (
                <div
                  key={run.id}
                  className="p-3 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium truncate">{run.strategy_name}</div>
                    <div className={`
                      text-xs px-2 py-0.5 rounded-full
                      ${run.status === 'completed' ? 'bg-success-500/10 text-success-600' :
                        run.status === 'running' ? 'bg-blue-500/10 text-blue-600' :
                        run.status === 'failed' ? 'bg-danger-500/10 text-danger-600' :
                        'bg-muted text-muted-foreground'
                      }
                    `}>
                      {run.status}
                    </div>
                  </div>
                  
                  {run.sharpe !== null && (
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <div className="text-muted-foreground">Sharpe</div>
                        <div className="font-medium">{run.sharpe?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">CAGR</div>
                        <div className="font-medium">{(run.cagr * 100)?.toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">DD</div>
                        <div className="font-medium">{(run.max_dd * 100)?.toFixed(1)}%</div>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                    <ClockIcon className="h-3 w-3" />
                    {new Date(run.created_at).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

