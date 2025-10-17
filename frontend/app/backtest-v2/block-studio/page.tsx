'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../../components/layout/Sidebar'
import { Header } from '../../../components/layout/Header'
import { Button } from '../../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card'
import {
  ArrowLeftIcon,
  SparklesIcon,
  PlayIcon,
  CheckIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function BlockStudio() {
  const router = useRouter()
  const [blockData, setBlockData] = useState({
    name: '',
    description: '',
    category: 'feature',
    code: `# Define your custom block
# 
# Your block will receive:
# - inputs: List of input values from connected blocks
# - params: Dictionary of parameters
# - data: OHLCV dataframe
#
# Return: Dictionary with your outputs
#
# Example - Custom RSI with smoothing:
def execute(inputs, params, data):
    import talib
    import numpy as np
    
    period = params.get('period', 14)
    smoothing = params.get('smoothing', 3)
    
    # Calculate RSI
    rsi = talib.RSI(data['close'].values, timeperiod=period)
    
    # Apply smoothing
    rsi_smooth = np.convolve(rsi, np.ones(smoothing)/smoothing, mode='valid')
    
    return {
        'rsi': rsi_smooth,
        'oversold': rsi_smooth < 30,
        'overbought': rsi_smooth > 70
    }`,
    parameters: `{
  "period": {
    "type": "integer",
    "default": 14,
    "min": 2,
    "max": 100,
    "description": "RSI period"
  },
  "smoothing": {
    "type": "integer",
    "default": 3,
    "min": 1,
    "max": 10,
    "description": "Smoothing window"
  }
}`,
    tags: ''
  })
  
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [showAI, setShowAI] = useState(false)
  const [aiInput, setAIInput] = useState('')
  const [aiLoading, setAILoading] = useState(false)
  const [aiLog, setAILog] = useState<any[]>([])
  const [aiLoadingStep, setAILoadingStep] = useState(0)

  const categories = [
    { id: 'data', name: 'Data Sources' },
    { id: 'feature', name: 'Features & Indicators' },
    { id: 'signal', name: 'Signal Generation' },
    { id: 'sizing', name: 'Position Sizing' },
    { id: 'risk', name: 'Risk Management' },
    { id: 'exec', name: 'Execution' },
    { id: 'other', name: 'Other' }
  ]

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/custom-blocks/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          code: blockData.code,
          parameters: blockData.parameters
        })
      })

      if (response.ok) {
        const result = await response.json()
        setTestResult(result)
        toast.success('Block tested successfully!')
      } else {
        const error = await response.json()
        setTestResult({ error: error.detail })
        toast.error('Test failed')
      }
    } catch (error) {
      toast.error('Failed to test block')
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async (publish: boolean = false) => {
    if (!blockData.name || !blockData.code) {
      toast.error('Name and code are required')
      return
    }

    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/custom-blocks/blocks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...blockData,
          tags: blockData.tags ? blockData.tags.split(',').map(t => t.trim()) : []
        })
      })

      if (response.ok) {
        const block = await response.json()
        
        if (publish) {
          // Publish the block
          await fetch(`/api/v1/custom-blocks/blocks/${block.id}/publish`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          toast.success('Block created and published!')
        } else {
          toast.success('Block created!')
        }
        
        router.push('/backtest-v2')
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to create block')
      }
    } catch (error) {
      toast.error('Failed to create block')
    }
  }

  const handleAIHelp = async () => {
    if (!aiInput.trim()) return
    
    setAILoading(true)
    setAILog([])
    setAILoadingStep(0)
    
    // Animate loading steps
    const stepInterval = setInterval(() => {
      setAILoadingStep(prev => (prev < 2 ? prev + 1 : prev))
    }, 2000)
    
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/custom-blocks/ai-help', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          request: aiInput,
          current_code: blockData.code
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        // Update code with animation
        if (data.code) {
          setBlockData({ ...blockData, code: data.code })
        }
        
        // Update parameters if provided
        if (data.parameters) {
          setBlockData(prev => ({ ...prev, parameters: data.parameters }))
        }
        
        // Show execution log
        if (data.execution_log && data.execution_log.length > 0) {
          setAILog(data.execution_log)
        }
        
        // Success notification with confetti effect
        toast.success('🎉 AI generated your code!', {
          duration: 4000,
          style: {
            background: '#10b981',
            color: '#fff',
            fontWeight: 'bold',
          },
        })
        
        // Scroll to code editor smoothly
        setTimeout(() => {
          const codeEditor = document.querySelector('textarea[rows="20"]')
          if (codeEditor) {
            codeEditor.scrollIntoView({ behavior: 'smooth', block: 'center' })
            // Flash animation
            codeEditor.classList.add('ring-4', 'ring-brand-bright-yellow', 'ring-opacity-50')
            setTimeout(() => {
              codeEditor.classList.remove('ring-4', 'ring-brand-bright-yellow', 'ring-opacity-50')
            }, 2000)
          }
        }, 100)
      } else {
        const error = await response.json()
        toast.error(error.detail || 'AI help failed')
      }
    } catch (error) {
      toast.error('Failed to get AI help')
    } finally {
      clearInterval(stepInterval)
      setAILoading(false)
      setAILoadingStep(0)
      setAIInput('')
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64" />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
              <button
                onClick={() => router.push('/backtest-v2')}
                className="flex items-center text-muted-foreground hover:text-foreground mb-4"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Back to Backtesting Studio
              </button>
              <h1 className="text-3xl font-bold">Block Creation Studio</h1>
              <p className="text-muted-foreground mt-2">
                Create custom blocks with Python. Use AI to help or write your own.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left - Block Info */}
              <div className="lg:col-span-1 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Block Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Block Name *</label>
                      <input
                        type="text"
                        value={blockData.name}
                        onChange={(e) => setBlockData({ ...blockData, name: e.target.value })}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        placeholder="e.g., Advanced RSI Divergence"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Description</label>
                      <textarea
                        value={blockData.description}
                        onChange={(e) => setBlockData({ ...blockData, description: e.target.value })}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        rows={3}
                        placeholder="What does this block do?"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Category *</label>
                      <select
                        value={blockData.category}
                        onChange={(e) => setBlockData({ ...blockData, category: e.target.value })}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                      >
                        {categories.map(cat => (
                          <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Tags</label>
                      <input
                        type="text"
                        value={blockData.tags}
                        onChange={(e) => setBlockData({ ...blockData, tags: e.target.value })}
                        className="w-full px-3 py-2 border border-input rounded-lg bg-background"
                        placeholder="rsi, divergence, momentum"
                      />
                      <p className="text-xs text-muted-foreground mt-1">Comma-separated</p>
                    </div>

                    <div>
                      <Button
                        variant="outline"
                        onClick={() => setShowAI(!showAI)}
                        className="w-full"
                      >
                        <SparklesIcon className="h-4 w-4 mr-2" />
                        {showAI ? 'Hide' : 'Show'} AI Helper
                      </Button>
                    </div>

                    {showAI && (
                      <div className="p-4 bg-muted rounded-lg">
                        <label className="block text-sm font-medium mb-2">Ask AI to help</label>
                        <textarea
                          value={aiInput}
                          onChange={(e) => setAIInput(e.target.value)}
                          className="w-full px-3 py-2 border border-input rounded-lg bg-background mb-2"
                          rows={3}
                          placeholder="e.g., Create a block that detects RSI divergence"
                          disabled={aiLoading}
                        />
                        <Button
                          onClick={handleAIHelp}
                          disabled={aiLoading || !aiInput.trim()}
                          size="sm"
                          className="w-full relative"
                        >
                          {aiLoading ? (
                            <span className="flex items-center gap-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              AI is thinking...
                            </span>
                          ) : (
                            <>
                              <SparklesIcon className="h-4 w-4 mr-2 inline" />
                              Generate Code
                            </>
                          )}
                        </Button>
                        {aiLoading && (
                          <div className="mt-3 text-xs text-muted-foreground">
                            <div className={`flex items-center gap-2 mb-1 transition-opacity ${aiLoadingStep >= 0 ? 'opacity-100' : 'opacity-30'}`}>
                              <div className="w-2 h-2 bg-brand-teal rounded-full animate-bounce"></div>
                              Analyzing your request...
                            </div>
                            <div className={`flex items-center gap-2 mb-1 transition-opacity ${aiLoadingStep >= 1 ? 'opacity-100' : 'opacity-30'}`}>
                              <div className="w-2 h-2 bg-brand-teal rounded-full animate-bounce"></div>
                              Testing algorithms...
                            </div>
                            <div className={`flex items-center gap-2 transition-opacity ${aiLoadingStep >= 2 ? 'opacity-100' : 'opacity-30'}`}>
                              <div className="w-2 h-2 bg-brand-teal rounded-full animate-bounce"></div>
                              Generating code...
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Documentation */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <BookOpenIcon className="h-5 w-5 mr-2" />
                      Quick Reference
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm space-y-2">
                    <div>
                      <div className="font-semibold text-brand-teal">Function Signature:</div>
                      <code className="text-xs bg-muted p-1 rounded">
                        execute(inputs, params, data)
                      </code>
                    </div>
                    <div>
                      <div className="font-semibold text-brand-teal">Available Libraries:</div>
                      <div className="text-muted-foreground">pandas, numpy, talib, scipy, sklearn</div>
                    </div>
                    <div>
                      <div className="font-semibold text-brand-teal">Return Format:</div>
                      <code className="text-xs bg-muted p-1 rounded block">
                        {`{"output_name": value}`}
                      </code>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Middle - Code Editor */}
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Python Code</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <textarea
                      value={blockData.code}
                      onChange={(e) => setBlockData({ ...blockData, code: e.target.value })}
                      className="w-full px-4 py-3 border border-input rounded-lg bg-black text-green-400 font-mono text-sm"
                      rows={20}
                      spellCheck={false}
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Parameters Schema (JSON)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <textarea
                      value={blockData.parameters}
                      onChange={(e) => setBlockData({ ...blockData, parameters: e.target.value })}
                      className="w-full px-4 py-3 border border-input rounded-lg bg-background font-mono text-sm"
                      rows={8}
                    />
                  </CardContent>
                </Card>

                {/* Test Results */}
                {testResult && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Test Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {testResult.error ? (
                        <div className="text-red-600 font-mono text-sm whitespace-pre-wrap">
                          {testResult.error}
                        </div>
                      ) : (
                        <div className="text-green-600 font-mono text-sm">
                          <CheckIcon className="h-5 w-5 inline mr-2" />
                          Block executed successfully!
                          <pre className="mt-2 text-muted-foreground">{JSON.stringify(testResult, null, 2)}</pre>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* AI Execution Log */}
                {aiLog.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <SparklesIcon className="h-5 w-5 mr-2 text-brand-bright-yellow" />
                        AI Execution Log
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {aiLog.map((log, idx) => (
                          <div key={idx} className="p-3 bg-muted rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-semibold text-brand-teal uppercase">
                                {log.tool}
                              </span>
                              {log.result?.success && (
                                <CheckIcon className="h-4 w-4 text-green-600" />
                              )}
                            </div>
                            {log.args?.description && (
                              <div className="text-sm text-muted-foreground mb-2">
                                {log.args.description}
                              </div>
                            )}
                            {log.result?.stdout && (
                              <pre className="text-xs bg-black text-green-400 p-2 rounded mt-2 overflow-x-auto">
                                {log.result.stdout}
                              </pre>
                            )}
                            {log.result?.stderr && (
                              <pre className="text-xs bg-black text-red-400 p-2 rounded mt-2 overflow-x-auto">
                                {log.result.stderr}
                              </pre>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Actions */}
                <div className="flex gap-4">
                  <Button
                    onClick={handleTest}
                    disabled={testing}
                    variant="outline"
                    className="flex-1"
                  >
                    <PlayIcon className="h-4 w-4 mr-2" />
                    {testing ? 'Testing...' : 'Test Block'}
                  </Button>
                  <Button
                    onClick={() => handleSave(false)}
                    className="flex-1"
                  >
                    Save (Private)
                  </Button>
                  <Button
                    onClick={() => handleSave(true)}
                    variant="outline"
                    className="flex-1"
                  >
                    Save & Publish
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
