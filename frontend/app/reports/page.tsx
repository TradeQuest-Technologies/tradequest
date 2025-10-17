'use client'

import { useState, useEffect } from 'react'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { 
  DocumentTextIcon,
  ArrowUpIcon,
  CalendarIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import { getAuthToken } from '../../lib/auth'

interface ReportType {
  id: string
  name: string
  description: string
  icon: any
  available: boolean
}

export default function Reports() {
  const router = useRouter()
  const [userPlan, setUserPlan] = useState<string>('free')
  const [loading, setLoading] = useState(true)
  const [generatingReport, setGeneratingReport] = useState<string | null>(null)

  useEffect(() => {
    fetchUserPlan()
  }, [])

  const fetchUserPlan = async () => {
    try {
      const token = getAuthToken()
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setUserPlan(data.plan || 'free')
      }
    } catch (error) {
      console.error('Failed to fetch user plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const reportTypes: ReportType[] = [
    {
      id: 'daily',
      name: 'Daily Report',
      description: 'Summary of today\'s trading activity, P&L, and key metrics',
      icon: CalendarIcon,
      available: true
    },
    {
      id: 'weekly',
      name: 'Weekly Report',
      description: 'Comprehensive weekly performance analysis with PDF export',
      icon: ChartBarIcon,
      available: true
    },
    {
      id: 'monthly',
      name: 'Monthly Report',
      description: 'Detailed monthly trends, regime shifts, and performance summary',
      icon: DocumentTextIcon,
      available: true
    }
  ]

  const handleGenerateReport = async (reportId: string) => {
    if (userPlan === 'free') {
      return
    }

    setGeneratingReport(reportId)
    
    try {
      const token = getAuthToken()
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/reports/${reportId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // If it's a PDF report, download it
        if (reportId === 'weekly' && data.pdf_content) {
          const blob = new Blob([Uint8Array.from(atob(data.pdf_content), c => c.charCodeAt(0))], { type: 'application/pdf' })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `weekly-report-${new Date().toISOString().split('T')[0]}.pdf`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
        } else {
          // Show the report data in a modal or new page
          console.log('Report data:', data)
          alert('Report generated successfully! Check console for details.')
        }
      } else {
        alert('Failed to generate report. Please try again.')
      }
    } catch (error) {
      console.error('Failed to generate report:', error)
      alert('Failed to generate report. Please try again.')
    } finally {
      setGeneratingReport(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex">
        <Sidebar className="w-64" />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 flex items-center justify-center">
            <div className="text-center">
              <ArrowPathIcon className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
              <p className="text-muted-foreground">Loading...</p>
            </div>
          </main>
        </div>
      </div>
    )
  }

  // Free plan - show upgrade prompt
  if (userPlan === 'free') {
    return (
      <div className="min-h-screen bg-background flex">
        <Sidebar className="w-64" />
        
        <div className="flex-1 flex flex-col">
          <Header />
          
          <main className="flex-1 p-6 overflow-auto">
            <div className="max-w-4xl mx-auto">
              {/* Header */}
              <div className="mb-8 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
                  <DocumentTextIcon className="h-8 w-8 text-primary" />
                </div>
                <h1 className="text-3xl font-bold text-foreground">Reports & Analytics</h1>
                <p className="text-muted-foreground mt-2">
                  Generate comprehensive PDF reports and trading analytics
                </p>
              </div>

              {/* Upgrade Card */}
              <Card className="max-w-2xl mx-auto border-2 border-brand-bright-yellow/20">
                <CardHeader className="text-center pb-4">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-brand-bright-yellow/10 rounded-full mb-4">
                    <ArrowUpIcon className="h-6 w-6 text-brand-bright-yellow" />
                  </div>
                  <CardTitle className="text-2xl">Upgrade to Plus for PDF Reports</CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-6">
                  <p className="text-muted-foreground text-lg">
                    Unlock professional PDF reports and advanced analytics with TradeQuest Plus
                  </p>
                  
                  <div className="bg-accent/50 rounded-lg p-6 space-y-4">
                    <h3 className="font-semibold text-foreground">Plus Plan Includes:</h3>
                    <div className="grid gap-3 text-sm text-left">
                      <div className="flex items-start space-x-3">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span><strong>Daily Reports:</strong> Summary of daily trading activity and P&L</span>
                      </div>
                      <div className="flex items-start space-x-3">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span><strong>Weekly PDF Reports:</strong> Comprehensive performance analysis with charts</span>
                      </div>
                      <div className="flex items-start space-x-3">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span><strong>Monthly Reports:</strong> Detailed trends and regime shift analysis</span>
                      </div>
                      <div className="flex items-start space-x-3">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span><strong>Export to PDF:</strong> Professional reports for your records</span>
                      </div>
                      <div className="flex items-start space-x-3">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span><strong>Plus:</strong> Unlimited trades, AI coaching, and backtesting</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button 
                      onClick={() => router.push('/upgrade?feature=Reports & Analytics')}
                      className="w-full max-w-xs bg-brand-bright-yellow hover:bg-brand-bright-yellow/90 text-gray-900 font-semibold"
                    >
                      <ArrowUpIcon className="h-4 w-4 mr-2" />
                      Upgrade to Plus - $29/month
                    </Button>
                    <p className="text-xs text-muted-foreground mt-3">
                      Cancel anytime. 30-day money-back guarantee.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Preview of Reports */}
              <div className="mt-8 max-w-2xl mx-auto">
                <h3 className="text-lg font-semibold mb-4 text-center">Available Report Types</h3>
                <div className="grid gap-4">
                  {reportTypes.map((report) => (
                    <Card key={report.id} className="opacity-60">
                      <CardContent className="p-4 flex items-start space-x-4">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <report.icon className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium">{report.name}</h4>
                          <p className="text-sm text-muted-foreground">{report.description}</p>
                        </div>
                        <div className="text-xs text-muted-foreground bg-accent px-2 py-1 rounded">
                          Plus Only
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    )
  }

  // Plus plan - show actual reports
  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-2">
                <DocumentTextIcon className="h-8 w-8 text-primary" />
                <h1 className="text-3xl font-bold text-foreground">Reports & Analytics</h1>
              </div>
              <p className="text-muted-foreground">
                Generate comprehensive PDF reports and trading analytics
              </p>
            </div>

            {/* Report Types */}
            <div className="grid gap-6">
              {reportTypes.map((report) => (
                <Card key={report.id} className="hover:border-primary/50 transition-colors">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4 flex-1">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <report.icon className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold mb-1">{report.name}</h3>
                          <p className="text-sm text-muted-foreground mb-4">{report.description}</p>
                          
                          {report.id === 'weekly' && (
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                              <DocumentArrowDownIcon className="h-4 w-4" />
                              <span>Includes PDF export</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <Button
                        onClick={() => handleGenerateReport(report.id)}
                        disabled={!report.available || generatingReport === report.id}
                        className="ml-4"
                      >
                        {generatingReport === report.id ? (
                          <>
                            <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                            Generate Report
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Info Card */}
            <Card className="mt-8 bg-accent/30">
              <CardContent className="p-6">
                <div className="flex items-start space-x-3">
                  <ClockIcon className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium mb-1">Report Generation</p>
                    <p className="text-muted-foreground">
                      Reports are generated based on your current trading data. Daily reports cover today's activity, 
                      weekly reports cover the last 7 days, and monthly reports cover the last 30 days. 
                      PDF reports will be automatically downloaded to your device.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}