"use client";
import React from "react";
import { X } from "lucide-react";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export default function Sidebar({ isOpen, onClose, title, children }: SidebarProps) {
  return (
    <div
      className={`fixed inset-y-0 left-0 z-50 w-72 transform bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-transform duration-300 ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-sidebar-border">
        {title && <h2 className="font-semibold text-sm">{title}</h2>}
        <button onClick={onClose} aria-label="Close sidebar">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="p-4 overflow-y-auto h-full">
        {children}
      </div>
    </div>
  );
}
