"use client";

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import ChatButton from '@/components/ChatButton';
import ChatTextArea from '@/components/ChatTextArea';
import ChatCard from '@/components/ChatCard';
import { MoveLeft, Send } from 'lucide-react';

type Message = {
  text: string;
  isUser: boolean;
  timestamp: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Format current time
  const formatTime = () => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
    }).format(new Date());
  };

  // Handle sending a message
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    // Add user message
    const newUserMessage: Message = {
      text: inputValue,
      isUser: true,
      timestamp: formatTime(),
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setInputValue('');
    setIsFirstMessage(false);
    
    // Simulate agent response (after a short delay)
    setTimeout(() => {
      const newAgentMessage: Message = {
        text: "Hello",
        isUser: false,
        timestamp: formatTime(),
      };
      setMessages(prev => [...prev, newAgentMessage]);
    }, 1000);
  };

  // Auto-scroll to bottom when new messages appear
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="container mx-auto px-4 py-8 flex flex-col h-[calc(100vh-100px)]">
      <h1 className="text-3xl font-bold mb-6">CodexWeb</h1>
      
      <div className={`flex flex-col flex-grow ${isFirstMessage ? 'justify-center' : 'justify-between'}`}>
        {messages.length > 0 && (
          <div 
            ref={messagesContainerRef}
            className="space-y-4 mb-4 overflow-y-auto transition-all duration-500 ease-in-out"
            style={{ 
              maxHeight: isFirstMessage ? '0' : '70vh',
              opacity: isFirstMessage ? 0 : 1
            }}
          >
            {messages.map((message, index) => (
              <ChatCard 
                key={index} 
                message={message.text} 
                isUser={message.isUser} 
                timestamp={message.timestamp}
              />
            ))}
          </div>
        )}          <div 
          className={`relative transition-all duration-500 ease-in-out ${
            isFirstMessage ? 'translate-y-0' : 'translate-y-0 mt-4'
          }`}
          style={{
            transform: isFirstMessage ? 'translateY(-50%)' : 'translateY(0)',
            marginBottom: isFirstMessage ? '0' : '0',
            maxWidth: '900px',
            margin: '0 auto'
          }}
        >
          <ChatTextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
          />          <div className="absolute bottom-3 right-3">
            <ChatButton 
              onClick={handleSendMessage}
              className="rounded-full p-3 h-12 w-12 flex items-center justify-center"
            >
              <Send size={20} />
            </ChatButton>
          </div>
        </div>
      </div>        <div className="absolute left-4 top-4">
        <Link href="/" passHref>
          <ChatButton className="p-2">
            <MoveLeft />
          </ChatButton>
        </Link>
      </div>
    </div>
  );
}
