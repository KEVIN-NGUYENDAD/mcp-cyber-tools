import TelegramCommandCenter from './telegramBot.js';
import { paths } from './paths.js';
import fs from 'fs';

function loadEnvFile() {
  console.log('[MAIN] Loading .env file...');

  const envPath = paths.envFile;

  if (!fs.existsSync(envPath)) {
    console.error('[ERROR] .env file not found at:', envPath);
    process.exit(1);
  }

  const content = fs.readFileSync(envPath, 'utf8');
  const lines = content.split('\n');

  const env = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      const value = valueParts.join('=').trim();
      if (key && value) {
        env[key.trim()] = value;
      }
    }
  }

  return env;
}

async function main() {
  console.log('[MAIN] Bot Starting...');
  console.log('[MAIN] Loading credentials from .env...');

  let env = {};
  try {
    env = loadEnvFile();
  } catch (error) {
    console.error('[ERROR] Failed to load .env:', error.message);
    process.exit(1);
  }

  const botToken = env.TELEGRAM_BOT_TOKEN;
  const chatId = env.TELEGRAM_CHAT_ID;

  if (!botToken) {
    console.error('[ERROR] TELEGRAM_BOT_TOKEN not found in .env');
    process.exit(1);
  }

  if (!chatId) {
    console.error('[ERROR] TELEGRAM_CHAT_ID not found in .env');
    process.exit(1);
  }

  console.log('[MAIN] Credentials loaded from .env');
  console.log('[MAIN] Bot Token:', botToken.substring(0, 10) + '...');
  console.log('[MAIN] Chat ID:', chatId);

  // Set environment variables for TelegramCommandCenter
  process.env.TELEGRAM_BOT_TOKEN = botToken;
  process.env.TELEGRAM_CHAT_ID = chatId;

  try {
    const bot = new TelegramCommandCenter();
    await bot.start();
    console.log('[MAIN] Bot Ready - Awaiting Telegram commands');

    process.on('SIGINT', () => {
      console.log('[SHUTDOWN] Stopping bot...');
      bot.bot.stopPolling();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      console.log('[SHUTDOWN] Stopping bot...');
      bot.bot.stopPolling();
      process.exit(0);
    });
  } catch (error) {
    console.error('[FATAL] Bot initialization failed:', error.message);
    process.exit(1);
  }
}

main();
