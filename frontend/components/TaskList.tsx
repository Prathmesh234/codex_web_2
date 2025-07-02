"use client"

import * as React from "react"
import { Card } from "@/components/ui/card"
import { XCircle, Loader2 } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { TaskCardToDo } from './TaskCardToDo';
import { TaskCardCompleted } from './TaskCardCompleted';
import { TaskCardDel } from './TaskCardDel';
import { useRouter } from 'next/navigation';

export type TaskStatus = "todo" | "completed" | "deleted" | "running" | "error"

export interface Task {
  id: string
  message: string
  status: TaskStatus
  repoName: string
  branchName: string
  browserCount: number
  browsers?: Record<string, {
    live_view_url: string
    session_id: string
    subtask: string
  }>
  sessionId?: string
  isLoading?: boolean
  documentation?: Record<string, any>
}

interface TaskListProps {
  tasks: Task[]
  onEndTask: (id: string) => void
}

const TABS = [
  { key: "completed", label: "Completed" },
  { key: "todo", label: "To Do" },
  { key: "deleted", label: "Deleted" },
] as const

type TabKey = typeof TABS[number]["key"]

export function TaskList({ tasks, onEndTask }: TaskListProps) {
  const [activeTab, setActiveTab] = React.useState<TabKey>("todo")
  const router = useRouter()

  const filteredTasks = tasks.filter(t => t.status === activeTab)

  const handleCardClick = (task: Task) => {
    if (task.browsers && Object.keys(task.browsers).length > 0) {
      // Navigate to browser view page with browser data
      const browsersParam = encodeURIComponent(JSON.stringify(task.browsers));
      const messageParam = encodeURIComponent(task.message);
      const sessionParam = task.sessionId ? `&session_id=${encodeURIComponent(task.sessionId)}` : '';
      router.push(`/browser-view?browsers=${browsersParam}&message=${messageParam}${sessionParam}`);
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto mt-0">
      {/* Tabs */}
      <div className="flex gap-4 border-b pb-1 justify-center">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`text-sm font-medium pb-0.5 border-b-2 transition-colors ${activeTab === tab.key ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-primary"}`}
            onClick={() => setActiveTab(tab.key as TabKey)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {/* Task Cards */}
      <div className="flex flex-col mt-3">
        {filteredTasks.length === 0 && (
          <div className="text-muted-foreground text-sm text-center py-6">No tasks</div>
        )}
        {filteredTasks.map((task, idx) => {
          const isLast = idx === filteredTasks.length - 1;
          const cardClass = isLast ? '' : 'mb-6';
          return activeTab === 'todo' ? (
            <div key={task.id} className={cardClass}>
              <TaskCardToDo
                message={task.message}
                repoName={task.repoName}
                branchName={task.branchName}
                browserCount={task.browserCount}
                onEndTask={() => onEndTask(task.id)}
                status={task.status}
                browsers={task.browsers}
                onCardClick={() => handleCardClick(task)}
                isLoading={task.isLoading}
              />
            </div>
          ) : activeTab === 'completed' ? (
            <div key={task.id} className={cardClass}>
              <TaskCardCompleted
                message={task.message}
                repoName={task.repoName}
                branchName={task.branchName}
                browserCount={task.browserCount}
                sessionId={task.sessionId}
                browsers={task.browsers}
                documentation={task.documentation}
              />
            </div>
          ) : (
            <div key={task.id} className={cardClass}>
              <TaskCardDel
                message={task.message}
                repoName={task.repoName}
                branchName={task.branchName}
                browserCount={task.browserCount}
              />
            </div>
          );
        })}
      </div>
    </div>
  )
} 