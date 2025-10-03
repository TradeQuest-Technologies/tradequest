'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { formatCurrency, formatDateTime, getColorForValue } from '../../lib/utils'

interface Trade {
  id: string
  symbol: string
  side: 'buy' | 'sell' | 'long' | 'short'
  qty: number
  avg_price: number
  filled_at: string
  submitted_at?: string
  pnl?: number
}

interface RecentTradesProps {
  trades: Trade[]
  className?: string
}

export function RecentTrades({ trades, className }: RecentTradesProps) {
  const getSideColor = (side: 'buy' | 'sell') => {
    return side === 'buy' ? 'text-success-600 dark:text-success-400' : 'text-danger-600 dark:text-danger-400'
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'open':
        return 'default'
      case 'closed':
        return 'success'
      case 'partial':
        return 'warning'
      default:
        return 'default'
    }
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {trades.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No trades yet. Start trading to see your activity here.
            </div>
          ) : (
            trades.map((trade) => (
              <div key={trade.id} className="flex items-center justify-between p-3 rounded-lg border bg-card">
                <div className="flex items-center space-x-3">
                  <div className="flex flex-col">
                    <span className="font-medium">{trade.symbol}</span>
                    <span className="text-sm text-muted-foreground">
                      {formatDateTime(trade.submitted_at || trade.filled_at)}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <Badge variant={(trade.side === 'buy' || trade.side === 'long') ? 'success' : 'destructive'}>
                      {trade.side.toUpperCase()}
                    </Badge>
                    <div className="text-sm text-muted-foreground mt-1">
                      {trade.qty} @ {formatCurrency(trade.avg_price)}
                    </div>
                  </div>
                  
                  {trade.pnl !== undefined && (
                    <div className="text-right min-w-[100px]">
                      <div className={`font-medium text-lg ${getColorForValue(trade.pnl)}`}>
                        {trade.pnl > 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
