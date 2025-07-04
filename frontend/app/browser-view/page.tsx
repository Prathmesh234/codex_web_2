"use client";

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ExternalLink, Monitor, Maximize2, Minimize2, FileText, GitCommit } from 'lucide-react';
import Link from 'next/link';
import DarkModeToggle from '@/components/DarkModeToggle';
import LLMThoughtStreamBar from '@/components/LLMThoughtStreamBar';
import DocumentationDisplay from '@/components/DocumentationDisplay';

interface BrowserInfo {
  live_view_url: string;
  session_id: string;
  subtask: string;
}


export default function BrowserViewPage() {
  const searchParams = useSearchParams();
  const [browsers, setBrowsers] = useState<Record<string, BrowserInfo>>({});
  const [taskMessage, setTaskMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [thoughtLines, setThoughtLines] = useState<string[]>([]);
  const [waiting, setWaiting] = useState(true);
  const [expandedIframe, setExpandedIframe] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [sessionData, setSessionData] = useState<any>(null);
  const [taskCompleted, setTaskCompleted] = useState(false);
  const [githubToken, setGithubToken] = useState<string | null>(null);
  const [urlRepoInfo, setUrlRepoInfo] = useState<any>(null);
  const [urlGithubToken, setUrlGithubToken] = useState<string | null>(null);

  useEffect(() => {
    // Get browser data and session_id from URL parameters
    const browsersParam = searchParams?.get('browsers');
    const messageParam = searchParams?.get('message');
    const sessionParam = searchParams?.get('session_id');
    const repoInfoParam = searchParams?.get('repo_info');
    const githubTokenParam = searchParams?.get('github_token');
    
    if (browsersParam) {
      try {
        const browsersData = JSON.parse(decodeURIComponent(browsersParam));
        setBrowsers(browsersData);
        console.log('Browser data loaded:', browsersData);
        // Always set sessionId from the session_id field in the first browser
        const firstBrowser = Object.values(browsersData)[0] as BrowserInfo;
        if (firstBrowser && firstBrowser.session_id) {
          setSessionId(firstBrowser.session_id);
        }
      } catch (error) {
        console.error('Error parsing browser data:', error);
      }
    }
    
    if (messageParam) {
      setTaskMessage(decodeURIComponent(messageParam));
    }
    
    setLoading(false);
    if (repoInfoParam) {
      try {
        const parsed = JSON.parse(decodeURIComponent(repoInfoParam));
        console.log('Received repo_info from URL:', parsed);
        setUrlRepoInfo(parsed);
      } catch (err) {
        console.error('Error parsing repo_info from URL:', err);
      }
    }
    if (githubTokenParam) {
      console.log('Received github_token from URL:', githubTokenParam);
      setUrlGithubToken(githubTokenParam);
    }
  }, [searchParams]);

  // Poll session status until task is completed, then stop
  useEffect(() => {
    if (!sessionId || taskCompleted) return;

    const pollSessionStatus = async () => {
      try {
        const response = await fetch(`/api/browser-session/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          setSessionData(data);
          console.log('Session data received:', data);
          
          // Check if all browsers are completed
          const browserValues = Object.values(data.browsers || {});
          const completedCount = browserValues.filter((browser: any) => 
            browser.status === 'completed'
          ).length;
          
          if (completedCount === browserValues.length && browserValues.length > 0) {
            setTaskCompleted(true);
            console.log('All tasks completed, stopping polling');
            return; // Stop polling
          }
        }
      } catch (error) {
        console.error('Error polling session status:', error);
      }
    };

    // Initial poll
    pollSessionStatus();

    // Set up interval polling every 5 seconds, but only if not completed
    const interval = setInterval(() => {
      if (!taskCompleted) {
        pollSessionStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId, taskCompleted]);

  // Listen to web agent logs via WebSocket for the first browser session (robust debug version)
  useEffect(() => {
    // Get all session IDs from browsers
    const sessionIds = Object.values(browsers).map(b => b.session_id);
    if (sessionIds.length === 0) return;

    // Use the sessionId from state (set above)
    if (!sessionId) return;
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
  }, [browsers, sessionId]);

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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header (Nav bar) */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between w-full">
            {/* Left: Back to Chat and Browser Sessions title */}
            <div className="flex items-center gap-4">
              <Link href="/chat">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Chat
                </Button>
              </Link>
              <h1 className="text-xl font-semibold dark:text-white whitespace-nowrap">Browser Sessions</h1>
            </div>
            {/* Right: Dark mode toggle, browser count, and commit button */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500 dark:text-gray-300 whitespace-nowrap">
                {Object.keys(browsers).length} browser{Object.keys(browsers).length > 1 ? 's' : ''} active
              </span>
              
              {/* View and Commit Documentation Button - Only show when all tasks completed */}
              {taskCompleted && (
                <Button
                  size="sm"
                  onClick={async () => {
                    try {
                      // Fetch fresh session data to get all documentation
                      const response = await fetch(`/api/browser-session/${sessionId}`);
                      let sessionData = null;
                      if (response.ok) {
                        sessionData = await response.json();
                      }
                      
                      const sessionParam = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
                      const browsersParam = browsers ? `&browsers=${encodeURIComponent(JSON.stringify(browsers))}` : '';
                      
                      // Get documentation from session data if available, otherwise from browsers
                      const documentationData: Record<string, any> = {};
                      if (sessionData?.browsers) {
                        Object.entries(sessionData.browsers).forEach(([key, browser]: [string, any]) => {
                          if (browser.documentation) {
                            documentationData[key] = browser.documentation;
                          }
                        });
                      } else {
                        // Fallback to browsers prop
                        Object.entries(browsers).forEach(([key, browser]: [string, any]) => {
                          if (browser.documentation) {
                            documentationData[key] = browser.documentation;
                          }
                        });
                      }
                      
                      const docParam = Object.keys(documentationData).length > 0 ? 
                        `&documentation=${encodeURIComponent(JSON.stringify(documentationData))}` : '';
                      const taskParam = sessionData?.task ? `&task=${encodeURIComponent(sessionData.task)}` : '';
                      
                      // When navigating to documentation-commit, carry repository info and GitHub token (URL-provided preferred)
                      const githubTokenToUse = urlGithubToken || githubToken;
                      const githubTokenParam2 = githubTokenToUse ? `&github_token=${encodeURIComponent(githubTokenToUse)}` : '';
                      const repoInfoToUse = urlRepoInfo || sessionData?.repo_info;
                      const repoParam2 = repoInfoToUse ? `&repo_info=${encodeURIComponent(JSON.stringify(repoInfoToUse))}` : '';
                      window.location.href =
                        `/documentation-commit${sessionParam}${browsersParam}${docParam}${taskParam}` +
                        `${githubTokenParam2}${repoParam2}`;
    } catch (error) {
      console.error('Error fetching session data:', error);
      // Fallback navigation, still carrying repo_info and github_token if available
      const sessionParam = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
      const browsersParam = browsers ? `&browsers=${encodeURIComponent(JSON.stringify(browsers))}` : '';
      const repoInfoToUse = urlRepoInfo || sessionData?.repo_info;
      const repoParam = repoInfoToUse ? `&repo_info=${encodeURIComponent(JSON.stringify(repoInfoToUse))}` : '';
      const githubTokenToUse = urlGithubToken || githubToken;
      const tokenParam = githubTokenToUse ? `&github_token=${encodeURIComponent(githubTokenToUse)}` : '';
      window.location.href =
        `/documentation-commit${sessionParam}${browsersParam}` +
        `${repoParam}${tokenParam}`;
    }
                  }}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white"
                >
                  <FileText className="w-4 h-4" />
                  <span className="hidden lg:inline">View & Commit Documentation</span>
                  <span className="lg:hidden">View & Commit</span>
                  <GitCommit className="w-4 h-4" />
                </Button>
              )}
              
              <DarkModeToggle />
            </div>
          </div>
        </div>
      </div>
      {/* LLM Thought Stream Bar with Task Message */}
      <div className="relative">
        {taskMessage && (
          <div className="container mx-auto px-4 pt-4 pb-2">
            <div className="flex items-center justify-center">
              <p className="text-sm text-gray-600 dark:text-gray-300 text-center font-medium max-w-6xl break-words">
                <span className="text-gray-500 dark:text-gray-400">Task:</span> {taskMessage}
              </p>
            </div>
          </div>
        )}
        <LLMThoughtStreamBar lines={thoughtLines} waiting={waiting} />
      </div>
      {/* Browser Grid */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {Object.entries(browsers).map(([browserKey, browserInfo]) => {
            return (
              <Card 
key={browserKey} 
className="overflow-hidden relative p-0 m-0 bg-white border rounded-xl shadow-sm cursor-pointer"
onClick={() => window.open(browserInfo.live_view_url, '_blank')}
>
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

      {/* Documentation Display */}
      <DocumentationDisplay 
        sessionId={sessionId}
        browsers={sessionData?.browsers || browsers}
        taskCompleted={taskCompleted}
      />
    </div>
  );
} 