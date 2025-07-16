from azure.storage.queue import QueueClient
import time
import json
import uuid
from typing import Dict, Optional

class AzureQueueManager:
    def __init__(self, connection_string: str, queue_name: str = "commandqueue"):
        """Initialize Azure Queue Manager with connection string and queue name"""
        print(f"[DEBUG] Initializing AzureQueueManager with connection string: {connection_string[:50]}...")
        print(f"[DEBUG] Queue name: {queue_name}")
        try:
            self.queue_client = QueueClient.from_connection_string(connection_string, queue_name)
            self.response_queue = QueueClient.from_connection_string(connection_string, "responsequeue")
            self.pending_messages = set()  # Track pending message IDs
            print("[DEBUG] AzureQueueManager initialized successfully")
        except Exception as e:
            print(f"[ERROR] Failed to create QueueClient: {str(e)}")
            raise
    
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
        # Add message_id to pending_messages if not already there
        if message_id not in self.pending_messages:
            self.pending_messages.add(message_id)
            
        start_time = time.time()
        while time.time() - start_time < timeout:
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

    def receive_command(self, timeout: int = 30) -> Optional[Dict]:
        """Receive a single command message from the command queue"""
        messages = self.queue_client.receive_messages(
            messages_per_page=1, visibility_timeout=timeout
        )
        for msg in messages:
            try:
                payload = json.loads(msg.content)
            except json.JSONDecodeError:
                # discard invalid message
                self.queue_client.delete_message(msg.id, msg.pop_receipt)
                continue
            # remove message from queue and return payload
            self.queue_client.delete_message(msg.id, msg.pop_receipt)
            return payload
        return None

    def receive_response(self, timeout: int = 30) -> Optional[Dict]:
        """Receive a single response message from the response queue"""
        messages = self.response_queue.receive_messages(
            messages_per_page=1, visibility_timeout=timeout
        )
        for msg in messages:
            try:
                payload = json.loads(msg.content)
            except json.JSONDecodeError:
                # discard invalid message
                self.response_queue.delete_message(msg.id, msg.pop_receipt)
                continue
            # remove message from queue and return payload
            self.response_queue.delete_message(msg.id, msg.pop_receipt)
            return payload
        return None