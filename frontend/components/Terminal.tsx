import React from 'react'

interface TerminalProps {
  input: string
  output: string
}

const Terminal: React.FC<TerminalProps> = ({ input, output }) => {
  return (
    <div className="bg-black text-green-400 font-mono rounded-md p-4 whitespace-pre-wrap">
      {input && (
        <div className="mb-2">
          <span className="text-blue-400">$ </span>
          {input}
        </div>
      )}
      {output && (
        <pre className="text-white">{output}</pre>
      )}
    </div>
  )
}

export default Terminal
