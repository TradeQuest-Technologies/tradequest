'use client'

import { Fragment, useState, useMemo, useRef, useEffect } from 'react'
import { Dialog, Transition, Tab } from '@headlessui/react'
import {
  XMarkIcon,
  ChartBarIcon,
  TableCellsIcon,
  AdjustmentsHorizontalIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  ShieldExclamationIcon,
  BeakerIcon,
  AdjustmentsVerticalIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { Line } from 'react-chartjs-2'
import RiskAnalysisTab from './RiskAnalysisTab'
import ValidationTab from './ValidationTab'
import OptimizerTab from './OptimizerTab'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface Trade {
  entry_time: string
  exit_time: string
  symbol?: string
  side: 'long' | 'short'
  entry_price: number
  exit_price: number
  quantity: number
  pnl: number
  pnl_pct: number
  fees: number
  slippage: number
  mfe: number
  mae: number
  holding_time_hours: number
}

interface BacktestRun {
  id: string
  strategy_graph_id: string
  config: any
  status: string
  progress: number
  metrics?: {
    cagr?: number
    total_return?: number
    sharpe_ratio?: number
    sortino_ratio?: number
    calmar_ratio?: number
    max_drawdown?: number
    max_drawdown_duration?: number
    win_rate?: number
    profit_factor?: number
    total_trades?: number
    avg_win?: number
    avg_loss?: number
    expectancy?: number
    exposure_pct?: number
    turnover?: number
    total_fees?: number
  }
  equity_curve?: Array<{
    timestamp: string
    equity: number
    drawdown_pct: number
    trade_count: number
  }>
  trades?: Trade[]
  warnings?: Array<{
    type: string
    message: string
    severity: string
  }>
  started_at?: string
  finished_at?: string
  duration_seconds?: number
  created_at: string
}

interface AdjustmentParams {
  leverage: number
  positionSizePercent: number
  stopLossPercent: number | null
  takeProfitPercent: number | null
  minHoldingHours: number | null
  maxHoldingHours: number | null
  filterLosers: boolean
  filterWinners: boolean
}

interface Props {
  run: BacktestRun | null
  isOpen: boolean
  onClose: () => void
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  toolCalls?: ToolCallDisplay[]
  charts?: ChartDisplay[]
  parameterUpdates?: ParameterUpdateDisplay[]
  backtestTriggered?: BacktestTriggeredDisplay
}

interface ToolCallDisplay {
  id: string
  tool: string
  params: any
  result?: any
  success?: boolean
  error?: string
  expanded?: boolean
}

interface ChartDisplay {
  id: string
  url: string
  title: string
  description?: string
}

interface ParameterUpdateDisplay {
  params: any
  reasoning: string
  approved?: boolean
}

interface BacktestTriggeredDisplay {
  runId: string
  config: any
  status?: string
}

export default function BacktestResultsModal({ run, isOpen, onClose }: Props) {
  const [adjustments, setAdjustments] = useState<AdjustmentParams>({
    leverage: 1,
    positionSizePercent: 100,
    stopLossPercent: null,
    takeProfitPercent: null,
    minHoldingHours: null,
    maxHoldingHours: null,
    filterLosers: false,
    filterWinners: false,
  })
  
  // AI Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "👋 Hello! I'm your **Advanced Quant Copilot** - an agentic AI system with full access to your backtest data.\n\n**What I can do:**\n- 📊 Analyze trades, metrics, and patterns\n- 🔍 Run statistical tests and validations\n- 📈 Generate custom visualizations\n- ⚙️ Modify parameters and optimize settings\n- 🚀 Trigger new backtest runs\n- 🎯 Provide data-driven recommendations\n\nYou'll see me using tools in real-time to analyze your strategy. Ask me anything!",
      timestamp: new Date()
    }
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  
  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])
  
  // Handle AI Chat submission with streaming
  const handleChatSubmit = async () => {
    if (!chatInput.trim() || !run || chatLoading) return
    
    const userMessage: ChatMessage = {
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date()
    }
    
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setChatLoading(true)
    
    // Create assistant message placeholder for streaming
    const assistantMessageId = Date.now()
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      toolCalls: [],
      charts: [],
      parameterUpdates: []
    }
    
    setChatMessages(prev => [...prev, assistantMessage])
    
    try {
      const token = localStorage.getItem('tq_session')
      
      // Prepare context
      const context = {
        metrics: run.metrics,
        config: run.config,
        total_trades: run.trades?.length || 0,
        warnings: run.warnings || []
      }
      
      const response = await fetch('/api/v1/backtest/v2/analyze-streaming', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          run_id: run.id,
          user_question: userMessage.content,
          context: context,
          chat_history: chatMessages.slice(-5).map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to start streaming analysis')
      }
      
      // Process SSE stream
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body')
      }
      
      console.log('[Chat] Starting SSE reader loop')
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('[Chat] Stream ended, processing remaining buffer:', buffer.length, 'chars')
          console.log('[Chat] Buffer sample:', buffer.substring(0, 300))
          console.log('[Chat] Buffer char codes around position 200:', 
            buffer.substring(195, 205).split('').map(c => c.charCodeAt(0)))
          console.log('[Chat] Buffer has \\n\\n count:', (buffer.match(/\n\n/g) || []).length)
          console.log('[Chat] Buffer has literal backslash-n count:', (buffer.match(/\\n\\n/g) || []).length)
          // Process all remaining events in buffer
          if (buffer.trim()) {
            const finalLines = buffer.split('\n\n')
            console.log('[Chat] Final buffer has', finalLines.length, 'lines after split')
            
            for (let i = 0; i < finalLines.length; i++) {
              const line = finalLines[i]
              console.log(`[Chat] Line ${i}:`, line.substring(0, 50), 'starts with data:', line.startsWith('data:'))
              if (!line.trim() || !line.startsWith('data: ')) {
                console.log('[Chat] Skipping line', i)
                continue
              }
              
              try {
                const event = JSON.parse(line.slice(6))
                console.log('[Chat] Processing final event:', event.type)
                
                setChatMessages(prev => {
                  const updated = [...prev]
                  const lastMsg = updated[updated.length - 1]
                  if (lastMsg.role !== 'assistant') return prev
                  
                  switch (event.type) {
                    case 'tool_call':
                      lastMsg.toolCalls = lastMsg.toolCalls || []
                      lastMsg.toolCalls.push({
                        id: event.call_id,
                        tool: event.tool,
                        params: event.params,
                        expanded: false
                      })
                      break
                    
                    case 'tool_result':
                      const toolCall = lastMsg.toolCalls?.find(tc => tc.id === event.call_id)
                      if (toolCall) {
                        toolCall.result = event.result
                        toolCall.success = event.success
                        toolCall.error = event.error
                      }
                      break
                    
                    case 'message':
                      console.log('[Chat] Adding message content:', event.content?.substring(0, 100))
                      lastMsg.content += event.content
                      break
                    
                    case 'chart':
                      lastMsg.charts = lastMsg.charts || []
                      lastMsg.charts.push({
                        id: event.chart_id,
                        url: event.url,
                        title: event.title,
                        description: event.description
                      })
                      break
                    
                    case 'done':
                      // Stream complete
                      break
                  }
                  
                  return updated
                })
              } catch (e) {
                console.error('Failed to parse final event:', e, line.substring(0, 200))
              }
            }
          }
          break
        }
        
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        console.log('[Chat] Received chunk, buffer length:', buffer.length)
        
        // Split by SSE delimiter, but don't pop last element during streaming
        const lines = buffer.split('\n\n')
        
        // Keep incomplete last line in buffer for next chunk (unless stream ended)
        if (lines[lines.length - 1] && !lines[lines.length - 1].includes('\n\n')) {
          buffer = lines.pop() || ''
        } else {
          buffer = ''
        }
        
        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) {
            continue
          }
          
          try {
            const event = JSON.parse(line.slice(6))
            console.log('[Chat] Received SSE event:', event.type, event)
            
            // Update assistant message based on event type
            setChatMessages(prev => {
              const updated = [...prev]
              const lastMsg = updated[updated.length - 1]
              
              if (lastMsg.role !== 'assistant') return prev
              
              switch (event.type) {
                case 'tool_call':
                  lastMsg.toolCalls = lastMsg.toolCalls || []
                  lastMsg.toolCalls.push({
                    id: event.call_id,
                    tool: event.tool,
                    params: event.params,
                    expanded: false
                  })
                  break
                
                case 'tool_result':
                  const toolCall = lastMsg.toolCalls?.find(tc => tc.id === event.call_id)
                  if (toolCall) {
                    toolCall.result = event.result
                    toolCall.success = event.success
                    toolCall.error = event.error
                  }
                  break
                
                case 'message':
                  console.log('[Chat] Appending message content:', event.content)
                  lastMsg.content += event.content
                  console.log('[Chat] Updated content:', lastMsg.content)
                  break
                
                case 'chart':
                  lastMsg.charts = lastMsg.charts || []
                  lastMsg.charts.push({
                    id: event.chart_id,
                    url: event.url,
                    title: event.title,
                    description: event.description
                  })
                  break
                
                case 'parameter_update':
                  lastMsg.parameterUpdates = lastMsg.parameterUpdates || []
                  lastMsg.parameterUpdates.push({
                    params: event.params,
                    reasoning: event.reasoning,
                    approved: false
                  })
                  break
                
                case 'backtest_triggered':
                  lastMsg.backtestTriggered = {
                    runId: event.run_id,
                    config: event.config
                  }
                  break
                
                case 'error':
                  lastMsg.content += `\n\n⚠️ Error: ${event.error}`
                  break
                
                case 'done':
                  // Stream complete
                  break
              }
              
              return updated
            })
          } catch (e) {
            console.error('Failed to parse SSE event:', e)
          }
        }
      }
      
    } catch (error) {
      console.error('Streaming chat error:', error)
      toast.error('Failed to get AI response. Please try again.')
      
      setChatMessages(prev => {
        const updated = [...prev]
        const lastMsg = updated[updated.length - 1]
        if (lastMsg.role === 'assistant') {
          lastMsg.content = "I'm having trouble analyzing your backtest right now. Please try asking your question again."
        }
        return updated
      })
    } finally {
      setChatLoading(false)
    }
  }
  
  // Handle parameter approval
  const handleParameterApproval = (messageIndex: number, updateIndex: number, approved: boolean) => {
    setChatMessages(prev => {
      const updated = [...prev]
      const msg = updated[messageIndex]
      if (msg.parameterUpdates && msg.parameterUpdates[updateIndex]) {
        msg.parameterUpdates[updateIndex].approved = approved
        
        if (approved) {
          // Apply the parameter updates to adjustments state
          const params = msg.parameterUpdates[updateIndex].params
          setAdjustments(curr => ({
            ...curr,
            ...params
          }))
          toast.success('Parameters updated!')
        }
      }
      return updated
    })
  }
  
  // Toggle tool call expansion
  const toggleToolCallExpanded = (messageIndex: number, toolCallIndex: number) => {
    setChatMessages(prev => {
      const updated = [...prev]
      const msg = updated[messageIndex]
      if (msg.toolCalls && msg.toolCalls[toolCallIndex]) {
        msg.toolCalls[toolCallIndex].expanded = !msg.toolCalls[toolCallIndex].expanded
      }
      return updated
    })
  }

  // Calculate adjusted metrics based on parameter changes
  const adjustedResults = useMemo(() => {
    if (!run?.trades || run.trades.length === 0) {
      return null
    }

    const initialCapital = run.config?.initial_capital || 10000
    let equity = initialCapital
    const equityCurve: number[] = [equity]
    let filteredTrades = [...run.trades]

    // Apply filters
    if (adjustments.filterLosers) {
      filteredTrades = filteredTrades.filter(t => t.pnl >= 0)
    }
    if (adjustments.filterWinners) {
      filteredTrades = filteredTrades.filter(t => t.pnl < 0)
    }
    if (adjustments.minHoldingHours !== null) {
      filteredTrades = filteredTrades.filter(t => t.holding_time_hours >= adjustments.minHoldingHours!)
    }
    if (adjustments.maxHoldingHours !== null) {
      filteredTrades = filteredTrades.filter(t => t.holding_time_hours <= adjustments.maxHoldingHours!)
    }

    // Recalculate with adjustments
    const adjustedTrades = filteredTrades.map(trade => {
      let adjustedPnl = trade.pnl
      
      // Apply leverage
      adjustedPnl *= adjustments.leverage
      
      // Apply position sizing
      adjustedPnl *= (adjustments.positionSizePercent / 100)
      
      // Apply stop loss
      if (adjustments.stopLossPercent !== null) {
        const maxLoss = -(trade.entry_price * trade.quantity * (adjustments.stopLossPercent / 100))
        if (adjustedPnl < maxLoss) {
          adjustedPnl = maxLoss
        }
      }
      
      // Apply take profit
      if (adjustments.takeProfitPercent !== null) {
        const maxGain = trade.entry_price * trade.quantity * (adjustments.takeProfitPercent / 100)
        if (adjustedPnl > maxGain) {
          adjustedPnl = maxGain
        }
      }

      return {
        ...trade,
        adjusted_pnl: adjustedPnl,
        adjusted_pnl_pct: (adjustedPnl / (trade.entry_price * trade.quantity)) * 100,
      }
    })

    // Calculate metrics
    let wins = 0
    let losses = 0
    let totalWin = 0
    let totalLoss = 0
    let maxDrawdown = 0
    let peak = equity

    adjustedTrades.forEach(trade => {
      equity += trade.adjusted_pnl
      equityCurve.push(equity)

      if (equity > peak) {
        peak = equity
      }
      const drawdown = ((peak - equity) / peak) * 100
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown
      }

      if (trade.adjusted_pnl > 0) {
        wins++
        totalWin += trade.adjusted_pnl
      } else {
        losses++
        totalLoss += Math.abs(trade.adjusted_pnl)
      }
    })

    const totalReturn = equity - initialCapital
    const totalReturnPct = (totalReturn / initialCapital) * 100
    const winRate = adjustedTrades.length > 0 ? (wins / adjustedTrades.length) * 100 : 0
    const avgWin = wins > 0 ? totalWin / wins : 0
    const avgLoss = losses > 0 ? totalLoss / losses : 0
    const profitFactor = totalLoss > 0 ? totalWin / totalLoss : 0
    const expectancy = adjustedTrades.length > 0 
      ? adjustedTrades.reduce((sum, t) => sum + t.adjusted_pnl, 0) / adjustedTrades.length 
      : 0

    return {
      trades: adjustedTrades,
      equityCurve,
      finalEquity: equity,
      totalReturn,
      totalReturnPct,
      winRate,
      profitFactor,
      maxDrawdown,
      avgWin,
      avgLoss,
      expectancy,
      totalTrades: adjustedTrades.length,
    }
  }, [run, adjustments])

  if (!run) return null

  const metrics = run.metrics || {}

  // Format number helpers
  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null || isNaN(val)) return 'N/A'
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (val?: number) => {
    if (val === undefined || val === null || isNaN(val)) return 'N/A'
    return `${val.toFixed(2)}%`
  }

  const formatNumber = (val?: number, decimals = 2) => {
    if (val === undefined || val === null || isNaN(val)) return 'N/A'
    return val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  }

  // Equity chart data
  const equityChartData = {
    labels: run.equity_curve?.map(p => new Date(p.timestamp).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Original Strategy',
        data: run.equity_curve?.map(p => p.equity) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.1,
      },
      ...(adjustedResults ? [{
        label: 'Adjusted Strategy',
        data: adjustedResults.equityCurve,
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.1,
      }] : []),
    ],
  }

  const equityChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Equity Curve',
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value: any) {
            return '$' + value.toLocaleString()
          }
        }
      }
    },
  }

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
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-7xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 shadow-xl transition-all">
                {/* Header */}
                <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                  <div>
                    <Dialog.Title className="text-2xl font-bold text-gray-900 dark:text-white">
                      Backtest Results
                    </Dialog.Title>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {run.config?.symbol} • {run.config?.timeframe} • {new Date(run.created_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={onClose}
                    className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <XMarkIcon className="h-6 w-6 text-gray-500" />
                  </button>
                </div>

                {/* Tabs */}
                <Tab.Group>
                  <Tab.List className="flex border-b border-gray-200 dark:border-gray-700 px-6 bg-gray-50 dark:bg-gray-900/50">
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <ChartBarIcon className="h-5 w-5" />
                        Overview
                      </div>
                    </Tab>
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <TableCellsIcon className="h-5 w-5" />
                        Trades ({run.trades?.length || 0})
                      </div>
                    </Tab>
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <AdjustmentsHorizontalIcon className="h-5 w-5" />
                        Adjust Parameters
                      </div>
                    </Tab>
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <ChatBubbleLeftRightIcon className="h-5 w-5" />
                        AI Chat
                      </div>
                    </Tab>
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <ShieldExclamationIcon className="h-5 w-5" />
                        Risk Analysis
                      </div>
                    </Tab>
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <BeakerIcon className="h-5 w-5" />
                        Validation
                      </div>
                    </Tab>
                    <Tab className={({ selected }) =>
                      `px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        selected
                          ? 'border-brand-dark-teal text-brand-dark-teal'
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      }`
                    }>
                      <div className="flex items-center gap-2">
                        <AdjustmentsVerticalIcon className="h-5 w-5" />
                        Optimizer
                      </div>
                    </Tab>
                  </Tab.List>

                  <Tab.Panels className="p-6 max-h-[calc(100vh-16rem)] overflow-y-auto">
                    {/* Overview Tab */}
                    <Tab.Panel>
                      <div className="space-y-6">
                        {/* Key Metrics Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <MetricCard
                            label="Total Return"
                            value={formatCurrency(metrics.total_return)}
                            subValue={formatPercent(metrics.total_return && run.config?.initial_capital ? (metrics.total_return / run.config.initial_capital) * 100 : undefined)}
                            trend={metrics.total_return && metrics.total_return > 0 ? 'up' : 'down'}
                          />
                          <MetricCard
                            label="Sharpe Ratio"
                            value={formatNumber(metrics.sharpe_ratio)}
                            trend={metrics.sharpe_ratio && metrics.sharpe_ratio > 1 ? 'up' : metrics.sharpe_ratio && metrics.sharpe_ratio > 0 ? 'neutral' : 'down'}
                          />
                          <MetricCard
                            label="Max Drawdown"
                            value={formatPercent(metrics.max_drawdown)}
                            trend="down"
                          />
                          <MetricCard
                            label="Win Rate"
                            value={formatPercent(metrics.win_rate)}
                            trend={metrics.win_rate && metrics.win_rate > 50 ? 'up' : 'down'}
                          />
                        </div>

                        {/* Equity Curve Chart */}
                        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                          <div style={{ height: '400px' }}>
                            <Line data={equityChartData} options={equityChartOptions} />
                          </div>
                        </div>

                        {/* Detailed Metrics */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Performance Metrics</h3>
                            <div className="space-y-3">
                              <MetricRow label="CAGR" value={formatPercent(metrics.cagr)} />
                              <MetricRow label="Sortino Ratio" value={formatNumber(metrics.sortino_ratio)} />
                              <MetricRow label="Calmar Ratio" value={formatNumber(metrics.calmar_ratio)} />
                              <MetricRow label="Profit Factor" value={formatNumber(metrics.profit_factor)} />
                              <MetricRow label="Expectancy" value={formatCurrency(metrics.expectancy)} />
                            </div>
                          </div>

                          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Trade Statistics</h3>
                            <div className="space-y-3">
                              <MetricRow label="Total Trades" value={formatNumber(metrics.total_trades, 0)} />
                              <MetricRow label="Avg Win" value={formatCurrency(metrics.avg_win)} />
                              <MetricRow label="Avg Loss" value={formatCurrency(metrics.avg_loss)} />
                              <MetricRow label="Total Fees" value={formatCurrency(metrics.total_fees)} />
                              <MetricRow label="Exposure" value={formatPercent(metrics.exposure_pct)} />
                            </div>
                          </div>
                        </div>

                        {/* Warnings */}
                        {run.warnings && run.warnings.length > 0 && (
                          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                            <h3 className="text-sm font-semibold text-yellow-900 dark:text-yellow-200 mb-2">Warnings</h3>
                            <ul className="space-y-1">
                              {run.warnings.map((warning, i) => (
                                <li key={i} className="text-sm text-yellow-800 dark:text-yellow-300">
                                  • {warning.message}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </Tab.Panel>

                    {/* Trades Tab */}
                    <Tab.Panel>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                          <thead className="bg-gray-50 dark:bg-gray-900">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Entry</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Exit</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Symbol</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Side</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Entry $</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Exit $</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">PnL</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">PnL %</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Duration</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {run.trades?.map((trade, i) => (
                              <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
                                  {new Date(trade.entry_time).toLocaleString()}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
                                  {new Date(trade.exit_time).toLocaleString()}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                                  {trade.symbol || 'N/A'}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                                    trade.side === 'long' 
                                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                                  }`}>
                                    {trade.side.toUpperCase()}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 text-right">
                                  ${trade.entry_price.toLocaleString()}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 text-right">
                                  ${trade.exit_price.toLocaleString()}
                                </td>
                                <td className={`px-4 py-3 text-sm text-right font-medium ${
                                  trade.pnl > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                }`}>
                                  {formatCurrency(trade.pnl)}
                                </td>
                                <td className={`px-4 py-3 text-sm text-right font-medium ${
                                  trade.pnl_pct > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                }`}>
                                  {formatPercent(trade.pnl_pct)}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 text-right">
                                  {trade.holding_time_hours.toFixed(2)}h
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Tab.Panel>

                    {/* Adjust Parameters Tab */}
                    <Tab.Panel>
                      <div className="space-y-6">
                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                          <p className="text-sm text-blue-900 dark:text-blue-200">
                            <strong>Experiment with different parameters</strong> without re-running the backtest. 
                            Adjust leverage, position sizing, risk management rules, and filters to see how they would have affected your results.
                          </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {/* Position Sizing */}
                          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                              <CurrencyDollarIcon className="h-5 w-5" />
                              Position Sizing
                            </h3>
                            <div className="space-y-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Leverage: {adjustments.leverage}x
                                </label>
                                <input
                                  type="range"
                                  min="1"
                                  max="10"
                                  step="0.5"
                                  value={adjustments.leverage}
                                  onChange={(e) => setAdjustments({ ...adjustments, leverage: parseFloat(e.target.value) })}
                                  className="w-full"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Position Size: {adjustments.positionSizePercent}%
                                </label>
                                <input
                                  type="range"
                                  min="10"
                                  max="100"
                                  step="5"
                                  value={adjustments.positionSizePercent}
                                  onChange={(e) => setAdjustments({ ...adjustments, positionSizePercent: parseFloat(e.target.value) })}
                                  className="w-full"
                                />
                              </div>
                            </div>
                          </div>

                          {/* Risk Management */}
                          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Risk Management</h3>
                            <div className="space-y-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Stop Loss %
                                </label>
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  step="0.5"
                                  value={adjustments.stopLossPercent || ''}
                                  onChange={(e) => setAdjustments({ ...adjustments, stopLossPercent: e.target.value ? parseFloat(e.target.value) : null })}
                                  placeholder="None"
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Take Profit %
                                </label>
                                <input
                                  type="number"
                                  min="0"
                                  max="1000"
                                  step="0.5"
                                  value={adjustments.takeProfitPercent || ''}
                                  onChange={(e) => setAdjustments({ ...adjustments, takeProfitPercent: e.target.value ? parseFloat(e.target.value) : null })}
                                  placeholder="None"
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                />
                              </div>
                            </div>
                          </div>

                          {/* Time Filters */}
                          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                              <ClockIcon className="h-5 w-5" />
                              Time Filters
                            </h3>
                            <div className="space-y-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Min Holding Hours
                                </label>
                                <input
                                  type="number"
                                  min="0"
                                  step="0.1"
                                  value={adjustments.minHoldingHours || ''}
                                  onChange={(e) => setAdjustments({ ...adjustments, minHoldingHours: e.target.value ? parseFloat(e.target.value) : null })}
                                  placeholder="None"
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Max Holding Hours
                                </label>
                                <input
                                  type="number"
                                  min="0"
                                  step="0.1"
                                  value={adjustments.maxHoldingHours || ''}
                                  onChange={(e) => setAdjustments({ ...adjustments, maxHoldingHours: e.target.value ? parseFloat(e.target.value) : null })}
                                  placeholder="None"
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                />
                              </div>
                            </div>
                          </div>

                          {/* Trade Filters */}
                          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Trade Filters</h3>
                            <div className="space-y-4">
                              <label className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  checked={adjustments.filterLosers}
                                  onChange={(e) => setAdjustments({ ...adjustments, filterLosers: e.target.checked })}
                                  className="rounded border-gray-300 text-brand-dark-teal focus:ring-brand-dark-teal"
                                />
                                <span className="text-sm text-gray-700 dark:text-gray-300">Exclude Losing Trades</span>
                              </label>
                              <label className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  checked={adjustments.filterWinners}
                                  onChange={(e) => setAdjustments({ ...adjustments, filterWinners: e.target.checked })}
                                  className="rounded border-gray-300 text-brand-dark-teal focus:ring-brand-dark-teal"
                                />
                                <span className="text-sm text-gray-700 dark:text-gray-300">Exclude Winning Trades</span>
                              </label>
                            </div>
                          </div>
                        </div>

                        {/* Adjusted Results */}
                        {adjustedResults && (
                          <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Adjusted Results Preview</h3>
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                              <div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Total Return</p>
                                <p className={`text-lg font-bold ${adjustedResults.totalReturn > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {formatCurrency(adjustedResults.totalReturn)}
                                </p>
                                <p className="text-xs text-gray-500">{formatPercent(adjustedResults.totalReturnPct)}</p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Win Rate</p>
                                <p className="text-lg font-bold text-gray-900 dark:text-white">
                                  {formatPercent(adjustedResults.winRate)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Profit Factor</p>
                                <p className="text-lg font-bold text-gray-900 dark:text-white">
                                  {formatNumber(adjustedResults.profitFactor)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Max DD</p>
                                <p className="text-lg font-bold text-red-600">
                                  {formatPercent(adjustedResults.maxDrawdown)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Total Trades</p>
                                <p className="text-lg font-bold text-gray-900 dark:text-white">
                                  {adjustedResults.totalTrades}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </Tab.Panel>

                    {/* AI Chat Tab */}
                    <Tab.Panel>
                      <div className="flex flex-col h-[calc(100vh-20rem)]">
                        {/* Chat Header */}
                        <div className="bg-gradient-to-r from-brand-dark-teal/10 to-brand-bright-yellow/10 border border-brand-dark-teal/20 rounded-lg p-4 mb-4">
                          <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow rounded-lg">
                              <SparklesIcon className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900 dark:text-white">AI Trading Analyst</h3>
                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                Ask questions about your backtest results
                              </p>
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <button
                              onClick={() => setChatInput("Why did this strategy lose money?")}
                              className="text-xs px-3 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                              Why did this strategy lose money?
                            </button>
                            <button
                              onClick={() => setChatInput("What patterns do you see in the losing trades?")}
                              className="text-xs px-3 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                              Analyze losing trades
                            </button>
                            <button
                              onClick={() => setChatInput("How can I improve this strategy?")}
                              className="text-xs px-3 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                              How to improve?
                            </button>
                            <button
                              onClick={() => setChatInput("What timeframes or symbols would work better?")}
                              className="text-xs px-3 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                              Better timeframes?
                            </button>
                          </div>
                        </div>

                        {/* Chat Messages */}
                        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 custom-scrollbar">
                          {chatMessages.map((message, msgIndex) => (
                            <div
                              key={msgIndex}
                              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              <div className={`max-w-[85%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                                <div className="flex items-start gap-3">
                                  {message.role === 'assistant' && (
                                    <div className="p-2 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow rounded-full flex-shrink-0">
                                      <SparklesIcon className="h-4 w-4 text-white" />
                                    </div>
                                  )}
                                  
                                  <div className="flex-1 space-y-2">
                                    {/* Tool Calls */}
                                    {message.toolCalls && message.toolCalls.length > 0 && (
                                      <div className="space-y-2">
                                        {message.toolCalls.map((toolCall, tcIndex) => (
                                          <div key={toolCall.id} className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                              <div className="flex items-center gap-2">
                                                <div className={`h-2 w-2 rounded-full ${
                                                  toolCall.success === false ? 'bg-red-500' :
                                                  toolCall.result ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'
                                                }`} />
                                                <span className="text-xs font-mono text-gray-700 dark:text-gray-300">
                                                  {toolCall.tool}
                                                </span>
                                              </div>
                                              <button
                                                onClick={() => toggleToolCallExpanded(msgIndex, tcIndex)}
                                                className="text-xs text-brand-dark-teal hover:text-brand-bright-yellow"
                                              >
                                                {toolCall.expanded ? 'Hide' : 'Show'} details
                                              </button>
                                            </div>
                                            {toolCall.expanded && (
                                              <div className="mt-2 space-y-2 text-xs">
                                                <div>
                                                  <div className="font-semibold text-gray-600 dark:text-gray-400">Parameters:</div>
                                                  <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded mt-1 overflow-x-auto">
                                                    {JSON.stringify(toolCall.params, null, 2)}
                                                  </pre>
                                                </div>
                                                {toolCall.result && (
                                                  <div>
                                                    <div className="font-semibold text-gray-600 dark:text-gray-400">Result:</div>
                                                    <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded mt-1 overflow-x-auto max-h-48">
                                                      {JSON.stringify(toolCall.result, null, 2)}
                                                    </pre>
                                                  </div>
                                                )}
                                                {toolCall.error && (
                                                  <div className="text-red-600 dark:text-red-400">
                                                    Error: {toolCall.error}
                                                  </div>
                                                )}
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {/* Main Message Content */}
                                    {message.content && (
                                      <div
                                        className={`p-4 rounded-lg ${
                                          message.role === 'user'
                                            ? 'bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow text-white'
                                            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                                        }`}
                                      >
                                        <div className="whitespace-pre-wrap text-sm">
                                          {message.content.split('\n').map((line, i) => {
                                            // Simple markdown rendering
                                            if (line.startsWith('**') && line.endsWith('**')) {
                                              return <p key={i} className="font-bold mb-2">{line.slice(2, -2)}</p>
                                            } else if (line.startsWith('- ')) {
                                              return <li key={i} className="ml-4 mb-1">{line.slice(2)}</li>
                                            } else if (line.trim() === '') {
                                              return <br key={i} />
                                            } else {
                                              return <p key={i} className="mb-2">{line}</p>
                                            }
                                          })}
                                        </div>
                                      </div>
                                    )}
                                    
                                    {/* Charts */}
                                    {message.charts && message.charts.length > 0 && (
                                      <div className="space-y-2">
                                        {message.charts.map(chart => (
                                          <div key={chart.id} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                                            <div className="bg-gray-50 dark:bg-gray-900 px-3 py-2">
                                              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{chart.title}</h4>
                                              {chart.description && (
                                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{chart.description}</p>
                                              )}
                                            </div>
                                            <img 
                                              src={chart.url} 
                                              alt={chart.title}
                                              className="w-full"
                                            />
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {/* Parameter Updates */}
                                    {message.parameterUpdates && message.parameterUpdates.length > 0 && (
                                      <div className="space-y-2">
                                        {message.parameterUpdates.map((update, upIndex) => (
                                          <div key={upIndex} className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                                            <div className="flex items-start justify-between mb-2">
                                              <div className="flex items-center gap-2">
                                                <AdjustmentsHorizontalIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                                                <span className="text-sm font-semibold text-blue-900 dark:text-blue-200">
                                                  Parameter Update
                                                </span>
                                              </div>
                                              {!update.approved && (
                                                <div className="flex gap-2">
                                                  <button
                                                    onClick={() => handleParameterApproval(msgIndex, upIndex, true)}
                                                    className="text-xs px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                                                  >
                                                    Apply
                                                  </button>
                                                  <button
                                                    onClick={() => handleParameterApproval(msgIndex, upIndex, false)}
                                                    className="text-xs px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                                                  >
                                                    Reject
                                                  </button>
                                                </div>
                                              )}
                                              {update.approved && (
                                                <span className="text-xs text-green-600 dark:text-green-400 font-semibold">
                                                  ✓ Applied
                                                </span>
                                              )}
                                            </div>
                                            <p className="text-sm text-blue-800 dark:text-blue-300 mb-2">{update.reasoning}</p>
                                            <pre className="text-xs bg-white dark:bg-gray-800 p-2 rounded overflow-x-auto">
                                              {JSON.stringify(update.params, null, 2)}
                                            </pre>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {/* Backtest Triggered */}
                                    {message.backtestTriggered && (
                                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                          <ArrowTrendingUpIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                                          <span className="text-sm font-semibold text-green-900 dark:text-green-200">
                                            New Backtest Triggered
                                          </span>
                                        </div>
                                        <p className="text-sm text-green-800 dark:text-green-300">
                                          Run ID: <code className="bg-white dark:bg-gray-800 px-1 py-0.5 rounded">{message.backtestTriggered.runId}</code>
                                        </p>
                                        <button
                                          onClick={() => window.location.reload()}
                                          className="mt-2 text-xs px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                                        >
                                          View New Run
                                        </button>
                                      </div>
                                    )}
                                    
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                      {message.timestamp.toLocaleTimeString()}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                          
                          {chatLoading && (
                            <div className="flex justify-start">
                              <div className="max-w-[80%]">
                                <div className="flex items-start gap-3">
                                  <div className="p-2 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow rounded-full flex-shrink-0 animate-pulse">
                                    <SparklesIcon className="h-4 w-4 text-white" />
                                  </div>
                                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                                    <div className="flex items-center gap-2">
                                      <div className="animate-bounce h-2 w-2 bg-brand-dark-teal rounded-full" style={{ animationDelay: '0ms' }} />
                                      <div className="animate-bounce h-2 w-2 bg-brand-dark-teal rounded-full" style={{ animationDelay: '150ms' }} />
                                      <div className="animate-bounce h-2 w-2 bg-brand-dark-teal rounded-full" style={{ animationDelay: '300ms' }} />
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          <div ref={chatEndRef} />
                        </div>

                        {/* Chat Input */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                          <div className="flex items-end gap-3">
                            <textarea
                              value={chatInput}
                              onChange={(e) => setChatInput(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                  e.preventDefault()
                                  handleChatSubmit()
                                }
                              }}
                              placeholder="Ask me anything about your backtest results..."
                              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-transparent resize-none"
                              rows={2}
                              disabled={chatLoading}
                            />
                            <button
                              onClick={handleChatSubmit}
                              disabled={chatLoading || !chatInput.trim()}
                              className="px-6 py-3 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                              <PaperAirplaneIcon className="h-5 w-5" />
                              Send
                            </button>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            💡 Press Enter to send, Shift+Enter for new line
                          </p>
                        </div>
                      </div>
                    </Tab.Panel>

                    {/* Risk Analysis Tab */}
                    <Tab.Panel>
                      <RiskAnalysisTab run={run} />
                    </Tab.Panel>

                    {/* Validation Tab */}
                    <Tab.Panel>
                      <ValidationTab run={run} />
                    </Tab.Panel>

                    {/* Optimizer Tab */}
                    <Tab.Panel>
                      <OptimizerTab run={run} />
                    </Tab.Panel>
                  </Tab.Panels>
                </Tab.Group>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

// Helper Components
function MetricCard({ label, value, subValue, trend }: { label: string; value: string; subValue?: string; trend?: 'up' | 'down' | 'neutral' }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-gray-600 dark:text-gray-400">{label}</p>
        {trend && (
          <span className={`${
            trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
          }`}>
            {trend === 'up' ? <ArrowTrendingUpIcon className="h-4 w-4" /> : trend === 'down' ? <ArrowTrendingDownIcon className="h-4 w-4" /> : null}
          </span>
        )}
      </div>
      <p className={`text-2xl font-bold ${
        trend === 'up' ? 'text-green-600 dark:text-green-400' : trend === 'down' ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'
      }`}>
        {value}
      </p>
      {subValue && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subValue}</p>}
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800 last:border-0">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <span className="text-sm font-medium text-gray-900 dark:text-white">{value}</span>
    </div>
  )
}

