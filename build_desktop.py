"""Explicit body-only PyInstaller build and recursive archive exclusion verification."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
DATA_FILES=('ui/index.html','ui/style.css','ui/app.js','atman_icon.png','desktop_worker.py')
FORBIDDEN_NAMES=('tsc','operator.auth','operator_auth','stage1-seal','seal.json','atman-private',
                 'psc.json','significant_events.json','pending_proposals.json','.env','credentials')
EXCLUDED=('core','atman_core','crate','seal','operator_auth','loop','reason','voice','senses',
          'cockpit','config','sleep','significant_events','torch','transformers','numpy',
          'cv2','faster_whisper','piper','sounddevice','matplotlib','pandas','IPython','pytest')


def verify_archive(executable):
    from PyInstaller.archive.readers import CArchiveReader
    archive=CArchiveReader(str(executable))
    names=list(archive.toc)
    pyz=archive.open_embedded_archive('PYZ.pyz')
    modules=list(pyz.toc)
    bad=[name for name in names+modules if any(word in name.lower() for word in FORBIDDEN_NAMES)]
    bad += [name for name in modules if name.split('.')[0] in EXCLUDED]
    if bad: raise RuntimeError('Release includes a prohibited file/module; build rejected.')
    # Inspect all text data included by our explicit body manifest for credential records.
    for name in DATA_FILES:
        data=archive.extract(name.replace('/', '\\')) if name.replace('/', '\\') in archive.toc else archive.extract(name)
        if name.endswith(('.py','.html','.js','.css')):
            for marker in (b'"salt":', b'"hash":', b'-----BEGIN PRIVATE KEY-----'):
                if marker in data: raise RuntimeError('Credential-shaped data in release; rejected.')
    return {'archive_entries':len(names),'python_modules':len(modules),
            'private_files_excluded':True,'mind_modules_excluded':True,
            'sha256':hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
            'body_files':list(DATA_FILES)}


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist')
    output=parser.parse_args().output_dir.resolve()
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
             '--name','ATMAN','--icon',str(ROOT/'atman_icon.ico'),
             '--distpath',str(output),'--workpath',str(ROOT/'build')]
    for name in DATA_FILES:
        destination=str(Path(name).parent)
        command += ['--add-data',str(ROOT/name)+';'+destination]
    for name in EXCLUDED: command += ['--exclude-module',name]
    command += [str(ROOT/'desktop.py')]
    subprocess.run(command,cwd=ROOT,check=True)
    result=verify_archive(output/'ATMAN.exe')
    (output/'RELEASE-CHECK.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
