'use client';
import { useContext } from 'react';
import { ThemeContext } from './ThemeProvider';
import { Button } from '@/components/ui/button';
import { Moon, Sun } from 'lucide-react';

export default function DarkModeToggle() {
  const { theme, toggleTheme } = useContext(ThemeContext);
  return (
    <Button variant="outline" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
      {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </Button>
  );
}
