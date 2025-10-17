'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { useUser } from '../../hooks/useUser'
import { getAuthToken } from '../../lib/auth'
import {
  PlayIcon,
  PlusIcon,
  ChartBarIcon,
  CodeBracketIcon,
  SparklesIcon,
  Cog6ToothIcon,
  RectangleStackIcon,
  FolderIcon,
  BeakerIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

import StrategyBuilder from '../../components/backtest/StrategyBuilder'
import AICopilotPanel from '../../components/backtest/AICopilotPanel'
import ResultsViewer from '../../components/backtest/ResultsViewer'
import NavigatorSidebar from '../../components/backtest/NavigatorSidebar'
import CodePad from '../../components/backtest/CodePad'

type Tab = 'builder' | 'code' | 'results'
type StrategyMode = 'basic' | 'advanced' | null

export default function BacktestV2() {
  const router = useRouter()
  const { user } = useUser()
  
  const [strategyMode, setStrategyMode] = useState<StrategyMode>(null)
  const [activeTab, setActiveTab] = useState<Tab>('builder')
  const [currentGraph, setCurrentGraph] = useState<any>(null)
  const [currentRun, setCurrentRun] = useState<any>(null)
  const [showNavigator, setShowNavigator] = useState(true)
  const [showAICopilot, setShowAICopilot] = useState(false)
  const [showConsole, setShowConsole] = useState(true)
  const [loading, setLoading] = useState(true)
  const [userPlan, setUserPlan] = useState<string>('free')
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
    const checkUserPlan = async () => {
      const token = getAuthToken()
      if (!token) {
        router.push('/auth')
        return
      }

      try {
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        
        if (response.ok) {
          const data = await response.json()
          const plan = data.plan || 'free'
          setUserPlan(plan)
          
          // If free user, redirect to upgrade page
          if (plan === 'free' || !plan) {
            router.push('/upgrade?feature=Backtesting Studio')
            return
          }
        }
      } catch (error) {
        console.error('Failed to fetch user plan:', error)
      }
      
      setLoading(false)
    }

    checkUserPlan()
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

  // Tabs change based on strategy mode
  const getTabsForMode = () => {
    if (!strategyMode) return []
    
    if (strategyMode === 'basic') {
      return [
        { id: 'builder' as Tab, label: 'Visual Builder', icon: RectangleStackIcon },
        { id: 'results' as Tab, label: 'Results', icon: ChartBarIcon }
      ]
    } else {
      return [
        { id: 'code' as Tab, label: 'Python Code', icon: CodeBracketIcon },
        { id: 'results' as Tab, label: 'Results', icon: ChartBarIcon }
      ]
    }
  }
  
  const tabs = getTabsForMode()

  // Show mode selection if no mode chosen
  if (!strategyMode) {
    return (
      <div className="h-screen bg-background flex overflow-hidden">
        <Sidebar className="w-64" />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="max-w-4xl w-full">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold mb-4">Choose Your Strategy Type</h1>
                <p className="text-muted-foreground text-lg">
                  Select how you want to build your trading strategy
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Basic Mode */}
                <button
                  onClick={() => {
                    setStrategyMode('basic')
                    setActiveTab('builder')
                  }}
                  className="group relative bg-card border-2 border-border hover:border-brand-teal rounded-2xl p-8 text-left transition-all duration-300 hover:shadow-xl hover:shadow-brand-teal/20"
                >
                  <div className="absolute top-4 right-4">
                    <div className="bg-green-500/10 text-green-500 px-3 py-1 rounded-full text-xs font-semibold">
                      RECOMMENDED
                    </div>
                  </div>
                  <RectangleStackIcon className="h-16 w-16 text-brand-teal mb-6 group-hover:scale-110 transition-transform" />
                  <h3 className="text-2xl font-bold mb-3">Basic Mode</h3>
                  <p className="text-muted-foreground mb-6">
                    Visual block-based strategy builder. Perfect for beginners and quick strategy testing.
                  </p>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-teal mr-2" />
                      Drag-and-drop blocks
                    </li>
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-teal mr-2" />
                      No coding required
                    </li>
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-teal mr-2" />
                      AI assistance available
                    </li>
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-teal mr-2" />
                      Pre-built indicators
                    </li>
                  </ul>
                </button>
                
                {/* Advanced Mode */}
                <button
                  onClick={() => {
                    setStrategyMode('advanced')
                    setActiveTab('code')
                  }}
                  className="group relative bg-card border-2 border-border hover:border-brand-bright-yellow rounded-2xl p-8 text-left transition-all duration-300 hover:shadow-xl hover:shadow-brand-bright-yellow/20"
                >
                  <div className="absolute top-4 right-4">
                    <div className="bg-yellow-500/10 text-yellow-500 px-3 py-1 rounded-full text-xs font-semibold">
                      FOR DEVELOPERS
                    </div>
                  </div>
                  <CodeBracketIcon className="h-16 w-16 text-brand-bright-yellow mb-6 group-hover:scale-110 transition-transform" />
                  <h3 className="text-2xl font-bold mb-3">Advanced Mode</h3>
                  <p className="text-muted-foreground mb-6">
                    Write custom Python code for complex strategies. Full control and flexibility.
                  </p>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-bright-yellow mr-2" />
                      Full Python support
                    </li>
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-bright-yellow mr-2" />
                      Custom indicators
                    </li>
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-bright-yellow mr-2" />
                      AI code assistance
                    </li>
                    <li className="flex items-center">
                      <CheckIcon className="h-4 w-4 text-brand-bright-yellow mr-2" />
                      Advanced logic
                    </li>
                  </ul>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

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
                {/* Mode indicator */}
                <div className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                  strategyMode === 'basic' 
                    ? 'bg-brand-teal/10 text-brand-teal' 
                    : 'bg-brand-bright-yellow/10 text-brand-bright-yellow'
                }`}>
                  {strategyMode === 'basic' ? 'BASIC MODE' : 'ADVANCED MODE'}
                </div>
                
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => {
                    setStrategyMode(null)
                    setCurrentGraph(null)
                  }}
                >
                  Change Mode
                </Button>
                
                <Button size="sm" variant="outline" onClick={() => setShowNavigator(!showNavigator)}>
                  <FolderIcon className="h-4 w-4 mr-2" />
                  {showNavigator ? 'Hide' : 'Show'} Navigator
                </Button>
                
                <Button 
                  size="sm" 
                  variant={showAICopilot ? "default" : "outline"}
                  onClick={() => {
                    setShowAICopilot(!showAICopilot)
                    if (!showAICopilot) {
                      setShowConsole(true) // Ensure right panel is open
                    }
                  }}
                >
                  <SparklesIcon className="h-4 w-4 mr-2" />
                  AI Copilot
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
              {strategyMode === 'basic' && activeTab === 'builder' && (
                <div className="h-full">
                  <StrategyBuilder 
                    graph={currentGraph} 
                    onChange={(updatedGraph) => {
                      setCurrentGraph(updatedGraph)
                    }}
                    onLog={addConsoleLog}
                    onSave={() => {
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
              
              {strategyMode === 'advanced' && activeTab === 'code' && (
                <div className="h-full">
                  <CodePad />
                </div>
              )}
              
              {activeTab === 'results' && (
                <div className="h-full">
                  <ResultsViewer 
                    run={currentRun}
                    strategyGraphId={currentGraph?.id}
                  />
                </div>
              )}
            </div>
          </div>
          
          {/* Right Panel - AI Copilot OR Console */}
          {(showAICopilot || showConsole) && (
            <div className="w-96 border-l border-border bg-card flex flex-col" style={{ height: '100%' }}>
              {/* Toggle between AI Copilot and Console */}
              <div className="p-4 border-b border-border flex-shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {showAICopilot ? (
                      <>
                        <SparklesIcon className="h-5 w-5 text-brand-bright-yellow" />
                        <h3 className="font-semibold">AI Copilot</h3>
                      </>
                    ) : (
                      <h3 className="font-semibold">Console</h3>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {!showAICopilot && (
                      <button 
                        onClick={() => setConsoleLogs([])}
                        className="text-xs text-muted-foreground hover:text-foreground"
                      >
                        Clear
                      </button>
                    )}
                    <button 
                      onClick={() => {
                        setShowConsole(false)
                        setShowAICopilot(false)
                      }}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Content: AI Copilot or Console */}
              {showAICopilot ? (
                <div className="flex-1 overflow-hidden">
                  <AICopilotPanel 
                    graph={currentGraph}
                    lastRun={currentRun}
                    onGraphUpdate={setCurrentGraph}
                  />
                </div>
              ) : (
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
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  )
}

