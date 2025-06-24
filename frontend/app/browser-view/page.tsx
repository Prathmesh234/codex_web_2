"use client";

import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ExternalLink, Monitor, Maximize2, Minimize2 } from 'lucide-react';
import Link from 'next/link';

interface BrowserInfo {
  live_view_url: string;
  session_id: string;
  subtask: string;
}

// LLM Thought Stream Bar Component
function LLMThoughtStreamBar({ lines, waiting }: { lines: string[]; waiting: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null);
  // Only keep the last 10 lines for clarity
  const visibleLines = lines.slice(-10);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [lines]);

  return (
    <div
      style={{
        position: 'relative',
        width: '640px',
        height: '90px',
        margin: '24px auto 0 auto',
        zIndex: 50,
        background: 'white',
        borderRadius: '18px',
        border: '1px solid #e5e7eb',
        boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        overflow: 'hidden',
        fontFamily: 'var(--font-mono, monospace)',
      }}
    >
      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: waiting && lines.length === 0 ? 'center' : 'flex-end',
          alignItems: 'center',
          padding: '8px 18px',
        }}
      >
        {waiting && lines.length === 0 ? (
          <BouncingEllipsis />
        ) : (
          <div style={{ width: '100%', maxWidth: 600 }}>
            {visibleLines.map((line, idx) => (
              <div
                key={idx}
                style={{
                  fontSize: '0.78rem',
                  color: '#222',
                  marginBottom: 1,
                  whiteSpace: 'pre-wrap',
                  textAlign: 'left',
                  opacity: 0.95 - (visibleLines.length - idx - 1) * 0.08,
                  transition: 'opacity 0.3s',
                }}
              >
                {line}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Bouncing Ellipsis Animation
function BouncingEllipsis() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 40 }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 10,
            height: 10,
            margin: '0 4px',
            borderRadius: '50%',
            background: '#bbb',
            animation: `bounce 1.2s infinite cubic-bezier(.68,-0.55,.27,1.55)`,
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-16px); }
        }
      `}</style>
    </div>
  );
}

export default function BrowserViewPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [browsers, setBrowsers] = useState<Record<string, BrowserInfo>>({});
  const [taskMessage, setTaskMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [thoughtLines, setThoughtLines] = useState<string[]>([]);
  const [waiting, setWaiting] = useState(true);
  const [expandedIframe, setExpandedIframe] = useState<string | null>(null);

  useEffect(() => {
    // Get browser data from URL parameters
    const browsersParam = searchParams?.get('browsers');
    const messageParam = searchParams?.get('message');
    
    if (browsersParam) {
      try {
        const browsersData = JSON.parse(decodeURIComponent(browsersParam));
        setBrowsers(browsersData);
        console.log('Browser data loaded:', browsersData);
      } catch (error) {
        console.error('Error parsing browser data:', error);
      }
    }
    
    if (messageParam) {
      setTaskMessage(decodeURIComponent(messageParam));
    }
    
    setLoading(false);
  }, [searchParams]);

  // Listen to web agent logs via WebSocket for the first browser session (robust debug version)
  useEffect(() => {
    // Get all session IDs from browsers
    const sessionIds = Object.values(browsers).map(b => b.session_id);
    if (sessionIds.length === 0) return;

    // For debugging, just use the first session
    const sessionId = sessionIds[0];
    setThoughtLines([]);
    setWaiting(true);

    // Construct the WebSocket URL robustly
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const backendHost = window.location.hostname + ':8000';
    const wsUrl = `${wsProtocol}://${backendHost}/ws/web-agent/${sessionId}`;
    console.log('Connecting to WebSocket:', wsUrl);

    const socket = new window.WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('WebSocket connected');
      setWaiting(true);
    };
    socket.onmessage = (event) => {
      console.log('WebSocket message:', event.data);
      setThoughtLines(prev => [...prev, event.data]);
      setWaiting(false);
    };
    socket.onerror = (err) => {
      console.error('WebSocket error:', err);
      setWaiting(false);
    };
    socket.onclose = (event) => {
      console.log('WebSocket closed:', event);
      setWaiting(false);
    };

    return () => {
      socket.close();
    };
  }, [JSON.stringify(browsers)]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading browser view...</p>
        </div>
      </div>
    );
  }

  if (Object.keys(browsers).length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Monitor className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">No Browser Sessions</h2>
          <p className="text-gray-600 mb-4">No browser sessions found for this task.</p>
          <Link href="/chat">
            <Button>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Chat
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header (Nav bar) */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/chat">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Chat
                </Button>
              </Link>
              <div>
                <h1 className="text-xl font-semibold">Browser Sessions</h1>
                {taskMessage && (
                  <p className="text-sm text-gray-600 mt-1">{taskMessage}</p>
                )}
              </div>
            </div>
            <div className="text-sm text-gray-500">
              {Object.keys(browsers).length} browser{Object.keys(browsers).length > 1 ? 's' : ''} active
            </div>
          </div>
        </div>
      </div>
      {/* LLM Thought Stream Bar below Nav bar */}
      <LLMThoughtStreamBar lines={thoughtLines} waiting={waiting} />
      {/* Browser Grid */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {Object.entries(browsers).map(([browserKey, browserInfo]) => {
            return (
              <Card key={browserKey} className="overflow-hidden relative p-0 m-0 bg-white border rounded-xl shadow-sm">
                <CardHeader className="bg-gray-50 border-b px-4 py-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-gray-600" />
                      <CardTitle className="text-base font-medium m-0">
                        {browserKey}
                      </CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">
                        Session: {browserInfo.session_id.slice(0, 8)}...
                      </span>
                      <a
                        href={browserInfo.live_view_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={expandedIframe === browserKey ? 'Collapse view' : 'Expand view'}
                        onClick={() => setExpandedIframe(expandedIframe === browserKey ? null : browserKey)}
                        style={{ marginLeft: 4 }}
                      >
                        {expandedIframe === browserKey ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                      </Button>
                    </div>
                  </div>
                  <CardDescription className="mt-0 truncate text-xs text-gray-500">
                    {browserInfo.subtask}
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0 m-0" style={{ height: 320 }}>
                  {browserInfo.live_view_url.startsWith('https://mock-browser.com') ? (
                    <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                      <div className="text-center">
                        <Monitor className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600">Mock Browser Session</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Session ID: {browserInfo.session_id}
                        </p>
                        <p className="text-xs text-gray-500">
                          Documentation collection in progress...
                        </p>
                      </div>
                    </div>
                  ) : (
                    <iframe
                      src={browserInfo.live_view_url}
                      className="w-full h-full border-0"
                      title={`${browserKey} Live View`}
                      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                      style={{ borderRadius: 0, transition: 'border-radius 0.3s' }}
                    />
                  )}
                </CardContent>
                {/* Fullscreen Modal for Expanded Iframe */}
                {expandedIframe === browserKey && (
                  <div
                    style={{
                      position: 'fixed',
                      top: 0,
                      left: 0,
                      width: '100vw',
                      height: '100vh',
                      background: 'rgba(0,0,0,0.65)',
                      zIndex: 1000,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                    onClick={() => setExpandedIframe(null)}
                  >
                    <div
                      style={{
                        position: 'relative',
                        width: '90vw',
                        height: '90vh',
                        background: 'white',
                        borderRadius: 12,
                        boxShadow: '0 4px 32px rgba(0,0,0,0.18)',
                        overflow: 'hidden',
                      }}
                      onClick={e => e.stopPropagation()}
                    >
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Close fullscreen"
                        onClick={() => setExpandedIframe(null)}
                        style={{ position: 'absolute', top: 16, right: 16, zIndex: 10 }}
                      >
                        <Minimize2 className="w-6 h-6" />
                      </Button>
                      <iframe
                        src={browserInfo.live_view_url}
                        className="w-full h-full border-0"
                        title={`${browserKey} Live View Fullscreen`}
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                        style={{ borderRadius: 0 }}
                      />
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
} 