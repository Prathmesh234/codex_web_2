"use client";

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import ChatButton from '@/components/ChatButton';
import ChatTextArea from '@/components/ChatTextArea';
import ChatCard from '@/components/ChatCard';
import { RepoSelector } from '@/components/RepoSelector';
import { BranchSelector } from '@/components/BranchSelector';
import { BrowserCountSelector } from '@/components/BrowserCountSelector';
import { TaskList, Task, TaskStatus } from '@/components/TaskList';
import { MoveLeft, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import DarkModeToggle from '@/components/DarkModeToggle';
// @ts-ignore
import { Client, Account, Models } from 'appwrite';

const client = new Client()
  .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || "")
  .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || "");
const account = new Account(client);

type Message = {
  text: string;
  isUser: boolean;
  timestamp: string;
};

interface Repository {
  id: number;
  name: string;
  full_name: string;
  html_url: string;
  clone_url: string;
  description: string | null;
}

interface Branch {
  name: string;
  commit: {
    sha: string;
    url: string;
  };
  protected?: boolean;
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [githubToken, setGithubToken] = useState<string | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null);
  const [selectedRepoInfo, setSelectedRepoInfo] = useState<{
    repoName: string;
    branchName: string;
    cloneUrl: string;
    fullRepoName: string;
  } | null>(null);
  const [browserCount, setBrowserCount] = useState<number | null>(null);
  const [reposLoading, setReposLoading] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);

  // Format current time
  const formatTime = () => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
    }).format(new Date());
  };

  // Fetch GitHub repositories
  const fetchRepositories = async (token: string) => {
    setReposLoading(true);
    try {
      const response = await fetch('https://api.github.com/user/repos?sort=updated&per_page=100', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      });
      
      if (response.ok) {
        const repos = await response.json();
        setRepositories(repos);
        console.log('Fetched repositories:', repos.length);
      } else {
        console.error('Failed to fetch repositories:', response.status);
      }
    } catch (error) {
      console.error('Error fetching repositories:', error);
    } finally {
      setReposLoading(false);
    }
  };

  // Handle repository selection
  const handleRepoSelect = (repo: Repository) => {
    setSelectedRepo(repo);
    setSelectedBranch(null); // Clear selected branch when repo changes
    setSelectedRepoInfo(null); // Clear repo info when repo changes
    console.log('Selected repository:', repo);
  };

  // Handle branch selection
  const handleBranchSelect = (branch: Branch) => {
    setSelectedBranch(branch);
    // Update selectedRepoInfo when both repo and branch are selected
    if (selectedRepo) {
      const repoInfo = {
        repoName: selectedRepo.name,
        branchName: branch.name,
        cloneUrl: selectedRepo.clone_url,
        fullRepoName: selectedRepo.full_name,
      };
      setSelectedRepoInfo(repoInfo);
      // Store repoInfo and also repoName and branchName in localStorage for cross-page access

      console.log('Selected repository info:', repoInfo);
    }
    console.log('Selected branch:', branch);
  };

  // Handle browser count selection
  const handleBrowserCountSelect = (count: number) => {
    setBrowserCount(count);
    console.log('Selected browser count:', count);
  };

  // Helper to truncate a message to 4-5 words
  function truncateMessage(msg: string) {
    const words = msg.split(' ');
    return words.length <= 5 ? msg : words.slice(0, 5).join(' ') + '...';
  }

  // Add this function
  const handleEndTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, status: 'deleted' } : t));
  };

  // Update handleSendMessage to add a task instead of a chat message
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    if (!selectedRepo || !selectedBranch) {
      console.log('Please select both repository and branch before sending a message');
      return;
    }
    if (selectedRepoInfo) {
      console.log('Sending message with repository info:', selectedRepoInfo);
    }
    
    const taskId = Date.now().toString();
    
    // Add to To Do list
    setTasks(prev => [
      ...prev,
      {
        id: taskId,
        message: truncateMessage(inputValue),
        status: 'todo',
        repoName: selectedRepo?.name || '',
        branchName: selectedBranch?.name || '',
        browserCount: browserCount || 1,
        isLoading: true, // Start with loading state
        repoInfo: selectedRepoInfo || undefined, // Store full repo info, avoid null
        githubToken: githubToken || undefined, // Store GitHub token, avoid null
      },
    ]);
    setInputValue('');
    setIsFirstMessage(false);
    
    // Retrieve GitHub token from localStorage
    const storedGithubToken = githubToken

    // Call orchestrator endpoint
    try {
      const response = await fetch("http://localhost:8000/api/orchestrator", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task: inputValue,
          browser_count: browserCount,
          repo_info: selectedRepoInfo,
          github_token: storedGithubToken,
        }),
      });
      const data = await response.json();
      console.log('Orchestrator response:', data);
      // Update task with browser information and set status to 'running' if browsers are present
      setTasks(prev => {
        const updatedTasks = prev.map(task => 
          task.id === taskId 
            ? { 
                ...task, 
                status: (data.browsers && Object.keys(data.browsers).length > 0 ? 'running' : 'todo') as TaskStatus,
                browsers: data.browsers || {},
                sessionId: data.session_id,
                documentation: data.documentation,
                isLoading: false
              }
            : task
        );
        console.log('Task updated after orchestrator response:', updatedTasks.find(t => t.id === taskId));
        return updatedTasks;
      });
      // Start polling for completion if session_id is present
      if (data.session_id) {
        const pollSessionStatus = async () => {
          let completed = false;
          while (!completed) {
            try {
              const resp = await fetch(`/api/browser-session/${data.session_id}`);
              if (resp.ok) {
                const sessionData = await resp.json();
                console.log('Session polling response:', sessionData);
                setTasks(prev => prev.map(task => {
                  if (task.id === taskId) {
                    // Only move to completed if status is completed and documentation is present
                    if (sessionData.status === 'completed' && sessionData.documentation && Object.keys(sessionData.documentation).length > 0) {
                      const updatedTask = {
                        ...task,
                        status: 'completed' as TaskStatus,
                        documentation: sessionData.documentation,
                        browsers: sessionData.browsers || task.browsers,
                        isLoading: false
                      };
                      console.log('Task marked as completed:', updatedTask);
                      return updatedTask;
                    } else {
                      // Update browsers and status if still running
                      const updatedTask = {
                        ...task,
                        status: (sessionData.status === 'completed' ? 'completed' : 'running') as TaskStatus,
                        browsers: sessionData.browsers || task.browsers,
                        isLoading: false
                      };
                      console.log('Task updated during polling:', updatedTask);
                      return updatedTask;
                    }
                  }
                  return task;
                }));
                if (sessionData.status === 'completed' && sessionData.documentation && Object.keys(sessionData.documentation).length > 0) {
                  completed = true;
                  break;
                }
              }
            } catch (err) {
              console.error('Error polling session status:', err);
              break;
            }
            await new Promise(res => setTimeout(res, 5000));
          }
        };
        pollSessionStatus();
      }
    } catch (err) {
      console.error("Error calling orchestrator endpoint:", err);
      // Update task status to error
      setTasks(prev => prev.map(task => 
        task.id === taskId 
          ? { ...task, status: 'error' }
          : task
      ));
    }
  };

  // Auto-scroll to bottom when new messages appear
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    account.getSession('current')
      .then(async (session: Models.Session) => {
        if (!session || session.provider !== 'github') {
          router.replace('/');
        } else {
          // Get the GitHub access token
          const token = (session as any).providerAccessToken;
          setGithubToken(token);
          console.log('GitHub Access Token:', token);
          // Store the token in localStorage for cross-page access
          if (token) {
            localStorage.setItem('github_token', token);
            console.log("GITHUB TOKEN SET")
          }
          
          // Fetch GitHub user information
          try {
            const response = await fetch('https://api.github.com/user', {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/vnd.github.v3+json'
              }
            });
            
            if (response.ok) {
              const userData = await response.json();
              console.log('GitHub User ID:', userData.id);
              console.log('GitHub Username:', userData.login);
              console.log('GitHub User Data:', userData);
              
              // Fetch repositories after getting user data
              await fetchRepositories(token);
            } else {
              console.error('Failed to fetch GitHub user data:', response.status);
            }
          } catch (error) {
            console.error('Error fetching GitHub user data:', error);
          }
          
          setLoading(false);
        }
      })
      .catch(() => {
        router.replace('/');
      });
  }, [router]);

  const handleLogout = async () => {
    await account.deleteSession('current');
    router.replace('/');
  };

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <div style={{ fontWeight: 'bold', fontSize: 22, marginBottom: 12, letterSpacing: 1 }}>
        Loading chat...
        <span className="animate-pulse" style={{ marginLeft: 8 }}>|</span>
      </div>
      <div style={{ color: '#888', fontSize: 16 }}>Please wait while we load your chat session.</div>
    </div>
  );

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <div className="absolute right-4 top-4 flex items-center gap-2">
        <div style={{ marginRight: '10px' }}>
          <DarkModeToggle />
        </div>
        <ChatButton className="p-2" onClick={handleLogout}>
          Logout
        </ChatButton>
      </div>
      <div className="container mx-auto px-4 py-8 flex flex-col items-center">
        <h1 className="text-3xl font-bold mb-12">CodexWeb</h1>
        {/* Chatbox always at the top below the title, strictly centered */}
        <div className="w-full flex flex-col items-center mt-8">
          <div className="relative w-full max-w-2xl mx-auto">
            <ChatTextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              className="w-full pb-16" // Add bottom padding for buttons
            />
            {/* Button container with flexbox layout - positioned at bottom of text area */}
            <div className="absolute bottom-3 left-3 flex items-center gap-3 z-10">
              <RepoSelector
                selectedRepo={selectedRepo}
                onRepoSelect={handleRepoSelect}
                repositories={repositories}
                isLoading={reposLoading}
              />
              <BranchSelector
                selectedRepo={selectedRepo}
                selectedBranch={selectedBranch}
                onBranchSelect={handleBranchSelect}
                githubToken={githubToken}
              />
              <BrowserCountSelector
                browserCount={browserCount}
                onBrowserCountSelect={handleBrowserCountSelect}
              />
            </div>
            {/* Send button absolutely positioned at bottom right, above all */}
            <div className="absolute bottom-3 right-3 z-20">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div>
                      <ChatButton 
                        onClick={handleSendMessage}
                        className="rounded-full p-2 h-8 w-8 flex items-center justify-center text-xs"
                        disabled={!selectedRepo || !selectedBranch}
                      >
                        <Send size={20} />
                      </ChatButton>
                    </div>
                  </TooltipTrigger>
                  {(!selectedRepo || !selectedBranch) && (
                    <TooltipContent>
                      <p>Select a repository and branch to continue</p>
                    </TooltipContent>
                  )}
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
        {/* Task List directly below chatbox, centered, with larger gap */}
        <div className="w-full max-w-2xl mx-auto mt-8">
          <TaskList tasks={tasks} onEndTask={handleEndTask} />
        </div>
      </div>
      <div className="absolute left-4 top-4">
        <Link href="/" passHref>
          <ChatButton className="p-2">
            <MoveLeft />
          </ChatButton>
        </Link>
      </div>
    </div>
  );
}
