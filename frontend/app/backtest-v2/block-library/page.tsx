'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '../../../components/layout/Sidebar'
import { Header } from '../../../components/layout/Header'
import { Button } from '../../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card'
import {
  ArrowLeftIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  StarIcon,
  CheckIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'

interface Block {
  id: string
  name: string
  description: string
  category: string
  downloads: number
  rating: number
  rating_count: number
  is_verified: boolean
  is_in_library: boolean
  tags: string[]
}

export default function BlockLibrary() {
  const router = useRouter()
  const [blocks, setBlocks] = useState<Block[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const categories = [
    { id: 'all', name: 'All Blocks' },
    { id: 'data', name: 'Data Sources' },
    { id: 'feature', name: 'Features & Indicators' },
    { id: 'signal', name: 'Signal Generation' },
    { id: 'sizing', name: 'Position Sizing' },
    { id: 'risk', name: 'Risk Management' },
    { id: 'exec', name: 'Execution' },
    { id: 'other', name: 'Other' }
  ]

  useEffect(() => {
    loadBlocks()
  }, [selectedCategory, searchQuery])

  const loadBlocks = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('tq_session')
      const params = new URLSearchParams()
      if (selectedCategory !== 'all') params.append('category', selectedCategory)
      if (searchQuery) params.append('search', searchQuery)

      const response = await fetch(`/api/v1/custom-blocks/blocks/public?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setBlocks(data)
      }
    } catch (error) {
      toast.error('Failed to load blocks')
    } finally {
      setLoading(false)
    }
  }

  const handleAddToLibrary = async (blockId: string) => {
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/custom-blocks/blocks/${blockId}/add-to-library`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success('Block added to your library!')
        // Update local state
        setBlocks(blocks.map(b => 
          b.id === blockId ? { ...b, is_in_library: true, downloads: b.downloads + 1 } : b
        ))
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to add block')
      }
    } catch (error) {
      toast.error('Failed to add block')
    }
  }

  const renderStars = (rating: number) => {
    const stars = []
    for (let i = 1; i <= 5; i++) {
      if (i <= rating) {
        stars.push(<StarSolidIcon key={i} className="h-4 w-4 text-yellow-500" />)
      } else {
        stars.push(<StarIcon key={i} className="h-4 w-4 text-gray-400" />)
      }
    }
    return stars
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
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold">Public Block Library</h1>
                  <p className="text-muted-foreground mt-2">
                    Browse and add community-created blocks to your library
                  </p>
                </div>
                <Button onClick={() => router.push('/backtest-v2/block-studio')}>
                  <CodeBracketIcon className="h-4 w-4 mr-2" />
                  Create Custom Block
                </Button>
              </div>
            </div>

            {/* Search and Filters */}
            <div className="mb-6 flex gap-4">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search blocks..."
                  className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background"
                />
              </div>
            </div>

            {/* Categories */}
            <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
              {categories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    selectedCategory === cat.id
                      ? 'bg-brand-teal text-white'
                      : 'bg-card text-muted-foreground hover:bg-muted'
                  }`}
                >
                  {cat.name}
                </button>
              ))}
            </div>

            {/* Can't find what you want? */}
            <Card className="mb-6 bg-gradient-to-r from-brand-dark-teal to-brand-teal border-brand-bright-yellow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">
                      Can't find what you need?
                    </h3>
                    <p className="text-gray-200">
                      Create your own custom block with Python and AI assistance
                    </p>
                  </div>
                  <Button
                    onClick={() => router.push('/backtest-v2/block-studio')}
                    variant="outline"
                    className="bg-white text-black hover:bg-gray-100"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Create Custom Block
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Blocks Grid */}
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-teal mx-auto"></div>
                <p className="text-muted-foreground mt-4">Loading blocks...</p>
              </div>
            ) : blocks.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <CodeBracketIcon className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No blocks found</h3>
                  <p className="text-muted-foreground mb-6">
                    Be the first to create a block in this category!
                  </p>
                  <Button onClick={() => router.push('/backtest-v2/block-studio')}>
                    Create Custom Block
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {blocks.map(block => (
                  <Card key={block.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg mb-1">
                            {block.name}
                            {block.is_verified && (
                              <CheckIcon className="inline-block h-4 w-4 ml-2 text-brand-teal" />
                            )}
                          </CardTitle>
                          <div className="text-xs text-muted-foreground capitalize">
                            {block.category}
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                        {block.description || 'No description provided'}
                      </p>

                      {/* Tags */}
                      {block.tags && block.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-4">
                          {block.tags.slice(0, 3).map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-muted text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Stats */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-1">
                          {renderStars(Math.round(block.rating))}
                          <span className="text-xs text-muted-foreground ml-1">
                            ({block.rating_count})
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {block.downloads} downloads
                        </div>
                      </div>

                      {/* Action */}
                      {block.is_in_library ? (
                        <Button
                          variant="outline"
                          className="w-full"
                          disabled
                        >
                          <CheckIcon className="h-4 w-4 mr-2" />
                          In Your Library
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleAddToLibrary(block.id)}
                          className="w-full"
                        >
                          <PlusIcon className="h-4 w-4 mr-2" />
                          Add to Library
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
