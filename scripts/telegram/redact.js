// Che thong tin ca nhan truoc khi roi khoi may.
//
// Nguyen tac: che DANH TINH, giu CAU TRUC.
//
// `C:\Users\tamng\Downloads\invoice.exe` -> `C:\Users\<USER>\Downloads\invoice.exe`
// chu khong phai `[PATH]`. Thu muc Downloads la mot phan cua ket luan phap chung:
// mot nhi phan chay tu Downloads khac han mot nhi phan chay tu System32. Che ca
// duong dan la xoa mat cau tra loi de giau mot cai ten.
//
// Vi cung ly do, IP KHONG bi che. `/hunt` va `/ioc` ton tai de tra loi "may nao
// noi chuyen voi may nao"; thay moi IP bang `[IP]` bien chung thanh tin nhan
// rong. IP noi bo khong phai bi mat ca nhan — ten nguoi dung, email, mat khau
// va token thi phai.

import os from 'os';

// Ten dang nhap that cua may nay. Doc mot lan luc nap module.
//
// Day la thu manh nhat trong tep: khi biet ten that la `tamng`, ta che duoc ca
// nhung cho no xuat hien TRAN TRUI — `Account Name: tamng`, `tamng@outlook.com`,
// `Welcome tamng` — chu khong chi trong duong dan. Cac regex ben duoi bat duoc
// hinh dang; cai nay bat duoc chinh cai ten.
function localIdentities() {
  const names = new Set();
  for (const raw of [process.env.USERNAME, process.env.USER, os.userInfo?.().username]) {
    const name = (raw || '').trim();
    // Ten qua ngan sinh ra thay the bua bai giua cac tu khac.
    if (name.length >= 3) names.add(name.toLowerCase());
  }
  return [...names];
}

const IDENTITIES = localIdentities();

// Ky tu dac biet trong ten dang nhap (vd. dau cham) phai duoc thoat truoc khi
// ghep vao regex, neu khong `.` se khop moi ky tu.
function escapeRegex(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

const RULES = [
  // Duong dan ho so nguoi dung — giu lai phan duoi, chi thay ten.
  {
    name: 'windows_user_path',
    pattern: /([A-Za-z]:\\Users\\)([^\\\/\s"'<>|]+)/gi,
    replace: (_m, prefix) => `${prefix}<USER>`
  },
  {
    name: 'unix_home_path',
    pattern: /(\/(?:home|Users)\/)([^\/\s"'<>|]+)/g,
    replace: (_m, prefix) => `${prefix}<USER>`
  },
  // Mat khau / token / khoa API: che GIA TRI, giu TEN TRUONG, de nguoi doc biet
  // o day co mot bi mat bi lo chu khong phai mot dong bien mat.
  {
    name: 'secret_assignment',
    pattern: /\b(pass(?:word|wd)?|pwd|secret|token|api[_-]?key|apikey|client[_-]?secret|bearer)\b(\s*[=:]\s*|\s+)("[^"]*"|'[^']*'|[^\s,;"')]+)/gi,
    replace: (_m, key, sep) => `${key}${sep}<REDACTED>`
  },
  {
    name: 'email',
    pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
    replace: () => '<EMAIL>'
  },
  // Chuoi base64 cua PowerShell -enc giu lai DO DAI: do dai la tin hieu san tim,
  // noi dung la thu co the chua thong tin dang nhap.
  {
    name: 'powershell_encoded',
    // `\b` truoc dau `-` KHONG BAO GIO khop: dau cach va dau `-` deu la ky tu
    // khong phai tu, nen khong co ranh gioi tu o giua. Dung `(?:^|\s)`.
    //
    // Va thu tu nhanh phai dai truoc ngan: regex chon nhanh dau tien khop duoc,
    // nen `-e` dat truoc se nuot mat `-enc` va `-encodedcommand`.
    pattern: /(^|\s)(-encodedcommand|-enc|-en|-e)\s+([A-Za-z0-9+/=]{40,})/gi,
    replace: (_m, lead, flag, blob) => `${lead}${flag} <ENCODED:${blob.length}chars>`
  },
  // Tai khoan Windows trong nhat ky su kien.
  {
    name: 'event_account_name',
    pattern: /(Account Name:\s*)([^\r\n\t]+)/g,
    replace: (_m, label, value) => {
      const name = value.trim();
      // Tai khoan may (`KEVIN$`) va tai khoan he thong khong phai danh tinh ca
      // nhan, va chung la manh moi phan biet dang nhap nen voi dang nhap nguoi
      // dung — giu nguyen.
      if (/\$$/.test(name) || /^(SYSTEM|LOCAL SERVICE|NETWORK SERVICE|ANONYMOUS LOGON|-)$/i.test(name)) {
        return _m;
      }
      return `${label}<USER>`;
    }
  }
];

// Ten dang nhap that, dung mot minh, ngoai moi ngu canh tren.
const IDENTITY_RULES = IDENTITIES.map(name => ({
  name: `local_identity:${name}`,
  pattern: new RegExp(`(?<![A-Za-z0-9_-])${escapeRegex(name)}(?![A-Za-z0-9_-])`, 'gi'),
  replace: () => '<USER>'
}));

/**
 * Che thong tin ca nhan trong mot chuoi.
 * @param {string} text
 * @returns {string}
 */
export function redact(text) {
  if (typeof text !== 'string' || !text) return text;
  let output = text;
  for (const rule of RULES) {
    output = output.replace(rule.pattern, rule.replace);
  }
  // Chay sau cung: luc nay duong dan da thanh `<USER>`, nen quy tac nay chi con
  // gap ten tran trui thuc su.
  for (const rule of IDENTITY_RULES) {
    output = output.replace(rule.pattern, rule.replace);
  }
  return output;
}

/**
 * Che de quy trong object/array. Dung cho du lieu co cau truc truoc khi dung chuoi.
 */
export function redactDeep(value) {
  if (typeof value === 'string') return redact(value);
  if (Array.isArray(value)) return value.map(redactDeep);
  if (value && typeof value === 'object') {
    const out = {};
    for (const [key, val] of Object.entries(value)) out[key] = redactDeep(val);
    return out;
  }
  return value;
}

/**
 * Boc `sendMessage` / `editMessageText` cua mot instance TelegramBot.
 *
 * Boc o tang van chuyen, khong sua tung handler. 25 cho goi sendMessage hom nay
 * va cho thu 26 duoc them vao thang sau deu di qua day. Mot bo loc phai duoc
 * NHO thi khong phai bo loc — no la mot loi cho san.
 *
 * @param {object} bot instance node-telegram-bot-api
 * @returns {object} chinh bot do, da duoc boc
 */
export function installRedaction(bot) {
  if (bot.__redactionInstalled) return bot;

  const originalSend = bot.sendMessage.bind(bot);
  bot.sendMessage = (chatId, text, options) => originalSend(chatId, redact(text), options);

  const originalEdit = bot.editMessageText.bind(bot);
  bot.editMessageText = (text, options) => originalEdit(redact(text), options);

  bot.__redactionInstalled = true;
  return bot;
}
