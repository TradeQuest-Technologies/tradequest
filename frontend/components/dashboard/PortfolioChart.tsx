'use client'

import React, { useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

interface Trade {
  id: string
  symbol: string
  filled_at: string
  submitted_at?: string
  pnl: number
}

interface PortfolioChartProps {
  trades: Trade[]
  mode?: 'pnl' | 'portfolio'
  className?: string
}

export function PortfolioChart({ trades, mode = 'pnl', className }: PortfolioChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [hoveredPoint, setHoveredPoint] = React.useState<number | null>(null)
  const [tooltip, setTooltip] = React.useState<{ x: number; y: number; data: any } | null>(null)
  const [zoomRange, setZoomRange] = React.useState<{ start: number; end: number }>({ start: 0, end: 1 })
  const [isPanning, setIsPanning] = React.useState(false)
  const [panStart, setPanStart] = React.useState<{ x: number; rangeStart: number; rangeEnd: number } | null>(null)

  // Calculate cumulative PnL over time
  const calculateChartData = () => {
    if (!trades.length) return []

    // Sort trades by date
    const sortedTrades = [...trades].sort((a, b) => 
      new Date(a.submitted_at || a.filled_at).getTime() - new Date(b.submitted_at || b.filled_at).getTime()
    )

    let cumulativePnL = 0
    const data = sortedTrades.map(trade => {
      cumulativePnL += parseFloat(trade.pnl?.toString() || '0')
      return {
        date: trade.submitted_at || trade.filled_at,
        value: cumulativePnL,
        trade: trade,
        pnl: parseFloat(trade.pnl?.toString() || '0')
      }
    })

    return data
  }

  const allData = calculateChartData()
  
  // Apply zoom to data
  const startIdx = Math.floor(allData.length * zoomRange.start)
  const endIdx = Math.ceil(allData.length * zoomRange.end)
  const data = allData.slice(startIdx, endIdx)

  // Add native wheel event listener to prevent page scroll AND handle zoom
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const handleNativeWheel = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()
      
      const rect = canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const padding = { left: 60, right: 20, top: 20, bottom: 40 }
      const chartWidth = rect.width - padding.left - padding.right
      
      // Calculate mouse position as ratio (0-1) within the chart area
      const mouseRatio = Math.max(0, Math.min(1, (mouseX - padding.left) / chartWidth))
      
      // Zoom in/out
      const zoomDelta = e.deltaY > 0 ? 0.1 : -0.1
      const currentRange = zoomRange.end - zoomRange.start
      const newRange = Math.max(0.02, Math.min(1, currentRange + zoomDelta))
      
      // Calculate zoom center based on mouse position
      const currentMousePos = zoomRange.start + (mouseRatio * currentRange)
      
      // Zoom toward mouse position
      let newStart = currentMousePos - (mouseRatio * newRange)
      let newEnd = currentMousePos + ((1 - mouseRatio) * newRange)
      
      // Clamp to valid range
      if (newStart < 0) {
        newStart = 0
        newEnd = newRange
      }
      if (newEnd > 1) {
        newEnd = 1
        newStart = 1 - newRange
      }
      
      setZoomRange({ start: newStart, end: newEnd })
    }

    canvas.addEventListener('wheel', handleNativeWheel, { passive: false })
    
    return () => {
      canvas.removeEventListener('wheel', handleNativeWheel)
    }
  }, [zoomRange])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !data.length) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height)

    // Calculate dimensions with proper padding
    const padding = { left: 60, right: 20, top: 20, bottom: 40 }
    const chartWidth = rect.width - padding.left - padding.right
    const chartHeight = rect.height - padding.top - padding.bottom

    // Find min/max values
    const values = data.map(d => d.value)
    const minValue = Math.min(...values, 0)  // Include 0 in range
    const maxValue = Math.max(...values, 0)
    const valueRange = maxValue - minValue || 1  // Avoid division by zero

    // Draw grid lines
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight / 4) * i
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(padding.left + chartWidth, y)
      ctx.stroke()
    }
    
    // Draw zero line if in range
    if (minValue < 0 && maxValue > 0) {
      const zeroY = padding.top + chartHeight - ((0 - minValue) / valueRange) * chartHeight
      ctx.strokeStyle = '#9ca3af'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(padding.left, zeroY)
      ctx.lineTo(padding.left + chartWidth, zeroY)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // Determine color based on overall performance
    const finalValue = values[values.length - 1]
    const isPositive = finalValue >= 0
    const lineColor = isPositive ? '#10b981' : '#ef4444'  // green for profit, red for loss
    const fillColor = isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'

    // Draw area fill
    ctx.fillStyle = fillColor
    ctx.beginPath()
    data.forEach((point, index) => {
      const x = padding.left + (chartWidth / Math.max(data.length - 1, 1)) * index
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    // Close the path along the bottom
    const lastX = padding.left + chartWidth
    const baseY = padding.top + chartHeight - ((0 - minValue) / valueRange) * chartHeight
    ctx.lineTo(lastX, baseY)
    ctx.lineTo(padding.left, baseY)
    ctx.closePath()
    ctx.fill()

    // Draw chart line
    ctx.strokeStyle = lineColor
    ctx.lineWidth = 3
    ctx.beginPath()

    data.forEach((point, index) => {
      const x = padding.left + (chartWidth / Math.max(data.length - 1, 1)) * index
      const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })

    ctx.stroke()

    // Draw data points (only if not too many)
    if (data.length < 200) {
      data.forEach((point, index) => {
        const x = padding.left + (chartWidth / Math.max(data.length - 1, 1)) * index
        const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

        // Highlight hovered point
        if (index === hoveredPoint) {
          ctx.fillStyle = '#ffffff'
          ctx.strokeStyle = lineColor
          ctx.lineWidth = 3
          ctx.beginPath()
          ctx.arc(x, y, 8, 0, 2 * Math.PI)
          ctx.fill()
          ctx.stroke()
        } else {
          ctx.fillStyle = lineColor
          ctx.beginPath()
          ctx.arc(x, y, 3, 0, 2 * Math.PI)
          ctx.fill()
        }
      })
    } else if (hoveredPoint !== null && hoveredPoint < data.length && data[hoveredPoint]) {
      // Only draw hovered point when there are too many points (with bounds check)
      const x = padding.left + (chartWidth / Math.max(data.length - 1, 1)) * hoveredPoint
      const y = padding.top + chartHeight - ((data[hoveredPoint].value - minValue) / valueRange) * chartHeight
      ctx.fillStyle = '#ffffff'
      ctx.strokeStyle = lineColor
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.arc(x, y, 8, 0, 2 * Math.PI)
      ctx.fill()
      ctx.stroke()
    }

    // Draw labels
    ctx.fillStyle = '#6b7280'
    ctx.font = '11px Inter'
    ctx.textAlign = 'right'

    // Y-axis labels
    for (let i = 0; i <= 4; i++) {
      const value = minValue + (valueRange / 4) * (4 - i)
      const y = padding.top + (chartHeight / 4) * i
      ctx.fillText(`$${value.toFixed(0)}`, padding.left - 10, y + 4)
    }

    // X-axis labels (show subset based on data length)
    ctx.textAlign = 'center'
    const labelInterval = Math.max(1, Math.floor(data.length / 8))
    data.forEach((point, index) => {
      if (index % labelInterval === 0 || index === data.length - 1) {
        const x = padding.left + (chartWidth / Math.max(data.length - 1, 1)) * index
        const date = new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        ctx.fillText(date, x, rect.height - padding.bottom / 2)
      }
    })
  }, [data, hoveredPoint])

  // Handle mouse move for tooltips and panning
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas || !data.length) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    // Handle panning
    if (isPanning && panStart) {
      const deltaX = x - panStart.x
      const chartWidth = rect.width - 80  // Account for padding
      const deltaRatio = deltaX / chartWidth
      
      const currentRange = panStart.rangeEnd - panStart.rangeStart
      const newStart = Math.max(0, Math.min(1 - currentRange, panStart.rangeStart - deltaRatio))
      const newEnd = newStart + currentRange
      
      setZoomRange({ start: newStart, end: newEnd })
      return
    }

    const padding = { left: 60, right: 20, top: 20, bottom: 40 }
    const chartWidth = rect.width - padding.left - padding.right
    
    // Find closest point
    let closestIndex = -1
    let closestDistance = Infinity

    data.forEach((point, index) => {
      const pointX = padding.left + (chartWidth / Math.max(data.length - 1, 1)) * index
      const distance = Math.abs(x - pointX)
      
      if (distance < closestDistance && distance < 30) {
        closestDistance = distance
        closestIndex = index
      }
    })

    if (closestIndex >= 0) {
      setHoveredPoint(closestIndex)
      setTooltip({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        data: data[closestIndex]
      })
    } else {
      setHoveredPoint(null)
      setTooltip(null)
    }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    
    const x = e.clientX - rect.left
    
    setIsPanning(true)
    setPanStart({
      x: x,
      rangeStart: zoomRange.start,
      rangeEnd: zoomRange.end
    })
  }

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsPanning(false)
    setPanStart(null)
  }

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    e.stopPropagation()
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const rect = canvas.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const padding = { left: 60, right: 20, top: 20, bottom: 40 }
    const chartWidth = rect.width - padding.left - padding.right
    
    // Calculate mouse position as ratio (0-1) within the chart area
    const mouseRatio = Math.max(0, Math.min(1, (mouseX - padding.left) / chartWidth))
    
    // Zoom in/out
    const zoomDelta = e.deltaY > 0 ? 0.1 : -0.1
    const currentRange = zoomRange.end - zoomRange.start
    const newRange = Math.max(0.02, Math.min(1, currentRange + zoomDelta))
    
    // Calculate zoom center based on mouse position
    const currentMousePos = zoomRange.start + (mouseRatio * currentRange)
    
    // Zoom toward mouse position
    let newStart = currentMousePos - (mouseRatio * newRange)
    let newEnd = currentMousePos + ((1 - mouseRatio) * newRange)
    
    // Clamp to valid range
    if (newStart < 0) {
      newStart = 0
      newEnd = newRange
    }
    if (newEnd > 1) {
      newEnd = 1
      newStart = 1 - newRange
    }
    
    setZoomRange({ start: newStart, end: newEnd })
  }

  const handleMouseLeave = () => {
    setHoveredPoint(null)
    setTooltip(null)
    setIsPanning(false)
    setPanStart(null)
  }

  const handleResetZoom = () => {
    setZoomRange({ start: 0, end: 1 })
  }

  return (
    <div 
      className="h-80 w-full relative overflow-hidden"
      onWheel={(e) => {
        // Prevent page scroll when scrolling over chart
        e.preventDefault()
        e.stopPropagation()
      }}
      style={{ touchAction: 'none' }}
    >
      {/* Reset Zoom Button */}
      {(zoomRange.start > 0 || zoomRange.end < 1) && (
        <button
          onClick={handleResetZoom}
          className="absolute top-2 right-2 z-20 px-3 py-1 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:bg-primary/90 transition-colors"
        >
          Reset Zoom
        </button>
      )}
      
      <canvas
        ref={canvasRef}
        className={`w-full h-full block ${isPanning ? 'cursor-grabbing' : 'cursor-grab'}`}
        style={{ width: '100%', height: '100%', display: 'block' }}
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      />
      
      {/* Tooltip */}
      {tooltip && !isPanning && (
        <div 
          className="absolute pointer-events-none bg-card border border-border rounded-lg shadow-xl p-3 z-10"
          style={{
            left: `${tooltip.x + 10}px`,
            top: `${tooltip.y - 80}px`,
            transform: tooltip.x > 300 ? 'translateX(-100%)' : 'none'
          }}
        >
          <div className="text-xs space-y-1">
            <div className="font-semibold text-foreground">{tooltip.data.trade?.symbol}</div>
            <div className="text-muted-foreground">
              {new Date(tooltip.data.date).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
            <div className={`font-semibold ${tooltip.data.pnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
              Trade P&L: {tooltip.data.pnl >= 0 ? '+' : ''}${tooltip.data.pnl.toFixed(2)}
            </div>
            <div className="font-semibold text-foreground border-t pt-1">
              Cumulative: ${tooltip.data.value.toFixed(2)}
            </div>
          </div>
        </div>
      )}
      
      {/* Zoom Hint */}
      {!isPanning && data.length > 10 && (
        <div className="absolute bottom-2 left-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
          💡 Scroll to zoom at cursor • Drag to pan
        </div>
      )}
    </div>
  )
}
