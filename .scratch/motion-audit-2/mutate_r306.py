#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R306 的变异表（第 305 轮 / Round 303）：第三批搬动之后，三处同步点各自要有牙。

本轮把四份判据卷的 14 行裸 stdout 读数改走 `CaptureReadings.emit`
（OffscreenSymbolInkProbeTests 4 + Round4MarkdownTests 4 + CapturePathWriteBudgetTests 3 + PerfBudgetTests 3），
于是登记值 29 → 15、派生名册 14 → 18、Swift 那张名字名册的通道表多两个名字；
另外把 `test_ledger_ids.py` 里 D 号与 BACKLOG 条目号的三位假设抬成 `\\d{3,4}`（363）。

三把刀打在**三个不同的同步点**上（D-285：每搬一次就要数清同步点并逐处配刀）：

· M882 登记值那一侧：把 `Round4MarkdownTests` 的一行改回裸 print ⇒ 覆盖率那一卷必须红在「盘上有 16 行」。
· M883 通道表那一侧：把 `PerfBudgetTests.swift` 从 Swift 的 `emitChannel` 名单里删掉 ⇒
  `testProbeFilePrintReadingsAreARosterNotACount` 必须红在与名册不符
  （那份读数已经走 emit，按 print 去找就一无所获，而两份标记仍登记着 ⇒ 空清单冒充扫过了）。
· M884 编号尺那一侧：把 `DEC_DEF_HEADING_ONLY` 改回只认三位 ⇒ 那条四位正对照必须红。

两种执行器各按自己的结论行认「跑起来了没」：python 卷看 `Ran N tests`，Swift 看
`Executed N tests, with M failures`（编译错 / 收集不到都不算 CAUGHT = D-243）；
判定按**失败的格子名 + 正文里的串**（D-244）。根由 `__file__` 推（D-260/D-262）；
needle 恰好命中一次、落刀后回读、还原逐字节一致（RESTORE_CLEAN）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R4 = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/Round4MarkdownTests.swift'
FIB = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/FrameIntervalBudgetTests.swift'
IDS = 'scripts/tests/test_ledger_ids.py'

PY_COV = 'scripts.tests.test_readings_channel_coverage'
PY_IDS = 'scripts.tests.test_ledger_ids'
SWIFT_ROSTER = 'FrameIntervalBudgetTests/testProbeFilePrintReadingsAreARosterNotACount'

# 期望正文里的数**不抄**：从守卫文件现读登记值再 +1。理由就在本轮自己身上 —— 重跑历史表时
# r303 的 M875/M876 与 r304 的 M879 全因为把棘轮旧值（30）抄进期望而 WRONG_CELL，
# 而这一把原本也写着「盘上有 16 行」，下一批搬完它一样会烂。
with open(os.path.join(ROOT, 'scripts', 'tests', 'test_readings_channel_coverage.py'),
          encoding='utf-8') as _handle:
    _ceil = re.search(r'^BARE_PRINT_LINE_CEILING = (\d+)', _handle.read(), re.M)
if not _ceil:
    sys.stderr.write(u'R306_PRECHECK_FAILED 读不到 BARE_PRINT_LINE_CEILING ⇒ 期望正文无从派生，不出表\n')
    sys.exit(1)
CEIL_EXPECT = u'盘上有 %d 行' % (int(_ceil.group(1)) + 1)

# (刀号, 说明, 执行器, 跑什么, 目标文件, needle, 替换, 期望红的格子, 期望正文里的串)
ARMS = [
    ('M882', u'把搬好的读数写回裸 stdout = 棘轮登记值那一侧', 'py', PY_COV, R4,
     u'        CaptureReadings.emit("MARKDOWN_PERF dense_40k_ms=',
     u'        print("MARKDOWN_PERF dense_40k_ms=',
     'test_bare_stdout_reading_lines_equal_the_registered_ceiling', CEIL_EXPECT),
    ('M883', u'从通道表里删一个名字 = Swift 名册瞎在换通道那一侧', 'swift', SWIFT_ROSTER, FIB,
     u'            "OffscreenSymbolInkProbeTests.swift", "PerfBudgetTests.swift",\n',
     u'            "OffscreenSymbolInkProbeTests.swift",\n',
     'testProbeFilePrintReadingsAreARosterNotACount', u'名册'),
    ('M884', u'把决定号的尺改回只认三位 = 边界正对照那一侧', 'py', PY_IDS, IDS,
     u'DEC_DEF_HEADING_ONLY = re.compile(r"^#{2,3} (D-\\d{3,4})\\b", re.M)',
     u'DEC_DEF_HEADING_ONLY = re.compile(r"^#{2,3} (D-\\d{3})\\b", re.M)',
     'test_four_digit_decision_ids_are_recognised', u'四位'),
]

RAN = re.compile(r'^Ran (\d+) tests', re.M)
PY_FAIL = re.compile(r'^FAIL: (\w+) ', re.M)
EXECUTED = re.compile(r'Executed (\d+) tests?, with (\d+) failures?')
SWIFT_FAILED = re.compile(r"Test Case '-\[[\w.]+ (\w+)\]' failed")


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def run_py(module):
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    proc = subprocess.run([sys.executable, '-B', '-W', 'ignore', '-m', 'unittest', '-v', module],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = RAN.findall(text)
    return (int(ran[-1]) if ran else 0), sorted(set(PY_FAIL.findall(text))), text


def run_swift(filter_name):
    env = dict(os.environ)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    try:
        env['SDKROOT'] = subprocess.check_output(
            ['xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=env).decode().strip()
    except Exception:
        env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', filter_name],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ex = EXECUTED.findall(text)
    return (int(ex[-1][0]) if ex else 0), sorted(set(SWIFT_FAILED.findall(text))), text


def execute(kind, what):
    return run_py(what) if kind == 'py' else run_swift(what)


def run_arm(arm_id, why, kind, what, target, needle, repl, want_fail, want_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        if read(target).count(repl) != 1:
            print('%s NOT_RUN 落刀后回读不是那一刀' % arm_id, flush=True)
            return 'NOT_RUN'
        ran, fails, text = execute(kind, what)
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not ran:
        tail = '\n'.join(text.strip().splitlines()[-3:])
        print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    body = [line for line in text.splitlines() if want_text in line]
    if want_fail in fails and body:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d）' % (arm_id, why, ', '.join(fails), ran), flush=True)
        print('   正文=%s' % body[0].strip()[:200], flush=True)
        return 'CAUGHT'
    print('%s %s ｜ 跑=%d 红=%s 正文含串=%s ⇒ 期望格子 %s 且正文含「%s」'
          % (arm_id, 'ESCAPED' if not fails else 'WRONG_CELL', ran, fails, bool(body),
             want_fail, want_text), flush=True)
    return 'ESCAPED' if not fails else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    unknown = only - set(a[0] for a in ARMS)
    if unknown:
        print('R306_MUTATE NOT_RUN 未知刀号 %s' % sorted(unknown), flush=True)
        return 2
    # 基线：两份 python 卷先绿。不绿的话，后面每一朵 CAUGHT 都不说明任何事。
    for module in (PY_COV, PY_IDS):
        ran, fails, _ = run_py(module)
        if not ran or fails:
            print('R306_BASELINE NOT_RUN %s 基线不绿（跑=%d 红=%s）⇒ 拒绝出表'
                  % (module, ran, fails), flush=True)
            return 1
    print('R306_BASELINE OK（两份 python 卷都绿）', flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'no' if 'RESTORE_FAILED' in kinds else 'yes'
    print('R306_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
