from azure.storage.queue import QueueClient
import time
import json
import uuid
import os
from typing import Dict, Optional

class AzureQueueManager:
    def __init__(self, connection_string: str, queue_name: str = "commandqueue"):
        """Initialize Azure Queue Manager with connection string and queue names (override via COMMAND_QUEUE/RESPONSE_QUEUE env vars)"""
        print(f"[DEBUG] Initializing AzureQueueManager with connection string: {connection_string[:50]}...")
        cmd_queue = os.getenv("COMMAND_QUEUE", queue_name)
        resp_queue = os.getenv("RESPONSE_QUEUE", "responsequeue")
        print(f"[DEBUG] Command queue name: {cmd_queue}")
        print(f"[DEBUG] Response queue name: {resp_queue}")
        print(f"[DEBUG] Connection string: {connection_string}")
        print(f"[DEBUG] The command being sent is")
        try:
            self.queue_client = QueueClient.from_connection_string(connection_string, cmd_queue)
            self.response_queue = QueueClient.from_connection_string(connection_string, resp_queue)
            self.pending_messages = set()  # Track pending message IDs
            
            # Verify queues exist (created by ARM template)
            try:
                cmd_properties = self.queue_client.get_queue_properties()
                print(f"[DEBUG] ✅ Connected to command queue '{cmd_properties.name}'")
            except Exception as e:
                print(f"[ERROR] Command queue '{cmd_queue}' does not exist: {e}")
                raise
                
            try:
                resp_properties = self.response_queue.get_queue_properties()
                print(f"[DEBUG] ✅ Connected to response queue '{resp_properties.name}'")
            except Exception as e:
                print(f"[ERROR] Response queue '{resp_queue}' does not exist: {e}")
                raise
                
            print("[DEBUG] AzureQueueManager initialized successfully")
        except Exception as e:
            print(f"[ERROR] Failed to create QueueClient: {str(e)}")
            raise
    
    def send_command(self, command: str, project_name: Optional[str] = None) -> str:
        """Send a command to the Azure queue and return message ID"""
        # Log the connection string (masked for security)
        masked_conn_str = self.queue_client.credential.account_key[:4] + '...' + self.queue_client.credential.account_key[-4:] if hasattr(self.queue_client.credential, 'account_key') else 'N/A'
        print(f"[DEBUG] Sending command using connection string (masked): {self.queue_client.account_name} ... {masked_conn_str}")
        message_id = str(uuid.uuid4())  # Generate unique message ID
        message = {
            "command": command,
            "project_name": project_name,
            "message_id": message_id,
            "timestamp": time.time()
        }
        print(f"[DEBUG] Sending message to queue: {json.dumps(message, indent=2)}")
        
        # Test queue connection before sending
        try:
            properties = self.queue_client.get_queue_properties()
            print(f"[DEBUG] ✅ Command queue exists: {properties.name}, message count: {properties.approximate_message_count}")
            
            # Extract storage account name from connection string for verification
            storage_account = self.queue_client.account_name
            queue_url = self.queue_client.url
            print(f"[DEBUG] 🔗 Sending to Storage Account: {storage_account}")
            print(f"[DEBUG] 🔗 Queue URL: {queue_url}")
            
        except Exception as e:
            print(f"[DEBUG] ❌ Command queue connection error: {e}")
            raise
        
        # Send message
        try:
            result = self.queue_client.send_message(json.dumps(message))
            print(f"[DEBUG] ✅ Message sent successfully. Result: {result}")
            
            # Show exact storage account and queue details for comparison with Azure Portal
            print(f"[DEBUG] 🎯 AZURE PORTAL VERIFICATION:")
            print(f"[DEBUG] 🎯 Storage Account Name: {self.queue_client.account_name}")
            print(f"[DEBUG] 🎯 Queue Name: {self.queue_client.queue_name}")
            print(f"[DEBUG] 🎯 Full Queue URL: {self.queue_client.url}")
            print(f"[DEBUG] 🎯 Message ID: {result.get('id', 'unknown')}")
            print(f"[DEBUG] 🎯 Message Content: {json.dumps(message)}")
            
        except Exception as e:
            print(f"[DEBUG] ❌ Failed to send message: {e}")
            raise
        
        # Verify message was added to queue
        try:
            properties = self.queue_client.get_queue_properties()
            print(f"[DEBUG] 📊 Queue depth after sending: {properties.approximate_message_count} messages")
            
            # Double-check by trying to peek at the message
            peeked_messages = self.queue_client.peek_messages(max_messages=5)
            print(f"[DEBUG] 👀 Peeked {len(peeked_messages)} messages from queue:")
            for i, msg in enumerate(peeked_messages):
                try:
                    content = json.loads(msg.content)
                    print(f"[DEBUG]   Message {i+1}: ID={content.get('message_id', 'unknown')}, command='{content.get('command', 'unknown')[:50]}...'")
                except:
                    print(f"[DEBUG]   Message {i+1}: Raw content={msg.content[:100]}...")
            
            # EXTRA VERIFICATION: Try to receive (but don't delete) the message we just sent
            print(f"[DEBUG] 🔍 EXTRA VERIFICATION - Attempting to receive message:")
            received_messages = self.queue_client.receive_messages(max_messages=1, visibility_timeout=10)
            received_count = 0
            for received_msg in received_messages:
                received_count += 1
                try:
                    received_content = json.loads(received_msg.content)
                    if received_content.get('message_id') == message_id:
                        print(f"[DEBUG] ✅ CONFIRMED: Message {message_id} successfully received from queue!")
                        print(f"[DEBUG] ✅ This proves the message is actually in Azure Storage!")
                    else:
                        print(f"[DEBUG] ⚠️  Received different message: {received_content.get('message_id')}")
                except Exception as parse_error:
                    print(f"[DEBUG] ⚠️  Could not parse received message: {parse_error}")
                
                # Important: Make message visible again (don't delete it)
                self.queue_client.update_message(received_msg.id, received_msg.pop_receipt, visibility_timeout=0)
                print(f"[DEBUG] 🔄 Made message visible again for container to process")
                break
            
            if received_count == 0:
                print(f"[DEBUG] ❌ PROBLEM: Could not receive the message we just sent!")
                print(f"[DEBUG] ❌ This indicates the message might not actually be in the queue!")
                    
        except Exception as e:
            print(f"[DEBUG] ⚠️  Could not verify queue depth: {e}")
        
        self.pending_messages.add(message_id)
        print(f"[DEBUG] Message ID {message_id} added to pending_messages")
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