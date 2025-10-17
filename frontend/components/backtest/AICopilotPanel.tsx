'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '../ui/Button'
import {
  PaperAirplaneIcon,
  SparklesIcon,
  LightBulbIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  changes?: any[]
  expected_impacts?: any[]
  suggested_next_steps?: string[]
}

interface AICopilotPanelProps {
  graph: any
  lastRun: any
  onGraphUpdate: (graph: any) => void
}

export default function AICopilotPanel({ graph, lastRun, onGraphUpdate }: AICopilotPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load conversation history when strategy changes
  useEffect(() => {
    if (graph?.id) {
      loadConversationHistory(graph.id)
    } else {
      // No strategy selected, show welcome message
      setMessages([{
        id: '1',
        role: 'assistant',
        content: '👋 Hi! I\'m your AI Copilot for backtesting. I can help you:\n\n• Analyze your trading history and create strategies\n• Design strategies from scratch\n• Optimize parameters\n• Diagnose issues\n• Add risk management\n\nWhat would you like to build?'
      }])
    }
  }, [graph?.id])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversationHistory = async (strategyId: string) => {
    setLoadingHistory(true)
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/backtest/v2/conversations/${strategyId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages.map((msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            changes: msg.metadata?.changes,
            expected_impacts: msg.metadata?.expected_impacts,
            suggested_next_steps: msg.metadata?.suggested_next_steps
          })))
        } else {
          // No history, show welcome
          setMessages([{
            id: '1',
            role: 'assistant',
            content: '👋 Hi! I\'m your AI Copilot. Ask me to analyze your trades or help build this strategy!'
          }])
        }
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error)
      setMessages([{
        id: '1',
        role: 'assistant',
        content: '👋 Hi! I\'m your AI Copilot. Ask me to analyze your trades or help build this strategy!'
      }])
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input
    }

    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
      
      // Use streaming endpoint to avoid timeouts on complex requests
      const response = await fetch('/api/v1/backtest/v2/copilot-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: input,
          strategy_graph_id: graph?.id,
          last_run_id: lastRun?.id,
          context: {}
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start copilot stream')
      }

      // Read the streaming response
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No reader available')
      }
      
      const decoder = new TextDecoder()
      let buffer = ''
      let finalData: any = null

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue
          
          try {
            const data = JSON.parse(line.substring(6))
            
            if (data.type === 'status') {
              // Show status in UI (you could add a status indicator if needed)
              console.log('Copilot status:', data.message)
            } else if (data.type === 'result') {
              finalData = data.data
            } else if (data.type === 'done' && finalData) {
              // Create assistant message
              const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: finalData.message,
                changes: finalData.changes,
                expected_impacts: finalData.expected_impacts,
                suggested_next_steps: finalData.suggested_next_steps
              }
              setMessages(prev => [...prev, assistantMessage])
            } else if (data.type === 'error') {
              throw new Error(data.message)
            }
          } catch (e) {
            console.error('Failed to parse SSE message:', e)
          }
        }
      }
    } catch (error) {
      console.error('Copilot error:', error)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleApplyChanges = (changes: any[]) => {
    if (!graph || !changes || changes.length === 0) {
      console.log('No graph or changes to apply')
      return
    }
    
    // Clone the current graph
    const updatedGraph = { ...graph }
    const nodes = [...(graph.nodes || [])]
    const edges = [...(graph.edges || [])]
    
    // Apply each change
    changes.forEach((change: any) => {
      if (change.op === 'add' && change.payload) {
        // Ensure payload has required fields
        const newNode = {
          id: change.payload.id || change.target || `node_${Date.now()}_${Math.random()}`,
          type: change.payload.type,
          params: change.payload.params || {},
          inputs: change.payload.inputs || [],
          position: change.payload.position || { x: 100 + nodes.length * 280, y: 100 }
        }
        
        // Add new node
        nodes.push(newNode)
        
        // Add edges based on inputs
        if (newNode.inputs && Array.isArray(newNode.inputs)) {
          newNode.inputs.forEach((inputId: string) => {
            edges.push({
              id: `${inputId}-${newNode.id}`,
              source: inputId,
              target: newNode.id
            })
          })
        }
      } else if (change.op === 'update' && change.target) {
        // Update existing node
        const nodeIndex = nodes.findIndex((n: any) => n.id === change.target)
        if (nodeIndex >= 0 && change.payload) {
          nodes[nodeIndex] = { ...nodes[nodeIndex], ...change.payload }
        }
      } else if (change.op === 'delete' && change.target) {
        // Delete node and its edges
        const nodeIndex = nodes.findIndex((n: any) => n.id === change.target)
        if (nodeIndex >= 0) {
          nodes.splice(nodeIndex, 1)
          // Remove connected edges
          const filteredEdges = edges.filter((e: any) => 
            e.source !== change.target && e.target !== change.target
          )
          edges.length = 0
          edges.push(...filteredEdges)
        }
      }
    })
    
    updatedGraph.nodes = nodes
    updatedGraph.edges = edges
    
    // Update the graph
    onGraphUpdate(updatedGraph)
    console.log('Applied changes:', changes.length, 'changes')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-full flex flex-col bg-card">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow flex items-center justify-center">
                <SparklesIcon className="h-5 w-5 text-white" />
              </div>
            )}

            <div className={`
              max-w-[80%] rounded-lg p-4
              ${message.role === 'user' 
                ? 'bg-brand-dark-teal text-white' 
                : 'bg-muted border border-border'
              }
            `}>
              {/* Message Content */}
              <div className="prose prose-sm max-w-none text-foreground">
                {message.content.split('\n').map((line, i) => {
                  // Format markdown-style headers
                  if (line.startsWith('### ')) {
                    return <h3 key={i} className="text-lg font-bold mt-4 mb-2 text-brand-bright-yellow">{line.replace('### ', '')}</h3>
                  } else if (line.startsWith('## ')) {
                    return <h2 key={i} className="text-xl font-bold mt-4 mb-2 text-brand-teal">{line.replace('## ', '')}</h2>
                  } else if (line.includes('**') && line.split('**').length >= 3) {
                    // Bold text inline: **text**
                    const parts = line.split('**')
                    return <p key={i} className="my-1">
                      {parts.map((part, j) => j % 2 === 1 ? <strong key={j} className="font-semibold text-brand-teal">{part}</strong> : part)}
                    </p>
                  } else if (line.startsWith('- ')) {
                    return <li key={i} className="ml-4 my-1">{line.replace('- ', '')}</li>
                  } else if (line.match(/^\d+\. /)) {
                    // Numbered list
                    return <li key={i} className="ml-4 my-1 list-decimal">{line.replace(/^\d+\. /, '')}</li>
                  } else if (line.trim().startsWith('![')) {
                    // Image: ![alt](path)
                    const match = line.match(/!\[([^\]]*)\]\(([^)]+)\)/)
                    if (match) {
                      const [, alt, src] = match
                      // Handle different image path formats
                      let imagePath = src
                      if (src.startsWith('sandbox:/')) {
                        imagePath = src.replace('sandbox:/', `/api/v1/coach/workspace/`)
                      }
                      return (
                        <div key={i} className="my-4">
                          <img 
                            src={imagePath} 
                            alt={alt} 
                            className="rounded-lg border border-border max-w-full shadow-lg"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                              console.error('Failed to load image:', imagePath)
                            }}
                          />
                          {alt && <p className="text-xs text-muted-foreground mt-2 text-center">{alt}</p>}
                        </div>
                      )
                    }
                  } else if (line.trim().startsWith('```')) {
                    // Skip code block markers
                    return null
                  } else if (line.trim()) {
                    return <p key={i} className="my-1">{line}</p>
                  }
                  return <br key={i} />
                })}
              </div>

              {/* Proposed Blocks */}
              {message.changes && message.changes.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border/50">
                  <div className="text-xs font-semibold text-brand-teal uppercase mb-2 flex items-center gap-2">
                    <CheckCircleIcon className="h-4 w-4" />
                    Proposed Blocks ({message.changes.length})
                  </div>
                  <div className="space-y-2 mb-3">
                    {message.changes.map((change: any, i: number) => (
                      <div key={i} className="bg-card border border-border rounded p-2 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-brand-bright-yellow">{change.op}</span>
                          <span className="font-semibold">{change.payload?.type || change.target}</span>
                        </div>
                        {change.payload?.params && (
                          <div className="text-muted-foreground mt-1">
                            {Object.entries(change.payload.params).slice(0, 3).map(([k, v]: any) => (
                              <span key={k} className="mr-2">{k}={JSON.stringify(v)}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => handleApplyChanges(message.changes!)}
                    className="w-full bg-brand-teal hover:bg-brand-dark-teal text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    <CheckCircleIcon className="h-4 w-4" />
                    Apply {message.changes.length} Blocks to Canvas
                  </button>
                </div>
              )}

              {/* Expected Impacts */}
              {message.expected_impacts && message.expected_impacts.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border/50">
                  <div className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                    Expected Impact
                  </div>
                  <div className="space-y-2">
                    {message.expected_impacts.map((impact: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <LightBulbIcon className="h-4 w-4 text-warning-500" />
                        <span className="font-medium">{impact.metric}:</span>
                        <span className={impact.delta.startsWith('+') ? 'text-success-600' : 'text-danger-600'}>
                          {impact.delta}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          (conf: {(impact.confidence * 100).toFixed(0)}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Changes */}
              {message.changes && message.changes.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border/50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs font-semibold text-muted-foreground uppercase">
                      Proposed Changes ({message.changes.length})
                    </div>
                    <Button 
                      size="sm" 
                      onClick={() => handleApplyChanges(message.changes!)}
                    >
                      <CheckCircleIcon className="h-4 w-4 mr-2" />
                      Apply
                    </Button>
                  </div>
                  <div className="space-y-1 text-xs font-mono">
                    {message.changes.map((change: any, i: number) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className={`
                          px-2 py-0.5 rounded
                          ${change.op === 'add' ? 'bg-success-500/10 text-success-600' :
                            change.op === 'update' ? 'bg-blue-500/10 text-blue-600' :
                            'bg-danger-500/10 text-danger-600'
                          }
                        `}>
                          {change.op}
                        </span>
                        <span>{change.target}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Next Steps */}
              {message.suggested_next_steps && message.suggested_next_steps.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border/50">
                  <div className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                    Suggested Next Steps
                  </div>
                  <ul className="space-y-1 text-sm">
                    {message.suggested_next_steps.map((step: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-brand-dark-teal mt-0.5">→</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <span className="text-sm font-semibold">You</span>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow flex items-center justify-center">
              <SparklesIcon className="h-5 w-5 text-white" />
            </div>
            <div className="bg-muted border border-border rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand-dark-teal" />
                <span className="text-sm text-muted-foreground">Analyzing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything... e.g., 'Build a mean-reversion strategy using RSI' or 'Why is my Sharpe ratio low?'"
            disabled={loading}
            rows={3}
            className="flex-1 px-4 py-3 border border-input rounded-lg bg-background resize-none focus:outline-none focus:ring-2 focus:ring-brand-dark-teal disabled:opacity-50"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="self-end"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </Button>
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}

