import React from 'react';
import Terminal from './Terminal';

interface CodexTerminalProps {
  thinkingText: string;
  commandText: string;
  outputText: string;
}

const CodexTerminal: React.FC<CodexTerminalProps> = ({ thinkingText, commandText, outputText }) => {
  return (
    <div className="w-full max-w-full">
      {/* Thinking text */}
      <div className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-400">
        {thinkingText}
      </div>
      
      {/* Terminal component */}
      <div className="w-full">
        <Terminal commandText={commandText} outputText={outputText} />
      </div>
    </div>
  );
};

export default CodexTerminal;