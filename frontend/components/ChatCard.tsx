import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface ChatCardProps {
  message: string;
  isUser: boolean;
  timestamp: string;
}

const ChatCard: React.FC<ChatCardProps> = ({ message, isUser, timestamp }) => {  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} my-3`}>
      <Card className={`max-w-[80%] ${isUser ? 'bg-gradient-to-br from-blue-50 to-blue-100' : 'bg-white'} shadow-md transition-all duration-300 hover:shadow-lg`}>
        <CardContent className="p-4">
          <p className="text-base text-gray-700 font-medium leading-relaxed">
            {message}
          </p>
          <span className="text-xs font-medium text-gray-500 mt-2 block tracking-wide">
            {isUser ? 'You' : 'Agent'} • {timestamp}
          </span>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatCard;
