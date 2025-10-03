'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { useUser } from '../../hooks/useUser'
import { 
  PaperAirplaneIcon,
  SparklesIcon,
  ChartBarIcon,
  LightBulbIcon,
  CheckCircleIcon,
  ClockIcon,
  UserIcon,
  CpuChipIcon,
  CircleStackIcon,
  CodeBracketIcon,
  ChartPieIcon,
  BoltIcon,
  TrashIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as SolidCheckCircle } from '@heroicons/react/24/solid'
import { formatDateTime } from '../../lib/utils'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  suggestions?: string[]
  insights?: {
    type: 'success' | 'warning' | 'info'
    title: string
    description: string
  }[]
  thinking?: {
    operations: Array<{
      type: 'function_call' | 'data_fetch' | 'calculation'
      name: string
      status: 'running' | 'completed' | 'failed'
      details?: string
      result?: any
    }>
  }
}

interface Conversation {
  session_id: string
  title: string
  last_message: string
  message_count: number
  created_at: string
  updated_at: string
}

export default function AICoach() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysisPhase, setAnalysisPhase] = useState('')
  const [currentOperations, setCurrentOperations] = useState<any[]>([]) // Live streaming operations
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null) // ID of message being streamed
  const [expandedThinking, setExpandedThinking] = useState<string | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [sessionId, setSessionId] = useState<string>(() => {
    // Generate or retrieve session ID
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('tq_coach_session_id')
      if (stored) return stored
    }
    return `session-${Date.now()}`
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { user } = useUser()
  
  // Save session ID to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('tq_coach_session_id', sessionId)
    }
  }, [sessionId])

  // Initial welcome message
  useEffect(() => {
    setMessages([
      {
        id: '1',
        type: 'assistant',
        content: "# TradeQuest AI Analytics Engine Initialized\n\n**System Status**: ✅ ONLINE | **Data Access**: FULL | **Compute**: READY\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nI am your quantitative trading analyst - powered by large-scale data infrastructure, powered by advanced AI and real-time data access.\n\n## What I Can Do:\n\n🔍 **Forensic Trade Analysis**\n- Deep dive into every trade with OHLCV data\n- Calculate technical indicators (RSI, MACD, Moving Averages)\n- Identify hidden patterns and behavioral inconsistencies\n\n📊 **Statistical Intelligence**\n- Execute Python code for advanced calculations\n- Run correlation analysis, regression tests\n- Find statistically significant patterns in your data\n\n💡 **Actionable Insights**\n- Provide evidence-based recommendations\n- Quantify expected improvements\n- Generate specific, implementable trading rules\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nI have direct access to your complete trading history, real-time market data, and Python execution environment. Every insight is backed by actual calculations on YOUR data.\n\n**What would you like to analyze?**",
        timestamp: new Date().toISOString(),
        suggestions: [
          "Run forensic analysis on my losses",
          "Find patterns in my winning trades",
          "Calculate my edge by symbol and side",
          "Analyze my entry timing quality",
          "What's my statistically significant weakness?"
        ]
      }
    ])
  }, [])

  // Fetch conversations function
  const fetchConversations = async () => {
    if (!user) return
    
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/coach/conversations', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setConversations(data)
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    }
  }
  
  // Fetch conversations on mount
  useEffect(() => {
    fetchConversations()
  }, [user, sessionId])

  // Load conversation when session changes
  const loadConversation = async (newSessionId: string) => {
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/coach/conversations/${newSessionId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setMessages(data)
        setSessionId(newSessionId)
      }
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  // Delete conversation
  const deleteConversation = async (sessionIdToDelete: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent loading the conversation
    
    if (!confirm('Delete this conversation?')) return
    
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/coach/session/${sessionIdToDelete}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        // Remove from list
        setConversations(prev => prev.filter(c => c.session_id !== sessionIdToDelete))
        
        // If deleting current conversation, start a new one
        if (sessionIdToDelete === sessionId) {
          const newSessionId = `session-${Date.now()}`
          setSessionId(newSessionId)
          setMessages([{
            id: '1',
            type: 'assistant',
            content: "# TradeQuest AI Analytics Engine Initialized\n\n**System Status**: ✅ ONLINE | **Data Access**: FULL | **Compute**: READY\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nI am your quantitative trading analyst - powered by large-scale data infrastructure and advanced AI. I have direct access to your complete trading history and can execute Python code to calculate any indicator or perform statistical analysis.\n\n## My Capabilities:\n\n🔍 **Forensic Trade Analysis**\n- Deep dive into every trade with OHLCV data\n- Calculate technical indicators (RSI, MACD, Moving Averages, Bollinger Bands)\n- Identify hidden patterns and behavioral inconsistencies\n\n📊 **Statistical Intelligence**\n- Execute Python code for advanced calculations\n- Run correlation analysis, regression tests, clustering\n- Find statistically significant patterns in your data\n\n💡 **Actionable Insights**\n- Provide evidence-based recommendations\n- Quantify expected improvements\n- Generate specific, implementable trading rules\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nEvery insight is backed by actual calculations on YOUR data. Ask me anything about your trading performance.\n\n**What would you like to analyze?**",
            timestamp: new Date().toISOString(),
            suggestions: [
              "Run forensic analysis on my losses",
              "Find patterns in my winning trades",
              "Calculate my edge by symbol and side",
              "Analyze my entry timing quality",
              "What's my statistically significant weakness?"
            ]
          }])
        }
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Analysis phase is handled by the placeholder message now
  // No need for separate loading state

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setCurrentOperations([]) // Clear previous operations
    setAnalysisPhase('Initializing analysis...')
    
    // Create placeholder assistant message immediately
    const assistantId = (Date.now() + 1).toString()
    setActiveMessageId(assistantId)
    setExpandedThinking(assistantId) // Auto-expand
    
    const placeholderMessage: Message = {
      id: assistantId,
      type: 'assistant',
      content: '🔄 Analyzing your request...',
      timestamp: new Date().toISOString(),
      thinking: {
        operations: []
      }
    }
    setMessages(prev => [...prev, placeholderMessage])

    try {
      const token = localStorage.getItem('tq_session')
      
      // Use EventSource for SSE streaming
      const url = new URL('/api/v1/coach/chat/stream', window.location.origin)
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          message: userMessage.content,
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start chat stream')
      }

      // Read the streaming response
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No reader available')
      }
      
      const decoder = new TextDecoder()
      let buffer = ''
      let finalMessage = ''
      let operations: any[] = []

      console.log('Starting stream read...')

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('Stream done - reader finished')
          setLoading(false)
          setCurrentOperations([])
          setAnalysisPhase('')
          break
        }
        
        const chunk = decoder.decode(value, { stream: true })
        console.log('Received chunk:', chunk)
        buffer += chunk
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (!line.trim()) continue
          
          console.log('Processing line:', line)
          
          if (!line.startsWith('data: ')) {
            console.warn('Line does not start with data:', line)
            continue
          }
          
          try {
            const data = JSON.parse(line.substring(6))
            console.log('Parsed data:', data)
            
            if (data.type === 'operation') {
              // Update live operations
              console.log('Operation update:', data.data)
              
              // Check if this operation already exists (update it) or is new (push it)
              const existingIndex = operations.findIndex(op => op.name === data.data.name && op.type === data.data.type)
              
              if (existingIndex >= 0) {
                // Update existing operation
                operations[existingIndex] = data.data
              } else {
                // Add new operation
                operations.push(data.data)
              }
              
              // Update the placeholder message in real-time
              setMessages(prev => prev.map(msg => 
                msg.id === assistantId 
                  ? { ...msg, thinking: { operations: [...operations] } }
                  : msg
              ))
              
              // Update analysis phase
              if (data.data.status === 'running') {
                setAnalysisPhase(data.data.name)
              } else if (data.data.status === 'completed') {
                // Clear phase when completed
                setAnalysisPhase('')
              }
            } else if (data.type === 'final_message') {
              finalMessage = data.data.message
              setSessionId(data.data.session_id)
              
              // Update placeholder with final content
              setMessages(prev => prev.map(msg =>
                msg.id === assistantId
                  ? { ...msg, content: finalMessage }
                  : msg
              ))
            } else if (data.type === 'done') {
              // Stream complete - cleanup
              console.log('Stream complete with', operations.length, 'operations')
              
              setLoading(false)
              setCurrentOperations([])
              setAnalysisPhase('')
              setActiveMessageId(null)
              
              // Refresh conversations list
              fetchConversations()
            } else if (data.type === 'error') {
              throw new Error(data.data.error)
            }
          } catch (e) {
            console.error('Failed to parse SSE message:', e)
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      
      // Update placeholder message with error
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, content: 'Failed to process your message. Please try again.' }
          : msg
      ))
      
      setLoading(false)
      setCurrentOperations([])
      setAnalysisPhase('')
      setActiveMessageId(null)
    } finally {
      // Always cleanup loading state
      setLoading(false)
      setCurrentOperations([])
      setAnalysisPhase('')
    }
  }

  // Legacy non-streaming fallback (keep this commented out)
  /*
  const handleSendMessageLegacy = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch('/api/v1/coach/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          message: userMessage.content,
          session_id: sessionId
        })
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: Message = {
          insights: data.insights,
          thinking: data.thinking
        }
        setMessages(prev => [...prev, assistantMessage])
        
        // Auto-expand thinking section if there are operations
        if (data.thinking?.operations?.length > 0) {
          setExpandedThinking(assistantMessage.id)
        }
      } else {
        throw new Error('Failed to get response')
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "⚠️ **System Error**\n\nI'm having trouble accessing the analytics engine right now. Please try again in a moment.\n\nIf the issue persists, check your connection or contact support.",
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }
  */

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-success-600" />
      case 'warning':
        return <LightBulbIcon className="h-5 w-5 text-warning-600" />
      case 'info':
        return <LightBulbIcon className="h-5 w-5 text-info-600" />
      default:
        return <LightBulbIcon className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'border-success-200 bg-success-50 dark:bg-success-950 dark:border-success-800'
      case 'warning':
        return 'border-warning-200 bg-warning-50 dark:bg-warning-950 dark:border-warning-800'
      case 'info':
        return 'border-info-200 bg-info-50 dark:bg-info-950 dark:border-info-800'
      default:
        return 'border-border bg-card'
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar className="w-64 fixed left-0 top-0 bottom-0" />
      
      <div className="flex-1 flex flex-col ml-64">
        <Header />
        
        <main className="flex-1 flex gap-6 p-6 overflow-hidden">
          {/* Left: Conversations & System Status */}
          <div className="w-80 flex flex-col gap-4 overflow-hidden">
            {/* Conversations List */}
            <Card className="border-border/50 flex-1 flex flex-col min-h-0">
              <div className="p-4 border-b border-border flex items-center justify-between flex-shrink-0">
                <h3 className="font-bold text-foreground">Conversations</h3>
                <Button
                  size="sm"
                  onClick={() => {
                    const newSessionId = `session-${Date.now()}`
                    setSessionId(newSessionId)
                    setMessages([{
                      id: '1',
                      type: 'assistant',
                      content: "# TradeQuest AI Analytics Engine Initialized\n\n**System Status**: ✅ ONLINE | **Data Access**: FULL | **Compute**: READY\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nI am your quantitative trading analyst - powered by large-scale data infrastructure and advanced AI. I have direct access to your complete trading history and can execute Python code to calculate any indicator or perform statistical analysis.\n\n## My Capabilities:\n\n🔍 **Forensic Trade Analysis**\n- Deep dive into every trade with OHLCV data\n- Calculate technical indicators (RSI, MACD, Moving Averages, Bollinger Bands)\n- Identify hidden patterns and behavioral inconsistencies\n\n📊 **Statistical Intelligence**\n- Execute Python code for advanced calculations\n- Run correlation analysis, regression tests, clustering\n- Find statistically significant patterns in your data\n\n💡 **Actionable Insights**\n- Provide evidence-based recommendations\n- Quantify expected improvements\n- Generate specific, implementable trading rules\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nEvery insight is backed by actual calculations on YOUR data. Ask me anything about your trading performance.\n\n**What would you like to analyze?**",
                      timestamp: new Date().toISOString(),
                      suggestions: [
                        "Run forensic analysis on my losses",
                        "Find patterns in my winning trades",
                        "Calculate my edge by symbol and side",
                        "Analyze my entry timing quality",
                        "What's my statistically significant weakness?"
                      ]
                    }])
                  }}
                  className="text-xs"
                >
                  + New
                </Button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {conversations.map((conv) => (
                  <div
                    key={conv.session_id}
                    className={`group relative rounded-lg transition-colors ${
                      conv.session_id === sessionId
                        ? 'bg-brand-dark-teal/10 border border-brand-dark-teal/30'
                        : 'hover:bg-secondary'
                    }`}
                  >
                    <button
                      onClick={() => loadConversation(conv.session_id)}
                      className="w-full text-left p-3 pr-10"
                    >
                      <div className="font-medium text-sm text-foreground line-clamp-1">
                        {conv.title}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {conv.message_count} messages • {new Date(conv.updated_at).toLocaleDateString()}
                      </div>
                    </button>
                    
                    {/* Delete button - shows on hover */}
                    <button
                      onClick={(e) => deleteConversation(conv.session_id, e)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded opacity-0 group-hover:opacity-100 hover:bg-destructive/10 transition-opacity"
                      title="Delete conversation"
                    >
                      <TrashIcon className="h-4 w-4 text-destructive" />
                    </button>
                  </div>
                ))}
                
                {conversations.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    No conversations yet.<br />Start chatting to create one!
                  </div>
                )}
              </div>
            </Card>
            
            {/* System Status */}
            <div className="flex flex-col gap-4">
            {/* System Status */}
            <Card className="border-2 border-brand-dark-teal/20 bg-gradient-to-br from-card to-brand-dark-teal/5">
              <div className="p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-brand-dark-teal/10 rounded-lg">
                    <CpuChipIcon className="h-6 w-6 text-brand-dark-teal" />
                  </div>
                  <div>
                    <h3 className="font-bold text-foreground">System Status</h3>
                    <p className="text-xs text-muted-foreground">Analytics Engine</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
                      <span className="text-sm text-muted-foreground">AI Model</span>
                    </div>
                    <Badge variant="success" className="text-xs">ONLINE</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
                      <span className="text-sm text-muted-foreground">Database</span>
                    </div>
                    <Badge variant="success" className="text-xs">CONNECTED</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
                      <span className="text-sm text-muted-foreground">OHLCV Service</span>
                    </div>
                    <Badge variant="success" className="text-xs">READY</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
                      <span className="text-sm text-muted-foreground">Python Executor</span>
                    </div>
                    <Badge variant="success" className="text-xs">READY</Badge>
                  </div>
                </div>
              </div>
            </Card>

            {/* Capabilities */}
            <Card className="border-border/50">
              <div className="p-4">
                <h3 className="font-bold text-foreground mb-3 flex items-center gap-2">
                  <BoltIcon className="h-5 w-5 text-brand-bright-yellow" />
                  Analytical Capabilities
                </h3>
                
                <div className="space-y-2">
                  <div className="flex items-start gap-2 text-sm">
                    <CircleStackIcon className="h-4 w-4 text-brand-dark-teal mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">Direct database access</span>
                  </div>
                  <div className="flex items-start gap-2 text-sm">
                    <ChartBarIcon className="h-4 w-4 text-brand-dark-teal mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">Multi-timeframe OHLCV</span>
                  </div>
                  <div className="flex items-start gap-2 text-sm">
                    <CodeBracketIcon className="h-4 w-4 text-brand-dark-teal mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">Python code execution</span>
                  </div>
                  <div className="flex items-start gap-2 text-sm">
                    <ChartPieIcon className="h-4 w-4 text-brand-dark-teal mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">Statistical analysis</span>
                  </div>
                </div>
              </div>
            </Card>

            </div>
          </div>

          {/* Right: Chat Interface */}
          <div className="flex-1 flex flex-col bg-card border border-border rounded-lg overflow-hidden">
            {/* Header */}
            <div className="border-b border-border bg-gradient-to-r from-brand-dark-teal/10 to-brand-bright-yellow/10 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow rounded-lg brand-glow">
                    <SparklesIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow bg-clip-text text-transparent">
                      TradeQuest AI Analytics
                    </h1>
                    <p className="text-sm text-muted-foreground">
                      Enterprise-Grade Trading Intelligence
                    </p>
                  </div>
                </div>
                
                <div className="px-3 py-1 rounded-full bg-success-500/10 border border-success-500/20 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
                  <span className="text-xs font-medium text-success-600 dark:text-success-400">LIVE</span>
                </div>
              </div>
            </div>

            {/* Loading/Auth State */}
            {!user && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-dark-teal mx-auto mb-4" />
                  <p className="text-muted-foreground">Initializing analytics engine...</p>
                </div>
              </div>
            )}

            {/* Messages */}
            {user && (
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-background/50 to-background">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-3xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                    <div className="flex items-start gap-3">
                      {message.type === 'assistant' && (
                        <div className="p-2 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow rounded-full brand-glow flex-shrink-0">
                          <SparklesIcon className="h-5 w-5 text-white" />
                        </div>
                      )}
                      
                      <div className="flex-1">
                        <div
                          className={`p-4 rounded-lg ${
                            message.type === 'user'
                              ? 'bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow text-white brand-glow'
                              : 'bg-card border border-border/50 hover-card'
                          }`}
                        >
                          <div className="whitespace-pre-wrap prose prose-sm dark:prose-invert max-w-none">
                            {message.content.split('\n').map((line, i) => {
                              // Check for image markdown: ![alt](url) or direct image references
                              const imageMatch = line.match(/!\[([^\]]*)\]\(([^\)]+)\)/)
                              if (imageMatch) {
                                const [, alt, imagePath] = imageMatch
                                // Convert relative path to API URL (includes user_id for security)
                                const imageUrl = imagePath.startsWith('http') 
                                  ? imagePath 
                                  : `${process.env.NEXT_PUBLIC_API_URL}/api/v1/coach/image/${user?.id}/${sessionId}/${imagePath}`
                                return (
                                  <div key={i} className="my-4">
                                    <img 
                                      src={imageUrl} 
                                      alt={alt} 
                                      className="rounded-lg shadow-lg max-w-full h-auto border border-border/50"
                                      onError={(e) => {
                                        console.error('Image load error:', imageUrl)
                                        e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23333" width="400" height="300"/%3E%3Ctext fill="%23666" x="50%25" y="50%25" text-anchor="middle"%3EImage not found%3C/text%3E%3C/svg%3E'
                                      }}
                                    />
                                    {alt && <p className="text-sm text-muted-foreground text-center mt-2">{alt}</p>}
                                  </div>
                                )
                              }
                              
                              // Simple markdown-like rendering
                              if (line.startsWith('# ')) {
                                return <h1 key={i} className="text-2xl font-bold mb-2 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow bg-clip-text text-transparent">{line.slice(2)}</h1>
                              } else if (line.startsWith('## ')) {
                                return <h2 key={i} className="text-xl font-bold mb-2 mt-4">{line.slice(3)}</h2>
                              } else if (line.startsWith('### ')) {
                                return <h3 key={i} className="text-lg font-semibold mb-2 mt-3">{line.slice(4)}</h3>
                              } else if (line.startsWith('**') && line.endsWith('**')) {
                                return <p key={i} className="font-bold">{line.slice(2, -2)}</p>
                              } else if (line.startsWith('- ')) {
                                return <li key={i} className="ml-4">{line.slice(2)}</li>
                              } else if (line.match(/^[0-9]+\. /)) {
                                return <li key={i} className="ml-4 list-decimal">{line.replace(/^[0-9]+\. /, '')}</li>
                              } else if (line.startsWith('━━━')) {
                                return <hr key={i} className="my-4 border-border" />
                              } else if (line.trim() === '') {
                                return <br key={i} />
                              } else {
                                // Handle inline bold and emojis
                                const parts = line.split(/(\*\*.*?\*\*|🔍|📊|💡|✅|❌|⚠️)/g)
                                return (
                                  <p key={i} className={message.type === 'user' ? 'text-white' : ''}>
                                    {parts.map((part, j) => {
                                      if (part.startsWith('**') && part.endsWith('**')) {
                                        return <strong key={j}>{part.slice(2, -2)}</strong>
                                      } else if (['🔍', '📊', '💡', '✅', '❌', '⚠️'].includes(part)) {
                                        return <span key={j} className="inline-block mx-1">{part}</span>
                                      }
                                      return part
                                    })}
                                  </p>
                                )
                              }
                            })}
                          </div>
                        </div>
                        
                        {/* Thinking Process - Integrated */}
                        {message.type === 'assistant' && message.thinking?.operations && Array.isArray(message.thinking.operations) && message.thinking.operations.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-border/30">
                            {/* Show current operation if still loading */}
                            {/* Loading indicator removed - handled by placeholder message content */}
                            
                            <button
                              onClick={() => setExpandedThinking(expandedThinking === message.id ? null : message.id)}
                              className="w-full text-left group"
                            >
                              <div className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                                <CodeBracketIcon className="h-4 w-4" />
                                <span className="font-medium">
                                  {message.id === activeMessageId && loading ? 'Analysis in progress' : 'View thought process'}
                                </span>
                                <span className="text-xs opacity-60">
                                  ({message.thinking.operations.length} operations)
                                </span>
                                <span className="ml-auto text-xs">
                                  {expandedThinking === message.id ? '▼ Collapse' : '▶ Expand'}
                                </span>
                              </div>
                            </button>
                            
                            {expandedThinking === message.id && (
                              <div className="mt-2 p-4 rounded-lg border border-border/50 bg-card space-y-3">
                                {message.thinking.operations.map((op: any, idx: number) => {
                                  if (!op) return null
                                  
                                  return (
                                    <div key={idx} className="flex items-start gap-3">
                                      <div className="flex-shrink-0 mt-1">
                                        {op.status === 'completed' && (
                                          <CheckCircleIcon className="h-5 w-5 text-success-500" />
                                        )}
                                        {op.status === 'running' && (
                                          <div className="w-5 h-5 rounded-full border-2 border-brand-dark-teal border-t-transparent animate-spin" />
                                        )}
                                        {op.status === 'failed' && (
                                          <XCircleIcon className="h-5 w-5 text-warning-500" />
                                        )}
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                          <span className="font-medium text-sm">{op.name || 'Operation'}</span>
                                          <Badge 
                                            variant={op.status === 'completed' ? 'success' : op.status === 'failed' ? 'warning' : 'default'}
                                            className="text-xs"
                                          >
                                            {op.status || 'unknown'}
                                          </Badge>
                                        </div>
                                        {op.details && (
                                          <pre className="text-xs text-muted-foreground mt-1 whitespace-pre-wrap font-mono bg-muted/50 p-2 rounded max-h-32 overflow-auto">
                                            {String(op.details)}
                                          </pre>
                                        )}
                                        {op.result && (
                                          <div className="text-xs text-success-600 dark:text-success-400 mt-1">
                                            ✓ {String(op.result)}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {/* Insights */}
                        {message.insights && message.insights.length > 0 && (
                          <div className="mt-3 space-y-2">
                            {message.insights.map((insight, index) => (
                              <div
                                key={index}
                                className={`p-3 rounded-lg border ${getInsightColor(insight.type)} hover-card`}
                              >
                                <div className="flex items-start gap-2">
                                  {getInsightIcon(insight.type)}
                                  <div>
                                    <h4 className="font-medium text-sm">{insight.title}</h4>
                                    <p className="text-sm text-muted-foreground mt-1">
                                      {insight.description}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        {/* Suggestions */}
                        {message.suggestions && message.suggestions.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {message.suggestions.map((suggestion, index) => (
                              <Button
                                key={index}
                                variant="outline"
                                size="sm"
                                onClick={() => handleSuggestionClick(suggestion)}
                                className="text-xs hover:border-brand-dark-teal hover:text-brand-dark-teal transition-colors"
                              >
                                {suggestion}
                              </Button>
                            ))}
                          </div>
                        )}
                        
                        <p className="text-xs text-muted-foreground mt-2">
                          {formatDateTime(message.timestamp)}
                        </p>
                      </div>
                      
                      {message.type === 'user' && (
                        <div className="p-2 bg-muted rounded-full flex-shrink-0">
                          <UserIcon className="h-5 w-5 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              <div ref={messagesEndRef} />
            </div>
            )}

            {/* Input */}
            {user && (
            <div className="border-t border-border p-4 bg-card">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me anything about your trading... (e.g., 'Analyze my losses', 'Calculate RSI for my last trade')"
                    className="w-full px-4 py-3 pr-12 border-2 border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-transparent transition-all"
                    disabled={loading}
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={loading || !input.trim()}
                  className="px-6 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow hover:opacity-90 transition-opacity"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </Button>
              </div>
            </div>
            )}
          </div>
        </main>
      </div>
      
      <style jsx global>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  )
}
