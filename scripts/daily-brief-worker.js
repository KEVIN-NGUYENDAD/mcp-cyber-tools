#!/usr/bin/env node
/**
 * PM2 Daily Brief Worker - Runs daily brief generation at 3:00 PM UTC
 *
 * Replaces Windows Task Scheduler with PM2-managed background worker.
 * Runs python run_daily_brief.py every day at 3:00 PM (15:00 UTC).
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const PROJECT_ROOT = path.resolve(__dirname, '..');
const LOGS_DIR = path.join(PROJECT_ROOT, 'logs');
const LOG_FILE = path.join(LOGS_DIR, 'daily-brief.log');
const SCRIPT_PATH = path.join(__dirname, 'run_daily_brief.py');

// Ensure logs directory exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

/**
 * Write log message to file and console
 */
function log(message) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ${message}\n`;

  // Write to file
  fs.appendFileSync(LOG_FILE, logEntry, 'utf-8');

  // Also output to console (PM2 will capture this)
  console.error(`[BRIEF-WORKER] ${message}`);
}

/**
 * Get time until next 3:00 PM UTC (15:00)
 */
function getTimeUntilNextRun() {
  const now = new Date();
  const schedule = new Date();

  // Set to 3:00 PM UTC
  schedule.setUTCHours(15, 0, 0, 0);

  // If we've already passed 3:00 PM today, schedule for tomorrow
  if (now >= schedule) {
    schedule.setDate(schedule.getDate() + 1);
  }

  const msUntilRun = schedule.getTime() - now.getTime();
  return msUntilRun;
}

/**
 * Run the Daily Brief Python script
 */
function runDailyBrief() {
  return new Promise((resolve, reject) => {
    const timestamp = new Date().toISOString();
    log(`Running Daily Brief at ${timestamp}`);

    // Change to scripts directory for execution
    const options = {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe']
    };

    const process = spawn('python', ['run_daily_brief.py'], options);
    let stdout = '';
    let stderr = '';

    process.stdout.on('data', (data) => {
      const line = data.toString().trim();
      stdout += line + '\n';
      log(`STDOUT: ${line}`);
    });

    process.stderr.on('data', (data) => {
      const line = data.toString().trim();
      stderr += line + '\n';
      log(`STDERR: ${line}`);
    });

    process.on('close', (code) => {
      if (code === 0) {
        log(`✓ Daily Brief completed successfully (exit code: ${code})`);
        resolve({ code, stdout, stderr });
      } else {
        log(`✗ Daily Brief failed (exit code: ${code})`);
        resolve({ code, stdout, stderr });
      }
    });

    process.on('error', (err) => {
      log(`✗ Failed to spawn Daily Brief process: ${err.message}`);
      reject(err);
    });
  });
}

/**
 * Main worker loop
 */
async function startWorker() {
  log('Daily Brief Worker Started');
  log(`Script: ${SCRIPT_PATH}`);
  log(`Logs: ${LOG_FILE}`);
  log(`Schedule: 3:00 PM UTC (15:00) every day`);
  log('');

  // Track last run date to prevent multiple runs on same day
  let lastRunDate = null;

  while (true) {
    const now = new Date();
    const today = now.toISOString().split('T')[0];

    // Check if it's 3:00 PM UTC (15:00-15:59)
    const utcHours = now.getUTCHours();
    const utcMinutes = now.getUTCMinutes();

    if (utcHours === 15 && utcMinutes < 59 && lastRunDate !== today) {
      try {
        await runDailyBrief();
        lastRunDate = today;
        log(`Scheduled next run for tomorrow (${new Date(new Date().getTime() + 86400000).toISOString().split('T')[0]})`);

        // Sleep until end of hour to avoid multiple runs
        const sleepMs = (60 - utcMinutes - 1) * 60000;
        log(`Sleeping for ${Math.round(sleepMs / 1000)}s to avoid duplicate runs`);
        await new Promise(resolve => setTimeout(resolve, sleepMs));
      } catch (err) {
        log(`✗ Error running Daily Brief: ${err.message}`);
      }
    }

    // Check every 60 seconds
    await new Promise(resolve => setTimeout(resolve, 60000));
  }
}

/**
 * Graceful shutdown handler
 */
process.on('SIGINT', () => {
  log('SIGINT received - shutting down gracefully');
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('SIGTERM received - shutting down gracefully');
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  log(`✗ UNCAUGHT EXCEPTION: ${err.message}`);
  log(`Stack: ${err.stack}`);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  log(`✗ UNHANDLED REJECTION: ${reason}`);
  process.exit(1);
});

// Start the worker
startWorker().catch(err => {
  log(`✗ Worker crashed: ${err.message}`);
  process.exit(1);
});
