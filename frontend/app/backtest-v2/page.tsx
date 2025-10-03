'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { useUser } from '../../hooks/useUser'
import {
  PlayIcon,
  PlusIcon,
  ChartBarIcon,
  CodeBracketIcon,
  SparklesIcon,
  Cog6ToothIcon,
  RectangleStackIcon,
  DocumentTextIcon,
  FolderIcon,
  BeakerIcon
} from '@heroicons/react/24/outline'

import StrategyBuilder from '../../components/backtest/StrategyBuilder'
import AICopilotPanel from '../../components/backtest/AICopilotPanel'
import ResultsViewer from '../../components/backtest/ResultsViewer'
import NavigatorSidebar from '../../components/backtest/NavigatorSidebar'
import CodePad from '../../components/backtest/CodePad'
import ResearchNotebook from '../../components/backtest/ResearchNotebook'

type Tab = 'builder' | 'copilot' | 'code' | 'results' | 'notebook'

export default function BacktestV2() {
  const router = useRouter()
  const { user } = useUser()
  
  const [activeTab, setActiveTab] = useState<Tab>('builder')
  const [currentGraph, setCurrentGraph] = useState<any>(null)
  const [currentRun, setCurrentRun] = useState<any>(null)
  const [showNavigator, setShowNavigator] = useState(true)
  const [showRightPanel, setShowRightPanel] = useState(true)
  const [loading, setLoading] = useState(true)
  const [consoleLogs, setConsoleLogs] = useState<Array<{type: string, message: string, timestamp: Date}>>([
    { type: 'info', message: 'Backtesting Studio initialized', timestamp: new Date() },
    { type: 'debug', message: 'Block registry loaded: 15+ block types available', timestamp: new Date() }
  ])
  const consoleEndRef = useRef<HTMLDivElement>(null)

  const addConsoleLog = useCallback((type: string, message: string) => {
    setConsoleLogs(prev => [...prev, { type, message, timestamp: new Date() }])
  }, [])

  // Auto-scroll console to bottom
  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [consoleLogs])

  const handleRunBacktest = async () => {
    if (!currentGraph) {
      addConsoleLog('error', 'No strategy selected')
      return
    }
    addConsoleLog('info', `Starting backtest for: ${currentGraph.name}`)
    // Switch to builder tab to trigger the run
    setActiveTab('builder')
  }
  
  useEffect(() => {
    const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
    if (!token) {
      router.push('/auth')
      return
    }
    setLoading(false)
  }, [router])

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-dark-teal mx-auto mb-4" />
          <p className="text-muted-foreground">Loading backtesting studio...</p>
        </div>
      </div>
    )
  }

  const tabs = [
    { id: 'builder' as Tab, label: 'Strategy Builder', icon: RectangleStackIcon },
    { id: 'copilot' as Tab, label: 'AI Copilot', icon: SparklesIcon },
    { id: 'code' as Tab, label: 'Code Pad', icon: CodeBracketIcon },
    { id: 'results' as Tab, label: 'Results', icon: ChartBarIcon },
    { id: 'notebook' as Tab, label: 'Research', icon: DocumentTextIcon }
  ]

  return (
    <div className="h-screen bg-background flex overflow-hidden">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        {/* Python-IDE style layout */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          
          {/* Left Navigator Sidebar */}
          {showNavigator && (
            <div className="h-full">
              <NavigatorSidebar 
                currentGraph={currentGraph}
                onGraphSelect={setCurrentGraph}
                onClose={() => setShowNavigator(false)}
              />
            </div>
          )}
          
          {/* Main Workspace */}
          <div className="flex-1 flex flex-col bg-card border-r border-border">
            
            {/* Top Bar */}
            <div className="border-b border-border bg-gradient-to-r from-brand-dark-teal/5 to-brand-bright-yellow/5 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <BeakerIcon className="h-5 w-5 text-brand-dark-teal" />
                  <h1 className="text-lg font-semibold">Backtesting Studio</h1>
                </div>
                
                {currentGraph && (
                  <div className="text-sm text-muted-foreground">
                    {currentGraph.name}
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => setShowNavigator(!showNavigator)}>
                  <FolderIcon className="h-4 w-4 mr-2" />
                  {showNavigator ? 'Hide' : 'Show'} Navigator
                </Button>
                
                <Button size="sm" variant="outline">
                  <Cog6ToothIcon className="h-4 w-4 mr-2" />
                  Settings
                </Button>
                
                <Button 
                  size="sm"
                  onClick={handleRunBacktest}
                  disabled={!currentGraph}
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Run Backtest
                </Button>
              </div>
            </div>
            
            {/* Tab Bar */}
            <div className="border-b border-border bg-muted/20">
              <div className="flex items-center gap-1 px-2 py-1">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors
                      ${activeTab === tab.id 
                        ? 'bg-card text-foreground border-t border-x border-border -mb-px' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
                      }
                    `}
                  >
                    <tab.icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Tab Content */}
            <div className="flex-1 overflow-hidden h-full">
              {activeTab === 'builder' && (
                <div className="h-full">
              <StrategyBuilder 
                graph={currentGraph} 
                onChange={(updatedGraph) => {
                  setCurrentGraph(updatedGraph)
                }}
                onLog={addConsoleLog}
                onSave={() => {
                  // Trigger a re-fetch of graphs in the navigator
                  window.dispatchEvent(new CustomEvent('refreshNavigator'))
                }}
                onRunUpdate={(run) => {
                  setCurrentRun(run)
                  if (run.status === 'failed' || run.status === 'completed') {
                    setActiveTab('results')
                  }
                }}
              />
                </div>
              )}
              
              {activeTab === 'copilot' && (
                <div className="h-full">
                  <AICopilotPanel 
                    graph={currentGraph}
                    lastRun={currentRun}
                    onGraphUpdate={setCurrentGraph}
                  />
                </div>
              )}
              
              {activeTab === 'code' && (
                <div className="h-full">
                  <CodePad />
                </div>
              )}
              
              {activeTab === 'results' && (
                <div className="h-full">
                  <ResultsViewer 
                    run={currentRun}
                  />
                </div>
              )}
              
              {activeTab === 'notebook' && (
                <div className="h-full">
                  <ResearchNotebook />
                </div>
              )}
            </div>
          </div>
          
          {/* Right Panel - Console */}
          {showRightPanel && (
            <div className="w-96 border-l border-border bg-card flex flex-col" style={{ height: '100%' }}>
              <div className="p-4 border-b border-border flex-shrink-0">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Console</h3>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => setConsoleLogs([])}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Clear
                    </button>
                    <button 
                      onClick={() => setShowRightPanel(false)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Console/Logs */}
              <div className="flex-1 overflow-y-auto p-4 space-y-1 font-mono text-xs custom-scrollbar">
                {consoleLogs.map((log, i) => (
                  <div 
                    key={i}
                    className={`flex items-start gap-2 ${
                      log.type === 'error' ? 'text-danger-600' :
                      log.type === 'warn' ? 'text-warning-600' :
                      log.type === 'success' ? 'text-success-600' :
                      log.type === 'info' ? 'text-blue-500' :
                      'text-muted-foreground'
                    }`}
                  >
                    <span className="text-muted-foreground opacity-50">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                    <span className="font-semibold">[{log.type.toUpperCase()}]</span>
                    <span className="flex-1">{log.message}</span>
                  </div>
                ))}
                
                {consoleLogs.length === 0 && (
                  <div className="text-center text-muted-foreground py-8">
                    Console is empty
                  </div>
                )}
                
                {/* Auto-scroll anchor */}
                <div ref={consoleEndRef} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

