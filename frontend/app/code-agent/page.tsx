"use client"

import { useState } from 'react'
import Terminal from '@/components/Terminal'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'

export default function CodeAgentPage() {
  const [command, setCommand] = useState('')
  const [output, setOutput] = useState('')

  const handleRun = () => {
    setOutput(`Running code agent with:\n${command}\n\n(backend logic not implemented)`)
  }

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-10 bg-gray-50 dark:bg-gray-900">
      <h1 className="text-2xl font-bold mb-6 text-gray-800 dark:text-gray-200">Code Agent</h1>
      <div className="w-full max-w-3xl space-y-4">
        <Textarea
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Enter instruction for the code agent"
          className="bg-white dark:bg-gray-800"
        />
        <Button onClick={handleRun}>Run</Button>
        <Terminal input={command} output={output} />
      </div>
    </div>
  )
}
