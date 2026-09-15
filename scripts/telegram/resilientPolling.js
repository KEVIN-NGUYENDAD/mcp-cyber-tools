// Ket noi lai sau khi mat mang hoac may thuc day.
//
// Hong that da do duoc: `bot.on('polling_error', e => console.error(e))`. Do la
// mot cai ghi nhat ky deo nhan xu ly loi. Bot im lang, PM2 thay tien trinh con
// song nen khong khoi dong lai, va nguoi truc khong biet gi — cho den khi ho hoi
// "sao toi khong nhan canh bao nao" vai tieng sau.
//
// Hai che do hong KHAC NHAU, can hai co che khac nhau:
//
//   1. Poll bao loi  -> `polling_error` no. Bat duoc, lui dan roi noi lai.
//   2. Poll treo im  -> KHONG co su kien nao no ca. May ngu day, socket chet
//                       nhung chua dong; vong poll ngoi doi mot phan hoi khong
//                       bao gio toi. Che do nay la thu che (1) khong thay, va
//                       la che do ma "may sleep" thuc su gay ra.
//
// Nen o day co ca nhip tim chu dong, khong chi trinh bat loi.

const SECOND = 1000;

// Lui dan: 1s, 2s, 4s ... tran 60s. Don vi la GIAY, khong phai mili-giay: mot
// giao dien mang vua sap khong hoi phuc trong 4ms, va lui dan mili-giay chi tao
// ra mot vong lap ban thay vi mot lan cho.
const BASE_DELAY = 1 * SECOND;
const MAX_DELAY = 60 * SECOND;

// Sau nguong nay thi ngung tu sua va thoat, de PM2 dung lai ca tien trinh.
// Tu thu lai vo han la cach mot bot chet tu giau minh khoi trinh giam sat:
// PM2 chi khoi dong lai thu da THOAT. Mot tien trinh song mai ma khong lam gi
// la truong hop PM2 khong cuu duoc.
const MAX_CONSECUTIVE_FAILURES = 10;

const HEARTBEAT_INTERVAL = 60 * SECOND;
const HEARTBEAT_TIMEOUT = 15 * SECOND;
const MAX_HEARTBEAT_FAILURES = 3;

// Loi khong the tu sua bang cach thu lai. Token sai thi thu lai mot nghin lan
// van sai; lap vong o day chi lam mo mat nguyen nhan that.
const FATAL_CODES = [401, 403];

function isFatal(error) {
  const status = error?.response?.statusCode ?? error?.code;
  if (FATAL_CODES.includes(status)) return true;
  return /401|403|unauthorized|forbidden/i.test(error?.message || '');
}

// 409 Conflict = mot instance khac dang poll cung token. Thu lai duoc (instance
// kia co the dang tat), nhung phai noi ro vi day thuong la loi trien khai:
// hai ban sao cung chay.
function isConflict(error) {
  const status = error?.response?.statusCode ?? error?.code;
  return status === 409 || /409|conflict|terminated by other/i.test(error?.message || '');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function withTimeout(promise, ms, label) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`${label} timeout sau ${ms}ms`)), ms);
    promise.then(
      value => { clearTimeout(timer); resolve(value); },
      error => { clearTimeout(timer); reject(error); }
    );
  });
}

export class ResilientPolling {
  /**
   * @param {object} bot instance node-telegram-bot-api
   * @param {object} [options]
   * @param {(event: object) => void} [options.onEvent] nhan su kien de ghi nhat ky / bao dong
   * @param {() => void} [options.onGiveUp] goi khi het luot thu (mac dinh: process.exit(1))
   */
  constructor(bot, options = {}) {
    this.bot = bot;
    this.onEvent = options.onEvent || (() => {});
    this.onGiveUp = options.onGiveUp || (() => process.exit(1));
    this.maxFailures = options.maxConsecutiveFailures ?? MAX_CONSECUTIVE_FAILURES;
    this.heartbeatInterval = options.heartbeatInterval ?? HEARTBEAT_INTERVAL;

    this.consecutiveFailures = 0;
    this.heartbeatFailures = 0;
    this.reconnecting = false;
    this.downSince = null;
    this.heartbeatTimer = null;
    this.stopped = false;
  }

  emit(type, detail) {
    this.onEvent({ type, at: new Date().toISOString(), ...detail });
  }

  // Lui dan co nhieu ngau nhien. Khong co jitter thi nhieu tien trinh cung mat
  // mang se cung thuc day dung mot thoi diem va dap vao API cung mot luc.
  delayFor(attempt) {
    const exponential = Math.min(BASE_DELAY * 2 ** attempt, MAX_DELAY);
    return Math.round(exponential * (0.5 + Math.random() * 0.5));
  }

  start() {
    this.bot.on('polling_error', (error) => this.handlePollingError(error));
    this.startHeartbeat();
    this.emit('watchdog_started', {
      heartbeatSeconds: this.heartbeatInterval / SECOND,
      maxFailures: this.maxFailures
    });
  }

  stop() {
    this.stopped = true;
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
  }

  handlePollingError(error) {
    const message = error?.message || String(error);

    if (isFatal(error)) {
      // Khong lui dan, khong thu lai. Mot token bi thu hoi can nguoi sua.
      this.emit('fatal_error', { message });
      console.error('[FATAL] Telegram tu choi xac thuc, khong the tu sua:', message);
      this.onGiveUp();
      return;
    }

    if (isConflict(error)) {
      this.emit('conflict', { message });
      console.error('[CONFLICT] Mot instance khac dang poll cung token:', message);
    }

    this.emit('polling_error', { message });
    this.reconnect(`polling_error: ${message}`);
  }

  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => this.checkAlive(), this.heartbeatInterval);
    // Khong giu tien trinh song chi vi cai hen gio nay.
    this.heartbeatTimer.unref?.();
  }

  // Nhip tim: che do hong (2). `getMe()` la lenh goi re nhat co phan hoi, va
  // quan trong hon — no CO thoi han. Vong poll treo khong co thoi han nao ca,
  // nen no im lang mai mai; lenh goi nay thi khong.
  async checkAlive() {
    if (this.reconnecting || this.stopped) return;

    try {
      await withTimeout(this.bot.getMe(), HEARTBEAT_TIMEOUT, 'getMe');
      if (this.heartbeatFailures > 0) {
        this.emit('heartbeat_recovered', { afterFailures: this.heartbeatFailures });
      }
      this.heartbeatFailures = 0;
    } catch (error) {
      this.heartbeatFailures += 1;
      this.emit('heartbeat_failed', {
        message: error?.message,
        consecutive: this.heartbeatFailures
      });
      console.error(`[HEARTBEAT] That bai ${this.heartbeatFailures}/${MAX_HEARTBEAT_FAILURES}:`,
        error?.message);

      if (this.heartbeatFailures >= MAX_HEARTBEAT_FAILURES) {
        this.heartbeatFailures = 0;
        this.reconnect('nhip tim that bai lien tiep — vong poll co the da treo');
      }
    }
  }

  async reconnect(reason) {
    // Mot lan mat mang sinh ra nhieu `polling_error` lien tiep. Neu moi cai deu
    // mo mot vong ket noi lai rieng, chung se chong len nhau va tranh nhau
    // startPolling. Chi mot vong duoc chay.
    if (this.reconnecting || this.stopped) return;
    this.reconnecting = true;
    if (!this.downSince) this.downSince = Date.now();

    this.emit('reconnect_started', { reason });
    console.error('[RECONNECT] Bat dau ket noi lai. Ly do:', reason);

    for (let attempt = 0; attempt < this.maxFailures; attempt += 1) {
      const delay = this.delayFor(attempt);
      console.error(`[RECONNECT] Lan thu ${attempt + 1}/${this.maxFailures}, cho ${Math.round(delay / SECOND)}s`);
      await sleep(delay);
      if (this.stopped) return;

      try {
        // Dung han roi bat lai. `startPolling` khong tu don dep vong cu, va hai
        // vong poll chong nhau tao ra chinh loi 409 ma ta dang chay khoi.
        await this.bot.stopPolling().catch(() => {});
        await this.bot.startPolling();
        await withTimeout(this.bot.getMe(), HEARTBEAT_TIMEOUT, 'getMe sau khi noi lai');

        const downtimeSeconds = Math.round((Date.now() - this.downSince) / SECOND);
        this.consecutiveFailures = 0;
        this.reconnecting = false;
        this.downSince = null;
        this.emit('reconnected', { attempts: attempt + 1, downtimeSeconds });
        console.log(`[RECONNECT] Da noi lai sau ${attempt + 1} lan thu, gian doan ${downtimeSeconds}s`);
        return;
      } catch (error) {
        this.consecutiveFailures = attempt + 1;
        this.emit('reconnect_failed', { attempt: attempt + 1, message: error?.message });
        console.error(`[RECONNECT] Lan thu ${attempt + 1} that bai:`, error?.message);
      }
    }

    // Het luot. Thoat de PM2 dung lai tu dau — mot tien trinh moi lay lai duoc
    // socket, DNS va bang dinh tuyen, nhung thu ma vong lap nay khong lam duoc.
    const downtimeSeconds = Math.round((Date.now() - this.downSince) / SECOND);
    this.reconnecting = false;
    this.emit('gave_up', { attempts: this.maxFailures, downtimeSeconds });
    console.error(`[FATAL] Khong ket noi lai duoc sau ${this.maxFailures} lan thu ` +
      `(${downtimeSeconds}s gian doan). Thoat de PM2 khoi dong lai.`);
    this.onGiveUp();
  }
}

export default ResilientPolling;
