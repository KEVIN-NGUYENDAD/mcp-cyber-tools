// Ket noi lai sau su co (PHASE 1).
//
// Cai duoc thay the la `on('polling_error', e => console.error(e))` — mot cau
// lenh ghi nhat ky deo nhan xu ly loi. Nen bo kiem nay khong hoi "co ghi nhat ky
// khong"; no hoi "co noi lai duoc khong, va co biet luc nao NEN THOI khong".
//
// Ca dat gia nhat o day la ca cuoi: het luot thu thi phai THOAT. Mot bot tu thu
// lai vo han la mot bot chet ma PM2 khong thay — PM2 chi khoi dong lai thu da
// thoat. Tu chua lanh mai mai la cach chac chan nhat de khong ai tren doi biet
// minh dang om.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ResilientPolling } from '../../scripts/telegram/resilientPolling.js';

function fakeBot(overrides = {}) {
  const calls = { stopPolling: 0, startPolling: 0, getMe: 0, handlers: {} };
  return {
    calls,
    on(event, handler) { calls.handlers[event] = handler; },
    async stopPolling() { calls.stopPolling += 1; },
    async startPolling() {
      calls.startPolling += 1;
      if (overrides.startPollingFails) throw new Error('mang van chua len');
    },
    async getMe() {
      calls.getMe += 1;
      if (overrides.getMeFails) throw new Error('ETIMEDOUT');
      return { username: 'test_bot' };
    },
    ...overrides.bot
  };
}

// Cho vong ket noi lai chay xong. Do tre da bi ep ve 1ms nen vai nhip la du.
async function settle(ms = 60) {
  await new Promise(resolve => setTimeout(resolve, ms));
}

function build(bot, options = {}) {
  const events = [];
  let gaveUp = 0;
  const polling = new ResilientPolling(bot, {
    onEvent: (event) => events.push(event),
    onGiveUp: () => { gaveUp += 1; },
    ...options
  });
  polling.delayFor = () => 1; // khong cho that trong bo kiem
  return { polling, events, gaveUp: () => gaveUp };
}

test('loi poll thong thuong -> dung han roi bat lai', async () => {
  const bot = fakeBot();
  const { polling, events } = build(bot);
  polling.start();

  bot.calls.handlers.polling_error(new Error('ECONNRESET'));
  await settle();
  polling.stop();

  assert.equal(bot.calls.stopPolling, 1, 'phai dung vong poll cu truoc');
  assert.equal(bot.calls.startPolling, 1);
  assert.ok(events.some(e => e.type === 'reconnected'));
});

test('ket noi lai duoc kiem lai bang mot lenh goi that, khong chi goi startPolling', async () => {
  // `startPolling()` tra ve thanh cong ngay ca khi mang van chua len. Neu khong
  // hoi lai API mot cau, ta se bao "da noi lai" trong luc van dang mat ket noi.
  const bot = fakeBot();
  const { polling } = build(bot);
  polling.start();
  bot.calls.handlers.polling_error(new Error('ECONNRESET'));
  await settle();
  polling.stop();

  assert.ok(bot.calls.getMe >= 1, 'phai xac nhan lai bang mot lenh goi that');
});

test('gian doan duoc do va ghi lai', async () => {
  const bot = fakeBot();
  const { polling, events } = build(bot);
  polling.start();
  bot.calls.handlers.polling_error(new Error('ECONNRESET'));
  await settle();
  polling.stop();

  const reconnected = events.find(e => e.type === 'reconnected');
  assert.ok(reconnected, 'phai co su kien reconnected');
  assert.equal(typeof reconnected.downtimeSeconds, 'number');
  assert.equal(reconnected.attempts, 1);
});

test('loi xac thuc 401 -> dung ngay, KHONG lui dan', async () => {
  const bot = fakeBot();
  const { polling, events, gaveUp } = build(bot);
  polling.start();

  const error = new Error('ETELEGRAM: 401 Unauthorized');
  error.response = { statusCode: 401 };
  bot.calls.handlers.polling_error(error);
  await settle();
  polling.stop();

  assert.equal(gaveUp(), 1, 'token sai thi phai giao lai cho nguoi');
  assert.equal(bot.calls.startPolling, 0, 'khong duoc thu lai mot lan nao');
  assert.ok(events.some(e => e.type === 'fatal_error'));
});

test('het luot thu -> THOAT de PM2 khoi dong lai', async () => {
  const bot = fakeBot({ startPollingFails: true });
  const { polling, events, gaveUp } = build(bot, { maxConsecutiveFailures: 3 });
  polling.start();

  bot.calls.handlers.polling_error(new Error('ENOTFOUND'));
  await settle(120);
  polling.stop();

  assert.equal(bot.calls.startPolling, 3, 'phai thu du so lan da khai bao');
  assert.equal(gaveUp(), 1, 'roi thi phai thoat, khong thu lai vo han');
  const gave = events.find(e => e.type === 'gave_up');
  assert.ok(gave);
  assert.equal(gave.attempts, 3);
});

test('nhieu loi poll cung luc -> chi mot vong ket noi lai', async () => {
  // Mot lan mat mang sinh ra hang chuc `polling_error` lien tiep. Neu moi cai mo
  // mot vong rieng, chung se tranh nhau goi startPolling va tu tao ra loi 409.
  const bot = fakeBot();
  const { polling } = build(bot);
  polling.start();

  for (let i = 0; i < 5; i += 1) {
    bot.calls.handlers.polling_error(new Error('ECONNRESET'));
  }
  await settle();
  polling.stop();

  assert.equal(bot.calls.startPolling, 1, 'nam loi chi duoc sinh ra mot lan noi lai');
});

test('nhip tim that bai lien tiep -> ket noi lai du KHONG co loi poll nao', async () => {
  // Day la che do hong ma may ngu day gay ra: vong poll treo im lang, khong su
  // kien nao no ca. Neu chi dua vao polling_error thi khong bao gio phat hien.
  const bot = fakeBot({ getMeFails: true });
  const { polling, events } = build(bot, { heartbeatInterval: 5 });
  polling.start();

  await settle(120);
  polling.stop();

  assert.ok(events.some(e => e.type === 'heartbeat_failed'));
  assert.ok(events.some(e => e.type === 'reconnect_started'),
    'ba nhip tim hong phai kich hoat ket noi lai');
});

test('nhip tim tot khong lam gi ca', async () => {
  const bot = fakeBot();
  const { polling, events } = build(bot, { heartbeatInterval: 5 });
  polling.start();
  await settle(60);
  polling.stop();

  assert.equal(bot.calls.startPolling, 0, 'khong duoc noi lai khi dang khoe');
  assert.ok(!events.some(e => e.type === 'reconnect_started'));
});

test('lui dan tang theo ham mu va co tran', () => {
  const polling = new ResilientPolling(fakeBot());
  const delays = [0, 1, 2, 3, 10].map(n => polling.delayFor(n));

  assert.ok(delays[0] >= 500 && delays[0] <= 1000, `lan dau ~1s, nhan ${delays[0]}`);
  assert.ok(delays[3] > delays[0], 'phai tang dan');
  assert.ok(delays[4] <= 60000, 'phai co tran 60s');
  // Khong co ngau nhien thi moi may cung mat mang se cung goi lai dung mot luc.
  const sample = new Set(Array.from({ length: 20 }, () => polling.delayFor(3)));
  assert.ok(sample.size > 1, 'phai co jitter');
});

test('dung co y khong bi hieu nham la su co', async () => {
  const bot = fakeBot({ getMeFails: true });
  const { polling, events } = build(bot, { heartbeatInterval: 5 });
  polling.start();
  polling.stop();
  await settle(60);

  assert.ok(!events.some(e => e.type === 'reconnect_started'),
    'sau khi stop() thi khong duoc tu mo lai ket noi');
});
