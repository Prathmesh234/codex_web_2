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

interface Branch {
  name: string
  commit: {
    sha: string
    url: string
  }
  protected?: boolean
}

interface BranchSelectorProps {
  selectedRepo: Repository | null
  selectedBranch: Branch | null
  onBranchSelect: (branch: Branch) => void
  githubToken: string | null
}

export function BranchSelector({ 
  selectedRepo, 
  selectedBranch, 
  onBranchSelect, 
  githubToken 
}: BranchSelectorProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [open, setOpen] = React.useState(false)
  const [branches, setBranches] = React.useState<Branch[]>([])
  const [loading, setLoading] = React.useState(false)

  // Fetch branches for the selected repository
  const fetchBranches = async (repoFullName: string, token: string) => {
    setLoading(true)
    try {
      const response = await fetch(`https://api.github.com/repos/${repoFullName}/branches`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })
      
      if (response.ok) {
        const branchData = await response.json()
        setBranches(branchData)
        console.log('Fetched branches:', branchData.length)
      } else {
        console.error('Failed to fetch branches:', response.status)
        setBranches([])
      }
    } catch (error) {
      console.error('Error fetching branches:', error)
      setBranches([])
    } finally {
      setLoading(false)
    }
  }

  // Fetch branches when repository changes
  React.useEffect(() => {
    if (selectedRepo && githubToken) {
      fetchBranches(selectedRepo.full_name, githubToken)
      setSearchQuery("") // Clear search when repo changes
    } else {
      setBranches([])
    }
  }, [selectedRepo, githubToken])

  // Filter branches based on search query
  const filteredBranches = searchQuery.trim() === "" 
    ? branches 
    : branches.filter(branch =>
        branch.name.toLowerCase().startsWith(searchQuery.toLowerCase())
      )

  const handleBranchSelect = (branchName: string) => {
    const branch = branches.find(b => b.name === branchName)
    if (branch) {
      onBranchSelect(branch)
      setOpen(false)
      setSearchQuery("") // Clear search when branch is selected
    }
  }

  // Don't render if no repository is selected
  if (!selectedRepo) {
    return (
      <Button 
        variant="outline" 
        className="h-10 px-4 rounded-lg border-dashed border-2 border-gray-300 transition-colors"
        disabled={true}
      >
        <GitBranch className="h-4 w-4 mr-2" />
        Select Branch
      </Button>
    )
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          className="min-w-[110px] h-8 px-2 rounded-lg border-dashed border-2 border-gray-300 hover:border-gray-400 transition-colors text-xs"
          disabled={loading || !selectedRepo}
        >
          <GitBranch className="h-4 w-4 mr-2" />
          {selectedBranch ?
            (selectedBranch.name.length > 10
              ? selectedBranch.name.slice(0, 10) + '...'
              : selectedBranch.name)
            : "Select Branch"}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-80 max-h-96 overflow-hidden">
        <DropdownMenuLabel className="px-3 py-2">
          <div className="flex items-center gap-2 mb-2">
            <Search className="h-4 w-4" />
            <span>Search branches</span>
          </div>
          <input
            type="text"
            placeholder="Search branches..."
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
            value={selectedBranch?.name || ""} 
            onValueChange={handleBranchSelect}
          >
            {filteredBranches.length > 0 ? (
              filteredBranches.map((branch) => (
                <DropdownMenuRadioItem
                  key={branch.name}
                  value={branch.name}
                  className="px-3 py-2 cursor-pointer"
                >
                  <div className="flex flex-col items-start">
                    <span className="font-medium text-sm">{branch.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {branch.commit.sha.substring(0, 7)}
                    </span>
                    {branch.protected && (
                      <span className="text-xs text-blue-600 mt-1">
                        Protected branch
                      </span>
                    )}
                  </div>
                </DropdownMenuRadioItem>
              ))
            ) : (
              <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                {loading ? "Loading branches..." : 
                 searchQuery ? "No branches found" : "No branches available"}
              </div>
            )}
          </DropdownMenuRadioGroup>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 