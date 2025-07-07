import React from 'react'

interface TerminalProps {
  commandText: string
  outputText: string
}

const Terminal: React.FC<TerminalProps> = ({ commandText, outputText }) => {
  return (
    <div className="bg-black text-green-400 font-mono rounded-lg p-4 w-full overflow-hidden">
      {commandText && (
        <div className="mb-2 break-words">
          <span className="text-blue-400">$ </span>
          <span className="text-green-400">{commandText}</span>
        </div>
      )}
      {outputText && (
        <div className="text-white text-sm leading-relaxed whitespace-pre-wrap break-words overflow-x-auto">
          {outputText}
        </div>
      )}
    </div>
  )
}

export default Terminal
