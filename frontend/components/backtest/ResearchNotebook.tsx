'use client'

import { DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline'

export default function ResearchNotebook() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="mb-4">
          <DocumentTextIcon className="h-16 w-16 mx-auto text-muted-foreground opacity-50" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Research Notebook</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Auto-generated documentation of your backtesting iterations, what you tried, and what worked.
        </p>
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <SparklesIcon className="h-4 w-4" />
          <span>Coming soon - AI will document your research journey</span>
        </div>
      </div>
    </div>
  )
}

