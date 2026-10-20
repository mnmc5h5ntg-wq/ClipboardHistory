#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R238 的变异表（BACKLOG 250）：两把刀各摘掉「定义行 = 标题 ∪ 粗体」里的一半。

为什么这轮必须有两把刀：本轮改动**只有一支守卫正则**（`scripts/tests/test_ledger_ids.py`），
而这条守卫在过去若干轮里一直是绿的、却看不见 28 条决定。「它绿了」不配当证据，
只有「把某一半摘掉 ⇒ 新表必须红」才配。

- M793 摘掉 DEC_DEF 的**粗体**那一半（退回 R238 之前的字面）⇒ `test_bold_definition_line_makes_the_citation_land`
  必须红。它问的是：两态对照里「给了粗体正文」那一态，是不是真的靠粗体那一半过的。
- M794 把 `strip_definition` 退回只认标题形 ⇒ `test_the_bold_definition_line_can_be_stripped_and_is_named` 必须红。
  这一刀的期望**第一版写错了**：当时指 `test_the_guard_itself_is_not_vacuous`，跑回来是 ESCAPED ——
  读判据才知道那条正对照挑 victim 靠「被引用且编号最大」，而 R237 把 D-222 从轮次标题里撤掉之后
  victim 落回标题形，于是粗体分支坏了它也无感。**修的是刀与判据各自的证人**：
  补一格直接在合成语料上抹粗体定义行（不依赖台账此刻引用了谁），并把期望改成那一格。
  这一格专防「正对照自己坏了还打 ok」（R100 那一族：还原臂只准还原它要问的那一处形状）。

两把都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核；
基线臂不可信 ⇒ 拒绝出表（exit 1），不许把红算成产品的。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
GUARD = 'scripts/tests/test_ledger_ids.py'

ARMS = [
    ('M793', u'摘掉 DEC_DEF 的粗体那一半（退回 R238 之前只认标题的字面）', GUARD,
     r'DEC_DEF = re.compile(r"^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)", re.M)',
     r'DEC_DEF = re.compile(r"^(?:#{2,3} (D-\d{3})\b)", re.M)',
     'test_bold_definition_line_makes_the_citation_land'),
    ('M794', u'把 strip_definition 退回只认标题形（粗体的 victim 抹不掉）', GUARD,
     r'    for pat in (r"^#{2,3} " + victim + r"\b", r"^\*\*" + victim + r"（"):',
     r'    for pat in (r"^#{2,3} " + victim + r"\b",):',
     'test_the_bold_definition_line_can_be_stripped_and_is_named'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, s):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(s)


def run_guard():
    """跑整支守卫文件，再从 -v 输出里点名**那一格**是不是 FAIL。

    只认退出码会把别的格的绿/红混成本刀的结论（R222 的同一句话）。
    这台机器的 python3.9 在 -v 下把失败印成两段：先 `test_x (Class) ... `，再单独一行
    `FAIL: test_x (Class)` ⇒ 两种形状都要认，否则真红会读成 ESCAPED。
    """
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    proc = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'scripts.tests.test_ledger_ids'],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode('utf-8', 'replace')


def red_names(out):
    names = set(re.findall(r'^FAIL: (\S+)', out, re.M))
    names |= set(re.findall(r'^(\S+).* \.\.\. FAIL', out, re.M))
    return sorted(n for n in names if n.startswith('test_'))


base = run_guard()
io.open('/tmp/r238_mutate_base.log', 'w', encoding='utf-8').write(base)
base_reds = red_names(base)
if 'Ran ' not in base or not base.rstrip().endswith('OK') or base_reds:
    print('R238_MUTATE_REFUSED 基线臂不可信 ran=%s 结尾OK=%s 红名=%s'
          % ('Ran ' in base, base.rstrip().endswith('OK'), ','.join(base_reds) or '无'))
    sys.exit(1)

# R245 / U-792：预检 mutate_needle_precheck.py 是 **import 每张表** 的，而本表的臂循环写在模块顶层，
# 于是「跑一次预检」= 把这张表的刀真跑一遍（会起 subprocess 跑测试、会插拔源码文件）。
# 修法：执行只在直接运行时发生；被 import 时只登记 ARMS —— needle 唯一性是静态检查，不需要跑测试。
if __name__ != '__main__':
    pass
else:
    rows = []
    caught = escaped = not_run = other = 0
    for mid, why, rel, old, new, want in ARMS:
        text = read(rel)
        hits = text.count(old)
        if hits != 1:
            not_run += 1
            rows.append((mid, 'NOT_RUN', 'needle 命中 %d 次（要恰好 1）' % hits, '', 'yes'))
            continue
        write(rel, text.replace(old, new, 1))
        out = run_guard()
        io.open('/tmp/r238_%s.log' % mid, 'w', encoding='utf-8').write(out)
        write(rel, text)
        restore = (read(rel) == text)
        reds = red_names(out)
        if not reds:
            escaped += 1
            verdict = 'ESCAPED'
        elif want in reds:
            caught += 1
            verdict = 'CAUGHT'
        else:
            other += 1
            verdict = 'WRONG_CELL'
        if not restore:
            verdict += '/RESTORE_DIRTY'
        rows.append((mid, verdict, ','.join(reds) or '无', want, 'yes' if restore else 'NO'))

    print('R238 变异表（对象=守卫自己，产品 0 文件）')
    print('%-6s %-14s %-42s %-52s %s' % ('刀号', '结论', '红名', '期望那一格', '还原'))
    for r in rows:
        print('%-6s %-14s %-42s %-52s %s' % (r[0], r[1], r[2][:42], r[3][:52], r[4]))
    print('R238_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d 抓错格=%d RESTORE_CLEAN=%s'
          % (len(ARMS), caught, escaped, not_run, other,
             'yes' if all(r[4] == 'yes' for r in rows) else 'NO'))
    sys.exit(0 if (caught == len(ARMS) and escaped == 0 and not_run == 0 and other == 0) else 1)
