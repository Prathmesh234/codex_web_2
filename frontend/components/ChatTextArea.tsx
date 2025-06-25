import React, { useEffect, useRef } from 'react';
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
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <Textarea
      ref={textareaRef}
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      className={`w-full resize-none rounded-2xl border-gray-300 focus:border-blue-400 focus:ring focus:ring-blue-200 focus:ring-opacity-50 transition-all duration-200 shadow-md text-gray-800 font-medium min-h-[120px] dark:text-white ${className}`}
      rows={1}
      style={{
        fontSize: '1rem',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        letterSpacing: '0.01em',
        overflowY: 'hidden'
      }}
    />
  );
};

export default ChatTextArea;
