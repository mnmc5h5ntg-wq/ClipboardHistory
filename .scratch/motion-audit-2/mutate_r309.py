#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R309 的变异表（第 308 轮 / Round 306）：新搬进仓库的那颗读数尺，每一侧都要有牙。

靶：`scripts/ledger_readings.py`（BACKLOG 348 的「数字对不对」那一格）；
被搜的卷：`scripts/tests/test_ledger_readings.py`（8 格，已知答案的合成日志 + 真产物对照）。

六把刀各钉一条轴（都是 R308 真栽过的那几种坏法的反面）：
· M895 恒等式闸门不许是装饰 —— 摘掉「全量卷不可能比单卷小」⇒ 抄到子集必须点名。
· M896 小节正文不许取错块（第一版的变异文写了 Swift 的 // 注释 ⇒ python 语法红 ⇒ NOT_RUN，改成 # 之后才有 CAUGHT）
 —— `re.split` 只吃分隔符，标题与正文同住一块；取错就什么也读不到。
· M897 取用的是**最后一跑** —— 改成取第一跑 ⇒ 台账会把「修之前那跑的红」写成结论。
· M898 早先那一跑的红不许抹 —— 只留最后一跑绿 = 把改动过程藏起来。
· M899 「没解析到 skip」不许读成 0（R140 的空对账、R171 的结论行形状）。
· M900 同一小节两行不一致不许静默取末 —— 哪一跑作数说不清就得红。

判定按失败正文里的**断言原文/中文说明**（D-244）；没有结论行一律 NOT_RUN（编译红不算 CAUGHT，D-243）；
未落刀先跑基线，基线不绿 ⇒ PRECHECK_FAILED 退出 1；根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

from readback import single_substitution_lands

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = 'scripts/ledger_readings.py'
GUARD = u'python:scripts.tests.test_ledger_readings'

N_GATE = u'if info[u"other_max"] is not None and int(run) < info[u"other_max"]:'
R_GATE = u'if False:'
N_BODY = u'out.append((bits[0].strip(), bits[1] if len(bits) > 1 else u""))'
R_BODY = u'out.append((bits[0].strip(), u""))  # MUTANT 正文取空'
N_LAST = u'title, run, skip, fail = rows[-1]'
R_LAST = u'title, run, skip, fail = rows[0]  # MUTANT 取第一跑'
N_ERASE = u'        if f_ != u"0":\n            info[u"red_passes"].append((t, f_))'
R_ERASE = u'        if False:  # MUTANT 抹掉早先那跑的红\n            info[u"red_passes"].append((t, f_))'
N_SKIP = u'    if skip is None:'
R_SKIP = u'    if False:  # MUTANT 读不到 skip 也不报'
N_AMB = u'        if len(seen) > 1:'
R_AMB = u'        if False:  # MUTANT 两行不一致也静默取末'

ARMS = [
    ('M895', u'恒等式闸门有牙：全量卷读到子集必须点名', TARGET, N_GATE, R_GATE, GUARD,
     u'这道闸门是假的'),
    ('M896', u'小节正文必须住在标题那一块里', TARGET, N_BODY, R_BODY, GUARD,
     u'正文没落到本块'),
    ('M897', u'取用的是最后一跑', TARGET, N_LAST, R_LAST, GUARD,
     u'assertEqual(u"0", info[u"fail"])'),
    ('M898', u'早先那一跑的红不许抹', TARGET, N_ERASE, R_ERASE, GUARD,
     u'原样留档'),
    ('M899', u'读不到 skip 不算 0', TARGET, N_SKIP, R_SKIP, GUARD,
     u'是两件事'),
    ('M900', u'同一小节两行不一致必须红', TARGET, N_AMB, R_AMB, GUARD,
     u'self.assertEqual([], rows)'),
]

PY_RAN = re.compile(r'^Ran (\d+) tests?', re.M)
PY_FAIL = re.compile(r'^FAILED \((?:failures=(\d+)|errors=(\d+))', re.M)
PY_HEAD = re.compile(r'^(test\w+) \([\w.]+\)')
PY_RESULT = re.compile(r'\.\.\. (FAIL|ERROR)')


def base_env():
    return {k: v for k, v in os.environ.items() if k != 'SDKROOT'}


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding='utf-8') as h:
        return h.read()


def write(rel, text):
    with io.open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as h:
        h.write(text)


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


def run_guard():
    env = base_env()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    proc = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', '-v',
                           GUARD.split(u':', 1)[1]],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = PY_RAN.findall(text)
    fails = PY_FAIL.findall(text)
    n_fail = sum(int(a or b) for pair in fails for a, b in [pair]) if fails else 0
    return (proc.returncode, int(ran[-1]) if ran else 0, n_fail, py_failed_cases(text), text)


def run_arm(arm_id, why, target, needle, repl, _filter, expect_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        after = read(target)
        # R368 / 426：判「盘上恰好等于预期 diff」（删臂也成立），不判替换串出现几次。
        if not single_substitution_lands(original, needle, repl, after):
            print('%s NOT_RUN 落刀后回读与预期 diff 不一致' % arm_id, flush=True)
            return 'NOT_RUN'
        code, n_ran, n_fail, names, text = run_guard()
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not n_ran:
        print('%s NOT_RUN 没有结论行：%s'
              % (arm_id, '\n'.join(text.strip().splitlines()[-3:])), flush=True)
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
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', names, n_ran, n_fail,
             expect_text), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    bad_ids = only - set(a[0] for a in ARMS)
    if bad_ids:
        print('R309_MUTATE ARG_ERROR 未知刀号 %s' % sorted(bad_ids), flush=True)
        return 2
    code0, ran0, fail0, names0, text0 = run_guard()
    if not ran0 or fail0 or code0 != 0:
        print('R309_MUTATE PRECHECK_FAILED 基线不绿（跑=%d 失败=%d exit=%d 红在 %s）'
              % (ran0, fail0, code0, names0), flush=True)
        return 1
    print('R309_MUTATE BASELINE 跑=%d 失败=0 exit=%d ⇒ 后面的 CAUGHT 才有意义'
          % (ran0, code0), flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    if not arms:
        print('R309_MUTATE ARG_ERROR 一臂都没选中', flush=True)
        return 2
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'no' if 'RESTORE_FAILED' in kinds else 'yes'
    print('R309_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
