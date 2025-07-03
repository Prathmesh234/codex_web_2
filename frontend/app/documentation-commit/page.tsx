"use client";

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft, GitCommit, FileText, Check, X, AlertCircle } from 'lucide-react';

export default function DocumentationCommitPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [sessionId, setSessionId] = useState<string>('');
  const [browsers, setBrowsers] = useState<Record<string, any>>({});
  const [documentation, setDocumentation] = useState<Record<string, any>>({});
  const [originalTask, setOriginalTask] = useState<string>('');
  const [repoInfo, setRepoInfo] = useState<any>(null);
  const [pullRequestMessage, setPullRequestMessage] = useState('');
  const [pullRequestDescription, setPullRequestDescription] = useState('');
  const [isCommitting, setIsCommitting] = useState(false);
  const [commitStatus, setCommitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [githubToken, setGithubToken] = useState<string | null>(null);
  const [pullRequestUrl, setPullRequestUrl] = useState<string | null>(null);

  useEffect(() => {
    // Parse URL parameters
    const sessionParam = searchParams.get('session_id');
    const browsersParam = searchParams.get('browsers');
    const docParam = searchParams.get('documentation');
    const taskParam = searchParams.get('task');
    const githubTokenParam = searchParams.get('github_token');
    const repoInfoParam = searchParams.get('repo_info');

    if (sessionParam) setSessionId(sessionParam);
    if (taskParam) setOriginalTask(decodeURIComponent(taskParam));
    if (githubTokenParam) setGithubToken(githubTokenParam);
    
    if (repoInfoParam) {
      try {
        const repoData = JSON.parse(decodeURIComponent(repoInfoParam));
        setRepoInfo(repoData);
        console.log('Repo info loaded:', repoData);
      } catch (e) {
        console.error('Error parsing repo info data:', e);
      }
    }
    
    if (browsersParam) {
      try {
        setBrowsers(JSON.parse(decodeURIComponent(browsersParam)));
      } catch (e) {
        console.error('Error parsing browsers data:', e);
      }
    }
    
    if (docParam) {
      try {
        const docData = JSON.parse(decodeURIComponent(docParam));
        setDocumentation(docData);
        console.log('Documentation loaded:', docData);
      } catch (e) {
        console.error('Error parsing documentation data:', e);
      }
    }

    // Fetch additional session data if we have sessionId but no documentation
    if (sessionParam && (!docParam || Object.keys(documentation).length === 0)) {
      fetchSessionData(sessionParam);
    }

    // Set default pull request message and description
    setPullRequestMessage('Add documentation from web research');
    setPullRequestDescription('Generated documentation from automated web research and collection.');
  }, [searchParams]);

  const fetchSessionData = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/browser-session/${sessionId}`);
      if (response.ok) {
        const sessionData = await response.json();
        console.log('Session data fetched:', sessionData);
        
        if (sessionData.task && !originalTask) {
          setOriginalTask(sessionData.task);
        }
        
        if (sessionData.browsers) {
          const docData: Record<string, any> = {};
          Object.entries(sessionData.browsers).forEach(([key, browser]: [string, any]) => {
            if (browser.documentation) {
              docData[key] = browser.documentation;
            }
          });
          
          if (Object.keys(docData).length > 0) {
            setDocumentation(docData);
            console.log('Documentation from session:', docData);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching session data:', error);
    }
  };

  const handleCreatePullRequest = async () => {
    if (!pullRequestMessage.trim()) {
      setErrorMessage('Please enter a pull request message');
      return;
    }

    setIsCommitting(true);
    setCommitStatus('idle');
    setErrorMessage('');

    try {
      // Retrieve GitHub token from localStorage
      const storedGithubToken = typeof window !== 'undefined' ? localStorage.getItem('github_token') : null;
      

      // Create the pull request task with documentation
      const pullRequestTask = `Create a pull request with the following documentation:\n\n${pullRequestMessage}\n\n${pullRequestDescription ? `Description: ${pullRequestDescription}` : ''}\n\nDocumentation to include:${Object.entries(documentation).map(([browserKey, docs]) => `\n--- ${browserKey.replace('_', ' ').toUpperCase()} ---\n${docs.response || 'No content'}`).join('\n')}`;

      // Prepare payload

      /*
      class OrchestratorRequest(BaseModel):
    task: str
    browser_count: Optional[int] = None
    repo_info: dict
    github_token: Optional[str] = None
    documentation: Optional[str] = None
    pullRequestMessage: Optional[str] = None
    pullRequestDescription: Optional[str] = None
      */
   
      const payload = {
        task: 'Git PR Task',
        browser_count: null,
        repo_info: repoInfo,
        github_token: storedGithubToken,
        documentation: JSON.stringify(documentation),
        pullRequestMessage,
        pullRequestDescription,
      };
      console.log('Sending PR payload to /api/orchestrator:', payload);

      // Call the orchestrator API
      const response = await fetch("http://localhost:8000/api/orchestrator", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Pull request orchestrator response:', data);
      
      // Extract PR URL from the orchestrator response
      // The orchestrator should return the tool response which contains pr_url
      let prUrl = null;
      
      // Try to extract PR URL from various possible response structures
      if (data.result) {
        try {
          const resultData = typeof data.result === 'string' ? JSON.parse(data.result) : data.result;
          prUrl = resultData.pr_url;
        } catch (e) {
          console.error('Error parsing result data:', e);
        }
      }
      
      // Also check if PR URL is directly in the response
      if (!prUrl && data.pr_url) {
        prUrl = data.pr_url;
      }
      
      if (prUrl) {
        setPullRequestUrl(prUrl);
        console.log('Pull request created:', prUrl);
      }
      
      setCommitStatus('success');
      
      // Don't automatically redirect if we have a PR URL to show
      if (!prUrl) {
        setTimeout(() => {
          router.push('/chat');
        }, 2000);
      }
    } catch (error) {
      console.error('Error creating pull request:', error);
      setCommitStatus('error');
      setErrorMessage(`Failed to create pull request: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsCommitting(false);
    }
  };

  const handleGoBack = () => {
    router.back();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            View & Commit Documentation
          </h1>
        </div>

        {/* Documentation Content */}
        <div className="space-y-6">
          {/* Documentation Display */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Collected Documentation
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(documentation).length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">No documentation collected yet</p>
                  {sessionId && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => fetchSessionData(sessionId)}
                      className="mt-2"
                    >
                      Refresh Documentation
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(documentation).map(([browserKey, docs]: [string, any]) => (
                    <div key={browserKey} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 capitalize">
                          {browserKey.replace('_', ' ')}
                        </h3>
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                          completed
                        </span>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 max-h-64 overflow-y-auto">
                        <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                          {docs.response ? (
                            docs.response.split('\n').map((line: string, index: number) => (
                              <div key={index} className="mb-2 last:mb-0">
                                {line.trim() === '' ? <br /> : line}
                              </div>
                            ))
                          ) : (
                            'No documentation content available'
                          )}
                        </div>
                      </div>
                      {docs.timestamp && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                          Collected at: {new Date(docs.timestamp).toLocaleString()}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Commit Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitCommit className="w-5 h-5" />
                Create Pull Request
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Pull Request Message *
                </label>
                <Input
                  value={pullRequestMessage}
                  onChange={(e) => setPullRequestMessage(e.target.value)}
                  placeholder="Enter pull request message"
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description (Optional)
                </label>
                <Textarea
                  value={pullRequestDescription}
                  onChange={(e) => setPullRequestDescription(e.target.value)}
                  placeholder="Enter detailed description of the documentation"
                  rows={3}
                  className="w-full"
                />
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 text-red-600 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {errorMessage}
                </div>
              )}

              {commitStatus === 'success' && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-green-600 text-sm">
                    <Check className="w-4 h-4" />
                    Pull request created successfully!
                  </div>
                  {pullRequestUrl && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <strong>PR URL:</strong>{' '}
                      <a 
                        href={pullRequestUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline break-all"
                      >
                        {pullRequestUrl}
                      </a>
                    </div>
                  )}
                </div>
              )}

              {commitStatus === 'error' && (
                <div className="flex items-center gap-2 text-red-600 text-sm">
                  <X className="w-4 h-4" />
                  {errorMessage}
                </div>
              )}

              <div className="flex gap-3 pt-4">
                {commitStatus === 'success' && pullRequestUrl ? (
                  // Show "View Pull Request" button when PR is created
                  <Button
                    onClick={() => window.open(pullRequestUrl, '_blank')}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <GitCommit className="w-4 h-4" />
                    View Pull Request
                  </Button>
                ) : (
                  // Show "Create Pull Request" button initially
                  <Button
                    onClick={handleCreatePullRequest}
                    disabled={isCommitting || commitStatus === 'success'}
                    className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white"
                  >
                    <GitCommit className="w-4 h-4" />
                    {isCommitting ? 'Creating Pull Request...' : 'Create Pull Request'}
                  </Button>
                )}
                
                <Button
                  variant="outline"
                  onClick={handleGoBack}
                  disabled={isCommitting}
                >
                  {commitStatus === 'success' && pullRequestUrl ? 'Back to Chat' : 'Cancel'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Original Task & Session Info */}
          {(originalTask || sessionId) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-gray-600 dark:text-gray-400">
                  Task & Session Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {originalTask && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Original Task:</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                      {originalTask}
                    </p>
                  </div>
                )}
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {sessionId && (
                    <>
                      Session ID: {sessionId}
                      <br />
                    </>
                  )}
                  Browsers: {Object.keys(browsers).length}
                  <br />
                  Documentation Sources: {Object.keys(documentation).length}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}