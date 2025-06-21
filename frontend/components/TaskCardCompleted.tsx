import * as React from "react"
import { Card } from "@/components/ui/card"

interface TaskCardCompletedProps {
  message: string
  repoName: string
  branchName: string
  browserCount: number
}

export function TaskCardCompleted({ message, repoName, branchName, browserCount }: TaskCardCompletedProps) {
  return (
    <Card className="flex items-center justify-between px-4 py-3 shadow-sm border rounded-lg">
      <div className="flex flex-col items-start w-full">
        <span className="text-base font-medium truncate w-full text-left">{message}</span>
        <span className="text-xs text-muted-foreground mt-1 text-left">
          {repoName} &bull; {branchName} &bull; {browserCount} browser{browserCount > 1 ? 's' : ''}
        </span>
      </div>
    </Card>
  )
} 