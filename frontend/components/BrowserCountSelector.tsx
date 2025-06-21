"use client"

import * as React from "react"
import { Globe } from "lucide-react"
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

interface BrowserCountSelectorProps {
  browserCount: number | null
  onBrowserCountSelect: (count: number) => void
}

export function BrowserCountSelector({ 
  browserCount, 
  onBrowserCountSelect 
}: BrowserCountSelectorProps) {
  const [open, setOpen] = React.useState(false)

  const handleCountSelect = (count: string) => {
    const numCount = parseInt(count)
    onBrowserCountSelect(numCount)
    setOpen(false)
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          className="min-w-[90px] h-8 px-2 rounded-lg border-dashed border-2 border-gray-300 hover:border-gray-400 transition-colors text-xs"
        >
          <Globe className="h-4 w-4 mr-2" />
          {browserCount ? `${browserCount} Browser${browserCount > 1 ? 's' : ''}` : "Select Browsers"}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64">
        <DropdownMenuLabel className="px-3 py-2 text-center">
          <span className="text-sm font-medium">How many async browsers needed?</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup 
          value={browserCount?.toString() || ""} 
          onValueChange={handleCountSelect}
        >
          <DropdownMenuRadioItem
            value="1"
            className="px-3 py-2 cursor-pointer"
          >
            <div className="flex flex-col items-start">
              <span className="font-medium text-sm">1 Browser</span>
              <span className="text-xs text-muted-foreground">
                Single browser session
              </span>
            </div>
          </DropdownMenuRadioItem>
          <DropdownMenuRadioItem
            value="2"
            className="px-3 py-2 cursor-pointer"
          >
            <div className="flex flex-col items-start">
              <span className="font-medium text-sm">2 Browsers</span>
              <span className="text-xs text-muted-foreground">
                Dual browser sessions
              </span>
            </div>
          </DropdownMenuRadioItem>
          <DropdownMenuRadioItem
            value="3"
            className="px-3 py-2 cursor-pointer"
          >
            <div className="flex flex-col items-start">
              <span className="font-medium text-sm">3 Browsers</span>
              <span className="text-xs text-muted-foreground">
                Triple browser sessions
              </span>
            </div>
          </DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 