"use client";
import React, { useState, useEffect } from "react";
import Sidebar from "./Sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff, Copy, Trash } from "lucide-react";

interface KeySidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface KeyField {
  id: number;
  name: string;
  value: string;
  show: boolean;
}

export default function KeySidebar({ isOpen, onClose }: KeySidebarProps) {
  const [keys, setKeys] = useState<KeyField[]>([
    { id: 1, name: "", value: "", show: false },
  ]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("codex_keys");
      if (stored) {
        const parsed = JSON.parse(stored) as { name: string; value: string }[];
        setKeys(
          parsed.map((k, idx) => ({ id: idx + 1, name: k.name, value: k.value, show: false }))
        );
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  const updateField = (id: number, field: "name" | "value", value: string) => {
    setKeys((prev) => prev.map((k) => (k.id === id ? { ...k, [field]: value } : k)));
  };

  const toggleShow = (id: number) => {
    setKeys((prev) => prev.map((k) => (k.id === id ? { ...k, show: !k.show } : k)));
  };

  const copyValue = async (id: number) => {
    const val = keys.find((k) => k.id === id)?.value || "";
    try {
      await navigator.clipboard.writeText(val);
    } catch {
      // ignore
    }
  };

  const deleteField = (id: number) => {
    setKeys((prev) => prev.filter((k) => k.id !== id));
  };

  const addField = () => {
    setKeys((prev) => [...prev, { id: Date.now(), name: "", value: "", show: false }]);
  };

  const saveKeys = () => {
    const toSave = keys.map(({ name, value }) => ({ name, value }));
    localStorage.setItem("codex_keys", JSON.stringify(toSave));
    onClose();
  };

  return (
    <Sidebar isOpen={isOpen} onClose={onClose} title="Manage Keys">
      <div className="space-y-4">
        {keys.map((k) => (
          <div key={k.id} className="space-y-2">
            <Input
              value={k.name}
              onChange={(e) => updateField(k.id, "name", e.target.value)}
              placeholder="Name"
            />
            <div className="relative">
              <Input
                type={k.show ? "text" : "password"}
                value={k.value}
                onChange={(e) => updateField(k.id, "value", e.target.value)}
                placeholder="Value"
                className="pr-20"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button type="button" onClick={() => toggleShow(k.id)} aria-label="Toggle visibility" className="text-muted-foreground">
                  {k.show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button type="button" onClick={() => copyValue(k.id)} aria-label="Copy value" className="text-muted-foreground">
                  <Copy className="w-4 h-4" />
                </button>
                <button type="button" onClick={() => deleteField(k.id)} aria-label="Delete" className="text-destructive">
                  <Trash className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addField} className="w-full">
          Add Key
        </Button>
        <Button onClick={saveKeys} className="w-full">Save</Button>
      </div>
    </Sidebar>
  );
}
