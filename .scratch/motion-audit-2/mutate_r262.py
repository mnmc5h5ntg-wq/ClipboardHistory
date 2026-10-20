#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R262 的变异表：新写的"写死颗数"尺（`scripts/mutation_verdict_scan.py`）四把刀（D-244 的两轴）。

对象是**尺自己**，不是产品 ⇒ 四把都走 python 通道（一条 `python3 -m unittest <格子全名>`，
不必 swift build，也不必重捕帧）。这一族的三种坏法是 R262 现读出来的：这一轮我正是被
`'Executed 4 tests' in text` 这类写法绊了一次（那一卷从 4 条长到 6 条 ⇒ 真红了会被读成"根本没跑"），
所以新尺的每一颗牙都要能被砍掉一次再红回来。

M819 docstring 不再跳过 ⇒ `test_comment_and_docstring_quote_do_not_feed_the_ruler` 必须红
     （守卫被散文喂饱 = R74 那一族；本轮我自己就在注释里引用了那句 `'Executed 4 tests' in text`）。
M820 取消 `Executed 0` 的豁免 ⇒ `test_zero_is_a_state_not_a_round_reading` 必须红
     （0 不是本轮读数，是"filter 一条都没匹配上"这个状态；把它当写死就是把尺用错地方）。
M821 把匹配串换成永远匹配不上的 ⇒ `test_planted_literal_count_is_named` 必须红
     （尺是摆设 —— 恒不报的尺比没有尺更坏，因为它长得像报过了）。
M822 目录不存在却 exit 0 ⇒ `test_missing_dir_exits_one` 必须红
     （空对账静默通过 = R99/R140 那一族：`COMPARED=0` 时的 `CHANGED=0`）。

四把刀都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
RULER = 'scripts/mutation_verdict_scan.py'
CLS = 'scripts.tests.test_mutation_verdict_scan.MutationVerdictScanTests'

ARMS = [
    ('M819', u'docstring 不再跳过（守卫被散文喂饱）', RULER,
     '                    doc_nodes.add(id(val))', '                    pass',
     CLS + '.test_comment_and_docstring_quote_do_not_feed_the_ruler'),
    ('M820', u'取消 Executed 0 的豁免（把状态当成本轮读数）', RULER,
     "            if m.group(1) != '0':", '            if True:',
     CLS + '.test_zero_is_a_state_not_a_round_reading'),
    ('M821', u'匹配串换成永远匹配不上（尺是摆设）', RULER,
     r"LITERAL = re.compile(r'Executed (\d+) tests?\b')", r"LITERAL = re.compile(r'Executed (\d+) zzzzz')",
     CLS + '.test_planted_literal_count_is_named'),
    ('M822', u'目录不存在却 exit 0（空对账静默通过）', RULER,
     '        return 1', '        return 0',
     CLS + '.test_missing_dir_exits_one'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_id):
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    proc = subprocess.run([sys.executable, '-m', 'unittest', test_id], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    m = re.search(r'Ran (\d+) tests?', text)
    return proc.returncode, (int(m.group(1)) if m else 0), text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        if needle == repl:
            not_run += 1
            print('%s NOT_RUN 变异文与原文逐字相同 ⇒ 这一刀没有对象' % arm_id, flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, _ = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 2
        if n_ran == 0:
            not_run += 1
            print('%s NOT_RUN 那一格根本没跑（Ran 0）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print('%s CAUGHT  %s ⇒ %s' % (arm_id, filt.split('.')[-1], why), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ⇒ %s' % (arm_id, filt.split('.')[-1], why), flush=True)
    print('R262_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
