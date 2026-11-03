#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性诊断：`install_local.sh` 的沙箱自检到底卡在哪一步（脚本自己的打印流出来看）。

为什么要做：脚本电池从 `Ran 719 / OK` 变成 `errors=2`（两条都是 TimeoutExpired=180s），
而这两条测试本早上还绿。要么是我的某一段改动动了它，要么是环境变了 —— 两种都要数分开。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'scripts', 'tests'))
from test_install_local import make_bundle, SCRIPT, APP_NAME, BINARY  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix='r565-dbg-install-'))
try:
    dest = tmp / 'cjk-dest'
    running = make_bundle(dest, 'RUNNING_OLD')
    exe = running / 'Contents' / 'MacOS' / BINARY
    src = exe.parent / 'autoexit.c'
    src.write_text('#include <unistd.h>\nint main(void){sleep(1);return 0;}\n', encoding='utf-8')
    cc = shutil.which('cc') or shutil.which('clang')
    built = subprocess.run([cc, '-o', str(exe), str(src)], capture_output=True, text=True, timeout=180)
    print('夹具编译 returncode=%d %s' % (built.returncode, built.stderr.strip()[-200:]))
    if built.returncode != 0:
        sdk_root = Path('/Library/Developer/CommandLineTools/SDKs')
        for sdk in sorted(sdk_root.glob('MacOSX*.sdk'), reverse=True):
            built = subprocess.run([cc, '-isysroot', str(sdk), '-o', str(exe), str(src)],
                                   capture_output=True, text=True, timeout=180)
            print('  SDK %s ⇒ %d' % (sdk.name, built.returncode))
            if built.returncode == 0:
                break
    exe.chmod(0o755)
    proc = subprocess.Popen([str(exe)])
    time.sleep(0.2)
    print('夹具 pid=%s poll=%s' % (proc.pid, proc.poll()))

    new_bundle = make_bundle(tmp / 'new', 'NEW_BUILD')
    t0 = time.time()
    child = subprocess.Popen(['bash', '-x', str(SCRIPT), '--yes', '--no-build', '--skip-smoke',
                              '--no-launch', '--bundle=%s' % new_bundle,
                              '--dest=%s' % dest, '--label=dbg-%d' % os.getpid()],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace')
    try:
        for line in child.stdout:
            print('[%6.1fs] %s' % (time.time() - t0, line.rstrip()))
            if time.time() - t0 > 100:
                print('!!! 100 秒没走完，杀掉')
                child.kill()
                break
    finally:
        child.kill()
        child.wait()
        proc.kill()
finally:
    shutil.rmtree(tmp, True)
