#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R302 的变异表（第 301 轮 / Round 299）：名册与棘轮必须各自有牙。

本轮做的两件事决定了刀的形状：
1. 358 —— `MotionFilmstripTests` 自己那份「两条腿」的实现删掉，只留一层指向
   `CaptureReadings.emit(_:to:)` 的薄壳（重复的十条行里，被锤过的锁与按 URL 记首次只在
   `CaptureReadings` 那一侧长过；没锁的那份每天在写 44 条动效读数）。
2. 覆盖率进了脚本电池：`scripts/tests/test_readings_channel_coverage.py` 把
   ① **名册 = 派生集**（用了 `emit(` 且代码里零裸 stdout 的文件，双向对账）
   ② **裸 stdout 行数 = 登记值 57**（双向棘轮：变多=新写了会死的通道，变少=修好了没重登）
   钉成会红的数。名册原来只有 Swift 侧那条守卫在读，而"把名册改短"这件事 Swift 侧**看不见**
   （它只扫名册里还写着的那些文件）—— 这正是 M873 要堵的洞。

三把刀各钉一侧：
· M872 往一份**已在名册里**的判据文件贴一行裸 stdout ⇒ 电池那一卷必须红在「盘上有」。
· M873 把名册改短一个名字 ⇒ 同一卷必须红在「未纳管」（Swift 侧那格对此是瞎的）。
· M874 把 `MotionFilmstripTests.emit` 的壳换回裸 stdout ⇒ Swift 侧守卫必须红在「只走 stdout」
  （它同时也会让电池那卷红在「已过期」，两条通道各自独立地抓住同一次违规）。

被搜的串（`pr` + `int(`）在替换文本里**拼出来**：刀表自己不该成为违规的现场。
「跑起来了没」按结论行形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
判定按**失败正文**而不只按格子名（D-244）。根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POPS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/MenuBarPopulationTests.swift'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
MOTION = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift'
PY_ROLL = 'scripts/tests/test_readings_channel_coverage.py'

# 名册里挑一个**不是**守卫本体的文件贴行，才说明扫描在看全部名册文件而不是只看守卫自己
NEEDLE_POP = u'import XCTest\n'
REPL_POP = (u'import XCTest\n\n'
            u'func r302InjectedBareReading() {\n'
            u'    pri' + u'nt("MOTION_INJECT files=1")\n'
            u'}\n')

# R306 重钉：这根针原本钉在 roster 的**头两行**，本轮按字母序往名单里插新文件名把头部挤走 ⇒ 命中 0 次。
# 与 286 那一族同形（腐烂的不只有源码注释，刀表自己的锚点也腐烂）。改钉**最后一行**：
# 字母序增长只会往上插，尾行只会在真的改名/删文件时动 —— 那才是这把刀要问的事。
NEEDLE_ROSTER = u'                      "UICaptureHarness.swift", "UIInteractionProbeTests.swift"]'
REPL_ROSTER = u'                      "UICaptureHarness.swift"]'

NEEDLE_EMIT = (u'    static func emit(_ line: String) {\n'
               u'        CaptureReadings.emit(line, to: readingsURL)\n'
               u'    }')
REPL_EMIT = (u'    static func emit(_ line: String) {\n'
             u'        pri' + u'nt(line)\n'
             u'    }')

GUARD_SWIFT = 'UICaptureTests/testCaptureReadingsUseTheFileChannel'
GUARD_PY = 'python:' + PY_ROLL

ARMS = [
    ('M872', u'名册里的判据文件长出一行裸 stdout = 棘轮必须响', POPS,
     NEEDLE_POP, REPL_POP, GUARD_PY, u'盘上有'),
    ('M873', u'名册被改短一个名字 = 未纳管必须红（Swift 侧对此是瞎的）', HARNESS,
     NEEDLE_ROSTER, REPL_ROSTER, GUARD_PY, u'未纳管'),
    ('M874', u'把 emit 的壳换回裸 stdout = Swift 侧扫描必须在看这个文件', MOTION,
     NEEDLE_EMIT, REPL_EMIT, GUARD_SWIFT, u'只走 stdout'),
]

EXECUTED = re.compile(r'Executed (\d+) tests?, with (\d+) failures?')
FAILED_CASE = re.compile(r"Test Case '-\[[\w.]+ (\w+)\]' failed")
PY_RAN = re.compile(r'^Ran (\d+) tests?', re.M)
PY_FAIL = re.compile(r'^FAILED \((?:failures=(\d+)|errors=(\d+))', re.M)
# R276/R277 那一族的老账：`unittest -v` 把格子 docstring 打在第一行，`... FAIL` 落在**另一行**，
# 所以按单行正则抓格子名会整批抓不到（那会把真 CAUGHT 报成 WRONG_CELL —— 坏在假阴性一侧）。
PY_HEAD = re.compile(r'^(test\w+) \([\w.]+\)')
PY_RESULT = re.compile(r'\.\.\. (FAIL|ERROR)')


def py_failed_cases(text):
    names, cur = [], None
    for line in text.split('\n'):
        head = PY_HEAD.match(line)
        if head:
            cur = head.group(1)
            if PY_RESULT.search(line):        # 单行形状：没有 docstring 的格子
                names.append(cur)
                cur = None
            continue
        if cur is not None and PY_RESULT.search(line):
            names.append(cur)
            cur = None
    return sorted(set(names))


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
    n_ran = int(executed[-1][0]) if executed else 0
    n_fail = int(executed[-1][1]) if executed else 0
    names = sorted(set(FAILED_CASE.findall(text)))
    return proc.returncode, n_ran, n_fail, names, text


def run_python(path):
    env = base_env()
    proc = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', '-v', path],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = PY_RAN.findall(text)
    n_ran = int(ran[-1]) if ran else 0
    fails = PY_FAIL.findall(text)
    n_fail = sum(int(a or b) for pair in fails for a, b in [pair]) if fails else 0
    names = py_failed_cases(text)
    return proc.returncode, n_ran, n_fail, names, text


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
        print('%s NOT_RUN 没有结论行（编译红/导入错不算 CAUGHT = D-243）：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    # Swift 侧的失败正文带 `error:`，python 侧的 unittest 摘要不带 ⇒ 两边按同一件事判：
    # 那一行里出现了期望的中文短语，并且这一跑真的有失败格子。
    named = [expect_text in ln for ln in text.splitlines()]
    if n_fail and names and any(named):
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d exit=%d）'
              % (arm_id, why, ', '.join(names), n_ran, n_fail, code), flush=True)
        for line in text.splitlines():
            if expect_text in line:
                print('   正文=%s' % line.strip()[:200], flush=True)
                break
        return 'CAUGHT'
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望格子 %s 且正文含「%s」'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', names, n_ran, n_fail,
             filter_name.split('/')[-1], expect_text), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R302_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R302_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
