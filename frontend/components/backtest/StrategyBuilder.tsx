'use client'

import { useState, useCallback, useRef, useEffect, useLayoutEffect } from 'react'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import {
  PlusIcon,
  TrashIcon,
  ArrowsPointingOutIcon,
  Cog6ToothIcon,
  PlayIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Block {
  id: string
  type: string
  params: Record<string, any>
  position: { x: number; y: number }
  inputs: string[]
}

interface StrategyBuilderProps {
  graph: any
  onChange: (graph: any) => void
  onLog?: (type: string, message: string) => void
  onSave?: () => void
  onRunUpdate?: (run: any) => void
}

const BLOCK_LIBRARY = {
  data: [
    { type: 'data.loader', name: 'Data Loader', color: '#3b82f6' },
    { type: 'data.resampler', name: 'Resampler', color: '#3b82f6' },
  ],
  features: [
    { type: 'feature.rsi', name: 'RSI', color: '#8b5cf6' },
    { type: 'feature.macd', name: 'MACD', color: '#8b5cf6' },
    { type: 'feature.ma', name: 'Moving Average', color: '#8b5cf6' },
    { type: 'feature.atr', name: 'ATR', color: '#8b5cf6' },
  ],
  signals: [
    { type: 'signal.rule', name: 'Rule Signal', color: '#10b981' },
    { type: 'signal.crossover', name: 'Crossover', color: '#10b981' },
    { type: 'signal.threshold', name: 'Threshold', color: '#10b981' },
  ],
  sizing: [
    { type: 'sizing.fixed', name: 'Fixed Size', color: '#f59e0b' },
    { type: 'sizing.vol_target', name: 'Vol Target', color: '#f59e0b' },
  ],
  risk: [
    { type: 'risk.stop_take', name: 'Stop/Take', color: '#ef4444' },
    { type: 'risk.trailing', name: 'Trailing Stop', color: '#ef4444' },
  ],
  execution: [
    { type: 'exec.market', name: 'Market Order', color: '#06b6d4' },
    { type: 'exec.limit', name: 'Limit Order', color: '#06b6d4' },
  ]
}

export default function StrategyBuilder({ graph, onChange, onLog, onSave, onRunUpdate }: StrategyBuilderProps) {
  const [blocks, setBlocks] = useState<Block[]>([])
  const [selectedBlock, setSelectedBlock] = useState<string | null>(null)
  const [showLibrary, setShowLibrary] = useState(true)
  const [draggedBlock, setDraggedBlock] = useState<any>(null)
  const [draggedBlockId, setDraggedBlockId] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })
  const [scale, setScale] = useState(1)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null)
  const [connectionPreview, setConnectionPreview] = useState<{x: number, y: number} | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const canvasRef = useRef<HTMLDivElement>(null)
  const isLoadingRef = useRef(false)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastProgressRef = useRef<number>(0)

  // Prevent page scroll on wheel ONLY when over canvas
  useLayoutEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const preventScroll = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()
      
      // Manually trigger zoom
      const delta = e.deltaY > 0 ? 0.95 : 1.05
      setScale(prev => Math.min(Math.max(0.3, prev * delta), 3))
    }

    canvas.addEventListener('wheel', preventScroll, { passive: false })
    return () => canvas.removeEventListener('wheel', preventScroll)
  }, [])

  // Load blocks when graph changes
  useEffect(() => {
    isLoadingRef.current = true // Mark as loading
    setHasUnsavedChanges(false) // Reset unsaved changes flag
    
    if (graph?.nodes) {
      // Convert graph nodes to blocks with positions
      const loadedBlocks = graph.nodes.map((node: any, index: number) => ({
        ...node,
        position: node.position || {
          x: 100 + (index % 3) * 280,
          y: 100 + Math.floor(index / 3) * 180
        }
      }))
      setBlocks(loadedBlocks)
      onLog?.('info', `Loaded strategy: ${graph.name} (${graph.nodes.length} blocks)`)
      
      // Reset view
      setScale(1)
      setPanOffset({ x: 50, y: 50 })
    } else {
      setBlocks([])
    }
    
    // Allow changes to trigger auto-save after a brief delay
    setTimeout(() => {
      isLoadingRef.current = false
    }, 100)
  }, [graph, onLog])

  // Generate error code from timestamp (format: YYYYMMDD-HHMMSS-mmm)
  const generateErrorCode = () => {
    const now = new Date()
    const date = now.toISOString().slice(0, 10).replace(/-/g, '')
    const time = now.toTimeString().slice(0, 8).replace(/:/g, '')
    const ms = now.getMilliseconds().toString().padStart(3, '0')
    return `ERR-${date}-${time}-${ms}`
  }

  // Manual save function
  const handleSave = async () => {
    if (!graph || graph.is_demo) {
      toast.error('Cannot save demo strategies. Run the backtest to create your own copy.')
      return
    }

    setIsSaving(true)
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/graphs/${graph.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          nodes: blocks
        })
      })

      if (response.ok) {
        const updatedGraph = await response.json()
        onLog?.('success', `✓ Saved ${blocks.length} blocks to ${graph.name}`)
        toast.success('Strategy saved!')
        onChange?.(updatedGraph) // Update the graph in parent
        onSave?.() // Notify parent to refresh navigator
      } else {
        const errorCode = generateErrorCode()
        const errorText = await response.text()
        
        onLog?.('error', `ERROR: Please contact support with error code: ${errorCode}`)
        onLog?.('error', `Save failed: ${errorText}`)
        
        console.error('Save error:', {
          errorCode,
          timestamp: new Date().toISOString(),
          error: errorText,
          graphId: graph.id
        })
        
        toast.error(`Failed to save strategy.\n\nError code: ${errorCode}`)
      }
    } catch (error: any) {
      const errorCode = generateErrorCode()
      
      console.error('Save exception:', {
        errorCode,
        timestamp: new Date().toISOString(),
        error: error.message || error,
        stack: error.stack
      })
      
      onLog?.('error', `ERROR: Please contact support with error code: ${errorCode}`)
      onLog?.('error', `Save failed: ${error.message || error}`)
      toast.error(`Failed to save strategy.\n\nError code: ${errorCode}`)
    } finally {
      setIsSaving(false)
    }
  }

  // Auto-save blocks when they change (debounced)
  useEffect(() => {
    // Don't auto-save if:
    // - No graph or it's a demo
    // - No blocks
    // - Currently loading (to prevent saving on initial load)
    // - No unsaved changes
    if (!graph || graph.is_demo || blocks.length === 0 || isLoadingRef.current || !hasUnsavedChanges) {
      return
    }

    const saveTimer = setTimeout(async () => {
      try {
        const token = localStorage.getItem('tq_session')
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/graphs/${graph.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            nodes: blocks
          })
        })

        if (response.ok) {
          const updatedGraph = await response.json()
          onLog?.('success', `✓ Auto-saved ${blocks.length} blocks`)
          onChange?.(updatedGraph) // Update the graph in parent
          onSave?.() // Notify parent to refresh navigator
          setHasUnsavedChanges(false) // Clear the flag after successful save
        } else {
          const error = await response.text()
          onLog?.('error', `Auto-save failed: ${error}`)
        }
      } catch (error) {
        console.error('Auto-save failed:', error)
        onLog?.('error', `Auto-save failed: ${error}`)
      }
    }, 2000) // Save 2 seconds after last change

    return () => clearTimeout(saveTimer)
  }, [blocks, graph, onLog, hasUnsavedChanges])

  const handleRunBacktest = async () => {
    if (!graph || blocks.length === 0) {
      onLog?.('error', 'No strategy selected or blocks are empty')
      toast.error('Please select or create a strategy first')
      return
    }

    // Clear any existing polling interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
    lastProgressRef.current = 0

    setIsRunning(true)
    onLog?.('info', `🚀 Starting backtest: ${graph.name}`)
    const loadingToast = toast.loading('🚀 Starting backtest...')
    
    try {
      const token = localStorage.getItem('tq_session')
      
      // First, create or update the strategy graph
      let graphId = graph.id
      
      if (graph.is_demo) {
        onLog?.('info', 'Creating user copy of demo strategy...')
        toast.loading('Creating strategy copy...', { id: loadingToast })
        
        // If it's a demo, create a new user graph from it
        const createResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/graphs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            name: `${graph.name} (My Copy)`,
            description: graph.description,
            nodes: blocks,
            edges: [],
            outputs: graph.outputs,
            tags: ['user-created']
          })
        })
        
        if (!createResponse.ok) {
          const error = await createResponse.text()
          onLog?.('error', `Failed to create strategy: ${error}`)
          throw new Error(`Failed to create strategy: ${error}`)
        }
        
        const newGraph = await createResponse.json()
        graphId = newGraph.id
        onLog?.('success', `Strategy created! ID: ${graphId.substring(0, 8)}...`)
        toast.success('Strategy created!', { id: loadingToast })
      }
      
      onLog?.('info', `Submitting backtest job for strategy: ${graphId.substring(0, 8)}...`)
      toast.loading('Submitting backtest job...', { id: loadingToast })
      
      // Create run
      const runResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          strategy_graph_id: graphId,
          config: {
            symbol: blocks[0]?.params?.symbol || 'BTC/USDT',
            timeframe: blocks[0]?.params?.timeframe || '1m',
            start_date: blocks[0]?.params?.start_date || '2024-01-01',
            end_date: blocks[0]?.params?.end_date || '2024-03-31',
            initial_capital: 10000,
            seeds: { numpy: 42, torch: 42 },
            priority: 'interactive',
            max_workers: 1
          }
        })
      })
      
      if (!runResponse.ok) {
        const error = await runResponse.text()
        onLog?.('error', `Failed to start backtest: ${error}`)
        throw new Error(`Failed to start backtest: ${error}`)
      }
      
      const run = await runResponse.json()
      
      onLog?.('success', `✅ Backtest queued! Run ID: ${run.id.substring(0, 8)}...`)
      onLog?.('info', `Status: ${run.status} | Progress: ${run.progress}%`)
      onLog?.('info', 'Switch to Results tab to monitor progress')
      
      toast.success(
        `✅ Backtest started!\nRun ID: ${run.id.substring(0, 8)}...\n\nCheck the Results tab or Console for progress.`,
        { 
          id: loadingToast,
          duration: 5000
        }
      )
      
      console.log('🚀 Backtest Run Started:', {
        runId: run.id,
        status: run.status,
        strategy: graph.name
      })
      
      // Poll for status updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/runs/${run.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          
          if (statusResponse.ok) {
            const updatedRun = await statusResponse.json()
            
            if (updatedRun.status === 'completed') {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current)
                pollIntervalRef.current = null
              }
              onLog?.('success', `✅ Backtest completed! Total trades: ${updatedRun.metrics?.total_trades || 0}`)
              toast.success('Backtest completed!', { duration: 3000 })
              onRunUpdate?.(updatedRun)
            } else if (updatedRun.status === 'failed') {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current)
                pollIntervalRef.current = null
              }
              const errorCode = generateErrorCode()
              
              onLog?.('error', `❌ Backtest FAILED!`)
              
              // Show user-friendly error message
              if (updatedRun.error_message) {
                const errorMsg = updatedRun.error_message
                
                // Parse common errors into user-friendly messages
                if (errorMsg.includes('No OHLCV data') || errorMsg.includes('Data loader')) {
                  onLog?.('error', `⚠️ Missing Data Loader block or data failed to load`)
                } else if (errorMsg.includes('not found') && errorMsg.includes('Feature')) {
                  onLog?.('error', `⚠️ Feature not found - check your block connections`)
                } else if (errorMsg.includes('No features in context')) {
                  onLog?.('error', `⚠️ No feature blocks connected - add RSI, MACD, or other indicators`)
                } else if (errorMsg.includes('Executor creation failed')) {
                  onLog?.('error', `⚠️ Invalid block configuration - check block parameters`)
                } else {
                  onLog?.('error', `⚠️ ${errorMsg}`)
                }
                
                // Always show the technical error for debugging
                onLog?.('error', `Technical details: ${errorMsg}`)
              }
              
              onLog?.('error', `For support, use error code: ${errorCode}`)
              
              toast.error(`❌ Backtest failed!\n\nCheck the console for details.\nError code: ${errorCode}`, { duration: 10000 })
              onRunUpdate?.(updatedRun)
            } else if (updatedRun.progress > lastProgressRef.current) {
              // Only log progress if it changed
              lastProgressRef.current = updatedRun.progress
              onLog?.('info', `Progress: ${updatedRun.progress}%`)
            }
          }
        } catch (e) {
          // Silently ignore polling errors
        }
      }, 2000) // Poll every 2 seconds
      
      // Stop polling after 5 minutes
      setTimeout(() => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
          pollIntervalRef.current = null
        }
      }, 300000)
      
    } catch (error: any) {
      const errorCode = generateErrorCode()
      const errorMsg = `ERROR: Please contact support with error code: ${errorCode}`
      
      onLog?.('error', errorMsg)
      onLog?.('error', `Details: ${error.message || error}`)
      
      console.error('❌ Run error:', {
        errorCode,
        timestamp: new Date().toISOString(),
        error: error.message || error,
        stack: error.stack
      })
      
      toast.error(
        `❌ Backtest failed!\n\nPlease contact support with error code:\n${errorCode}`,
        { id: loadingToast, duration: 10000 }
      )
    } finally {
      setIsRunning(false)
    }
  }

  const handleLibraryDragStart = (blockType: any) => {
    setDraggedBlock(blockType)
  }

  const handleBlockMouseDown = (blockId: string, e: React.MouseEvent) => {
    if ((e.target as HTMLElement).tagName === 'BUTTON' || (e.target as HTMLElement).tagName === 'INPUT') {
      return // Don't drag if clicking on button or input
    }
    
    if (graph?.is_demo) {
      onLog?.('warn', 'Cannot move demo strategy blocks. Run it to create an editable copy!')
      return
    }
    
    e.preventDefault()
    e.stopPropagation()
    
    const block = blocks.find(b => b.id === blockId)
    if (!block) return

    setDraggedBlockId(blockId)
    
    // Calculate offset in canvas space
    const startX = (e.clientX - panOffset.x) / scale
    const startY = (e.clientY - panOffset.y) / scale
    const offsetX = startX - block.position.x
    const offsetY = startY - block.position.y
    
    onLog?.('debug', `Dragging block: ${block.type}`)
    
    // Attach global listeners
    const handleGlobalMouseMove = (moveEvent: MouseEvent) => {
      const x = (moveEvent.clientX - panOffset.x) / scale - offsetX
      const y = (moveEvent.clientY - panOffset.y) / scale - offsetY
      
      setBlocks(prev => prev.map(b =>
        b.id === blockId
          ? { ...b, position: { x, y } }
          : b
      ))
    }
    
    const handleGlobalMouseUp = () => {
      setDraggedBlockId(null)
      setHasUnsavedChanges(true)
      onLog?.('success', `Block moved!`)
      document.removeEventListener('mousemove', handleGlobalMouseMove)
      document.removeEventListener('mouseup', handleGlobalMouseUp)
    }
    
    document.addEventListener('mousemove', handleGlobalMouseMove)
    document.addEventListener('mouseup', handleGlobalMouseUp)
  }

  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    // Only pan if clicking empty space
    if ((e.target as HTMLElement).closest('.block-node')) return
    
    e.preventDefault()
    setIsPanning(true)
    setPanStart({
      x: e.clientX - panOffset.x,
      y: e.clientY - panOffset.y
    })
  }

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return
    
    setPanOffset({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    })
  }

  const handleCanvasMouseUp = () => {
    setIsPanning(false)
  }


  const handleFitToScreen = () => {
    if (blocks.length === 0 || !canvasRef.current) return
    
    // Find bounds of all blocks
    const minX = Math.min(...blocks.map(b => b.position.x))
    const minY = Math.min(...blocks.map(b => b.position.y))
    const maxX = Math.max(...blocks.map(b => b.position.x + 200))
    const maxY = Math.max(...blocks.map(b => b.position.y + 100))
    
    // Calculate center
    const centerX = (minX + maxX) / 2
    const centerY = (minY + maxY) / 2
    
    // Pan to center
    const rect = canvasRef.current.getBoundingClientRect()
    setPanOffset({
      x: rect.width / 2 - centerX * scale,
      y: rect.height / 2 - centerY * scale
    })
    
    onLog?.('info', 'Fit to screen')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedBlock || !canvasRef.current) return

    // Get cursor position relative to canvas
    const rect = canvasRef.current.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top
    
    // Convert to block space (accounting for pan and zoom)
    const x = (canvasX - panOffset.x) / scale
    const y = (canvasY - panOffset.y) / scale

    const newBlock: Block = {
      id: `${draggedBlock.type}_${Date.now()}`,
      type: draggedBlock.type,
      params: getDefaultParams(draggedBlock.type),
      position: { x, y },
      inputs: []
    }

    setBlocks([...blocks, newBlock])
    setHasUnsavedChanges(true)
    setDraggedBlock(null)
    onLog?.('success', `Added ${draggedBlock.name} at (${x.toFixed(0)}, ${y.toFixed(0)})`)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const getDefaultParams = (type: string): Record<string, any> => {
    switch (type) {
      case 'data.loader':
        return { symbol: 'BTC/USDT', timeframe: '1m', start_date: '2024-01-01', end_date: '2024-12-31' }
      case 'feature.rsi':
        return { period: 14, output_name: 'rsi' }
      case 'feature.macd':
        return { fast_period: 12, slow_period: 26, signal_period: 9 }
      case 'feature.ma':
        return { type: 'EMA', period: 20, source: 'close', output_name: 'ma_20' }
      case 'feature.ema':
        return { type: 'EMA', period: 20, source: 'close', output_name: 'ema_20' }
      case 'feature.atr':
        return { period: 14, output_name: 'atr' }
      case 'signal.threshold':
        return { feature: 'rsi', upper_threshold: 70, lower_threshold: 30 }
      case 'signal.rule':
        return { 
          long_entry: 'rsi < 30',
          short_entry: 'rsi > 70',
          exit_rule: 'rsi > 50'
        }
      case 'signal.crossover':
        return { fast_feature: 'ema_fast', slow_feature: 'ema_slow' }
      case 'sizing.fixed':
        return { sizing_mode: 'contracts', size_value: 1.0 }
      case 'sizing.vol_target':
        return { target_vol: 0.15, lookback: 30, max_position: 1.5 }
      case 'risk.stop_take':
        return { stop_atr_mult: 2.0, take_atr_mult: 3.0 }
      case 'risk.trailing':
        return { trail_atr_mult: 2.0 }
      case 'exec.market':
        return { slippage_bps: 5, fee_bps: 2 }
      case 'exec.limit':
        return { limit_offset_bps: 10, fee_bps: 2, fill_probability: 0.7 }
      default:
        return {}
    }
  }

  const getBlockColor = (type: string) => {
    for (const category of Object.values(BLOCK_LIBRARY)) {
      const block = category.find(b => b.type === type)
      if (block) return block.color
    }
    return '#6b7280'
  }

  const handleBlockDoubleClick = (blockId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedBlock(blockId)
    onLog?.('info', `Editing block: ${blockId}`)
  }

  const handleDeleteBlock = (blockId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setBlocks(blocks.filter(b => b.id !== blockId))
    setHasUnsavedChanges(true)
    if (selectedBlock === blockId) setSelectedBlock(null)
    onLog?.('info', `Deleted block: ${blockId}`)
  }

  const handleParamChange = (blockId: string, param: string, value: any) => {
    setBlocks(blocks.map(b => 
      b.id === blockId 
        ? { ...b, params: { ...b.params, [param]: value } }
        : b
    ))
    setHasUnsavedChanges(true)
  }

  const handleStartConnection = (blockId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (graph?.is_demo) {
      toast.error('Cannot modify demo strategies')
      return
    }
    setConnectingFrom(blockId)
    onLog?.('info', `Connecting from: ${blockId.split('_')[0]}`)
  }

  const handleCompleteConnection = (targetId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!connectingFrom || connectingFrom === targetId) {
      setConnectingFrom(null)
      setConnectionPreview(null)
      return
    }

    // Add connection
    setBlocks(prev => prev.map(b =>
      b.id === targetId
        ? { ...b, inputs: [...(b.inputs || []).filter(id => id !== connectingFrom), connectingFrom] }
        : b
    ))
    setHasUnsavedChanges(true)

    onLog?.('success', `Connected ${connectingFrom.split('_')[0]} → ${targetId.split('_')[0]}`)
    setConnectingFrom(null)
    setConnectionPreview(null)
  }

  const handleRemoveConnection = (blockId: string, inputId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setBlocks(prev => prev.map(b =>
      b.id === blockId
        ? { ...b, inputs: b.inputs?.filter(id => id !== inputId) || [] }
        : b
    ))
    setHasUnsavedChanges(true)
    onLog?.('info', `Removed connection`)
  }

  const handleCanvasMouseMoveWithConnection = (e: React.MouseEvent) => {
    if (connectingFrom && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect()
      const x = (e.clientX - rect.left - panOffset.x) / scale
      const y = (e.clientY - rect.top - panOffset.y) / scale
      setConnectionPreview({ x, y })
    }
  }

  return (
    <div className="h-full flex">
      {/* Block Library */}
      {showLibrary && (
        <div className="w-64 border-r border-border bg-card flex flex-col" style={{ height: '100%' }}>
          <div className="p-4 border-b border-border flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Block Library</h3>
              <button 
                onClick={() => setShowLibrary(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                ×
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {Object.entries(BLOCK_LIBRARY).map(([category, categoryBlocks]) => (
              <div key={category} className="mb-6">
                <div className="text-xs font-semibold uppercase text-muted-foreground mb-2">
                  {category}
                </div>
                <div className="space-y-1">
                  {categoryBlocks.map(block => (
                    <div
                      key={block.type}
                      draggable
                      onDragStart={() => handleLibraryDragStart(block)}
                      className="p-3 rounded-lg border border-border hover:border-brand-dark-teal/50 cursor-move transition-colors"
                      style={{ borderLeftWidth: '3px', borderLeftColor: block.color }}
                    >
                      <div className="font-medium text-sm">{block.name}</div>
                      <div className="text-xs text-muted-foreground mt-1">{block.type}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Canvas */}
      <div className="flex-1 flex flex-col">
        <div className="border-b border-border bg-muted/20 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!showLibrary && (
              <Button size="sm" variant="outline" onClick={() => setShowLibrary(true)}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Show Library
              </Button>
            )}
            <span className="text-sm text-muted-foreground">
              {blocks.length} blocks • Zoom: {(scale * 100).toFixed(0)}%
            </span>
            {graph?.is_demo && (
              <span className="text-xs px-2 py-1 rounded-full bg-brand-bright-yellow/20 text-brand-bright-yellow">
                DEMO (Read-only)
              </span>
            )}
            <span className="text-xs text-muted-foreground">
              {connectingFrom 
                ? '🔗 Click a block to connect • Click canvas to cancel' 
                : 'Scroll to zoom • Drag to pan • Click dots to connect • Double-click to edit'
              }
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <Button 
              size="sm" 
              variant="outline"
              onClick={handleFitToScreen}
              disabled={blocks.length === 0}
            >
              <ArrowsPointingOutIcon className="h-4 w-4 mr-2" />
              Fit to Screen
            </Button>
            {graph && !graph.is_demo && (
              <Button
                size="sm"
                onClick={handleSave}
                disabled={isSaving || blocks.length === 0}
                variant="outline"
                className="border-brand-dark-teal text-brand-dark-teal hover:bg-brand-dark-teal/10"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand-dark-teal mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                    Save
                  </>
                )}
              </Button>
            )}
            <Button 
              size="sm" 
              onClick={handleRunBacktest}
              disabled={isRunning || blocks.length === 0}
            >
              {isRunning ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Running...
                </>
              ) : (
                <>
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Run
                </>
              )}
            </Button>
          </div>
        </div>

        <div 
          ref={canvasRef}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onMouseDown={handleCanvasMouseDown}
          onMouseMove={(e) => {
            handleCanvasMouseMove(e)
            handleCanvasMouseMoveWithConnection(e)
          }}
          onMouseUp={handleCanvasMouseUp}
          onMouseLeave={handleCanvasMouseUp}
          onClick={() => {
            if (connectingFrom) {
              setConnectingFrom(null)
              setConnectionPreview(null)
              onLog?.('info', 'Connection cancelled')
            }
          }}
          className="flex-1 overflow-hidden bg-muted/5 relative"
          style={{
            backgroundImage: 'radial-gradient(circle, #888 1px, transparent 1px)',
            backgroundSize: `${20 * scale}px ${20 * scale}px`,
            backgroundPosition: `${panOffset.x}px ${panOffset.y}px`,
            cursor: isPanning ? 'grabbing' : draggedBlockId ? 'grabbing' : 'grab',
            touchAction: 'none',
            overscrollBehavior: 'none'
          }}
        >
          <div 
            className="absolute"
            style={{
              transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${scale})`,
              transformOrigin: '0 0'
            }}
          >
          {blocks.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-muted-foreground mb-2">
                  <PlusIcon className="h-16 w-16 mx-auto opacity-50" />
                </div>
                <div className="text-lg font-medium mb-2">Drag blocks to start building</div>
                <div className="text-sm text-muted-foreground">
                  Choose from the library or use AI Copilot to generate a strategy
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Draw connections between blocks */}
              <svg className="absolute pointer-events-none" style={{ zIndex: 0, width: '5000px', height: '5000px', left: 0, top: 0 }}>
                {blocks.flatMap(block => {
                  if (!block.inputs || block.inputs.length === 0) return []
                  
                  return block.inputs.map(inputId => {
                    const inputBlock = blocks.find(b => b.id === inputId)
                    if (!inputBlock) return null
                    
                    const x1 = inputBlock.position.x + 200
                    const y1 = inputBlock.position.y + 50
                    const x2 = block.position.x
                    const y2 = block.position.y + 50
                    
                    return (
                      <line
                        key={`${inputId}-${block.id}`}
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#059669"
                        strokeWidth="2"
                        strokeDasharray="5,5"
                        opacity="0.6"
                        markerEnd="url(#arrowhead)"
                      />
                    )
                  }).filter(line => line !== null)
                })}
                
                {/* Connection preview while connecting */}
                {connectingFrom && connectionPreview && (() => {
                  const sourceBlock = blocks.find(b => b.id === connectingFrom)
                  if (!sourceBlock) return null
                  
                  return (
                    <line
                      x1={sourceBlock.position.x + 200}
                      y1={sourceBlock.position.y + 50}
                      x2={connectionPreview.x}
                      y2={connectionPreview.y}
                      stroke="#f59e0b"
                      strokeWidth="2"
                      strokeDasharray="5,5"
                      opacity="0.8"
                    />
                  )
                })()}
                
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="10"
                    markerHeight="10"
                    refX="9"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 10 3, 0 6" fill="#059669" opacity="0.6" />
                  </marker>
                </defs>
              </svg>

              {/* Render blocks */}
              {blocks.map(block => (
                <div
                  key={block.id}
                  className="block-node"
                  onDoubleClick={(e) => handleBlockDoubleClick(block.id, e)}
                  onMouseDown={(e) => handleBlockMouseDown(block.id, e)}
                  draggable={false}
                  style={{
                    left: block.position.x,
                    top: block.position.y,
                    minWidth: '200px',
                    borderLeftWidth: '4px',
                    borderLeftColor: getBlockColor(block.type),
                    zIndex: draggedBlockId === block.id ? 100 : 1,
                    userSelect: 'none'
                  }}
                  className={`
                    absolute px-4 py-3 rounded-lg border-2 bg-card shadow-lg
                    ${selectedBlock === block.id 
                      ? 'border-brand-dark-teal ring-2 ring-brand-dark-teal/20 scale-105' 
                      : 'border-border hover:border-brand-dark-teal/50'
                    }
                    ${graph?.is_demo ? 'cursor-default' : 'cursor-move hover:shadow-xl'}
                    ${draggedBlockId === block.id ? 'opacity-80 shadow-2xl' : ''}
                  `}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {/* Connection dot (click to start connection) */}
                      {!graph?.is_demo && (
                        <button
                          onMouseDown={(e) => e.stopPropagation()}
                          onClick={(e) => 
                            connectingFrom ? handleCompleteConnection(block.id, e) : handleStartConnection(block.id, e)
                          }
                          className={`w-3 h-3 rounded-full border-2 transition-all ${
                            connectingFrom === block.id 
                              ? 'bg-brand-bright-yellow border-brand-bright-yellow animate-pulse' 
                              : connectingFrom
                              ? 'bg-brand-dark-teal/20 border-brand-dark-teal hover:bg-brand-dark-teal/50'
                              : 'bg-muted border-border hover:bg-brand-dark-teal/30 hover:border-brand-dark-teal'
                          }`}
                          title={connectingFrom ? 'Click to connect here' : 'Click to start connection'}
                        />
                      )}
                      <div className="font-semibold text-sm capitalize">{block.type.split('.')[1]}</div>
                    </div>
                    {!graph?.is_demo && (
                      <button
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => handleDeleteBlock(block.id, e)}
                        className="text-muted-foreground hover:text-danger-600"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground mb-2">{block.type}</div>
                  
                  {/* Quick param display */}
                  <div className="text-xs space-y-1">
                    {Object.entries(block.params).slice(0, 3).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-2">
                        <span className="text-muted-foreground truncate">{key}:</span>
                        <span className="font-mono text-right truncate">{String(value).substring(0, 20)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </>
          )}
          </div>
        </div>
      </div>

      {/* Parameter Panel */}
      {selectedBlock && (
        <div className="w-80 border-l border-border bg-card flex flex-col" style={{ height: '100%' }}>
          <div className="p-4 border-b border-border flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Parameters</h3>
              <button 
                onClick={() => setSelectedBlock(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                ×
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {(() => {
              const block = blocks.find(b => b.id === selectedBlock)
              if (!block) return null

              return (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase">
                      Block ID
                    </label>
                    <div className="text-sm font-mono mt-1">{block.id}</div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase">
                      Type
                    </label>
                    <div className="text-sm mt-1">{block.type}</div>
                  </div>

                  <div className="border-t border-border pt-4">
                    {/* Show connected inputs */}
                    {block.inputs && block.inputs.length > 0 && (
                      <div className="mb-4">
                        <div className="text-xs font-medium text-muted-foreground uppercase mb-2">
                          Inputs ({block.inputs.length})
                        </div>
                        <div className="space-y-1">
                          {block.inputs.map(inputId => {
                            const inputBlock = blocks.find(b => b.id === inputId)
                            return (
                              <div 
                                key={inputId}
                                className="flex items-center justify-between p-2 bg-muted/30 rounded text-xs"
                              >
                                <span className="font-mono truncate">
                                  {inputBlock ? inputBlock.type : inputId}
                                </span>
                                {!graph?.is_demo && (
                                  <button
                                    onClick={(e) => handleRemoveConnection(block.id, inputId, e)}
                                    className="text-danger-600 hover:text-danger-700"
                                  >
                                    ×
                                  </button>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    <div className="text-xs font-medium text-muted-foreground uppercase mb-3">
                      Parameters
                    </div>
                    
                    {/* Context hints for rule blocks */}
                    {block.type === 'signal.rule' && (
                      <div className="mb-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs">
                        <div className="font-semibold text-blue-600 mb-1">Available Features:</div>
                        {block.inputs && block.inputs.length > 0 ? (
                          block.inputs.map(inputId => {
                            const inputBlock = blocks.find(b => b.id === inputId)
                            if (!inputBlock) return null
                            
                            const outputName = inputBlock.params.output_name || 
                                             (inputBlock.type === 'feature.macd' ? 'macd_line, macd_signal, macd_hist' : 
                                              inputBlock.type.split('.')[1])
                            
                            return (
                              <div key={inputId} className="font-mono text-brand-dark-teal">
                                • {outputName}
                              </div>
                            )
                          })
                        ) : (
                          <div className="text-muted-foreground italic">Connect feature blocks to use them in rules</div>
                        )}
                        <div className="mt-2 text-muted-foreground">
                          Use operators: &lt; &gt; &lt;= &gt;= == and or
                        </div>
                      </div>
                    )}
                    
                    <div className="space-y-3">
                      {Object.entries(block.params).map(([key, value]) => (
                        <div key={key}>
                          <label className="text-sm font-medium mb-1 block capitalize">
                            {key.replace(/_/g, ' ')}
                          </label>
                          
                          {/* Special handling for MA type */}
                          {key === 'type' && block.type === 'feature.ma' ? (
                            <select
                              value={String(value)}
                              onChange={(e) => handleParamChange(block.id, key, e.target.value)}
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm"
                            >
                              <option value="EMA">EMA (Exponential)</option>
                              <option value="SMA">SMA (Simple)</option>
                              <option value="WMA">WMA (Weighted)</option>
                              <option value="HMA">HMA (Hull)</option>
                            </select>
                          ) : key === 'sizing_mode' && block.type === 'sizing.fixed' ? (
                            <select
                              value={String(value)}
                              onChange={(e) => handleParamChange(block.id, key, e.target.value)}
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm"
                            >
                              <option value="contracts">Contracts / Shares</option>
                              <option value="percent_balance">% of Balance</option>
                              <option value="usd_value">USD Value</option>
                            </select>
                          ) : key === 'source' ? (
                            <select
                              value={String(value)}
                              onChange={(e) => handleParamChange(block.id, key, e.target.value)}
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm"
                            >
                              <option value="close">Close</option>
                              <option value="open">Open</option>
                              <option value="high">High</option>
                              <option value="low">Low</option>
                              <option value="hl2">(High + Low) / 2</option>
                              <option value="hlc3">(High + Low + Close) / 3</option>
                            </select>
                          ) : typeof value === 'boolean' ? (
                            <div className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={value}
                                onChange={(e) => handleParamChange(block.id, key, e.target.checked)}
                                className="rounded border-input"
                              />
                              <span className="text-sm text-muted-foreground">
                                {value ? 'Enabled' : 'Disabled'}
                              </span>
                            </div>
                          ) : key === 'long_entry' || key === 'short_entry' || key === 'exit_rule' ? (
                            <textarea
                              value={String(value)}
                              onChange={(e) => handleParamChange(block.id, key, e.target.value)}
                              rows={2}
                              placeholder={
                                key === 'long_entry' ? 'e.g., rsi < 30 and macd_hist > 0' :
                                key === 'short_entry' ? 'e.g., rsi > 70 and macd_hist < 0' :
                                'e.g., rsi > 50'
                              }
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm font-mono resize-none"
                            />
                          ) : key === 'rule' ? (
                            <textarea
                              value={String(value)}
                              onChange={(e) => handleParamChange(block.id, key, e.target.value)}
                              rows={4}
                              placeholder="rsi < 30 -> long; rsi > 70 -> short"
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm font-mono resize-none"
                            />
                          ) : (
                            <input
                              type={typeof value === 'number' ? 'number' : 'text'}
                              value={String(value)}
                              onChange={(e) => handleParamChange(
                                block.id, 
                                key, 
                                typeof value === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
                              )}
                              step={typeof value === 'number' && value < 1 ? '0.01' : '1'}
                              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm font-mono"
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      )}
    </div>
  )
}

