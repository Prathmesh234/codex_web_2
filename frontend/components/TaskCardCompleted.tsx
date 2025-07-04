import * as React from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, GitCommit } from "lucide-react"

interface TaskCardCompletedProps {
  message: string
  repoName: string
  branchName: string
  browserCount: number
  sessionId?: string
  browsers?: Record<string, any>
  documentation?: Record<string, any>
  repoInfo?: {
    repoName: string
    branchName: string
    cloneUrl: string
    fullRepoName: string
  }
  githubToken?: string
}

export function TaskCardCompleted({ 
  message, 
  repoName, 
  branchName, 
  browserCount, 
  sessionId,
  browsers,
  documentation,
  repoInfo,
  githubToken
}: TaskCardCompletedProps) {
  
  const handleViewAndCommitDocumentation = () => {
    // Navigate to documentation view with commit functionality
    const sessionParam = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const browsersParam = browsers ? `&browsers=${encodeURIComponent(JSON.stringify(browsers))}` : '';
    const docParam = documentation ? `&documentation=${encodeURIComponent(JSON.stringify(documentation))}` : '';
    
    // repoInfo must be provided from the Chat page (full owner/repo identifier)
    if (!repoInfo) {
      console.error("TaskCardCompleted: missing repoInfo; cannot view & commit documentation.");
      return;
    }
    const repoInfoToUse = repoInfo;
    const repoParam = `&repo_info=${encodeURIComponent(JSON.stringify(repoInfoToUse))}`;
    const tokenParam = githubToken ? `&github_token=${encodeURIComponent(githubToken)}` : '';
    
    // Navigate to a new documentation commit page
    window.location.href = `/documentation-commit${sessionParam}${browsersParam}${docParam}${repoParam}${tokenParam}`;
  };

  return (
    <Card className="flex items-center justify-between px-4 py-3 shadow-sm border rounded-lg">
      <div className="flex flex-col items-start flex-1">
        <span className="text-base font-medium truncate w-full text-left">{message}</span>
        <span className="text-xs text-muted-foreground mt-1 text-left">
          {repoName} &bull; {branchName} &bull; {browserCount} browser{browserCount > 1 ? 's' : ''}
        </span>
      </div>
      
      {/* View and Commit Documentation Button */}
      <div className="flex items-center gap-2 ml-4">
        <Button
          size="sm"
          onClick={handleViewAndCommitDocumentation}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white"
        >
          <FileText className="w-4 h-4" />
          <span className="hidden sm:inline">View & Commit Documentation</span>
          <span className="sm:hidden">View & Commit</span>
          <GitCommit className="w-4 h-4" />
        </Button>
      </div>
    </Card>
  )
} 