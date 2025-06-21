import * as React from "react"
import { Card } from "@/components/ui/card"
import { XCircle, Loader2, ExternalLink, AlertCircle } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface TaskCardToDoProps {
  message: string
  repoName: string
  branchName: string
  browserCount: number
  onEndTask: () => void
  status?: "todo" | "running" | "error" | "completed" | "deleted"
  browsers?: Record<string, {
    live_view_url: string
    session_id: string
    subtask: string
  }>
  onCardClick?: () => void
  isLoading?: boolean
}

export function TaskCardToDo({ 
  message, 
  repoName, 
  branchName, 
  browserCount, 
  onEndTask, 
  status = "todo",
  browsers,
  onCardClick,
  isLoading = false
}: TaskCardToDoProps) {
  const getStatusIcon = () => {
    // Show loading spinner
    if (isLoading) {
      return <Loader2 className="animate-spin text-blue-500 w-5 h-5" />
    }
    
    // If browsers are available, show running icon regardless of status
    if (browsers && Object.keys(browsers).length > 0) {
      return <Loader2 className="animate-spin text-blue-500 w-5 h-5" />
    }
    
    switch (status) {
      case "running":
        return <Loader2 className="animate-spin text-blue-500 w-5 h-5" />
      case "error":
        return <AlertCircle className="text-red-500 w-5 h-5" />
      default:
        return <Loader2 className="animate-spin text-muted-foreground w-5 h-5" />
    }
  }

  const getStatusText = () => {
    // Show loading state
    if (isLoading) {
      return "Loading...";
    }
    
    // If browsers are available, show "Running" regardless of status
    if (browsers && Object.keys(browsers).length > 0) {
      return "Running";
    }
    
    switch (status) {
      case "running":
        return "Running"
      case "error":
        return "Error"
      default:
        return "Pending"
    }
  }

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on the end task button
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    
    // Don't allow clicking if still loading
    if (isLoading) {
      return;
    }
    
    // Only allow clicking if there are browsers
    if (browsers && Object.keys(browsers).length > 0) {
      onCardClick?.();
    }
  }

  const hasBrowsers = browsers && Object.keys(browsers).length > 0;
  const isClickable = !isLoading && hasBrowsers;

  return (
    <Card 
      className={`flex items-center px-4 py-3 shadow-sm border rounded-lg transition-shadow ${
        isClickable 
          ? 'cursor-pointer hover:shadow-md hover:border-blue-300' 
          : 'cursor-default'
      }`}
      onClick={handleCardClick}
    >
      <div className="flex items-center w-full min-w-0">
        <div className="flex flex-col min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-base font-medium truncate text-left">
              {message}
            </span>
            {getStatusIcon()}
            <span className="text-xs text-muted-foreground">
              {getStatusText()}
            </span>
            {isClickable && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                View Browser
              </span>
            )}
          </div>
          <span className="text-xs text-muted-foreground mt-0.5 truncate">
            {repoName} &bull; {branchName} &bull; {browserCount} browser{browserCount > 1 ? 's' : ''}
          </span>
          {/* Browser URLs */}
          {browsers && Object.keys(browsers).length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.entries(browsers).map(([browserKey, browserInfo]) => (
                <TooltipProvider key={browserKey}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a
                        href={browserInfo.live_view_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="w-3 h-3" />
                        {browserKey}
                      </a>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Open {browserKey} live view</p>
                      <p className="text-xs text-muted-foreground mt-1">{browserInfo.subtask}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3 ml-auto">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button onClick={onEndTask} className="hover:scale-110 transition-transform">
                  <XCircle className="text-red-500 w-5 h-5" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                End task
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </Card>
  )
} 