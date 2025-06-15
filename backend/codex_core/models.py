from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class CommandEntry(BaseModel):
    """Represents a single command execution with its output"""
    command: str = Field(..., description="The command that was executed")
    output: str = Field(..., description="The output of the command")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the command was executed")
    success: bool = Field(..., description="Whether the command executed successfully")
    error: Optional[str] = Field(None, description="Error message if the command failed")

class CommandHistory(BaseModel):
    """Maintains a history of executed commands"""
    entries: List[CommandEntry] = Field(default_factory=list, description="List of command entries")
    
    def add_command(self, command: str, output: str, success: bool = True, error: Optional[str] = None) -> None:
        """Add a new command entry to the history"""
        self.entries.append(CommandEntry(
            command=command,
            output=output,
            success=success,
            error=error
        ))
    
    def get_last_n(self, n: int = 5) -> List[CommandEntry]:
        """Get the last n commands from history"""
        return self.entries[-n:] if self.entries else []
    
    def get_all(self) -> List[CommandEntry]:
        """Get all command entries"""
        return self.entries
    
    def get_sequence(self) -> List[Dict]:
        """Get a numbered sequence of commands and their outputs"""
        return [
            {
                "sequence": i + 1,
                "command": entry.command,
                "output": entry.output,
                "success": entry.success,
                "error": entry.error,
                "timestamp": entry.timestamp.isoformat()
            }
            for i, entry in enumerate(self.entries)
        ]

class TaskState(BaseModel):
    """Represents the current state of a task execution"""
    task_name: str = Field(..., description="The name/description of the task")
    command_history: CommandHistory = Field(default_factory=CommandHistory, description="History of executed commands")
    retry_count: int = Field(default=0, description="Number of retry attempts for failed commands")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts allowed")
    current_directory: str = Field(default="/projects", description="Current working directory")
    
    def add_command(self, command: str, output: str, success: bool = True, error: Optional[str] = None) -> None:
        """Add a command to the history and update task state"""
        self.command_history.add_command(command, output, success, error)
        if not success:
            self.retry_count += 1
    
    def reset_retry_count(self) -> None:
        """Reset the retry counter after a successful command"""
        self.retry_count = 0
    
    def should_retry(self) -> bool:
        """Check if we should retry after a failed command"""
        return self.retry_count < self.max_retries
    
    def to_dict(self) -> Dict:
        """Convert task state to dictionary for template rendering"""
        return {
            "task_name": self.task_name,
            "command_sequence": self.command_history.get_sequence(),  # Get numbered sequence
            "last_command": self.command_history.entries[-1].command if self.command_history.entries else None,
            "last_output": self.command_history.entries[-1].output if self.command_history.entries else None,
            "total_commands": len(self.command_history.entries),
            "current_directory": self.current_directory
        } 