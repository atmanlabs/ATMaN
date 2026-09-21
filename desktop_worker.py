"""EXO desktop adapter. Runs in the installed backend Python, never in a web server.

Only structured, allowlisted commands arrive over the parent's private stdin pipe.
No private values or backend diagnostics are forwarded to stdout/stderr.
"""
from __future__ import annotations
import contextlib
import io
import json
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

ROOT = Path.home() / 'Documents' / 'exo-live'
COMMANDS = frozenset({'boot', 'diagnostics', 'authenticate', 'continue', 'poll', 'chat',
    'telemetry', 'memories', 'events', 'sleep', 'wake', 'sense', 'record_start',
    'record_stop', 'settings', 'quit'})


def local_network_only(event, args):
    if event == 'socket.connect':
        address = args[1]
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1'):
            raise PermissionError('External connections are disabled.')
    if event == 'socket.getaddrinfo' and args[0] not in ('localhost', '127.0.0.1', '::1', None):
        raise PermissionError('External name lookup is disabled.')
    if event == 'subprocess.Popen':
        executable, argv = args[:2]
        # The existing cockpit's fixed NVIDIA instrument is the only child allowed.
        if executable is not None and Path(str(executable)).name.lower() not in ('nvidia-smi', 'nvidia-smi.exe'):
            raise PermissionError('Desktop backend child process blocked.')
        expected = ['nvidia-smi', '--query-gpu=gpu_name,memory.used,memory.total,utilization.gpu',
                    '--format=csv,noheader,nounits']
        if argv != expected and argv != subprocess.list2cmdline(expected):
            raise PermissionError('Non-telemetry process arguments blocked.')


class DesktopService:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.mind = None
        self.ready = False
        self.state = 'crate'
        self.busy = False
        self.lock = threading.RLock()
        self.messages = queue.Queue(maxsize=2048)
        self.senses = {'camera': False, 'mic': False, 'open_mic': False}
        self.settings = {'hotkey': 'Space', 'chimes': True, 'close_to_tray': True}
        self.stream = None
        self.frames = []
        self.record_started = 0
        self.last_sound = 0
        self.level = 0
        self.secret_patterns = []
        self.auth_attempts = []
        self.settings_path = self.root / 'runtime' / 'desktop-settings.json'
        try:
            saved = json.loads(self.settings_path.read_text())
            self._settings(saved, persist=False)
        except (OSError, ValueError, TypeError):
            pass

    def clean(self, value):
        if isinstance(value, str):
            for pattern in self.secret_patterns:
                value = pattern.sub('[protected]', value)
            value = re.sub(r'(?i)(?:[A-Z]:\\[^\n]*?(?:exo-private|operator\.auth)[^\n]*|(?:password|passphrase|api[_-]?key|token)\s*[:=]\s*\S+)', '[protected]', value)
            return value[:24000]
        if isinstance(value, list):
            return [self.clean(v) for v in value[:500]]
        if isinstance(value, dict):
            return {k: self.clean(v) for k, v in value.items() if k not in
                    {'tsc', '_data', 'thought', 'capture', 'proposals', 'rationale', 'passphrase'}}
        return value

    def emit(self, kind, **data):
        item = self.clean({'kind': kind, **data})
        try:
            self.messages.put_nowait(item)
        except queue.Full:
            self.messages.get_nowait()
            self.messages.put_nowait(item)

    def dispatch(self, command, payload=None):
        if type(command) is not str or command not in COMMANDS or not isinstance(payload, (dict, type(None))):
            self.emit('denial', text='Unlisted desktop operation blocked.')
            return {'ok': False, 'error': 'Permission fence blocked this operation.'}
        payload = payload or {}
        # Every call passes this boundary; backend action/tool policy is checked again below.
        try:
            if command == 'boot':
                return self._boot()
            if command == 'poll':
                events = []
                for _ in range(150):
                    try: events.append(self.messages.get_nowait())
                    except queue.Empty: break
                return {'ok': True, 'events': events, 'state': self.state,
                        'busy': self.busy, 'level': float(self.level), 'senses': self.senses.copy()}
            if command == 'quit':
                self._stop_recording(False)
                # Drain any in-flight mind/consolidation operation before process exit.
                with self.lock:
                    pass
                return {'ok': True}
            if self.mind is None:
                raise ValueError('The crate has not passed verification.')
            if command == 'diagnostics': return self._diagnostics()
            if command == 'authenticate': return self._authenticate(payload)
            if command == 'continue':
                self.ready = True
                self.state = 'idle'
                return {'ok': True}
            if not self.ready:
                raise ValueError('Complete the first-run screen first.')
            if command == 'settings':
                return {'ok': True, 'settings': self._settings(payload)}
            if command == 'telemetry':
                self._fence('tool_call')
                return {'ok': True, 'telemetry': self._instrument('system_telemetry')['data'],
                        'clock': self._instrument('clock_timer')['data']}
            if command in ('memories', 'events'):
                self._fence('status')
                with self.lock:
                    records = self.mind.psc.memories if command == 'memories' else self.mind.events_log.events
                    # Serialize only explicitly public record fields, never arbitrary objects.
                    fields = ('text', 'memory', 'candidate', 'raw', 'source', 'timestamp', 't', 'consolidated')
                    result = [{k: r[k] for k in fields if k in r} if isinstance(r, dict) else str(r)
                              for r in records[-300:]]
                return {'ok': True, 'records': self.clean(result)}
            if command == 'sense': return self._sense(payload)
            if command == 'record_start': return self._start_recording()
            if command == 'record_stop':
                self._stop_recording(True)
                return {'ok': True}
            if command == 'chat':
                text = payload.get('text')
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= 8000:
                    raise ValueError('Enter a message of 1–8,000 characters.')
                self._fence('respond')
                if self.state == 'sleeping': raise ValueError('Wake JARVIS before sending a message.')
                self._stop_recording(False)
                self._task(lambda: self._chat(text), 'thinking')
                return {'ok': True}
            if command == 'sleep':
                self._fence('reflect')
                self._stop_recording(False)
                self._task(self._sleep, 'consolidating')
                return {'ok': True}
            if command == 'wake':
                self._fence('status')
                if self.busy: raise ValueError('Wait for the current operation to finish.')
                from crate import verify
                if not verify(): raise ValueError('Crate verification failed. Owner action required.')
                self.state = 'idle'
                self.emit('wake')
                return {'ok': True}
        except Exception as exc:
            # Never forward backend exception text: it can contain private input/identity.
            from config import PermissionFenceError
            if isinstance(exc, PermissionFenceError):
                self.emit('denial', text='The permission fence blocked this request.')
            safe = str(exc) if type(exc) is ValueError else 'Operation unavailable. Check local setup or permissions.'
            return {'ok': False, 'error': self.clean(safe)}

    def _fence(self, action):
        from config import PermissionFenceError
        if not self.mind.config.is_action_permitted(action):
            raise PermissionFenceError('Blocked')

    def _boot(self):
        if self.mind is not None:
            return {'ok': True, 'settings': self.settings, 'enrolled': self.auth.is_enrolled()}
        from crate import verify
        if not verify():
            return {'ok': False, 'error': 'Crate verification failed. Owner action required.'}
        from loop import MindLoop
        import operator_auth
        self.auth = operator_auth
        self.mind = MindLoop()
        endpoint = urlsplit(str(self.mind.config.get('mind', 'ollama_endpoint', default='')))
        if endpoint.scheme != 'http' or endpoint.hostname not in ('127.0.0.1', 'localhost', '::1'):
            self.mind = None
            raise ValueError('Ollama must use a local HTTP address.')
        # Build an in-memory output filter; protect internal security commands and rules.
        def strings(value):
            if isinstance(value, str): yield value
            elif hasattr(value, 'values'):
                for child in value.values(): yield from strings(child)
            elif isinstance(value, (tuple, list)):
                for child in value: yield from strings(child)
        protected = list(strings(self.mind.tsc.principles)) + list(strings(self.mind.tsc.commands))
        self.secret_patterns = [re.compile(re.escape(s), re.I) for s in protected if len(s) >= 4]
        # UI-only sense state is an overlay; the immutable backend config and files stay unchanged.
        base = self.mind.config
        owner_state = self.senses
        class SenseView:
            def get(self, *keys, default=None):
                if keys == ('mind', 'camera_enabled'): return owner_state['camera']
                if keys == ('mind', 'voice_enabled'): return owner_state['mic']
                return base.get(*keys, default=default)
        self.mind.camera.config = SenseView()
        self.mind.voice.config = SenseView()
        original = self.mind.cockpit.execute_tool
        self._instrument = original
        def audited_tool(name, args=None):
            self._fence('tool_call')
            from config import PermissionFenceError
            if name == 'workspace_inspect' and (args or {}).get('action') == 'read':
                path = str((args or {}).get('path', ''))
                # Desktop never permits credential/private/runtime file inspection.
                if path not in {'STAGE-PLAN.md', 'RELEASE-NOTES-v2.md', 'LICENSE', 'UPSTREAM.md'}:
                    self.emit('tool', name=name, text='Read blocked: not a public desktop-readable document.')
                    raise PermissionFenceError('Desktop file boundary')
            try:
                result = original(name, args)
                self.emit('tool', name=name, text=result.get('output', 'Completed'))
                return result
            except PermissionFenceError:
                self.emit('tool', name=str(name)[:80], text='Blocked by permission fence')
                raise
        self.mind.cockpit.execute_tool = audited_tool
        return {'ok': True, 'enrolled': self.auth.is_enrolled(), 'settings': self.settings,
                'backend': str(base.get('mind', 'backend', default='rule-based'))}

    def _authenticate(self, payload):
        now = time.monotonic()
        self.auth_attempts = [x for x in self.auth_attempts if now-x < 60]
        if len(self.auth_attempts) >= 5: raise ValueError('Wait one minute before trying again.')
        self.auth_attempts.append(now)
        phrase = payload.get('passphrase', '')
        if not isinstance(phrase, str) or not 1 <= len(phrase) <= 512:
            raise ValueError('Enter a valid passphrase.')
        if not self.auth.is_enrolled():
            if phrase != payload.get('confirm'): raise ValueError('The passphrases do not match.')
            if len(phrase) < 12: raise ValueError('Use at least 12 characters for your passphrase.')
            success = self.auth.enroll(phrase)
        else:
            success = self.auth.verify_passphrase(phrase)
        if not success: raise ValueError('Passphrase not accepted.')
        self.mind.operator_authenticated = True
        self.ready = True
        self.state = 'idle'
        return {'ok': True}

    def _diagnostics(self):
        import urllib.request
        values = {'ollama': 'Unavailable — start the installed Ollama app.',
                  'qwen': 'Not found — install the configured model manually in Ollama.',
                  'moondream': 'Not found — install Moondream manually in Ollama.',
                  'mic': 'Allow desktop microphone access in Windows Settings > Privacy & security > Microphone.',
                  'cam': 'Allow desktop camera access in Windows Settings > Privacy & security > Camera. Tested only after you turn it on.'}
        try:
            endpoint = self.mind.config.get('mind', 'ollama_endpoint')
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(endpoint + '/api/tags', timeout=3) as reply:
                names = [x['name'] for x in json.load(reply).get('models', [])]
            values['ollama'] = 'Ready — running on this PC'
            if self.mind.config.get('mind', 'ollama_model') in names: values['qwen'] = 'Ready — installed locally'
            if any(x.startswith('moondream:') for x in names): values['moondream'] = 'Ready — installed locally'
        except Exception: pass
        try:
            import sounddevice as sd
            inputs = [x for x in sd.query_devices() if x['max_input_channels'] > 0]
            if inputs: values['mic'] = 'Microphone detected. If capture fails, allow desktop microphone access in Windows Settings.'
        except Exception: pass
        return {'ok': True, 'diagnostics': values}

    def _settings(self, data, persist=True):
        if set(data) - set(self.settings): raise ValueError('Unknown setting.')
        if 'hotkey' in data and data['hotkey'] not in ('Space', 'Enter', 'Control', 'Alt'):
            raise ValueError('Choose a listed hotkey.')
        if any(type(data[k]) is not bool for k in ('chimes', 'close_to_tray') if k in data):
            raise ValueError('Invalid switch value.')
        self.settings.update(data)
        if persist:
            self.settings_path.parent.mkdir(exist_ok=True)
            temp = self.settings_path.with_suffix('.tmp')
            temp.write_text(json.dumps(self.settings), encoding='utf-8')
            temp.replace(self.settings_path)
        return dict(self.settings)

    def _sense(self, data):
        name, enabled = data.get('name'), data.get('enabled')
        if name not in self.senses or type(enabled) is not bool: raise ValueError('Invalid sense control.')
        self._fence('observe')
        # This command exists only on the operator pipe. Agent tool dispatch cannot reach it.
        if name == 'camera': self.mind.camera.enable(caller='owner_config')
        else: self.mind.voice.enable(caller='owner_config')
        if name == 'open_mic' and enabled and not self.senses['mic']:
            raise ValueError('Turn the microphone on first.')
        self.senses[name] = enabled
        if name == 'mic' and not enabled:
            self.senses['open_mic'] = False
            self._stop_recording(False)
        if name == 'open_mic' and not enabled: self._stop_recording(False)
        return {'ok': True, 'senses': self.senses.copy()}

    def _task(self, fn, state):
        if self.busy: raise ValueError('JARVIS is finishing the current operation.')
        self.busy = True
        self.state = state
        def run():
            try:
                with self.lock: fn()
            except Exception:
                self.emit('error', text='That operation could not complete. Check local models and device permissions.')
            finally:
                self.busy = False
                if self.state != 'sleeping': self.state = 'idle'
                self.emit('done')
        threading.Thread(target=run, daemon=True).start()

    def _chat(self, text, source='operator'):
        # Explicit shell/tool requests are denied before sensory capture or reasoning.
        forbidden = r'(?:powershell|cmd|bash|curl|raw_socket|modify_core|enable_camera|enable_voice|voice_listen)'
        if re.search(r'\b(?:execute|run|invoke|launch|start)\b.{0,120}\b'+forbidden+r'\b', text, re.I | re.S):
            self.emit('denial', text='Shells, external connections, and self-enabling senses are blocked.')
            self.emit('reply_start')
            self.emit('reply_chunk', text='The desktop permission fence blocked that request.')
            self.emit('reply_end', imprinted=False)
            return
        if self.senses['camera']:
            frame = self.mind.camera.capture_frame()
            if frame is not None:
                description = self.mind.camera.describe_frame_with_vision(frame,
                    model=self.mind.config.get('mind', 'vision_model'),
                    endpoint=self.mind.config.get('mind', 'ollama_endpoint'))
                if description: text += '\n[Live camera observation] ' + description
        result = self.mind.run_cycle({'raw': text, 'source': source})
        action = result['action_result']
        if not result['verdict'].approved:
            self.emit('denial', text='Request rejected by the Judge. No rejected content was imprinted.')
            reply = 'The permission fence or identity guard blocked that request.'
        else:
            reply = self.clean(action.get('content') or action.get('output_text') or 'Done.')
        self.emit('reply_start')
        # Only post-Judge text crosses the boundary, in chunks; never raw model tokens.
        for offset in range(0, len(reply), 28):
            self.emit('reply_chunk', text=reply[offset:offset+28])
            time.sleep(.018)
        self.emit('reply_end', imprinted=bool(result.get('imprinted')))
        if self.senses['mic']:
            self.state = 'speaking'
            self.emit('speaking', active=True)
            try: self.mind.voice.tts.speak(reply, play_audio=True)
            finally: self.emit('speaking', active=False)
        if action.get('action') == 'shutdown': self._sleep()

    def _sleep(self):
        from sleep import SleepConsolidator
        service = self
        class ProgressConsolidator(SleepConsolidator):
            scanned = 0
            kept = 0
            def evaluate_candidacy(self, event):
                result = super().evaluate_candidacy(event)
                self.scanned += 1
                self.kept += bool(result)
                service.emit('sleep_progress', scanned=self.scanned, candidates=self.kept,
                             dropped=self.scanned-self.kept)
                return result
        result = ProgressConsolidator(events_log=self.mind.events_log, tsc=self.mind.tsc,
             config=self.mind.config, proposals_path=self.root/'pending_proposals.json').consolidate()
        self.state = 'sleeping'
        self.emit('sleep_complete', scanned=result.events_scanned, candidates=result.candidates_proposed,
                  dropped=result.events_scanned-result.candidates_proposed, applied=0,
                  verified=bool(result.tsc_verified))

    def _start_recording(self):
        self._fence('observe')
        if not self.senses['mic']: raise ValueError('Turn the microphone on in Flight Deck first.')
        if self.busy or self.state == 'sleeping': raise ValueError('Wait until JARVIS is awake and ready.')
        if self.stream is not None: return {'ok': True}
        import numpy as np
        import sounddevice as sd
        self.frames = []
        self.record_started = self.last_sound = time.monotonic()
        def capture(indata, frames, timing, status):
            self.frames.append(indata[:, 0].copy())
            self.level = float(np.sqrt(np.mean(indata ** 2)))
            if self.level > .012: self.last_sound = time.monotonic()
        self.stream = sd.InputStream(samplerate=16000, channels=1, dtype='float32', callback=capture)
        self.stream.start()
        self.state = 'listening'
        stream = self.stream
        def monitor():
            while self.stream is stream:
                elapsed = time.monotonic()-self.record_started
                if elapsed > 30 or (self.senses['open_mic'] and elapsed > 2 and time.monotonic()-self.last_sound > 1.5):
                    self._stop_recording(True)
                    break
                time.sleep(.1)
        threading.Thread(target=monitor, daemon=True).start()
        return {'ok': True}

    def _stop_recording(self, transcribe):
        stream, self.stream = self.stream, None
        if stream is None: return
        stream.stop()
        stream.close()
        frames, self.frames = self.frames, []
        self.level = 0
        self.state = 'idle'
        if transcribe and frames:
            def process():
                import numpy as np
                text = self.mind.voice.stt.transcribe(np.concatenate(frames))
                if text.strip():
                    self.emit('transcript', text=text)
                    self._chat(text, source='operator')
            self._task(process, 'thinking')


def main():
    protocol = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                      DO_NOT_TRACK='1', NO_PROXY='localhost,127.0.0.1,::1')
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    sys.addaudithook(local_network_only)
    service = DesktopService()
    for line in sys.stdin:
        try:
            if len(line) > 20000: raise ValueError()
            request = json.loads(line)
            result = service.dispatch(request.get('command'), request.get('payload'))
        except Exception:
            result = {'ok': False, 'error': 'Desktop request rejected.'}
        protocol.write(json.dumps(result, ensure_ascii=True) + '\n')
        protocol.flush()


if __name__ == '__main__':
    main()
