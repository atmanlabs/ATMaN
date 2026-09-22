"""Stage 1 verification with synthetic identities; never opens the real soul."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class CrateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root/'atman-live'
        self.private = self.root/'atman-private'
        self.build.mkdir()
        self.private.mkdir()
        for name in ('core.py','atman_core.py','crate.py','wake.py','seal.py','gate_policy.json'):
            shutil.copyfile(Path(__file__).parent/name, self.build/name)
        self.soul = self.private/'tsc.atman.private.json'
        self.soul.write_text(json.dumps({'name':'Fixture','operator':'Owner','immutable':True,
                                        'self':['I am Fixture.'],'principles':[]}),encoding='utf-8')
        self.original = self.soul.read_bytes()

    def run_script(self, *args):
        return subprocess.run([sys.executable,*args],cwd=self.build,capture_output=True,
                              text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'})

    def seal(self):
        self.assertEqual(self.run_script('seal.py','--operator-confirm').returncode,0)

    def test_clean_wake_and_no_core_or_memory_writes(self):
        self.seal()
        result=self.run_script('wake.py')
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertTrue(result.stdout.endswith('ATMAN is in his crate correctly\n'))
        self.assertNotIn('I am Fixture',result.stdout)
        self.assertEqual(self.soul.read_bytes(),self.original)
        self.assertFalse((self.build/'psc.json').exists())
        self.assertFalse((self.build/'tsc.json').exists())

    def test_missing_seal_fails_before_executor_import(self):
        (self.build/'core.py').write_text('raise RuntimeError("UNTRUSTED EXECUTOR RAN")')
        result=self.run_script('wake.py')
        self.assertEqual(result.returncode,1)
        self.assertNotIn('UNTRUSTED EXECUTOR RAN',result.stdout+result.stderr)

    def test_executor_tamper_fails_before_import(self):
        self.seal()
        (self.build/'core.py').write_text('raise RuntimeError("UNTRUSTED EXECUTOR RAN")')
        result=self.run_script('wake.py')
        self.assertEqual(result.returncode,1)
        self.assertNotIn('UNTRUSTED EXECUTOR RAN',result.stdout+result.stderr)

    def test_soul_drift_fails_without_restoring_or_resealing(self):
        self.seal()
        self.soul.write_text('invalid json')
        self.assertEqual(self.run_script('wake.py').returncode,1)
        self.assertEqual(self.soul.read_text(),'invalid json')
        self.assertEqual(self.run_script('seal.py','--operator-confirm').returncode,1)

    def test_policy_drift_fails(self):
        self.seal()
        (self.build/'gate_policy.json').write_text('{}')
        self.assertEqual(self.run_script('wake.py').returncode,1)

    def test_no_confirmation_no_seal(self):
        self.assertNotEqual(self.run_script('seal.py').returncode,0)
        self.assertFalse((self.private/'stage1-seal.json').exists())

    def test_deep_and_attribute_immutability(self):
        code = '''from atman_core import TSC, ImmutableViolation
t=TSC()
actions=[lambda: t.__init__(),lambda: setattr(t,'name','Other'),lambda: setattr(t,'_data',{}),
         lambda: t.write(name='Other'),lambda: t.commands[0].__setitem__('pattern',''),
         lambda: t.iam.__setitem__(0,'Changed')]
for action in actions:
    try: action()
    except (ImmutableViolation,TypeError,AttributeError): pass
    else: raise AssertionError('write succeeded')
assert t.verify()
'''
        result=self.run_script('-c',code)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.soul.read_bytes(),self.original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
