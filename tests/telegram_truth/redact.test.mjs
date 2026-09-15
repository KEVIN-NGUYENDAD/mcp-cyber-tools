// Che danh tinh truoc khi tin nhan roi khoi may (PHASE 1).
//
// Bo kiem nay hoi hai cau, va cau thu hai quan trong ngang cau thu nhat:
//
//   1. Thu can che co bi che khong?
//   2. Thu KHONG duoc che co con nguyen khong?
//
// Cau thu hai ton tai vi che qua tay va ro ri deu lam hong cung mot thu. Mot
// canh bao lateral movement da thay het IP bang `[IP]` thi khong con tra loi
// duoc cau hoi no sinh ra de tra loi — no an toan, va vo dung. Duong dan cung
// vay: `C:\Users\<USER>\Downloads\hoadon.exe` van noi duoc dieu can noi, con
// `[PATH]` thi khong.

import { test } from 'node:test';
import assert from 'node:assert/strict';

// Bat buoc dat TRUOC khi nap module: `redact.js` doc ten dang nhap mot lan luc
// nap. Dung `import` tinh o day se nap module truoc khi dong nay chay.
process.env.USERNAME = 'tamng';
const { redact, redactDeep, installRedaction } = await import('../../scripts/telegram/redact.js');

test('duong dan ho so nguoi dung: che ten, giu cau truc', () => {
  assert.equal(
    redact(String.raw`C:\Users\tamng\Downloads\hoadon.exe`),
    String.raw`C:\Users\<USER>\Downloads\hoadon.exe`
  );
  assert.equal(
    redact(String.raw`"C:\Users\tamng\AppData\Local\Programs\Zalo\Zalo.exe"`),
    String.raw`"C:\Users\<USER>\AppData\Local\Programs\Zalo\Zalo.exe"`
  );
  assert.equal(redact('/home/tamng/.ssh/id_rsa'), '/home/<USER>/.ssh/id_rsa');
});

test('thu muc sau ten nguoi dung duoc giu lai - do la phan mang y nghia', () => {
  const output = redact(String.raw`C:\Users\tamng\AppData\Local\Temp\a.exe`);
  assert.ok(output.includes('Temp'), 'Temp phai con lai de doc duoc ket luan');
  assert.ok(output.includes('AppData'));
  assert.ok(!output.includes('tamng'));
});

test('duong dan he thong khong chua danh tinh thi khong bi dung toi', () => {
  const path = String.raw`C:\Windows\System32\cmd.exe`;
  assert.equal(redact(path), path);
});

test('email bi che', () => {
  assert.equal(redact('lien he admin@congty.vn ngay'), 'lien he <EMAIL> ngay');
});

test('bi mat: che GIA TRI, giu TEN TRUONG', () => {
  // Giu ten truong de nguoi doc biet o day CO mot bi mat bi lo - mot dong bien
  // mat hoan toan thi khong ai dieu tra duoc nua.
  assert.equal(redact('password=SieuMatKhau123!'), 'password=<REDACTED>');
  assert.equal(redact('api_key: abcdef1234567890'), 'api_key: <REDACTED>');
  assert.equal(redact('token = "Bearer xyz"'), 'token = <REDACTED>');
  assert.equal(redact('pwd:hunter2'), 'pwd:<REDACTED>');
});

test('lenh PowerShell ma hoa: giu DO DAI, bo noi dung', () => {
  const blob = 'S'.repeat(64);
  const output = redact(`powershell.exe -enc ${blob}`);
  assert.ok(!output.includes(blob), 'noi dung base64 phai bi bo');
  assert.ok(output.includes('<ENCODED:64chars>'), 'do dai la tin hieu san tim, phai giu');
});

test('dia chi IP KHONG bi che - do la quyet dinh co y', () => {
  const text = 'Ket noi toi 192.168.1.50 tu 10.0.0.7';
  assert.equal(redact(text), text);
});

test('Account Name: tai khoan nguoi dung bi che, tai khoan may thi khong', () => {
  assert.equal(redact('Account Name:\t\ttamng'), 'Account Name:\t\t<USER>');
  // `KEVIN$` la tai khoan may - no la manh moi phan biet dang nhap nen voi dang
  // nhap nguoi dung, va no khong phai danh tinh ca nhan.
  assert.equal(redact('Account Name:\t\tKEVIN$'), 'Account Name:\t\tKEVIN$');
  assert.equal(redact('Account Name:\t\tSYSTEM'), 'Account Name:\t\tSYSTEM');
});

test('ten dang nhap that bi che ca khi dung tran trui', () => {
  assert.equal(redact('Welcome back tamng'), 'Welcome back <USER>');
  // Khong duoc che nham khi ten nam trong mot tu dai hon.
  assert.equal(redact('tamnghiep la mot tu khac'), 'tamnghiep la mot tu khac');
});

test('redactDeep di vao object va mang long nhau', () => {
  const input = {
    incident: 'INC-1',
    assets: [String.raw`C:\Users\tamng\a.exe`],
    nested: { mail: 'a@b.vn', port: 443 }
  };
  const output = redactDeep(input);
  assert.equal(output.assets[0], String.raw`C:\Users\<USER>\a.exe`);
  assert.equal(output.nested.mail, '<EMAIL>');
  assert.equal(output.nested.port, 443, 'so khong bi dung toi');
  assert.equal(input.assets[0], String.raw`C:\Users\tamng\a.exe`, 'ban goc khong bi sua');
});

test('installRedaction chan o tang van chuyen, khong o tung handler', () => {
  const sent = [];
  const edited = [];
  const fakeBot = {
    sendMessage(chatId, text, options) { sent.push({ chatId, text, options }); return 'ok'; },
    editMessageText(text, options) { edited.push({ text, options }); return 'ok'; }
  };

  installRedaction(fakeBot);
  fakeBot.sendMessage(1, String.raw`Asset: C:\Users\tamng\secret.txt`, { parse_mode: 'Markdown' });
  fakeBot.editMessageText('lien he tamng@congty.vn', { chat_id: 1 });

  assert.equal(sent[0].text, String.raw`Asset: C:\Users\<USER>\secret.txt`);
  assert.equal(sent[0].options.parse_mode, 'Markdown', 'tuy chon di qua nguyen ven');
  assert.equal(edited[0].text, 'lien he <EMAIL>');
});

test('boc hai lan khong che hai lan', () => {
  const sent = [];
  const fakeBot = {
    sendMessage(chatId, text) { sent.push(text); },
    editMessageText(text) { sent.push(text); }
  };
  installRedaction(fakeBot);
  installRedaction(fakeBot);
  fakeBot.sendMessage(1, 'password=abc');
  assert.equal(sent[0], 'password=<REDACTED>');
  assert.equal(sent.length, 1);
});

test('dau vao khong phai chuoi di qua nguyen ven', () => {
  assert.equal(redact(null), null);
  assert.equal(redact(undefined), undefined);
  assert.equal(redact(''), '');
});
