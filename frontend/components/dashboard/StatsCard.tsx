'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { cn, formatCurrency, formatPercentage, getColorForValue } from '../../lib/utils'
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline'

interface StatsCardProps {
  title: string
  value: number
  change?: number
  changeType?: 'currency' | 'percentage' | 'number'
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  className?: string
  description?: string
  periodLabel?: string
}

export function StatsCard({
  title,
  value,
  change,
  changeType = 'currency',
  icon,
  trend,
  className,
  description,
  periodLabel,
}: StatsCardProps) {
  const formatValue = (val: number) => {
    if (changeType === 'percentage') {
      return formatPercentage(val)
    } else if (changeType === 'number') {
      return val.toLocaleString()
    }
    return formatCurrency(val)
  }

  const getTrendIcon = () => {
    if (trend === 'up') return <ArrowTrendingUpIcon className="h-4 w-4" />
    if (trend === 'down') return <ArrowTrendingDownIcon className="h-4 w-4" />
    return null
  }

  const getTrendColor = () => {
    if (change === undefined) return 'text-muted-foreground'
    return getColorForValue(change)
  }

  return (
    <Card className={cn('hover:shadow-lg transition-all duration-200', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground font-brand">
          {title}
        </CardTitle>
        {icon && (
          <div className="h-4 w-4 text-muted-foreground">
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold font-brand-display">{formatValue(value)}</div>
        {change !== undefined && (
          <div className={cn('flex items-center space-x-1 text-xs', getTrendColor())}>
            {getTrendIcon()}
            <span>
              {change > 0 ? '+' : ''}{formatValue(change)}
            </span>
            {periodLabel && <span className="text-muted-foreground">from {periodLabel}</span>}
          </div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  )
}
