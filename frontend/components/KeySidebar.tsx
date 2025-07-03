"use client";
import React, { useState } from "react";
import Sidebar from "./Sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff } from "lucide-react";

interface KeySidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function KeySidebar({ isOpen, onClose }: KeySidebarProps) {
  const [keyName, setKeyName] = useState("");
  const [keyValue, setKeyValue] = useState("");
  const [show, setShow] = useState(false);

  return (
    <Sidebar isOpen={isOpen} onClose={onClose} title="Add Key">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Key name</label>
          <Input
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            placeholder="e.g. OPENAI_API_KEY"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Key value</label>
          <div className="relative">
            <Input
              type={show ? "text" : "password"}
              value={keyValue}
              onChange={(e) => setKeyValue(e.target.value)}
              placeholder="Enter key..."
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShow((s) => !s)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
            >
              {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
        <Button onClick={onClose}>Save</Button>
      </div>
    </Sidebar>
  );
}
