from azure.storage.queue import QueueClient
import time
import json
import uuid
from typing import Dict, Optional

class AzureQueueManager:
    def __init__(self, connection_string: str, queue_name: str = "commandqueue"):
        """Initialize Azure Queue Manager with connection string and queue name"""
        self.queue_client = QueueClient.from_connection_string(connection_string, queue_name)
        self.response_queue = QueueClient.from_connection_string(connection_string, "responsequeue")
        self.pending_messages = set()  # Track pending message IDs
    
    def send_command(self, command: str, project_name: Optional[str] = None) -> str:
        """Send a command to the Azure queue and return message ID"""
        message_id = str(uuid.uuid4())  # Generate unique message ID
        message = {
            "command": command,
            "project_name": project_name,
            "message_id": message_id,
            "timestamp": time.time()
        }
        result = self.queue_client.send_message(json.dumps(message))
        self.pending_messages.add(message_id)
        return message_id
    
    def wait_for_response(self, message_id: str, timeout: int = 300) -> Dict:
        """Wait for response from the container instance"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if message_id not in self.pending_messages:
                raise ValueError(f"Message ID {message_id} is not being tracked")
                
            messages = self.response_queue.receive_messages(messages_per_page=32)
            for message in messages:
                try:
                    response = json.loads(message.content)
                    if response.get("message_id") == message_id:
                        # Delete the response message after receiving it
                        self.response_queue.delete_message(message.id, message.pop_receipt)
                        self.pending_messages.remove(message_id)
                        return response
                except json.JSONDecodeError:
                    continue
            time.sleep(5)  # Wait 5 seconds before checking again
        raise TimeoutError(f"No response received for message {message_id} within {timeout} seconds")
    
    def execute_command(self, command: str, project_name: Optional[str] = None) -> Dict:
        """Execute a command and wait for response"""
        message_id = self.send_command(command, project_name)
        return self.wait_for_response(message_id) 