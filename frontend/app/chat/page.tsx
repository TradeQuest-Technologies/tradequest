'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  ArrowLeftIcon,
  PaperAirplaneIcon,
  UserIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import toast from 'react-hot-toast'
import AppShell from '../../components/AppShell'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  tools?: any[]
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your AI trading coach. I can analyze your trades, help you backtest strategies, and provide insights on your performance. What would you like to know?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/auth')
        return
      }

      // For now, simulate AI response
      // In production, this would call your AI endpoint
      setTimeout(() => {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: getSimulatedResponse(input.trim()),
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
        setIsLoading(false)
      }, 1000)

    } catch (error) {
      toast.error('Failed to send message')
      setIsLoading(false)
    }
  }

  const getSimulatedResponse = (userInput: string): string => {
    const input = userInput.toLowerCase()
    
    if (input.includes('analyze') || input.includes('trade')) {
      return "I'd be happy to analyze your trades! I can look at your recent trades, examine market context around your entries, and provide insights on execution quality. Try asking me to 'analyze my last trade' or 'analyze my trades from today'."
    } else if (input.includes('backtest') || input.includes('strategy')) {
      return "I can help you backtest trading strategies! I support SMA crossover, RSI mean reversion, and ATR trailing stop strategies. Try asking me to 'backtest SMA cross on BTC' or 'test RSI strategy on ETH'."
    } else if (input.includes('performance') || input.includes('stats')) {
      return "I can show you your trading performance metrics including win rate, P&L, drawdown, and best/worst performing symbols. I can also identify patterns in your trading behavior."
    } else if (input.includes('help') || input.includes('what can you do')) {
      return "I can help you with:\n• Trade analysis and execution quality\n• Strategy backtesting\n• Performance metrics and patterns\n• Market context around your trades\n• Risk management insights\n\nWhat would you like to explore?"
    } else {
      return "I understand you're asking about trading. I can help analyze your trades, backtest strategies, or review your performance. Could you be more specific about what you'd like to know?"
    }
  }

  const quickPrompts = [
    "Analyze my last trade",
    "Show my performance stats",
    "Backtest SMA cross on BTC",
    "What's my win rate?",
    "Analyze my trades from today"
  ]

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center mb-6">
          <CpuChipIcon className="h-6 w-6 text-brand-dark-teal mr-2" />
          <h1 className="text-xl font-semibold text-gray-900">AI Coach</h1>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-[600px] flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`flex-shrink-0 ${message.role === 'user' ? 'ml-3' : 'mr-3'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' 
                        ? 'bg-primary-600 text-white' 
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {message.role === 'user' ? (
                        <UserIcon className="h-5 w-5" />
                      ) : (
                        <CpuChipIcon className="h-5 w-5" />
                      )}
                    </div>
                  </div>
                  <div className={`px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="flex">
                  <div className="flex-shrink-0 mr-3">
                    <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center">
                      <CpuChipIcon className="h-5 w-5" />
                    </div>
                  </div>
                  <div className="px-4 py-2 rounded-lg bg-gray-100">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          {messages.length === 1 && (
            <div className="px-6 pb-4">
              <p className="text-sm text-gray-500 mb-2">Try asking:</p>
              <div className="flex flex-wrap gap-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <form onSubmit={handleSendMessage} className="flex space-x-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me about your trades, strategies, or performance..."
                className="flex-1 input"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="btn-primary"
              >
                <PaperAirplaneIcon className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
