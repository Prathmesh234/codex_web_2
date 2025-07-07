"use client";

import React, { useState, useEffect } from 'react';
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
  const [executeResponse, setExecuteResponse] = useState<any>(null);
  const [containerStatus, setContainerStatus] = useState<'unknown' | 'running' | 'not_running'>('unknown');
  const [containerMessage, setContainerMessage] = useState<string>('');

  // Generate a unique session ID using the same pattern as browser agent
  const sessionId = React.useMemo(() => {
    return crypto.randomUUID();
  }, []);


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
        
        // Update container status based on response
        if (data.success) {
          setContainerStatus('running');
          setContainerMessage('Container is running and task completed successfully');
        } else {
          setContainerStatus('not_running');
          setContainerMessage(data.message || 'Container is not running or task failed');
        }
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
              {containerStatus === 'unknown' && <div className="w-4 h-4 bg-gray-300 rounded-full"></div>}
              {containerStatus === 'running' && <div className="w-4 h-4 bg-green-500 rounded-full"></div>}
              {containerStatus === 'not_running' && <div className="w-4 h-4 bg-red-500 rounded-full"></div>}
              
              <span className="text-sm font-medium">
                {containerStatus === 'unknown' && 'Container Status'}
                {containerStatus === 'running' && 'Container Running'}
                {containerStatus === 'not_running' && 'Container Not Running'}
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

        {/* Content */}
        <div className="space-y-8 w-full">
          {/* CodexTerminal Components */}
          <CodexTerminal 
            thinkingText="I need to analyze the repository structure to understand the codebase better."
            commandText="ls -la"
            outputText="total 64
drwxr-xr-x  12 user  staff   384 Dec 15 10:30 .
drwxr-xr-x   8 user  staff   256 Dec 15 10:30 ..
drwxr-xr-x  16 user  staff   512 Dec 15 10:30 .git
-rw-r--r--   1 user  staff   156 Dec 15 10:30 .gitignore
-rw-r--r--   1 user  staff  2847 Dec 15 10:30 README.md
drwxr-xr-x   6 user  staff   192 Dec 15 10:30 backend
drwxr-xr-x   8 user  staff   256 Dec 15 10:30 frontend
-rw-r--r--   1 user  staff   425 Dec 15 10:30 package.json

Found React/Next.js project structure. Let me check the components."
          />

          <CodexTerminal 
            thinkingText="Now let me explore the frontend components to understand the current architecture."
            commandText="find frontend/components -name '*.tsx' -type f"
            outputText="frontend/components/Terminal.tsx
frontend/components/BranchSelector.tsx
frontend/components/RepoSelector.tsx
frontend/components/CodexTerminal.tsx

Good! I can see the component structure. Let me check the main application entry point."
          />

          <CodexTerminal 
            thinkingText="Let me examine the backend to understand the orchestrator implementation."
            commandText="python backend/app.py --help"
            outputText="Usage: app.py [OPTIONS]

Codex Web Backend API Server

Options:
  --port INTEGER  Port to run the server on (default: 8000)
  --host TEXT     Host to bind to (default: 127.0.0.1)
  --debug         Enable debug mode
  --help          Show this message and exit.

Backend server ready. API endpoints available at /api/orchestrator"
          />
        </div>
      </div>
    </div>
  );
}