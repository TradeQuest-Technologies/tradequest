'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '../ui/Button'
import {
  PaperAirplaneIcon,
  SparklesIcon,
  LightBulbIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
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
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '👋 Hi! I\'m your AI Copilot for backtesting. I can help you:\n\n• Design strategies from scratch\n• Optimize parameters\n• Diagnose issues (overfit, leakage, poor metrics)\n• Add risk management\n• Run walk-forward validation\n\nWhat would you like to build?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtest/v2/copilot`, {
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

      if (response.ok) {
        const data = await response.json()
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.message,
          changes: data.changes,
          expected_impacts: data.expected_impacts,
          suggested_next_steps: data.suggested_next_steps
        }

        setMessages(prev => [...prev, assistantMessage])
      } else {
        throw new Error('Failed to get copilot response')
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
    // Apply changes to graph
    console.log('Applying changes:', changes)
    // TODO: Implement actual graph mutation
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
              <div className="whitespace-pre-wrap text-sm">{message.content}</div>

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

