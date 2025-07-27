const express = require('express');
const bodyParser = require('body-parser');
const morgan = require('morgan');
const { spawn, execSync } = require('child_process');
const path = require('path');
const { QueueClient } = require('@azure/storage-queue');

// Application bootstrap
console.log(`Starting application at ${new Date().toISOString()}`);

const PORT = process.env.PORT || 3000;
const PROJECTS_DIR = '/projects';
const shellBin = 'bash';

// Verify shell availability
try {
  const version = execSync(`${shellBin} --version`).toString().trim();
  console.log(`Shell available: ${version}`);
} catch (err) {
  console.error(`Shell '${shellBin}' not available:`, err.message);
  process.exit(1);
}

function runCommand(cmd, opts = {}) {
  console.log(`Executing command: ${cmd} (cwd=${opts.cwd || 'default'})`);
  return new Promise((resolve, reject) => {
    const child = spawn(shellBin, ['-c', cmd], { ...opts, env: process.env });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', d => {
      const text = d.toString();
      stdout += text;
      console.log(`stdout: ${text.trim()}`);
    });
    child.stderr.on('data', d => {
      const text = d.toString();
      stderr += text;
      console.error(`stderr: ${text.trim()}`);
    });
    child.on('close', code => {
      console.log(`Command exited with code ${code}`);
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(stderr));
    });
    child.on('error', err => {
      console.error(`Failed to spawn: ${err.message}`);
      reject(err);
    });
  });
}

(async () => {
  console.log('Initializing queues');
  const connStr = process.env.AZURE_STORAGE_CONNECTION_STRING;
  console.log('AZURE_STORAGE_CONNECTION_STRING:', connStr); // Log the connection string at startup
  
  // Extract and log storage account name for verification
  try {
    const accountMatch = connStr.match(/AccountName=([^;]+)/);
    if (accountMatch) {
      const storageAccountName = accountMatch[1];
      console.log(`🎯 CONTAINER VERIFICATION:`);
      console.log(`🎯 Container using Storage Account: ${storageAccountName}`);
      console.log(`🎯 This should match the sender's storage account!`);
    }
  } catch (e) {
    console.log('Could not parse storage account name from connection string');
  }
  
  // Allow overriding queue names via environment variables
  const commandQueueName = process.env.COMMAND_QUEUE || 'commandqueue';
  const responseQueueName = process.env.RESPONSE_QUEUE || 'responsequeue';
  console.log(`Using command queue: ${commandQueueName}`);
  console.log(`Using response queue: ${responseQueueName}`);
  const cmdQueue = new QueueClient(connStr, commandQueueName);
  const rspQueue = new QueueClient(connStr, responseQueueName);
  
  // Verify queues exist with retry logic (created by ARM template)
  async function verifyQueuesWithRetry(maxRetries = 10, baseDelay = 5000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`🔄 Queue verification attempt ${attempt}/${maxRetries}`);
        
        // Test command queue
        const cmdProps = await cmdQueue.getProperties();
        console.log(`✅ Command queue ready: ${cmdProps.name}`);
        
        // Test response queue  
        const rspProps = await rspQueue.getProperties();
        console.log(`✅ Response queue ready: ${rspProps.name}`);
        
        console.log(`🎉 All queues verified successfully on attempt ${attempt}`);
        return true;
        
      } catch (error) {
        console.error(`❌ Queue verification attempt ${attempt} failed:`, error.message);
        
        if (attempt === maxRetries) {
          console.error(`❌ All ${maxRetries} queue verification attempts failed!`);
          console.error(`❌ This likely means:`);
          console.error(`❌ 1. Storage account connection string is invalid`);
          console.error(`❌ 2. Queues don't exist in storage account`);
          console.error(`❌ 3. Network connectivity issues`);
          console.error(`❌ Container will continue but queue operations will fail`);
          return false;
        }
        
        // Exponential backoff: 5s, 10s, 20s, 40s, etc.
        const delay = baseDelay * Math.pow(2, attempt - 1);
        console.log(`⏳ Waiting ${delay/1000}s before retry ${attempt + 1}...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    return false;
  }
  
  const queuesReady = await verifyQueuesWithRetry();

  const app = express();
  app.use(morgan('combined'));
  app.use(bodyParser.json());

  app.get('/health', (_req, res) => {
    const healthStatus = {
      status: 'ok',
      shell: shellBin,
      timestamp: new Date().toISOString(),
      queues: {
        verified: queuesReady,
        consecutiveErrors,
        storageAccount: connStr ? connStr.match(/AccountName=([^;]+)/)?.[1] : 'unknown'
      },
      uptime: process.uptime(),
      memory: process.memoryUsage()
    };
    
    console.log('🩺 Health check:', JSON.stringify(healthStatus, null, 2));
    res.json(healthStatus);
  });

  app.post('/execute', async (req, res) => {
    console.log('Execute request:', req.body);
    const { command, projectName } = req.body;
    if (!command) {
      console.error('Missing command');
      return res.status(400).json({ error: 'command required' });
    }
    // Resolve cwd: absolute or relative under /projects
    let cwd;
    if (projectName) {
      cwd = path.isAbsolute(projectName)
        ? projectName
        : path.join(PROJECTS_DIR, projectName);
    }
    try {
      const { stdout, stderr } = await runCommand(command, { cwd });
      console.log('Execute success');
      res.json({ success: true, stdout, stderr });
    } catch (e) {
      console.error('Execute error:', e.message);
      res.status(500).json({ success: false, error: e.message });
    }
  });

  app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));

  console.log('🚀 Starting resilient polling loop');
  console.log(`📊 Queue status: ${queuesReady ? 'Ready' : 'Failed verification (will retry operations)'}`);
  
  let consecutiveErrors = 0;
  const maxConsecutiveErrors = 5;
  
  /**
   * Poll the command queue at intervals to process incoming messages.
   */
  async function pollQueue() {
    try {
      console.log('🔍 Polling for commands at', new Date().toISOString());
      const { receivedMessageItems } = await cmdQueue.receiveMessages({ numberOfMessages: 1, visibilityTimeout: 30 });
      
      // Reset error counter on successful poll
      consecutiveErrors = 0;
      
      if (receivedMessageItems.length === 0) {
        console.log('📭 No messages, waiting...');
      } else {
        for (const msg of receivedMessageItems) {
          console.log('Message received');
          console.log('AZURE_STORAGE_CONNECTION_STRING (on command receive):', connStr);
          let payload, result;
          try {
            payload = JSON.parse(msg.messageText);
            console.log('Payload:', payload);
          } catch {
            console.error('Invalid JSON');
            result = { success: false, error: 'Bad JSON' };
          }
          if (!result) {
            const { command, project_name, message_id } = payload;
            const cwd = project_name && (path.isAbsolute(project_name)
              ? project_name
              : path.join(PROJECTS_DIR, project_name));
            try {
              const { stdout, stderr } = await runCommand(command, { cwd });
              result = { success: true, stdout, stderr };
            } catch (e) {
              console.error('Command error:', e.message);
              result = { success: false, error: e.message };
            }
            await rspQueue.sendMessage(JSON.stringify({ message_id, ...result }));
            console.log('Response sent for', message_id);
          }
          await cmdQueue.deleteMessage(msg.messageId, msg.popReceipt);
          console.log('Message deleted');
        }
      }
    } catch (err) {
      consecutiveErrors++;
      console.error(`❌ Polling error (${consecutiveErrors}/${maxConsecutiveErrors}):`, err.message);
      
      if (consecutiveErrors >= maxConsecutiveErrors) {
        console.error(`🚨 Too many consecutive polling errors (${maxConsecutiveErrors})`);
        console.error(`🚨 This might indicate:`);
        console.error(`🚨 1. Network connectivity issues`);
        console.error(`🚨 2. Storage account access problems`);
        console.error(`🚨 3. Queue permissions issues`);
        console.error(`🔄 Will continue polling but with longer delays...`);
        
        // Use longer delay after multiple errors
        setTimeout(pollQueue, 30000); // 30 seconds
        return;
      }
      
      // Normal error recovery with exponential backoff
      const errorDelay = 5000 * Math.pow(2, Math.min(consecutiveErrors - 1, 3)); // Max 40s
      console.log(`⏳ Error recovery: waiting ${errorDelay/1000}s before next poll...`);
      setTimeout(pollQueue, errorDelay);
      return;
    }
    
    // Normal polling interval
    setTimeout(pollQueue, 5000);
  }
  
  console.log('🏃 Starting queue polling...');
  pollQueue();
})();