import TelegramCommandCenter from './telegramBot.js';
import AlertDelivery from './alertDelivery.js';
import IncidentAlerter from './incidentAlerter.js';

console.log('Testing ESM imports...\n');

console.log('[1] TelegramCommandCenter imported:', typeof TelegramCommandCenter === 'function' ? '✅' : '❌');
console.log('[2] AlertDelivery imported:', typeof AlertDelivery === 'function' ? '✅' : '❌');
console.log('[3] IncidentAlerter imported:', typeof IncidentAlerter === 'function' ? '✅' : '❌');

console.log('\nAll imports successful.\n');

process.exit(0);
