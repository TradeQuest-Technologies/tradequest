'use client'

import { useState } from 'react'
import { Button } from '../ui/Button'
import { PlayIcon, CodeBracketIcon } from '@heroicons/react/24/outline'

export default function CodePad() {
  const [code, setCode] = useState(`# Python Code Pad
# Write custom analysis or strategy logic here

import pandas as pd
import numpy as np

# Example: Calculate custom indicator
def custom_indicator(df):
    return df['close'].rolling(20).mean()

# Access data from blocks via context
# result = custom_indicator(df)
`)

  const [output, setOutput] = useState('')

  const handleRun = () => {
    setOutput('Code execution not implemented yet.\nThis will run in a sandboxed Python environment.')
  }

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-border bg-muted/20 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CodeBracketIcon className="h-5 w-5 text-brand-dark-teal" />
          <span className="font-semibold">Python Code Pad</span>
        </div>
        <Button size="sm" onClick={handleRun}>
          <PlayIcon className="h-4 w-4 mr-2" />
          Run
        </Button>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Editor */}
        <div className="flex-1 overflow-auto">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-full p-4 font-mono text-sm bg-background resize-none focus:outline-none"
            spellCheck={false}
          />
        </div>

        {/* Output */}
        {output && (
          <div className="h-48 border-t border-border bg-muted/50 overflow-auto">
            <div className="p-4">
              <div className="text-xs font-semibold text-muted-foreground uppercase mb-2">Output</div>
              <pre className="font-mono text-sm whitespace-pre-wrap">{output}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

