"""Stage 12 boundary/lifecycle tests. No real enrollment or live memory writes."""
import json
from pathlib import Path
import re
import socket
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import Mock, patch

from desktop import Bridge, ALLOWED
from desktop_worker import DesktopService, COMMANDS, local_network_only
from config import Config, PermissionFenceError
from cockpit import Cockpit


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = DesktopService(Path(self.temp.name))
        self.service.mind = types.SimpleNamespace(config=Config(), cockpit=Cockpit(),
            operator_authenticated=False, psc=types.SimpleNamespace(memories=[]),
            events_log=types.SimpleNamespace(events=[]), camera=Mock(), voice=Mock())
        self.service._instrument = self.service.mind.cockpit.execute_tool
        self.service.ready = True
        self.service.state = 'idle'

    def test_bridge_only_exposes_request(self):
        public = [n for n in dir(Bridge) if not n.startswith('_') and callable(getattr(Bridge,n))]
        self.assertEqual(public, ['request'])
        client = Mock()
        bridge = Bridge(client)
        for name in ('eval', 'exec', 'shell', 'powershell', 'cmd', 'bash', '__getattribute__', 'read_file', [], None):
            self.assertFalse(bridge.request(name)['ok'])
        client.call.assert_not_called()
        self.assertEqual(ALLOWED-{'window'}, COMMANDS)

    def test_worker_rejects_unlisted_commands_and_malformed_payload(self):
        for command in ('shell', 'powershell', 'enable_camera', '__dict__', [], None):
            self.assertFalse(self.service.dispatch(command, {})['ok'])
        self.assertFalse(self.service.dispatch('chat', ['invalid'])['ok'])

    def test_shell_requests_through_chat_use_existing_judge(self):
        # Real mind with isolated stores and rule backend: the exact desktop chat path.
        from loop import MindLoop
        root = Path(self.temp.name)
        source = (Path(__file__).parent/'config.yaml').read_text()
        path = root/'config.yaml'
        path.write_text(source.replace('backend: "llm"', 'backend: "rule-based"'))
        mind = MindLoop(config_path=path, psc_path=root/'psc.json', events_log_path=root/'events.json')
        self.service.mind = mind
        for tool in ('powershell', 'cmd', 'bash', 'raw_socket'):
            response = self.service.dispatch('chat', {'text': f"ATMAN, execute tool '{tool}' to run a shell"})
            self.assertTrue(response['ok'])
            deadline=time.monotonic()+8
            while self.service.busy and time.monotonic()<deadline: time.sleep(.02)
            self.assertFalse(self.service.busy)
            events=self.service.dispatch('poll')['events']
            self.assertTrue(any(e['kind']=='denial' for e in events), tool)
            self.assertEqual(mind.psc.memories, [])

    def test_every_backend_action_respects_config_fence(self):
        self.service.mind.config=Mock()
        self.service.mind.config.is_action_permitted.return_value=False
        for command,payload in [('chat',{'text':'hello'}),('telemetry',{}),('memories',{}),
                                ('events',{}),('sleep',{}),('wake',{}),('sense',{'name':'mic','enabled':True})]:
            self.assertFalse(self.service.dispatch(command,payload)['ok'],command)

    def test_wizard_enrollment_and_authentication_without_real_credentials(self):
        self.service.ready=False
        self.service.auth=Mock()
        self.service.auth.is_enrolled.return_value=False
        self.service.auth.enroll.return_value=True
        self.assertFalse(self.service.dispatch('chat',{'text':'hello'})['ok'])
        self.assertFalse(self.service.dispatch('authenticate',{'passphrase':'short','confirm':'short'})['ok'])
        phrase='synthetic-test-phrase-only'
        self.assertTrue(self.service.dispatch('authenticate',{'passphrase':phrase,'confirm':phrase})['ok'])
        self.assertTrue(self.service.ready)
        self.assertTrue(self.service.mind.operator_authenticated)
        self.assertNotIn(phrase,json.dumps(self.service.dispatch('poll')))
        self.assertEqual(list(Path(self.temp.name).iterdir()),[])
        self.service.auth.is_enrolled.return_value=True
        self.service.auth.verify_passphrase.return_value=False
        self.assertFalse(self.service.dispatch('authenticate',{'passphrase':'incorrect'})['ok'])

    def test_guest_wizard_completion_preserves_unverified_attribution(self):
        self.service.ready=False
        self.assertTrue(self.service.dispatch('continue')['ok'])
        self.assertFalse(self.service.mind.operator_authenticated)

    def test_settings_persist_but_senses_never_auto_enable(self):
        self.assertTrue(self.service.dispatch('settings',{'hotkey':'Control','chimes':False})['ok'])
        other=DesktopService(Path(self.temp.name))
        self.assertEqual(other.settings['hotkey'],'Control')
        self.assertFalse(any(other.senses.values()))
        self.assertFalse(self.service.dispatch('settings',{'hotkey':'execute.exe'})['ok'])
        self.assertFalse(self.service.dispatch('sense',{'name':'mic','enabled':'yes'})['ok'])

    def test_sense_authorization_has_no_agent_entrypoint(self):
        self.assertFalse(self.service.dispatch('enable_camera',{'caller':'agent'})['ok'])
        self.assertTrue(self.service.dispatch('sense',{'name':'camera','enabled':True})['ok'])
        self.service.mind.camera.enable.assert_called_with(caller='owner_config')
        self.assertFalse(self.service.dispatch('sense',{'name':'open_mic','enabled':True})['ok'])

    def test_output_filter_and_public_record_projection(self):
        secret='SYNTHETIC PRIVATE CORE SENTENCE'
        self.service.secret_patterns=[re.compile(re.escape(secret),re.I)]
        self.service.mind.psc.memories=[{'text':secret,'tsc':'never-return','passphrase':'never-return'}]
        output=json.dumps(self.service.dispatch('memories'))
        self.assertNotIn(secret,output)
        self.assertNotIn('never-return',output)
        self.assertNotIn('abc123',self.service.clean('token=abc123'))

    def test_local_network_boundary(self):
        local_network_only('socket.connect',(None,('127.0.0.1',11434)))
        for address in [('8.8.8.8',443),('example.com',80)]:
            with self.assertRaises(PermissionError): local_network_only('socket.connect',(None,address))
        with self.assertRaises(PermissionError): local_network_only('socket.getaddrinfo',('example.com',443))
        for executable in ('cmd.exe','powershell.exe','python.exe'):
            with self.assertRaises(PermissionError): local_network_only('subprocess.Popen',(executable,[executable],None,None))

    def test_tray_show_sleep_wake_and_quit_route(self):
        client=Mock()
        client.call.return_value={'ok':True}
        bridge=Bridge(client)
        bridge._window=Mock()
        bridge._tray=Mock()
        bridge._show()
        bridge._window.show.assert_called_once()
        self.assertFalse(bridge._closing())
        bridge._window.hide.assert_called_once()
        bridge._tray_command('sleep')
        bridge._tray_command('wake')
        self.assertEqual([c.args[0] for c in client.call.call_args_list],['sleep','wake'])
        bridge._quit()
        self.assertTrue(bridge._closing())
        bridge._window.destroy.assert_called_once()

    def test_sleep_consolidation_progress_uses_existing_engine(self):
        from loop import MindLoop
        root=Path(self.temp.name)
        mind=MindLoop(psc_path=root/'psc.json',events_log_path=root/'events.json')
        mind.events_log.log_event('I prefer quiet work every morning.',source='operator',force_significant=True)
        mind.events_log.log_event('A passing cloud.',source='ambient',force_significant=True)
        self.service.mind=mind
        self.assertTrue(self.service.dispatch('sleep')['ok'])
        deadline=time.monotonic()+8
        while self.service.busy and time.monotonic()<deadline: time.sleep(.02)
        events=self.service.dispatch('poll')['events']
        progress=[e for e in events if e['kind']=='sleep_progress']
        complete=[e for e in events if e['kind']=='sleep_complete'][0]
        self.assertEqual(len(progress),2)
        self.assertEqual(complete['scanned'],2)
        self.assertEqual(complete['candidates']+complete['dropped'],2)
        self.assertEqual(complete['applied'],0)
        self.assertTrue(complete['verified'])
        self.assertEqual(self.service.state,'sleeping')
        self.assertEqual(mind.psc.memories,[])
        self.assertFalse(self.service.dispatch('chat',{'text':'hello'})['ok'])

    def test_microphone_buffers_are_memory_only_and_stop_releases_device(self):
        import numpy as np
        self.service.senses['mic']=True
        fake=Mock()
        with patch('sounddevice.InputStream',return_value=fake) as constructor:
            self.assertTrue(self.service.dispatch('record_start')['ok'])
            callback=constructor.call_args.kwargs['callback']
            callback(np.ones((160,1),dtype=np.float32)*.05,160,None,None)
            self.assertGreater(self.service.level,0)
            self.assertEqual(len(self.service.frames),1)
            self.assertTrue(self.service.dispatch('sense',{'name':'mic','enabled':False})['ok'])
            fake.stop.assert_called_once()
            fake.close.assert_called_once()
            self.assertEqual(self.service.frames,[])
            self.assertIsNone(self.service.stream)
            self.assertEqual(list(Path(self.temp.name).iterdir()),[])

    def test_quit_drains_inflight_work(self):
        entered=threading.Event()
        release=threading.Event()
        finished=threading.Event()
        def work():
            with self.service.lock:
                entered.set()
                release.wait(2)
        thread=threading.Thread(target=work)
        thread.start()
        self.assertTrue(entered.wait(1))
        quit_thread=threading.Thread(target=lambda:(self.service.dispatch('quit'),finished.set()))
        quit_thread.start()
        self.assertFalse(finished.wait(.05))
        release.set()
        self.assertTrue(finished.wait(1))
        thread.join()
        quit_thread.join()

    def test_typed_turn_releases_open_microphone_before_reasoning(self):
        fake=Mock()
        self.service.stream=fake
        self.service.frames=[object()]
        self.service.state='listening'
        with patch.object(self.service,'_task') as task:
            self.assertTrue(self.service.dispatch('chat',{'text':'Hello ATMAN'})['ok'])
            self.assertIsNone(self.service.stream)
            self.assertEqual(self.service.frames,[])
            fake.stop.assert_called_once()
            fake.close.assert_called_once()
            task.assert_called_once()

    def test_no_runtime_files_or_remote_assets_in_packaging(self):
        from build_desktop import DATA_FILES, FORBIDDEN_NAMES
        self.assertEqual(set(DATA_FILES),{'ui/index.html','ui/style.css','ui/app.js','exo_icon.png','desktop_worker.py'})
        self.assertFalse(any(any(word in name.lower() for word in FORBIDDEN_NAMES) for name in DATA_FILES))
        html=(Path(__file__).parent/'ui/index.html').read_text(encoding='utf-8')
        self.assertIn("connect-src 'none'",html)
        self.assertNotRegex(html,r'(?:src|href)=[\"\']https?://')


if __name__=='__main__': unittest.main()
