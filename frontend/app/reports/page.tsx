'use client'

import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { 
  DocumentTextIcon,
  ArrowTopRightOnSquareIcon,
  ClockIcon,
  SparklesIcon,
  ChartBarIcon,
  DocumentArrowDownIcon,
  ShareIcon
} from '@heroicons/react/24/outline'

export default function Reports() {
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
                Comprehensive performance reports and trading analytics
              </p>
            </div>

            {/* Coming Soon Card */}
            <Card className="max-w-2xl mx-auto">
              <CardHeader className="text-center pb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-amber-100 dark:bg-amber-900/20 rounded-full mb-4">
                  <ClockIcon className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                </div>
                <CardTitle className="text-2xl">Coming Soon</CardTitle>
              </CardHeader>
              <CardContent className="text-center space-y-6">
                <div className="space-y-4">
                  <p className="text-muted-foreground text-lg">
                    We're building advanced reporting tools to give you deep insights into your trading performance.
                  </p>
                  
                  <div className="bg-accent/50 rounded-lg p-6 space-y-4">
                    <h3 className="font-semibold text-foreground">Planned Report Types</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <ChartBarIcon className="h-4 w-4 text-brand-dark-teal" />
                        <span>Performance Reports</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <DocumentArrowDownIcon className="h-4 w-4 text-brand-dark-teal" />
                        <span>Tax Documents</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <ShareIcon className="h-4 w-4 text-brand-dark-teal" />
                        <span>Risk Analysis</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <DocumentTextIcon className="h-4 w-4 text-brand-dark-teal" />
                        <span>Strategy Reports</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 rounded-full bg-brand-bright-yellow"></div>
                        <span>Custom Reports</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 rounded-full bg-brand-bright-yellow"></div>
                        <span>Comparative Analysis</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-medium text-foreground">What to expect:</h4>
                    <ul className="text-sm text-muted-foreground space-y-2 text-left max-w-md mx-auto">
                      <li className="flex items-start space-x-2">
                        <SparklesIcon className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                        <span>PDF and Excel export formats</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <SparklesIcon className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                        <span>Automated tax document generation</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <SparklesIcon className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                        <span>Interactive charts and visualizations</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <SparklesIcon className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                        <span>Benchmark comparisons</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <SparklesIcon className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                        <span>Scheduled report delivery</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Want to be notified when reports are available? 
                    <a 
                      href="mailto:support@tradequest.tech?subject=Reports Notification" 
                      className="text-primary hover:underline ml-1 inline-flex items-center"
                    >
                      Contact us
                      <ArrowTopRightOnSquareIcon className="h-3 w-3 ml-1" />
                    </a>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Alternative Options */}
            <div className="mt-8 max-w-2xl mx-auto">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">In the meantime...</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3 p-4 bg-accent/30 rounded-lg">
                      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-medium text-primary">1</span>
                      </div>
                      <div>
                        <h4 className="font-medium">Dashboard Analytics</h4>
                        <p className="text-sm text-muted-foreground">
                          Use our dashboard to view real-time performance metrics and charts.
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-3 p-4 bg-accent/30 rounded-lg">
                      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-medium text-primary">2</span>
                      </div>
                      <div>
                        <h4 className="font-medium">Backtesting Results</h4>
                        <p className="text-sm text-muted-foreground">
                          Generate detailed strategy performance reports through our backtesting engine.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 p-4 bg-accent/30 rounded-lg">
                      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-medium text-primary">3</span>
                      </div>
                      <div>
                        <h4 className="font-medium">Export Trade Data</h4>
                        <p className="text-sm text-muted-foreground">
                          Export your trading journal data to CSV for external analysis tools.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}