from codex_agent.azure_queue import AzureQueueManager

conn_str = ""

print("Testing Azure Queue system...")
queue_mgr = AzureQueueManager(conn_str)

# Test simple command first
print("\n1. Testing simple echo command:")
result = queue_mgr.execute_command("echo 'Testing queue system'")
print("Result:", result)

# Test git clone command
print("\n2. Testing git clone command:")
result = queue_mgr.execute_command("git clone https://github.com/Prathmesh234/local_gpt.git /projects/local_gpt")
print("Result:", result)

# Test listing projects directory
print("\n3. Testing directory listing:")
result = queue_mgr.execute_command("ls -la /projects")
print("Result:", result)