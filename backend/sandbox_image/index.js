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
  const cmdQueue = new QueueClient(connStr, 'commandqueue');
  const rspQueue = new QueueClient(connStr, 'responsequeue');
  await cmdQueue.createIfNotExists(); console.log('Command queue ready');
  await rspQueue.createIfNotExists(); console.log('Response queue ready');

  const app = express();
  app.use(morgan('combined'));
  app.use(bodyParser.json());

  app.get('/health', (_req, res) => {
    console.log('Health check');
    res.json({ status: 'ok', shell: shellBin });
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

  console.log('Starting polling loop');
  while (true) {
    try {
      const { receivedMessageItems } = await cmdQueue.receiveMessages({ numberOfMessages: 1, visibilityTimeout: 30 });
      if (!receivedMessageItems.length) {
        await new Promise(r => setTimeout(r, 5000));
        continue;
      }
      for (const msg of receivedMessageItems) {
        console.log('Message received');
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
          // Resolve cwd for queue tasks
          let cwd = project_name && (path.isAbsolute(project_name)
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
    } catch (err) {
      console.error('Polling error:', err.message);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
})();