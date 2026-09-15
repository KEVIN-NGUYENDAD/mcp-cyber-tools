# -*- coding: utf-8 -*-
"""
Khoa bon ban va CRITICAL cua AUDIT_SECURITY_AND_DATA.md.

Bon lo nay khong phai bon loi roi rac. Chung la mot lop loi: MOT GIA TRI DO
NGUOI DUNG DUA VAO DUOC NOI VAO MOT CHUOI ROI CHUOI DO DUOC DEM DI PHAN TICH
CU PHAP — boi cmd.exe (INJ-01), boi PowerShell (INJ-02), boi git/HTTP (EXP-02),
hoac boi chinh vong doi tien trinh (FAIL-SAFE).

Nen bo kiem nay khong hoi "ma nguon co dep khong". No TIEM dung mot payload vao
tung cho va hoi payload do co duoc THUC THI khong. Mot ca kiem chi doc ma nguon
se van xanh vao ngay ai do viet lai bang cu phap khac.

Hai ca dau chay Node that (spawn `node`), nen chung cham. Do la gia phai tra de
ket qua noi ve HANH VI chu khong ve van ban.
"""

from __future__ import print_function

import io
import json
import os
import re
import socket
import subprocess
import sys
import time

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TESTS_DIR))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tests', 'detection_quality'))

from harness import Suite  # noqa: E402

MARKER = 'CHEN-LENH-DA-CHAY'


def _node(script, env_extra=None):
    """Chay mot doan ES module trong goc du an, tra ve (stdout, stderr, ma)."""
    path = os.path.join(PROJECT_ROOT, '_probe_%d.mjs' % os.getpid())
    with io.open(path, 'w', encoding='utf-8') as fh:
        fh.write(script)
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.Popen([_node_exe(), path], cwd=PROJECT_ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(timeout=120)
        return (out.decode('utf-8', 'replace'),
                err.decode('utf-8', 'replace'), proc.returncode)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _node_exe():
    return 'node.exe' if sys.platform == 'win32' else 'node'


def _read(*parts):
    with io.open(os.path.join(PROJECT_ROOT, *parts), encoding='utf-8') as fh:
        return fh.read()


def _free_port():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


# ---------------------------------------------------------------------------
# INJ-01 — cmd.exe khong con nhin thay tham so
# ---------------------------------------------------------------------------

def check_inj01(suite):
    # `& whoami` la mot TOAN TU cua cmd.exe. Voi `execSync` no chay; voi
    # `execFileSync` no chi la mot phan cua ten may.
    out, _err, _code = _node(u'''
import { runCmdArgs, hostSchema } from "./modules/shared.js";
const evil = "127.0.0.1 & echo %s";
const parsed = hostSchema.safeParse(evil);
const r = runCmdArgs("cmd", ["/c", "echo", evil]);
console.log(JSON.stringify({
  zodRejected: !parsed.success,
  output: (r.data || r.error || "")
}));
''' % MARKER)
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        suite.check('INJ-01: doc duoc ket qua tu Node', False, out[:200])
        return

    suite.check('INJ-01: hostSchema tu choi host chua toan tu shell',
                res['zodRejected'])
    # Phep kiem that: `echo <marker>` KHONG duoc chay nhu mot lenh rieng. Neu
    # no chay, dau ra co dong chi chua marker, khong con "127.0.0.1 &".
    ran_as_command = any(line.strip() == MARKER
                         for line in res['output'].splitlines())
    suite.check('INJ-01: execFile khong tach `&` thanh lenh thu hai',
                not ran_as_command, res['output'][:160])
    suite.check('INJ-01: ... payload di qua nguyen van nhu DU LIEU',
                MARKER in res['output'] and '&' in res['output'],
                res['output'][:160])

    # Va khong con cho nao trong network.js dung dong lenh noi chuoi cho ba
    # tool nay nua. Day la ca DOC MA — no khong thay the ca hanh vi o tren, no
    # chan duong quay lai bang mot lan sua khac.
    net = _read('modules', 'network.js')
    for tool, pattern in (('ping', r'runCmd\(`ping'),
                          ('tracert', r'runCmd\(`tracert'),
                          ('nslookup', r'runCmd\(`nslookup')):
        suite.check('INJ-01: %s khong con dung runCmd noi chuoi' % tool,
                    re.search(pattern, net) is None)
    suite.check('INJ-01: ba tool deu dung runCmdArgs',
                net.count('runCmdArgs(') >= 3, str(net.count('runCmdArgs(')))


# ---------------------------------------------------------------------------
# INJ-02 — PowerShell khong dien dich lai gia tri tham so
# ---------------------------------------------------------------------------

def check_inj02(suite):
    # `$(...)` bung NGAY BEN TRONG nhay kep, nen ca tan cong nay khong can
    # thoat dau nhay. Day la ly do "da dung -EncodedCommand" khong phai mot
    # cau tra loi: base64 bao ve DONG LENH, khong bao ve THAN SCRIPT.
    out, _err, _code = _node(u'''
import { runPowerShell } from "./modules/shared.js";
const evil = "$(Write-Output %s)";
const viaParam = runPowerShell(`Write-Output "duong dan: $targetPath"`, { targetPath: evil });
const real    = runPowerShell(`Get-FileHash -LiteralPath $targetPath -Algorithm SHA256 | ConvertTo-Json`,
                              { targetPath: "package.json" });
console.log(JSON.stringify({
  param: (viaParam.data || viaParam.error || "").trim(),
  hash:  (real.data || real.error || "").replace(/\\s+/g, " ")
}));
''' % MARKER)
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        suite.check('INJ-02: doc duoc ket qua tu Node', False, out[:200])
        return

    # Neu PowerShell da thuc thi `$(...)`, dau ra la "duong dan: <marker>".
    # Neu khong, dau ra giu nguyen ca dau `$(` — day la khac biet quyet dinh.
    suite.check('INJ-02: $(...) KHONG duoc thuc thi',
                '$(Write-Output' in res['param'], res['param'][:160])
    suite.check('INJ-02: ... gia tri di qua nhu chuoi tho',
                res['param'].endswith(')') and MARKER in res['param'],
                res['param'][:160])
    # Doi chung: bit duong tan cong ma lam hong tinh nang thi khong phai ban va.
    suite.check('INJ-02: duong dan that van bam duoc (khong ha tinh nang)',
                re.search(r'"Hash"\s*:\s*"[0-9A-F]{64}"', res['hash']) is not None,
                res['hash'][:120])

    # Khong con `"${path}"` trong bat ky script PowerShell nao cua forensics.
    forensics = _read('modules', 'forensics.js')
    suite.check('INJ-02: forensics.js khong con noi `${path}` vao nhay kep',
                '"${path}"' not in forensics)
    net = _read('modules', 'network.js')
    suite.check('INJ-02: network.js khong con noi `${host}` vao script PowerShell',
                '-ComputerName ${host}' not in net)


# ---------------------------------------------------------------------------
# EXP-02 — trang thai khong nam trong git, va /api doi khoa
# ---------------------------------------------------------------------------

def check_exp02(suite):
    tracked = subprocess.check_output(
        ['git', 'ls-files', 'state/'], cwd=PROJECT_ROOT).decode('utf-8').split()
    leaked = [f for f in tracked if f.endswith('.json') or f.endswith('.prev')]
    suite.check('EXP-02: khong con state/*.json nao duoc git theo doi',
                leaked == [], str(leaked[:5]))

    ignore = _read('.gitignore')
    suite.check('EXP-02: .gitignore chan state/*.json',
                'state/*.json' in ignore and 'state/**/*.json' in ignore)

    # Ban than .gitignore chua du: mot tep DA theo doi van bi theo doi tiep du
    # co dong ignore. Nen hoi git, khong hoi tep cau hinh — o tren da hoi roi.
    # O day hoi them: tep VAN CON tren dia (go khoi index, khong phai xoa du lieu).
    on_disk = [f for f in os.listdir(os.path.join(PROJECT_ROOT, 'state'))
               if f.endswith('.json')]
    suite.check('EXP-02: ... nhung tep van con tren dia (go index, khong xoa)',
                len(on_disk) > 0, '%d tep' % len(on_disk))

    # Va hanh vi HTTP that.
    port = _free_port()
    env = dict(os.environ)
    env['PORT'] = str(port)
    env['API_KEY'] = 'kiem-tra-khoa-0123456789'
    proc = subprocess.Popen([_node_exe(), os.path.join('web', 'server.js')],
                            cwd=PROJECT_ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        codes = _probe_server(port, env['API_KEY'])
    finally:
        proc.kill()
        proc.communicate()

    if codes is None:
        suite.check('EXP-02: server web khoi dong duoc de kiem', False)
        return
    suite.check('EXP-02: /api khong khoa -> 401', codes['no_key'] == 401,
                str(codes))
    suite.check('EXP-02: /api sai khoa -> 401', codes['bad_key'] == 401,
                str(codes))
    suite.check('EXP-02: /api dung khoa -> 200', codes['good_key'] == 200,
                str(codes))
    suite.check('EXP-02: /api/health van cong khai (health check Render)',
                codes['health'] == 200, str(codes))


def _probe_server(port, key):
    try:
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
    except ImportError:                                    # pragma: no cover
        from urllib2 import Request, urlopen, HTTPError    # noqa: F401

    def get(path, headers=None):
        req = Request('http://127.0.0.1:%d%s' % (port, path),
                      headers=headers or {})
        try:
            return urlopen(req, timeout=5).getcode()
        except HTTPError as err:
            return err.code

    for _ in range(40):                       # doi toi 8 giay cho server len
        try:
            get('/api/health')
            break
        except Exception:                     # noqa: BLE001
            time.sleep(0.2)
    else:
        return None

    try:
        return {
            'no_key': get('/api/assets'),
            'bad_key': get('/api/assets', {'x-api-key': 'sai'}),
            'good_key': get('/api/assets', {'x-api-key': key}),
            'health': get('/api/health'),
        }
    except Exception:                         # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# FAIL-SAFE — mot promise lac khong duoc giet 90 tool
# ---------------------------------------------------------------------------

def check_failsafe(suite):
    src = _read('server.js')
    # Cat o `\n});` chu khong o `});`: dau `});` dau tien nam trong chinh loi
    # goi `console.error({...})`, nen cat o do se doc hut than handler.
    block = src.split("process.on('unhandledRejection'")[-1].split('\n});')[0]
    suite.check('FAIL-SAFE: handler unhandledRejection khong con process.exit',
                'process.exit' not in block, block[-200:])
    suite.check('FAIL-SAFE: ... nhung van ghi log co nhan dem duoc',
                'UNHANDLED-REJECTION-SURVIVED' in src)

    # `uncaughtException` PHAI van thoat. Hai thu nay khac nhau: sau mot ngoai
    # le khong bat, trang thai tien trinh that su khong con dam bao. Go nham
    # ca hai la mot loi nguoc chieu, nen no cung phai bi chan.
    uncaught = src.split("process.on('uncaughtException'")[-1].split('\n});')[0]
    suite.check('FAIL-SAFE: uncaughtException VAN thoat (co y, khong gop chung)',
                'process.exit(1)' in uncaught)

    # Hanh vi that: hai rejection lien tiep, tien trinh phai song qua ca hai.
    out, _err, code = _node(u'''
let n = 0;
process.on("unhandledRejection", () => { n += 1; });
Promise.reject(new Error("tool A hong"));
Promise.reject(new Error("tool B hong"));
setTimeout(() => { console.log(JSON.stringify({ survived: true, n })); }, 200);
''')
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        suite.check('FAIL-SAFE: tien trinh song qua rejection', False, out[:200])
        return
    suite.check('FAIL-SAFE: tien trinh song qua 2 rejection, thoat 0',
                res['survived'] and res['n'] == 2 and code == 0,
                'n=%s code=%s' % (res['n'], code))


# ---------------------------------------------------------------------------
# SEC-01/02 — khong con chuoi bi mat trong tep duoc theo doi
# ---------------------------------------------------------------------------

def check_secrets(suite):
    # Hinh dang token Telegram: <bot id so>:<35 ky tu base64url>. Quet theo
    # HINH DANG, khong theo gia tri: mot token MOI bi dan vao ngay mai cung
    # phai bi bat, chu khong chi hai chuoi lan nay.
    pattern = re.compile(r'\b\d{8,12}:[A-Za-z0-9_-]{30,}\b')
    tracked = subprocess.check_output(
        ['git', 'ls-files'], cwd=PROJECT_ROOT).decode('utf-8').splitlines()

    hits = []
    for rel in tracked:
        if not rel or os.path.splitext(rel)[1].lower() not in (
                '.md', '.py', '.js', '.json', '.yaml', '.yml', '.txt', '.ps1'):
            continue
        full = os.path.join(PROJECT_ROOT, rel)
        if not os.path.isfile(full):
            continue
        try:
            with io.open(full, encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
        except IOError:
            continue
        for match in pattern.findall(text):
            hits.append('%s: %s...' % (rel, match[:14]))

    suite.check('SEC-01: khong tep duoc theo doi nao chua token hinh dang Telegram',
                hits == [], str(hits[:4]))
    suite.check('SEC-02: .env khong nam trong git',
                '.env' not in tracked)


EXP01_PROBE = u'''
import { registerForensicsTools } from "./modules/forensics.js";
const tools = {};
registerForensicsTools({ tool: (n, d, s, h) => { tools[n] = h; } });
const out = {};
const run = async (key, p) => {
  const r = await tools.readLogFile({ path: p, lines: 200 });
  out[key] = r.content[0].text;
};
await run("dotenv_rel", "..\\\\.env");
await run("dotenv_slash", "../.env");
await run("dotenv_abs", process.cwd() + "\\\\.env");
await run("outside_abs", "C:\\\\Windows\\\\win.ini");
await run("sibling", "..\\\\logs-backup\\\\x.log");
await run("empty", "");
await run("control", "pipeline.log");
console.log(JSON.stringify(out));
'''


def check_exp01(suite):
    """EXP-01: readLogFile phai bi nhot trong logs/.

    Day la lo dong bo voi SEC-01: chung nao tool con doc duoc duong dan bat ky,
    viec go token khoi cac tep khong co nghia gi — client MCP van hoi duoc `.env`.
    Nen ca kiem quyet dinh la GOI THAT tool va doi chieu voi noi dung `.env`
    tren dia, chu khong doc ma nguon.
    """
    out, err, _ = _node(EXP01_PROBE)
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        suite.check('EXP-01: probe readLogFile chay duoc', False, (err or out)[:200])
        return

    env_path = os.path.join(PROJECT_ROOT, '.env')
    secret = ''
    if os.path.isfile(env_path):
        with io.open(env_path, encoding='utf-8', errors='ignore') as fh:
            secret = fh.read().strip()

    for key, label in (('dotenv_rel', "'..\\.env'"),
                       ('dotenv_slash', "'../.env'"),
                       ('dotenv_abs', 'duong dan tuyet doi toi .env'),
                       ('outside_abs', 'C:\\Windows\\win.ini'),
                       ('sibling', 'thu muc anh em logs-backup')):
        text = res.get(key, '')
        suite.check('EXP-01: tu choi %s' % label,
                    text.startswith('ERROR:'), text[:120])
        # Phan quyet that su: du bao loi hay khong, NOI DUNG khong duoc lot ra.
        if secret:
            suite.check('EXP-01: khong ro ri noi dung .env qua %s' % label,
                        secret[:40] not in text, text[:80])

    suite.check('EXP-01: duong dan rong bi tu choi',
                res.get('empty', '').startswith('ERROR:'), res.get('empty', '')[:80])
    # Doi chung: chan duong tan cong ma lam hong tinh nang thi khong phai la va.
    suite.check('EXP-01: van doc duoc tep trong logs/',
                not res.get('control', 'ERROR:').startswith('ERROR:'),
                res.get('control', '')[:120])


def run():
    suite = Suite('an toan thuc thi + lo lot (AUDIT_SECURITY_AND_DATA, 4 CRITICAL)')
    check_inj01(suite)
    check_inj02(suite)
    check_exp01(suite)
    check_exp02(suite)
    check_failsafe(suite)
    check_secrets(suite)
    return suite


if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass
    from harness import render
    sys.exit(render([run()]))
