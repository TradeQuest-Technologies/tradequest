'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Button } from '../ui/Button'
import { 
  PlusIcon, 
  ChartBarIcon, 
  CogIcon, 
  DocumentTextIcon,
  ArrowUpTrayIcon,
  PlayIcon
} from '@heroicons/react/24/outline'

interface QuickActionsProps {
  className?: string
}

export function QuickActions({ className }: QuickActionsProps) {
  const router = useRouter()
  
  const actions = [
    {
      title: 'Add Trade',
      description: 'Record a new trade',
      icon: <PlusIcon className="h-5 w-5" />,
      variant: 'default' as const,
      onClick: () => router.push('/journal/add')
    },
    {
      title: 'Import Data',
      description: 'AI-powered broker import',
      icon: <ArrowUpTrayIcon className="h-5 w-5" />,
      variant: 'outline' as const,
      onClick: () => router.push('/journal/import')
    },
    {
      title: 'Run Backtest',
      description: 'Test your strategy',
      icon: <PlayIcon className="h-5 w-5" />,
      variant: 'outline' as const,
      onClick: () => router.push('/backtesting')
    },
    {
      title: 'View Reports',
      description: 'Analyze performance',
      icon: <ChartBarIcon className="h-5 w-5" />,
      variant: 'outline' as const,
      onClick: () => router.push('/reports')
    },
    {
      title: 'Trading Journal',
      description: 'Review your trades',
      icon: <DocumentTextIcon className="h-5 w-5" />,
      variant: 'outline' as const,
      onClick: () => router.push('/journal')
    },
    {
      title: 'Settings',
      description: 'Configure preferences',
      icon: <CogIcon className="h-5 w-5" />,
      variant: 'outline' as const,
      onClick: () => router.push('/settings')
    }
  ]

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant}
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={action.onClick}
            >
              {action.icon}
              <div className="text-center">
                <div className="font-medium text-sm">{action.title}</div>
                <div className="text-xs text-muted-foreground">{action.description}</div>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
