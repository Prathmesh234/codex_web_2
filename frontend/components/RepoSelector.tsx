"use client"

import * as React from "react"
import { Search, GitBranch } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

interface Repository {
  id: number
  name: string
  full_name: string
  html_url: string
  clone_url: string
  description: string | null
}

interface RepoSelectorProps {
  selectedRepo: Repository | null
  onRepoSelect: (repo: Repository) => void
  repositories: Repository[]
  isLoading?: boolean
}

export function RepoSelector({ 
  selectedRepo, 
  onRepoSelect, 
  repositories, 
  isLoading = false 
}: RepoSelectorProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [open, setOpen] = React.useState(false)

  // Filter repositories based on search query
  const filteredRepos = searchQuery.trim() === "" 
    ? repositories 
    : repositories.filter(repo =>
        repo.name.toLowerCase().startsWith(searchQuery.toLowerCase()) ||
        repo.full_name.toLowerCase().startsWith(searchQuery.toLowerCase())
      )

  const handleRepoSelect = (repoName: string) => {
    const repo = repositories.find(r => r.full_name === repoName)
    if (repo) {
      onRepoSelect(repo)
      setOpen(false)
      setSearchQuery("") // Clear search when repo is selected
    }
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          className="min-w-[140px] h-8 px-2 rounded-lg border-dashed border-2 border-gray-300 hover:border-gray-400 transition-colors text-xs"
          disabled={isLoading}
        >
          <GitBranch className="h-4 w-4 mr-2" />
          {selectedRepo ?
            (selectedRepo.name.length > 14
              ? selectedRepo.name.slice(0, 14) + '...'
              : selectedRepo.name)
            : "Select Repository"}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-80 max-h-96 overflow-hidden">
        <DropdownMenuLabel className="px-3 py-2">
          <div className="flex items-center gap-2 mb-2">
            <Search className="h-4 w-4" />
            <span>Search repositories</span>
          </div>
          <input
            type="text"
            placeholder="Search repositories..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            className={cn(
              "flex h-8 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            )}
          />
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="max-h-64 overflow-y-auto">
          <DropdownMenuRadioGroup 
            value={selectedRepo?.full_name || ""} 
            onValueChange={handleRepoSelect}
          >
            {filteredRepos.length > 0 ? (
              filteredRepos.map((repo) => (
                <DropdownMenuRadioItem
                  key={repo.id}
                  value={repo.full_name}
                  className="px-3 py-2 cursor-pointer"
                >
                  <div className="flex flex-col items-start">
                    <span className="font-medium text-sm">{repo.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {repo.full_name}
                    </span>
                    {repo.description && (
                      <span className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {repo.description}
                      </span>
                    )}
                  </div>
                </DropdownMenuRadioItem>
              ))
            ) : (
              <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                {searchQuery ? "No repositories found" : "No repositories available"}
              </div>
            )}
          </DropdownMenuRadioGroup>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 