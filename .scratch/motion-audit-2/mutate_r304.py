#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R304 的变异表（第 303 轮 / Round 301）：搬第二批之后，两处新写的账各钉一侧。

本轮做的事：`MotionDriverTests` / `PressFeedbackTests` / `SettingsFailureReceiptTests`
三份共 13 行裸 stdout 读数改走 `CaptureReadings.emit`；覆盖率棘轮 42 → 现读 29；
派生名册 11 → 14；Swift 那张按文件的名字名册新增一张 `emitChannel` 表（搬过的文件按 `emit("` 数）。

两把刀：
· M878 **通道表要有牙**：把 `MotionDriverTests.swift` 从 `emitChannel` 里删掉 ⇒
  那份文件的名字清单会「测到空」而登记非空 ⇒ `testProbeFilePrintReadingsAreARosterNotACount` 必须红。
  （R303 的教训反过来用：通道写错不会只影响计数，它会让整份清单凭空消失而守卫仍绿。）
· M879 **上界仍有牙**：把其中一行改回裸 stdout ⇒ 电池那一卷必须红在「盘上有 30 行」。

被搜的串（`pr` + `int(`）在替换文本里拼出来。判定按失败正文（D-244）；没有结论行一律 NOT_RUN
（编译红不算 CAUGHT = D-243）；根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DRIVER = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionDriverTests.swift'
ROSTER = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/FrameIntervalBudgetTests.swift'
GUARD_PY = 'python:scripts/tests/test_readings_channel_coverage.py'
GUARD_SWIFT = 'FrameIntervalBudgetTests/testProbeFilePrintReadingsAreARosterNotACount'

NEEDLE_CHANNEL = u'            "SettingsFailureReceiptTests.swift", "MotionDriverTests.swift",\n'
REPL_CHANNEL = u'            "SettingsFailureReceiptTests.swift",\n'

NEEDLE_LINE = u'        CaptureReadings.emit("BANNER_DRIVE 调用点 \\(gates.count) 个、键 \\(keys.count) 条、"'
REPL_LINE = u'        pri' + u'nt("BANNER_DRIVE 调用点 \\(gates.count) 个、键 \\(keys.count) 条、"'

ARMS = [
    ('M878', u'通道表里删掉一个搬过的名字 = 那份文件的名字清单必须红', ROSTER,
     NEEDLE_CHANNEL, REPL_CHANNEL, GUARD_SWIFT, u'与名册不符'),
    ('M879', u'把搬好的读数改回裸 stdout = 棘轮上界有牙', DRIVER,
     NEEDLE_LINE, REPL_LINE, GUARD_PY, u'盘上有 30 行'),
]

EXECUTED = re.compile(r'Executed (\d+) tests?, with (\d+) failures?')
FAILED_CASE = re.compile(r"Test Case '-\[[\w.]+ (\w+)\]' failed")
PY_RAN = re.compile(r'^Ran (\d+) tests?', re.M)
PY_FAIL = re.compile(r'^FAILED \((?:failures=(\d+)|errors=(\d+))', re.M)
PY_HEAD = re.compile(r'^(test\w+) \([\w.]+\)')
PY_RESULT = re.compile(r'\.\.\. (FAIL|ERROR)')


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def base_env():
    env = dict(os.environ)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    return env


def run_swift(filter_name):
    env = base_env()
    try:
        env['SDKROOT'] = subprocess.check_output(
            ['xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=env).decode().strip()
    except Exception:
        env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', filter_name],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    executed = EXECUTED.findall(text)
    return (proc.returncode, int(executed[-1][0]) if executed else 0,
            int(executed[-1][1]) if executed else 0,
            sorted(set(FAILED_CASE.findall(text))), text)


def py_failed_cases(text):
    names, cur = [], None
    for line in text.split('\n'):
        head = PY_HEAD.match(line)
        if head:
            cur = head.group(1)
            if PY_RESULT.search(line):
                names.append(cur)
                cur = None
            continue
        if cur is not None and PY_RESULT.search(line):
            names.append(cur)
            cur = None
    return sorted(set(names))


def run_python(path):
    proc = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', '-v', path],
                          cwd=ROOT, env=base_env(),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = PY_RAN.findall(text)
    fails = PY_FAIL.findall(text)
    n_fail = sum(int(a or b) for pair in fails for a, b in [pair]) if fails else 0
    return (proc.returncode, int(ran[-1]) if ran else 0, n_fail, py_failed_cases(text), text)


def run(filter_name):
    return run_python(filter_name.split(u':', 1)[1]) if filter_name.startswith(u'python:') \
        else run_swift(filter_name)


def run_arm(arm_id, why, target, needle, repl, filter_name, expect_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        code, n_ran, n_fail, names, text = run(filter_name)
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not n_ran:
        tail = '\n'.join(text.strip().splitlines()[-3:])
        print('%s NOT_RUN 没有结论行：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    if n_fail and names and any(expect_text in ln for ln in text.splitlines()):
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d exit=%d）'
              % (arm_id, why, ', '.join(names), n_ran, n_fail, code), flush=True)
        for line in text.splitlines():
            if expect_text in line:
                print('   正文=%s' % line.strip()[:180], flush=True)
                break
        return 'CAUGHT'
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望正文含「%s」'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', names, n_ran, n_fail, expect_text), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R304_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R304_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
