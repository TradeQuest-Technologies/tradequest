'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Sidebar } from '../../components/layout/Sidebar'
import { Header } from '../../components/layout/Header'
import { MobileNav } from '../../components/layout/MobileNav'
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
  XCircleIcon,
  SpeakerWaveIcon,
  PaperClipIcon,
  MicrophoneIcon,
  DocumentIcon,
  PauseIcon as StopIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as SolidCheckCircle } from '@heroicons/react/24/solid'
import { formatDateTime, cn } from '../../lib/utils'
import { getAuthToken } from '../../lib/auth'
import { HelpButton } from '../../components/onboarding/HelpButton'
import { ContextualHelpTooltip } from '../../components/onboarding/ContextualHelpTooltip'
import toast from 'react-hot-toast'

// Utility functions for operation rendering
const getOperationIcon = (type: string) => {
  switch(type) {
    case 'code': return <CodeBracketIcon className="w-4 h-4" />
    case 'chart': return <ChartBarIcon className="w-4 h-4" />
    case 'analysis': return <CpuChipIcon className="w-4 h-4" />
    default: return <SparklesIcon className="w-4 h-4" />
  }
}

const getOperationStatusIcon = (status: string) => {
  switch(status) {
    case 'completed': return <SolidCheckCircle className="w-4 h-4 text-green-500" />
    case 'running': return <ClockIcon className="w-4 h-4 text-blue-500 animate-pulse" />
    case 'error': return <XCircleIcon className="w-4 h-4 text-red-500" />
    default: return null
  }
}

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
  const router = useRouter()
  const searchParams = useSearchParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  
  // Check for pre-filled message from URL params
  useEffect(() => {
    const messageParam = searchParams?.get('message')
    if (messageParam && !input) {
      // Only set if input is empty (don't overwrite user's current input)
      try {
        // Try to decode, but handle malformed URIs gracefully
        const decoded = decodeURIComponent(messageParam)
        setInput(decoded)
      } catch (e) {
        // If decoding fails (malformed URI), use the param as-is
        console.warn('Failed to decode message param, using as-is:', e)
        setInput(messageParam)
      }
      // Clear the URL param after setting the message
      const url = new URL(window.location.href)
      url.searchParams.delete('message')
      window.history.replaceState({}, '', url.pathname + url.search)
    }
  }, [searchParams])
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
  
  // Enhanced features
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [coachMode, setCoachMode] = useState<'aggressive' | 'conservative' | 'balanced'>('balanced')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const recognitionRef = useRef<any>(null)
  const synthesisRef = useRef<SpeechSynthesis | null>(null)
  const { user } = useUser()
  
  // Save session ID to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('tq_coach_session_id', sessionId)
    }
  }, [sessionId])

  // Initialize voice features
  useEffect(() => {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = false
      recognitionRef.current.lang = 'en-US'
      
      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        setInput(transcript)
        setIsListening(false)
      }
      
      recognitionRef.current.onerror = () => {
        setIsListening(false)
      }
    }

    // Initialize speech synthesis
    synthesisRef.current = window.speechSynthesis
  }, [])

  // Initial welcome message
  useEffect(() => {
    setMessages([
      {
        id: '1',
        type: 'assistant',
        content: "# 🎯 Enhanced AI Trading Coach\n\n**System Status**: ✅ ONLINE | **Voice**: 🎤 READY | **Multi-Modal**: 📎 ACTIVE\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nI'm your advanced AI trading coach with enhanced capabilities:\n\n## 🚀 Enhanced Features:\n\n🎤 **Voice Interaction**\n- Speak your questions naturally\n- Listen to responses with text-to-speech\n- Hands-free trading analysis\n\n📎 **Multi-Modal Input**\n- Upload chart screenshots for analysis\n- Share trade documents for review\n- Visual pattern recognition\n\n💡 **Smart Suggestions**\n- Context-aware question recommendations\n- Personalized coaching based on your data\n- Adaptive learning from your preferences\n\n🎯 **Coach Modes**\n- **Aggressive**: Direct, no-nonsense feedback\n- **Conservative**: Gentle, supportive guidance\n- **Balanced**: Professional, data-driven insights\n\n## 🔍 Core Capabilities:\n\n**Forensic Trade Analysis**\n- Deep dive into every trade with OHLCV data\n- Calculate technical indicators (RSI, MACD, Moving Averages)\n- Identify hidden patterns and behavioral inconsistencies\n\n**Statistical Intelligence**\n- Execute Python code for advanced calculations\n- Run correlation analysis, regression tests\n- Find statistically significant patterns in your data\n\n**Actionable Insights**\n- Provide evidence-based recommendations\n- Quantify expected improvements\n- Generate specific, implementable trading rules\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**Try asking me something or use voice input!**",
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
      const token = getAuthToken()
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
      const token = getAuthToken()
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
      const token = getAuthToken()
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

  // Voice control functions
  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true)
      recognitionRef.current.start()
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }

  const speakText = (text: string) => {
    if (synthesisRef.current && voiceEnabled) {
      // Stop any current speech
      synthesisRef.current.cancel()
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.9
      utterance.pitch = 1
      utterance.volume = 0.8
      
      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      
      synthesisRef.current.speak(utterance)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      console.log('File selected:', file.name)
    }
  }

  // Analysis phase is handled by the placeholder message now
  // No need for separate loading state

  const handleSendMessage = async () => {
    if ((!input.trim() && !selectedFile) || loading) return

    let messageContent = input.trim()
    let fileUrl: string | null = null

    // Upload file first if one is selected
    if (selectedFile) {
      try {
        const token = getAuthToken()
        const formData = new FormData()
        formData.append('file', selectedFile)
        if (sessionId) {
          formData.append('session_id', sessionId)
        }

        const uploadResponse = await fetch('/api/v1/coach/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        })

        if (!uploadResponse.ok) {
          const errorData = await uploadResponse.json()
          throw new Error(errorData.detail || 'Failed to upload file')
        }

        const uploadData = await uploadResponse.json()
        fileUrl = uploadData.url || uploadData.relative_path

        // Build absolute URL if relative
        if (fileUrl && !fileUrl.startsWith('http')) {
          const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          fileUrl = `${apiBase}${fileUrl.startsWith('/') ? '' : '/'}${fileUrl}`
        }

        // Add image reference to message content
        if (selectedFile.type.startsWith('image/')) {
          messageContent = messageContent 
            ? `${messageContent}\n\n![${selectedFile.name}](${fileUrl})`
            : `![${selectedFile.name}](${fileUrl})`
        } else {
          messageContent = messageContent
            ? `${messageContent}\n\n[Attachment: ${selectedFile.name}](${fileUrl})`
            : `[Attachment: ${selectedFile.name}](${fileUrl})`
        }
      } catch (error) {
        console.error('File upload error:', error)
        toast.error(error instanceof Error ? error.message : 'Failed to upload file')
        return
      }
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: messageContent,
      timestamp: new Date().toISOString()
    }

    const assistantId = `assistant-${Date.now()}`

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setSelectedFile(null) // Clear selected file after sending
    if (fileInputRef.current) {
      fileInputRef.current.value = '' // Reset file input
    }
    setLoading(true)
    setCurrentOperations([])
    setAnalysisPhase('')
    setActiveMessageId(assistantId)

    try {
      const token = getAuthToken()
      
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
      let operations: any[] = []

      while (true) {
        const { done, value } = await reader.read()
        
        // Process chunk BEFORE checking done
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          buffer += chunk
        }
        
        // Process all complete lines in buffer
        // Backend sends LITERAL \n characters (backslash-n), not actual newlines!
        // So we need to split by the literal string "\\n\\n"
        let lines = buffer.split('\\n\\n')
        
        // If stream is done, process all remaining lines including the last one
        // Otherwise, keep the last (potentially incomplete) line in buffer
        if (!done) {
          buffer = lines.pop() || ''
        } else {
          buffer = ''
        }
        
        for (const line of lines) {
          if (!line.trim()) continue
          
          if (!line.startsWith('data: ')) {
            continue
          }
          
          try {
            // Remove "data: " prefix
            let jsonStr = line.substring(6)
            
            // The backend sends escaped JSON (with \" and \\n), so we need to unescape it
            let data
            try {
              // Try parsing as-is first (in case it's properly formatted)
              data = JSON.parse(jsonStr)
            } catch (firstError) {
              // If that fails, the string is double-escaped, so unescape by wrapping in quotes and parsing
              const unescapedStr = JSON.parse(`"${jsonStr}"`)
              data = JSON.parse(unescapedStr)
            }
            
            if (data.type === 'operation') {
              // Update live operations
              // Check if this operation already exists (update it) or is new (push it)
              const existingIndex = operations.findIndex(op => op.name === data.data.name && op.type === data.data.type)
              
              if (existingIndex >= 0) {
                // Update existing operation
                operations[existingIndex] = data.data
              } else {
                // Add new operation
                operations.push(data.data)
              }
              
              // Store operations for live loading indicator
              setCurrentOperations([...operations])
              
              // Update analysis phase
              if (data.data.status === 'running') {
                setAnalysisPhase(data.data.name)
              }
            } else if (data.type === 'final_message') {
              const finalMessage = data.data.message
              setSessionId(data.data.session_id)
              
              // Add complete assistant message as NEW entry (not updating placeholder)
              const completeMessage: Message = {
                id: assistantId,
                type: 'assistant',
                content: finalMessage,
                timestamp: new Date().toISOString(),
                thinking: operations.length > 0 ? { operations: [...operations] } : undefined
              }
              
              setMessages(prev => [...prev, completeMessage])
              
              // Clear loading states
              setLoading(false)
              setCurrentOperations([])
              setAnalysisPhase('')
              setActiveMessageId(null)
              
              // Scroll to bottom
              setTimeout(() => {
                messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
              }, 100)
            } else if (data.type === 'done') {
              // Refresh conversations list
              fetchConversations()
            } else if (data.type === 'error') {
              throw new Error(data.data.error)
            }
          } catch (e) {
            console.error('Failed to parse SSE message:', e)
          }
        }
        
        // Check if stream is done AFTER processing all lines
        if (done) {
          break
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      toast.error('Failed to process your message. Please try again.')
      
      setLoading(false)
      setCurrentOperations([])
      setAnalysisPhase('')
      setActiveMessageId(null)
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
      const token = getAuthToken()
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

  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background flex mobile-nav-padding">
      <Sidebar 
        className="w-64 flex-shrink-0 z-30" 
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
      />
      
      <div className="flex-1 flex flex-col lg:ml-0">
        <Header onMobileMenuToggle={() => setIsMobileSidebarOpen(true)} />
        
        <main className="flex-1 flex gap-6 p-4 lg:p-6 overflow-hidden">
          {/* Left: Conversations & System Status */}
          <div className="w-80 flex flex-col gap-4 h-full overflow-hidden">
            {/* Conversations List */}
            <Card className="border-border/50 h-[420px] flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border flex items-center justify-between flex-shrink-0">
                <h3 className="font-bold text-foreground">Conversations</h3>
                <div className="flex items-center gap-2">
                  <HelpButton page="coach" />
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
              </div>
              
              <div className="flex-1 overflow-y-auto p-2 space-y-1 brand-scrollbar">
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
          <div className="flex-1 flex flex-col bg-card border border-border rounded-lg overflow-hidden h-full">
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
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-background/50 to-background brand-scrollbar">
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
              
              {/* Live Loading Indicator */}
              {loading && currentOperations.length > 0 && (
                <div className="flex justify-start">
                  <div className="max-w-3xl">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gradient-to-br from-brand-dark-teal to-brand-bright-yellow rounded-full brand-glow flex-shrink-0 animate-pulse">
                        <SparklesIcon className="h-5 w-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="p-4 rounded-lg bg-card border border-border/50">
                          <div className="text-sm font-medium text-foreground mb-3">
                            🔄 {analysisPhase || 'Processing...'}
                          </div>
                          <div className="space-y-2">
                            {currentOperations.map((op, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                                {getOperationIcon(op.type)}
                                <span className="font-medium">{op.name}</span>
                                <span className="flex-1">{op.details || op.status}</span>
                                {getOperationStatusIcon(op.status)}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            )}

            {/* Enhanced Input */}
            {user && (
            <div className="border-t border-border p-4 bg-card">
              {/* Coach Controls */}
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Coach Mode:</span>
                    <select
                      value={coachMode}
                      onChange={(e) => setCoachMode(e.target.value as any)}
                      className="px-2 py-1 border border-border rounded bg-background text-sm"
                    >
                      <option value="aggressive">Aggressive</option>
                      <option value="conservative">Conservative</option>
                      <option value="balanced">Balanced</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant={voiceEnabled ? "default" : "outline"}
                      size="sm"
                      onClick={() => setVoiceEnabled(!voiceEnabled)}
                      className="flex items-center space-x-1"
                    >
                      <SpeakerWaveIcon className="h-4 w-4" />
                      <span>Voice</span>
                    </Button>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-1">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      voiceEnabled ? "bg-green-500" : "bg-gray-400"
                    )} />
                    <span>Voice {voiceEnabled ? 'On' : 'Off'}</span>
                  </div>
                  {isSpeaking && (
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                      <span>Speaking</span>
                    </div>
                  )}
                </div>
              </div>

              {/* File Upload */}
              {selectedFile && (
                <div className="mb-4 flex items-center space-x-2 p-2 bg-muted rounded-lg">
                  <DocumentIcon className="h-4 w-4" />
                  <span className="text-sm">{selectedFile.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                    className="p-1"
                  >
                    ×
                  </Button>
                </div>
              )}

              {/* Input Controls */}
              <div className="flex gap-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  className="hidden"
                  accept="image/*,.pdf,.doc,.docx"
                />
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center space-x-1"
                >
                  <PaperClipIcon className="h-4 w-4" />
                  <span>Attach</span>
                </Button>
                
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me anything about your trading... (e.g., 'Analyze my losses', 'Calculate RSI for my last trade')"
                    className="w-full px-4 py-3 pr-20 border-2 border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-dark-teal focus:border-transparent transition-all"
                    disabled={loading}
                  />
                  
                  <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                    {isListening ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={stopListening}
                        className="p-1 text-red-500"
                      >
                        <StopIcon className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={startListening}
                        className="p-1"
                      >
                        <MicrophoneIcon className="h-4 w-4" />
                      </Button>
                    )}
                    
                    <Button
                      onClick={handleSendMessage}
                      disabled={loading || !input.trim()}
                      className="px-3 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow hover:opacity-90 transition-opacity"
                    >
                      <PaperAirplaneIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
              
              {/* Voice Status */}
              {isListening && (
                <div className="mt-2 flex items-center space-x-2 text-sm text-blue-600">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span>Listening... Speak now</span>
                </div>
              )}
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
