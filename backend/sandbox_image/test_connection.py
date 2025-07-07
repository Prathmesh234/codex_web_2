#!/usr/bin/env python3
"""Test script to verify Azure Storage connection string"""

import os
import sys
from azure.storage.queue import QueueClient

def test_connection_string():
    """Test the Azure Storage connection string"""
    # Load connection string from environment
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not found in environment")
        return False
    
    print(f"✅ Connection string found: {connection_string[:50]}...")
    
    # Test connection by creating a QueueClient
    try:
        queue_client = QueueClient.from_connection_string(connection_string, "commandqueue")
        print("✅ QueueClient created successfully")
        
        # Try to get queue properties to verify connection
        properties = queue_client.get_queue_properties()
        print(f"✅ Queue properties retrieved: {properties.name}")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Azure Storage connection string...")
    success = test_connection_string()
    sys.exit(0 if success else 1)