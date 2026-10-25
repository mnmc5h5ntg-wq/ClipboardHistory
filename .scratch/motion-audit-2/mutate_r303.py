#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R303 的变异表（第 302 轮 / Round 300）：搬完一份之后，三个方向都必须还有牙。

本轮做的事：把 `UIInteractionProbeTests.swift` 里 15 行只走 stdout 的读数
（FOCUS-CHAIN / TAB-KEY-CHAIN / KEYBOARD-UIMODE / AX-VISITED / KEYCHAIN* / FILTER_FOCUS /
FOCUSCHAIN-RING / RINGVIEWS）改走 `CaptureReadings.emit`，于是
① 棘轮的登记值从 57 降到现读的 42；② 那份文件从「未覆盖名单」退场、并进派生集 ⇒ 名册 11 个。

三把刀各钉一个新面：
· M875 **反方向的上界**：把其中一行改回裸 stdout ⇒ 棘轮必须红在「盘上有 N+1 行」（N 由表现读登记值，不抄常数）。
· M876 **棘轮的下界**（R74：放宽要成对两刀）：把登记值本身抬到 43（模拟「修好了却没重登」
  之外的另一种坏法 —— 拿登记值去容纳现状）⇒ 必须红在「登记值是 43」。
  这一把的 needle 就在判据文件里，是本轮唯一一把**改尺子而不是改被测量**的刀：
  它证明这根棘轮的两端都是人写的数，不是从盘上抄回来的常数（后者恒真）。
· M877 **名册只准加长、退场要看得见**：把刚进名册的那个名字删掉 ⇒ 必须红在「未纳管」。

被搜的串（`pr` + `int(`）在替换文本里拼出来。判定按失败正文（D-244），编译红不算 CAUGHT（D-243）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROBE = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
GUARD_FILE = 'scripts/tests/test_readings_channel_coverage.py'
GUARD_PY = 'python:' + GUARD_FILE

NEEDLE_LINE = u'        CaptureReadings.emit("FOCUS-CHAIN " + chain.joined(separator: " | "))'
REPL_LINE = u'        pri' + u'nt("FOCUS-CHAIN " + chain.joined(separator: " | "))'

# R306：这三处原本把**棘轮的当前值**抄进刀表（needle `= 29`、期望正文「盘上有 30 行」，而文件开头的
# 说明还写着 43 —— 一份表里三个数），于是每搬一批读数就要回来改三行，改慢一格就是 NOT_RUN / WRONG_CELL。
# 现在让表**自己定位**：登记值从被改的那份文件里现读，needle 与两处期望全部由它派生
# （与 R298 那条「死基线会腐烂 ⇒ 让判据自己找生日」同一修法）。
with io.open(os.path.join(ROOT, GUARD_FILE), encoding='utf-8') as _handle:
    _ceil = re.search(r'^BARE_PRINT_LINE_CEILING = (\d+)', _handle.read(), re.M)
if not _ceil:
    sys.stderr.write(u'R303_PRECHECK_FAILED 读不到 BARE_PRINT_LINE_CEILING ⇒ 三把针无从派生，不出表\n')
    sys.exit(1)
CEIL_NOW = int(_ceil.group(1))

# R383 重钉：`%` 拼出来的针 static 不可解（hidden_arms 把 M876 报成 rot，盘上其实是活的）。
# 改成**字面量针**，并在 main 里加一条漂移断言：登记值一变就当场报「重新钉 M876」而不是静默腐烂。
NEEDLE_CEIL = u'BARE_PRINT_LINE_CEILING = 15'
REPL_CEIL = u'BARE_PRINT_LINE_CEILING = 16'
EXPECT_CEIL = u'登记值是 16'

NEEDLE_ROSTER = u'                      "UICaptureHarness.swift", "UIInteractionProbeTests.swift"]'
REPL_ROSTER = u'                      "UICaptureHarness.swift"]'

ARMS = [
    ('M875', u'把一行搬好的读数改回裸 stdout = 上界有牙', PROBE,
     NEEDLE_LINE, REPL_LINE, GUARD_PY, u'盘上有 %d 行' % (CEIL_NOW + 1)),
    ('M876', u'把登记值抬去容纳现状 = 下界有牙（放宽要成对）', GUARD_FILE,
     NEEDLE_CEIL, REPL_CEIL, GUARD_PY, EXPECT_CEIL),
    ('M877', u'刚进名册的名字被删掉 = 未纳管必须红', HARNESS,
     NEEDLE_ROSTER, REPL_ROSTER, GUARD_PY, u'未纳管'),
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
    env = base_env()
    proc = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', '-v', path],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
                print('   正文=%s' % line.strip()[:200], flush=True)
                break
        return 'CAUGHT'
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望正文含「%s」'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', names, n_ran, n_fail,
             expect_text), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    if CEIL_NOW != 15:
        print('R303_MUTATE PRECHECK_FAILED BARE_PRINT_LINE_CEILING 漂到 %d ⇒ 重钉 M876'
              '（needle / mutant / 期望三处）' % CEIL_NOW, flush=True)
        return 1
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R303_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R303_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
