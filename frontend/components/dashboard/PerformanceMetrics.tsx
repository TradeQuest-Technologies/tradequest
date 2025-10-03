'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Progress } from '../ui/Progress'
import { Badge } from '../ui/Badge'
import { formatCurrency, formatPercentage, getColorForValue } from '../../lib/utils'

interface PerformanceMetricsProps {
  className?: string
}

export function PerformanceMetrics({ className }: PerformanceMetricsProps) {
  // Empty state for new users
  const hasData = false
  
  if (!hasData) {
    return (
      <div className={className}>
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <div className="text-muted-foreground mb-4">
                <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">No Performance Data</h3>
              <p className="text-muted-foreground text-sm">
                Start trading to see your performance metrics and risk analysis.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {metrics.map((metric, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">
                    {metric.label}
                  </span>
                  <Badge 
                    variant={metric.trend === 'up' ? 'success' : metric.trend === 'down' ? 'destructive' : 'default'}
                    className="text-xs"
                  >
                    {metric.trend === 'up' ? '↗' : metric.trend === 'down' ? '↘' : '→'}
                  </Badge>
                </div>
                <div className="text-2xl font-bold">
                  {metric.changeType === 'percentage' 
                    ? formatPercentage(metric.value)
                    : formatCurrency(metric.value)
                  }
                </div>
                <div className={`text-sm ${getColorForValue(metric.change, metric.changeType === 'percentage')}`}>
                  {metric.change > 0 ? '+' : ''}
                  {metric.changeType === 'percentage' 
                    ? formatPercentage(metric.change)
                    : formatCurrency(metric.change)
                  } from last period
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Risk Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {riskMetrics.map((metric, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{metric.label}</span>
                  <span className="text-sm font-bold">{metric.value}</span>
                </div>
                <Progress value={metric.progress} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
