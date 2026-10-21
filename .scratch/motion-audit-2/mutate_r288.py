#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R288 的变异表（第 287 轮 / Round 285）：给 331 那卷观测式名册补两把刀（D-244 各钉一条轴）。

· M840 归属轴 —— 把「表头行 + 结果行」配对里**同一行**那条结果丢掉（退回我第一版的错法）：
  恒等式闸门必须红，且红话里要出现「恒等式」那一格才有的字样（`归属漏了`）。
  这一把证明：那格闸门真的在数归属，不是在数它自己。
· M841 排除轴 —— 把「排除观察者」那行拆掉：观察者那一格就会落进「名单外出现 skip」，
  红话必须是 `名单外`。这一把证明：排除动作是有承重的一格，不是一句注释。

两把刀各红在**不同判据字样**上（同一格里的不同断言）⇒ 只看"这一格红了"不足以区分两条轴，
所以判定读的是失败消息，不是格子名。执行器是 python（被测对象是脚本卷），根由 `__file__` 推（D-260）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = 'scripts.tests.test_skip_roster'
T = 'scripts/tests/test_skip_roster.py'

N_PAIR = ("            r0 = RESULT.search(line)\n"
          "            if r0:\n"
          "                records[current] = r0.group(1)\n"
          "                current = None\n"
          "            else:\n"
          "                records.setdefault(current, 'unknown')\n"
          "            continue")
R_PAIR = ("            records.setdefault(current, 'unknown')\n"
          "            continue")

N_EXCL = "        actual = [n for n in actual if n != OBSERVER_ID]"
R_EXCL = "        # M841 刀：拆掉排除观察者这一行"

ARMS = [
    ('M840', u'同一行的结果被丢掉 = 归属轴', T, N_PAIR, R_PAIR, u'归属漏了'),
    ('M841', u'排除观察者被拆掉 = 排除轴', T, N_EXCL, R_EXCL, u'名单外出现 skip'),
]

RAN_SHAPE = re.compile(r'^Ran (\d+) tests?', re.M)
FAILED_SHAPE = re.compile(r'^FAILED', re.M)


def run_arm(arm_id, why, rel_target, needle, repl, expected_text):
    target = os.path.join(ROOT, rel_target)
    original = io.open(target, encoding='utf-8').read()
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        io.open(target, 'w', encoding='utf-8').write(original.replace(needle, repl, 1))
        env = dict(os.environ)
        env.pop('SDKROOT', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONUTF8'] = '1'
        proc = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', MODULE],
                              cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = proc.stdout.decode('utf-8', 'replace')
    finally:
        io.open(target, 'w', encoding='utf-8').write(original)
        if io.open(target, encoding='utf-8').read() != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    ran = RAN_SHAPE.findall(text)
    n_ran = int(ran[-1]) if ran else 0
    if not n_ran or not FAILED_SHAPE.search(text):
        print('%s %s 跑=%d（没有结论行=NOT_RUN；绿了=ESCAPED）'
              % (arm_id, 'NOT_RUN' if not n_ran else 'ESCAPED', n_ran), flush=True)
        return 'NOT_RUN' if not n_ran else 'ESCAPED'
    if expected_text in text:
        print('%s CAUGHT  %s ｜ 红话里点名了「%s」（跑=%d）' % (arm_id, why, expected_text, n_ran), flush=True)
        return 'CAUGHT'
    tail = [l for l in text.splitlines() if 'AssertionError' in l]
    print('%s WRONG_REASON ｜ 红了但没点名「%s」，实得：%s' % (arm_id, expected_text, (tail or ['无'])[:1]), flush=True)
    return 'WRONG_REASON'


def main():
    kinds = [run_arm(*a) for a in ARMS]
    caught = kinds.count('CAUGHT')
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R288_MUTATE 刀=%d CAUGHT=%d 其它=%s RESTORE_CLEAN=%s'
          % (len(ARMS), caught, ','.join(k for k in kinds if k != 'CAUGHT') or '无', clean), flush=True)
    return 0 if (caught == len(ARMS) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
