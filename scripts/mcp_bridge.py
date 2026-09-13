#!/usr/bin/env python3
"""
MCP BRIDGE (Sprint: Live MCP Hunting Bridge)

Cầu nối để pipeline Python gọi được 99 tool của MCP server Node qua stdio.

Vì sao phải nói chuyện MCP thay vì tự chạy PowerShell trong Python: câu truy vấn
của mỗi cuộc săn chỉ nên tồn tại ở MỘT nơi. Repo này đã ba lần trả giá cho việc
có hai nguồn sự thật cho cùng một dữ liệu (risk_engine.py đọc khoá đã chết,
assets.json hai producer, shadow_asset_detector.py lấy MAC từ nơi không có MAC).
Sao chép truy vấn PowerShell sang Python sẽ là lần thứ tư.

Giao thức: JSON-RPC 2.0, mỗi thông điệp một dòng.
    initialize -> notifications/initialized -> tools/call ...

Một tiến trình server phục vụ nhiều lời gọi: khởi động mất khoảng 1-2 giây, và
mỗi cuộc săn không đáng phải trả lại chi phí đó.
"""

import json
import os
import subprocess
import sys
import threading
import time

PROTOCOL_VERSION = '2024-11-05'
CLIENT_NAME = 'sentinelops-pipeline'
DEFAULT_STARTUP_TIMEOUT = 60
DEFAULT_CALL_TIMEOUT = 120


class McpBridgeError(Exception):
    """Cầu nối không dùng được. Người gọi phải xử lý, không được nuốt."""


class McpBridge(object):
    """Client MCP stdio tối thiểu, đủ cho `tools/call`."""

    def __init__(self, project_root=None, server_script='server.js',
                 node_bin='node', startup_timeout=DEFAULT_STARTUP_TIMEOUT):
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = project_root
        self.server_script = server_script
        self.node_bin = node_bin
        self.startup_timeout = startup_timeout

        self.proc = None
        self._next_id = 0
        self._stderr_tail = []
        self._stderr_thread = None
        self.server_info = None

    # -- vòng đời ---------------------------------------------------------

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return False

    def start(self):
        script_path = os.path.join(self.project_root, self.server_script)
        if not os.path.exists(script_path):
            raise McpBridgeError('Không tìm thấy MCP server: {}'.format(script_path))

        try:
            self.proc = subprocess.Popen(
                [self.node_bin, self.server_script],
                cwd=self.project_root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
        except OSError as error:
            raise McpBridgeError('Không khởi động được node: {}'.format(error))

        # stderr của server là log chẩn đoán, không phải lỗi. Đọc trong luồng
        # riêng để nó không lấp đầy pipe và treo server.
        self._stderr_thread = threading.Thread(target=self._drain_stderr)
        self._stderr_thread.daemon = True
        self._stderr_thread.start()

        reply = self._request('initialize', {
            'protocolVersion': PROTOCOL_VERSION,
            'capabilities': {},
            'clientInfo': {'name': CLIENT_NAME, 'version': '1.0.0'},
        }, timeout=self.startup_timeout)

        if 'result' not in reply:
            raise McpBridgeError('initialize thất bại: {}'.format(
                json.dumps(reply)[:300]))

        self.server_info = reply['result'].get('serverInfo')
        self._notify('notifications/initialized', {})
        return self

    def stop(self):
        if not self.proc:
            return
        try:
            self.proc.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None

    # -- lớp giao thức ----------------------------------------------------

    def _drain_stderr(self):
        try:
            for line in iter(self.proc.stderr.readline, b''):
                text = line.decode('utf-8', 'replace').rstrip()
                if text:
                    self._stderr_tail.append(text)
                    # Giữ đuôi log đủ để chẩn đoán, không giữ cả biển.
                    if len(self._stderr_tail) > 80:
                        del self._stderr_tail[:-80]
        except Exception:
            pass

    def _send(self, payload):
        if not self.proc or self.proc.poll() is not None:
            raise McpBridgeError('MCP server đã dừng. stderr: {}'.format(
                ' | '.join(self._stderr_tail[-5:])))
        data = (json.dumps(payload) + '\n').encode('utf-8')
        try:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except (OSError, ValueError) as error:
            raise McpBridgeError('Không gửi được tới MCP server: {}'.format(error))

    def _notify(self, method, params):
        self._send({'jsonrpc': '2.0', 'method': method, 'params': params})

    def _request(self, method, params, timeout):
        self._next_id += 1
        request_id = self._next_id
        self._send({'jsonrpc': '2.0', 'id': request_id,
                    'method': method, 'params': params})

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise McpBridgeError('MCP server thoát giữa chừng (mã {}). stderr: {}'
                                     .format(self.proc.returncode,
                                             ' | '.join(self._stderr_tail[-5:])))
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            try:
                message = json.loads(line.decode('utf-8', 'replace'))
            except ValueError:
                # Dòng không phải JSON: bỏ qua, đó là nhiễu chứ không phải trả lời.
                continue
            if message.get('id') == request_id:
                return message
            # Thông báo hoặc trả lời của request khác: không quan tâm ở đây.

        raise McpBridgeError('Quá {}s khi chờ {}'.format(timeout, method))

    # -- API công khai ----------------------------------------------------

    def list_tools(self, timeout=30):
        reply = self._request('tools/list', {}, timeout)
        if 'result' not in reply:
            raise McpBridgeError('tools/list thất bại: {}'.format(
                json.dumps(reply)[:300]))
        return [t['name'] for t in reply['result'].get('tools', [])]

    def call_tool(self, name, arguments=None, timeout=DEFAULT_CALL_TIMEOUT):
        """Gọi một tool. Trả về dict mô tả đầy đủ kết quả, kể cả khi rỗng.

        Không bao giờ ném exception vì tool trả về rỗng - rỗng là một câu trả
        lời hợp lệ ("máy này sạch"), và người gọi cần phân biệt nó với lỗi.
        """
        started = time.time()
        reply = self._request('tools/call', {
            'name': name,
            'arguments': arguments or {},
        }, timeout)
        elapsed = round(time.time() - started, 2)

        result = {
            'tool': name,
            'ok': False,
            'empty': True,
            'raw_text': '',
            'parsed': None,
            'error': None,
            'duration': elapsed,
        }

        if 'error' in reply:
            result['error'] = str(reply['error'])[:400]
            return result

        payload = reply.get('result') or {}
        content = payload.get('content') or []
        text = ''
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text += block.get('text', '')

        result['raw_text'] = text
        result['ok'] = not payload.get('isError')
        result['empty'] = not text.strip()

        if text.strip():
            try:
                result['parsed'] = json.loads(text)
            except ValueError:
                # Một số tool trả văn bản thô. Vẫn là dữ liệu thật.
                result['parsed'] = None

        if payload.get('isError'):
            result['error'] = text[:400] or 'tool báo isError'

        return result


def as_list(parsed):
    """PowerShell ConvertTo-Json trả về object khi chỉ có 1 phần tử.

    Không chuẩn hoá chỗ này thì mọi nơi tiêu thụ đều phải tự đoán, và sẽ có nơi
    đoán sai.
    """
    if parsed is None:
        return []
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return [parsed]
    return []


def main():
    """Chạy trực tiếp để kiểm tra cầu nối: python scripts/mcp_bridge.py [tool ...]"""
    tools = sys.argv[1:] or ['huntPersistence']
    try:
        with McpBridge() as bridge:
            info = {'server': bridge.server_info, 'tools_available': len(bridge.list_tools())}
            results = []
            for name in tools:
                outcome = bridge.call_tool(name)
                results.append({
                    'tool': name,
                    'ok': outcome['ok'],
                    'empty': outcome['empty'],
                    'records': len(as_list(outcome['parsed'])),
                    'duration': outcome['duration'],
                    'error': outcome['error'],
                })
            info['results'] = results
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0
    except McpBridgeError as error:
        print(json.dumps({'status': 'bridge_error', 'error': str(error)},
                         indent=2, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
