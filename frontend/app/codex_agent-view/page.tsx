"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Bot, Loader2 } from 'lucide-react';
import CodexTerminal from '@/components/CodexTerminal';

export default function CodexAgentViewPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [task, setTask] = useState<string>('');
  const [githubToken, setGithubToken] = useState<string>('');
  const [repoInfo, setRepoInfo] = useState<any>(null);
  const [executeStatus, setExecuteStatus] = useState<'idle' | 'loading' | 'completed' | 'error'>('idle');
  const [commandHistory, setCommandHistory] = useState<Array<{command: string, response: string, timestamp: string}>>([]);
  const [currentCommand, setCurrentCommand] = useState<string>('');
  const [pendingCommands, setPendingCommands] = useState<Array<{command: string, timestamp: string}>>([]);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [wsConnecting, setWsConnecting] = useState<boolean>(false);
  const [shouldShowWsStatus, setShouldShowWsStatus] = useState<boolean>(false);
  const [executeResponse, setExecuteResponse] = useState<any>(null);
  const [containerStatus, setContainerStatus] = useState<'unknown' | 'running' | 'not_running'>('unknown');
  const [containerMessage, setContainerMessage] = useState<string>('');
  const [containerConnecting, setContainerConnecting] = useState<boolean>(false);

  // Generate a unique session ID using the same pattern as browser agent
  const sessionId = React.useMemo(() => {
    return crypto.randomUUID();
  }, []);

  // Use refs to store WebSocket and timeout references
  const wsRef = useRef<WebSocket | null>(null);
  const containerCheckTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef<boolean>(false);

  // Container status checking function
  const checkContainerStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/container/status');
      const data = await response.json();
      return data.initialized;
    } catch (error) {
      console.error('Error checking container status:', error);
      return false;
    }
  }, []);

  // WebSocket connection function
  const connectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    wsRef.current = new WebSocket('ws://localhost:8000/ws/commands');
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
      setWsConnecting(false);
    };
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        if (data.type === 'command') {
          const command = data.data.command || '';
          const timestamp = new Date().toLocaleTimeString();
          
          // Add to pending commands immediately when received
          setPendingCommands(prev => [...prev, {
            command: command,
            timestamp: timestamp
          }]);
          
          setCurrentCommand(command);
          console.log('Received command:', command);
        } else if (data.type === 'response') {
          const command = data.data.command || 'Unknown command';
          const response = data.data.stdout || data.data.output || data.data.stderr || 'No output';
          const timestamp = new Date().toLocaleTimeString();
          
          // Move from pending to history
          setCommandHistory(prev => [...prev, {
            command: command,
            response: response,
            timestamp: timestamp
          }]);
          
          // Remove from pending commands
          setPendingCommands(prev => prev.filter(cmd => cmd.command !== command));
          
          setCurrentCommand('');
          console.log('Received response:', response);
          
          // Check if task is completed
          if (data.data.status === 'completed' || data.data.task_completed === true) {
            console.log('Task completed, closing WebSocket');
            if (wsRef.current) {
              wsRef.current.close();
            }
          }
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.data.message);
          setCurrentCommand('');
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
      setWsConnecting(false);
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
      setWsConnecting(false);
    };
  }, []);

  // Container connection attempt function
  const attemptContainerConnection = useCallback(async () => {
    if (isConnectingRef.current) {
      return;
    }
    
    isConnectingRef.current = true;
    setContainerConnecting(true);
    setWsConnecting(true);
    setContainerMessage('Checking container status...');
    
    try {
      const isInitialized = await checkContainerStatus();
      if (isInitialized) {
        console.log('Container initialized, connecting WebSocket');
        setContainerStatus('running');
        setContainerMessage('Container is running and WebSocket connected');
        setContainerConnecting(false);
        connectWebSocket();
      } else {
        console.log('Container not ready, checking again in 15 seconds');
        setContainerMessage('Container not ready, checking again in 15 seconds...');
        containerCheckTimeoutRef.current = setTimeout(attemptContainerConnection, 15000);
      }
    } catch (error) {
      console.error('Error during container connection attempt:', error);
      setContainerStatus('not_running');
      setContainerMessage('Error connecting to container');
      setContainerConnecting(false);
      setWsConnecting(false);
    }
    
    isConnectingRef.current = false;
  }, [checkContainerStatus, connectWebSocket]);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (containerCheckTimeoutRef.current) {
      clearTimeout(containerCheckTimeoutRef.current);
      containerCheckTimeoutRef.current = null;
    }
    setWsConnected(false);
    setWsConnecting(false);
    setContainerConnecting(false);
    isConnectingRef.current = false;
  }, []);

  // Effect for cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);


  const executeTask = async () => {
    if (!task || !repoInfo) {
      console.error('Task or repo info missing');
      return;
    }

    try {
      setExecuteStatus('loading');
      
      const response = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: task,
          repo_url: repoInfo.cloneUrl,
          project_name: repoInfo.repoName,
          container_type: "azure"
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setExecuteStatus('completed');
        setExecuteResponse(data);
        console.log('Execute response:', data);
        
        // Connect websocket immediately for real-time streaming
        console.log('Task started, connecting websocket for real-time updates...');
        setShouldShowWsStatus(true);
        setWsConnecting(true);
        attemptContainerConnection();
      } else {
        setExecuteStatus('error');
        setExecuteResponse(data);
        console.error('Execute error:', data);
        
        // Update container status for error case
        if (data.message && data.message.includes('Container is not running')) {
          setContainerStatus('not_running');
          setContainerMessage(data.message);
        } else {
          setContainerStatus('unknown');
          setContainerMessage('Error executing task');
        }
      }
    } catch (error) {
      console.error('Error executing task:', error);
      setExecuteStatus('error');
      setContainerStatus('unknown');
      setContainerMessage('Failed to connect to server');
    }
  };

  useEffect(() => {
    console.log("CodexAgentViewPage: Parsing URL parameters...");

    if (!searchParams) return;

    const taskParam = searchParams.get('task');
    const githubTokenParam = searchParams.get('github_token');
    const repoInfoParam = searchParams.get('repo_info');

    if (taskParam) {
      const decodedTask = decodeURIComponent(taskParam);
      console.log('Received task:', decodedTask);
      setTask(decodedTask);
    }

    if (githubTokenParam) {
      console.log('Received github_token from URL:', githubTokenParam);
      setGithubToken(githubTokenParam);
    }
    
    if (repoInfoParam) {
      console.log('Received raw repo_info param:', repoInfoParam);
      try {
        const repoData = JSON.parse(decodeURIComponent(repoInfoParam));
        console.log('Parsed repo_info data:', repoData);
        setRepoInfo(repoData);
      } catch (e) {
        console.error('Error parsing repo_info data:', e);
      }
    }

  }, [searchParams]);

  // Execute task when we have both task and repo info
  useEffect(() => {
    if (task && repoInfo) {
      executeTask();
    }
  }, [task, repoInfo]);

  const handleGoBack = () => {
    router.back();
  };


  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleGoBack}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Bot className="w-8 h-8" />
            Codex Agent
          </h1>
        </div>


        {/* Container Status */}
        <div className="mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              {containerConnecting ? (
                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
              ) : containerStatus === 'unknown' ? (
                <div className="w-4 h-4 bg-gray-300 rounded-full"></div>
              ) : containerStatus === 'running' ? (
                <div className="w-4 h-4 bg-green-500 rounded-full"></div>
              ) : (
                <div className="w-4 h-4 bg-red-500 rounded-full"></div>
              )}
              
              <span className="text-sm font-medium">
                {containerConnecting ? 'Container Connecting...' : 
                 containerStatus === 'unknown' ? 'Container Status' :
                 containerStatus === 'running' ? 'Container Running' :
                 'Container Not Running'}
              </span>
            </div>
            
            {containerMessage && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {containerMessage}
              </p>
            )}
          </div>
        </div>

        {/* Execute Status */}
        <div className="mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              {executeStatus === 'idle' && <div className="w-4 h-4 bg-gray-300 rounded-full"></div>}
              {executeStatus === 'loading' && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
              {executeStatus === 'completed' && <div className="w-4 h-4 bg-green-500 rounded-full"></div>}
              {executeStatus === 'error' && <div className="w-4 h-4 bg-red-500 rounded-full"></div>}
              
              <span className="text-sm font-medium">
                {executeStatus === 'idle' && 'Task Status'}
                {executeStatus === 'loading' && 'Executing Task...'}
                {executeStatus === 'completed' && 'Task Completed'}
                {executeStatus === 'error' && 'Task Error'}
              </span>
            </div>
            
            {executeResponse && executeResponse.message && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {executeResponse.message}
              </p>
            )}
          </div>
        </div>

        {/* WebSocket Status - Only show if we should be streaming */}
        {shouldShowWsStatus && (
          <div className="mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                {wsConnected ? (
                  <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                ) : wsConnecting ? (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                ) : (
                  <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                )}
                <span className="text-sm font-medium">
                  {wsConnected ? 'WebSocket Connected' : wsConnecting ? 'WebSocket Connecting...' : 'WebSocket Disconnected'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="space-y-8 w-full">
          {/* Command History */}
          {commandHistory.map((item, index) => (
            <CodexTerminal 
              key={`history-${index}`}
              thinkingText={`Command ${index + 1} executed at ${item.timestamp}`}
              commandText={item.command}
              outputText={item.response}
            />
          ))}

          {/* Pending Commands */}
          {pendingCommands.map((item, index) => (
            <div key={`pending-${index}`} className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-700">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 bg-yellow-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">Awaiting approval for command:</span>
              </div>
              <code className="text-sm bg-yellow-100 dark:bg-yellow-900/40 px-2 py-1 rounded">
                {item.command}
              </code>
              <div className="text-xs text-yellow-600 dark:text-yellow-400 mt-2">
                Received at {item.timestamp}
              </div>
            </div>
          ))}

          {/* Current Command Display */}
          {currentCommand && (
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">Executing Command:</span>
              </div>
              <code className="text-sm bg-blue-100 dark:bg-blue-900/40 px-2 py-1 rounded">
                {currentCommand}
              </code>
            </div>
          )}
          
          {/* Fallback for HTTP response - only show if no command history */}
          {executeResponse && executeResponse.stdout && commandHistory.length === 0 && !executeResponse.command_history && (
            <CodexTerminal 
              thinkingText="Task completed via HTTP endpoint"
              commandText={task}
              outputText={executeResponse.stdout}
            />
          )}
          
          {/* Empty state */}
          {commandHistory.length === 0 && !currentCommand && !executeResponse && pendingCommands.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Waiting for commands...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}