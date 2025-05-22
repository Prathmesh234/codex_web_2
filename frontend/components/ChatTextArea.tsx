import React from 'react';
import { Textarea } from '@/components/ui/textarea';

interface ChatTextAreaProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  className?: string;
}

const ChatTextArea: React.FC<ChatTextAreaProps> = ({
  value,
  onChange,
  onKeyDown,
  placeholder = 'Type your message here...',
  className = '',
}) => {  return (
    <Textarea
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      className={`w-[900px] resize-none rounded-2xl border-gray-300 focus:border-blue-400 focus:ring focus:ring-blue-200 focus:ring-opacity-50 transition-all duration-200 shadow-md text-gray-800 font-medium ${className}`}
      rows={4}
      style={{
        height: '120px',
        maxHeight: '120px',
        overflowY: 'auto',
        fontSize: '1rem',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        letterSpacing: '0.01em'
      }}
    />
  );
};

export default ChatTextArea;
