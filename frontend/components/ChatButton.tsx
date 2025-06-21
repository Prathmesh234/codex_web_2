import React from 'react';
import { Button as UIButton } from '@/components/ui/button';

interface ChatButtonProps {
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
}

const ChatButton: React.FC<ChatButtonProps> = ({
  onClick,
  children,
  className = '',
  type = 'button',
  disabled = false,
}) => {  return (
    <UIButton 
      onClick={onClick} 
      className={`font-semibold shadow-md transition-all duration-300 hover:shadow-lg hover:scale-105 active:scale-95 ${className}`} 
      type={type}
      disabled={disabled}
    >
      {children}
    </UIButton>
  );
};

export default ChatButton;
