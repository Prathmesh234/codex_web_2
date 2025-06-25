"use client";

import React, { useEffect, useState, useRef, useContext } from 'react';
import { ThemeContext } from './ThemeProvider';

interface AnimatedThoughtLineProps {
  text: string;
  isLatest: boolean;
  delay?: number;
}

function AnimatedThoughtLine({ text, isLatest, delay = 0 }: AnimatedThoughtLineProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const { theme } = useContext(ThemeContext);

  useEffect(() => {
    if (!isLatest) {
      setDisplayedText(text);
      setIsComplete(true);
      return;
    }

    setDisplayedText('');
    setIsComplete(false);
    
    const timeout = setTimeout(() => {
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex <= text.length) {
          setDisplayedText(text.slice(0, currentIndex));
          currentIndex++;
        } else {
          clearInterval(interval);
          setIsComplete(true);
        }
      }, 30);
      
      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [text, isLatest, delay]);

  return (
    <div
      style={{
        fontSize: '0.78rem',
        color: theme === 'dark' ? '#ffffff' : '#222',
        marginBottom: 2,
        whiteSpace: 'pre-wrap',
        textAlign: 'left',
        opacity: isLatest ? 1 : 0.7,
        transform: isLatest ? 'translateY(0)' : 'translateY(-2px)',
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        animation: isLatest ? 'slideInUp 0.4s ease-out' : 'none',
      }}
    >
      {displayedText}
      {isLatest && !isComplete && (
        <span
          style={{
            display: 'inline-block',
            width: '2px',
            height: '1em',
            backgroundColor: '#3b82f6',
            marginLeft: '1px',
            animation: 'blink 1s infinite',
          }}
        />
      )}
    </div>
  );
}

function BouncingEllipsis() {
  const { theme } = useContext(ThemeContext);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: 40,
      gap: '6px'
    }}>
      <span style={{ 
        fontSize: '0.85rem', 
        color: theme === 'dark' ? '#ffffff' : '#64748b', 
        marginRight: '8px',
        fontWeight: '500'
      }}>
        Thinking
      </span>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            animation: `bounce 1.4s infinite cubic-bezier(0.68, -0.55, 0.27, 1.55)`,
            animationDelay: `${i * 0.15}s`,
            boxShadow: '0 2px 4px rgba(59, 130, 246, 0.3)',
          }}
        />
      ))}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { 
            transform: translateY(0) scale(1); 
            opacity: 0.7;
          }
          40% { 
            transform: translateY(-12px) scale(1.1); 
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}

interface LLMThoughtStreamBarProps {
  lines: string[];
  waiting: boolean;
}

export default function LLMThoughtStreamBar({ lines, waiting }: LLMThoughtStreamBarProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [animatedLines, setAnimatedLines] = useState<string[]>([]);
  const { theme } = useContext(ThemeContext);
  
  const visibleLines = lines.slice(-8);

  useEffect(() => {
    if (visibleLines.length > animatedLines.length) {
      const newLines = visibleLines.slice(animatedLines.length);
      newLines.forEach((line, index) => {
        setTimeout(() => {
          setAnimatedLines(prev => [...prev, line]);
        }, index * 200);
      });
    } else {
      setAnimatedLines(visibleLines);
    }
  }, [visibleLines.length]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [animatedLines]);

  return (
    <>
      <style>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        .scrollbar-visible::-webkit-scrollbar {
          width: 8px;
        }
        .scrollbar-visible::-webkit-scrollbar-track {
          background: ${theme === 'dark' ? '#2d3748' : '#f7fafc'};
          border-radius: 4px;
        }
        .scrollbar-visible::-webkit-scrollbar-thumb {
          background: ${theme === 'dark' ? '#4a5568' : '#cbd5e0'};
          border-radius: 4px;
        }
        .scrollbar-visible::-webkit-scrollbar-thumb:hover {
          background: ${theme === 'dark' ? '#718096' : '#a0aec0'};
        }
      `}</style>
      <div
        style={{
          position: 'relative',
          width: '680px',
          height: '95px',
          margin: '24px auto 0 auto',
          zIndex: 50,
          background: theme === 'dark' 
            ? 'linear-gradient(145deg, #1f2937, #111827)' 
            : 'linear-gradient(145deg, #ffffff, #f8fafc)',
          borderRadius: '20px',
          border: theme === 'dark' ? '1px solid #ffffff' : '1px solid #e2e8f0',
          boxShadow: theme === 'dark' 
            ? '0 4px 12px rgba(255,255,255,0.1), 0 2px 4px rgba(255,255,255,0.05)'
            : '0 4px 12px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.02)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          overflow: 'hidden',
          fontFamily: 'var(--font-mono, monospace)',
          transition: 'all 0.3s ease',
        }}
      >
        <div
          ref={containerRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            overflowX: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: waiting && animatedLines.length === 0 ? 'center' : 'flex-start',
            alignItems: 'center',
            padding: '10px 20px',
            scrollBehavior: 'smooth',
            scrollbarWidth: 'thin',
            scrollbarColor: theme === 'dark' ? '#4a5568 #2d3748' : '#cbd5e0 #f7fafc',
          }}
          className="scrollbar-visible"
        >
          {waiting && animatedLines.length === 0 ? (
            <BouncingEllipsis />
          ) : (
            <div style={{ width: '100%', maxWidth: 620 }}>
              {animatedLines.map((line, idx) => (
                <AnimatedThoughtLine
                  key={`${idx}-${line.slice(0, 10)}`}
                  text={line}
                  isLatest={idx === animatedLines.length - 1}
                  delay={0}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}