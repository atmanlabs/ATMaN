"""Native EXO body: WebView2, private pipe to the installed mind, Windows tray."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

ASSETS = Path(__file__).resolve().parent
BACKEND = Path.home() / 'Documents' / 'exo-live'
PYTHON = Path.home() / 'AppData/Local/Programs/Python/Python311/python.exe'
ALLOWED = frozenset({'boot', 'diagnostics', 'authenticate', 'continue', 'poll', 'chat',
    'telemetry', 'memories', 'events', 'sleep', 'wake', 'sense', 'record_start',
    'record_stop', 'settings', 'quit', 'window'})


class PipeClient:
    def __init__(self):
        self.lock = threading.Lock()
        self.process = subprocess.Popen([str(PYTHON), '-u', str(ASSETS/'desktop_worker.py')],
            cwd=str(BACKEND), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    def call(self, command, payload):
        with self.lock:
            self.process.stdin.write(json.dumps({'command': command, 'payload': payload})+'\n')
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line: return {'ok': False, 'error': 'The local mind process stopped. Restart EXO.'}
            return json.loads(line)

    def close(self):
        try:
            self.call('quit', {})
            self.process.stdin.close()
            self.process.wait(timeout=4)
        except Exception:
            self.process.terminate()


class Bridge:
    # Deliberately only one public method; no window/backend object exposed to JS.
    def __init__(self, client):
        self._client = client
        self._window = None
        self._tray = None
        self._close_to_tray = True
        self._quitting = False

    def request(self, command, payload=None):
        if type(command) is not str or command not in ALLOWED or not isinstance(payload, (dict, type(None))):
            return {'ok': False, 'error': 'Unlisted desktop operation blocked.'}
        payload = payload or {}
        try:
            if len(json.dumps(payload)) > 18000:
                return {'ok': False, 'error': 'Request too large.'}
            if command == 'window':
                action = payload.get('action')
                if action == 'minimize': self._window.minimize()
                elif action == 'hide' and self._tray is not None: self._window.hide()
                elif action == 'close': self._window.destroy()
                else: return {'ok': False, 'error': 'Window action unavailable.'}
                return {'ok': True}
            result = self._client.call(command, payload)
            if result.get('ok') and 'settings' in result:
                self._close_to_tray = result['settings']['close_to_tray']
            return result
        except Exception:
            return {'ok': False, 'error': 'Desktop operation unavailable. Restart EXO if needed.'}

    def _closing(self):
        if self._close_to_tray and self._tray is not None and not self._quitting:
            self._window.hide()
            return False
        return True

    def _quit(self, *args):
        self._quitting = True
        self._window.destroy()

    def _show(self, *args):
        self._window.show()
        self._window.restore()

    def _tray_command(self, command):
        # Reuses precisely the same policy boundary as the UI.
        result = self.request(command)
        if not result.get('ok'):
            self._show()
            self._window.evaluate_js('window.desktopNotice('+json.dumps(result.get('error'))+')')

    def _start_tray(self):
        import pystray
        from PIL import Image
        self._tray = pystray.Icon('JARVIS', Image.open(ASSETS/'exo_icon.png'), 'JARVIS — Personal AI',
            pystray.Menu(pystray.MenuItem('Show JARVIS', self._show, default=True),
                         pystray.MenuItem('Sleep', lambda: self._tray_command('sleep')),
                         pystray.MenuItem('Wake', lambda: self._tray_command('wake')),
                         pystray.MenuItem('Quit', self._quit)))
        self._tray.run_detached()


def main():
    import webview
    # One body per backend memory store. No competing desktop writers.
    import ctypes
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Local\\EXO-Desktop-Stage12')
    if ctypes.windll.kernel32.GetLastError() == 183:
        ctypes.windll.user32.MessageBoxW(None, 'JARVIS is already running. Use the tray icon to show him.', 'JARVIS', 0)
        return
    if not PYTHON.exists() or not (BACKEND/'loop.py').exists():
        ctypes.windll.user32.MessageBoxW(None, 'The existing local JARVIS backend or Python installation is missing.', 'JARVIS', 0)
        return
    client = PipeClient()
    bridge = Bridge(client)
    # Inline the three trusted assets: no HTTP listener and no external asset loading.
    html = (ASSETS/'ui/index.html').read_text(encoding='utf-8')
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        '<style>'+(ASSETS/'ui/style.css').read_text(encoding='utf-8')+'</style>')
    html = html.replace('<script src="app.js"></script>',
                        '<script>'+(ASSETS/'ui/app.js').read_text(encoding='utf-8')+'</script>')
    webview.settings['ALLOW_DOWNLOADS'] = False
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False
    window = webview.create_window('JARVIS', html=html, js_api=bridge, width=1280, height=840,
                                  min_size=(900, 650), background_color='#080c12', frameless=True,
                                  easy_drag=False, text_select=True)
    bridge._window = window
    window.events.closing += bridge._closing
    def started():
        try: bridge._start_tray()
        except Exception:
            window.evaluate_js('window.desktopNotice("Tray unavailable; closing will quit JARVIS.")')
    try:
        webview.start(started, gui='edgechromium', debug=False, private_mode=True,
                      http_server=False)
    finally:
        if bridge._tray is not None: bridge._tray.stop()
        client.close()
        ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == '__main__':
    main()
