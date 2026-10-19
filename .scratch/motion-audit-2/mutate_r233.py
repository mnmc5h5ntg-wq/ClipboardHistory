#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R233 变异刀：纯文本那一格的期望是不是**真的**由那张按机器表推导（BACKLOG 253 的接续）。

形状：本轮没有产品改动，被审的是判据侧新加的三样东西 ——
① `plain_expectation_from_row` 里 `问题 = hard + not_run` 那条推导；
② 同一函数里「引用了盲区探针的关系不该打规则行」那条推导；
③ `parse_plain_profile` 里「尺自陈的 问题= 必须等于它自己点名的（没对象 + 真红）」那道闸门。
每一把都退回 259 之前那一版的病（把本机的能力当另一台机器的地板 / 让缺席冒充结论 /
让计数与名单各说各话），红了才算这一族契约是载荷的。

刀号接 R232 的 M779 / M780 ⇒ M781 / M782 / M783（全局唯一；已在台账与全部 mutate_r*.py 里查重）。
字节码缓存教训（R154）：整卷在 `PYTHONDONTWRITEBYTECODE=1` 下跑，且替换串长度故意不同。
"""
import os
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
TESTS = os.path.join(ROOT, 'scripts', 'tests')
TGT = os.path.join(TESTS, 'test_surface_left_axes.py')

# 跑整卷（不只新格）：RealFrameTests 要帧、PlainContractTests 要契约、CiExitTests 是对面那一半
CMD = [sys.executable, '-m', 'unittest', 'test_surface_left_axes']
ENVS = dict(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
            CLIPBOARD_HISTORY_UI_SHOTS='/tmp/shots_r232')

# (刀号, 文件, 锚点【必须恰好命中一次】, 替换成【退回的形状】, 这一刀要证的病)
KNIVES = [
    ('M781', TGT,
     "want_problems = row[u'hard'] + row[u'not_run']",
     "want_problems = row[u'hard']  # 刀",
     '把"尺没有对象"从 问题= 里摘掉 ⇒ 等于对 runner 说四条盲区没问题（259 之前那一版的病）'),
    ('M782', TGT,
     'if not (set(probes) & set(blind))',
     'if (set(probes) & set(blind))',
     '规则行推导反号 ⇒ 本机要求"只有盲区探针才打行"、runner 要求"一条都不打"，两侧都该红'),
    ('M783', TGT,
     'if problems != len(blind) + len(hard):',
     'if problems != len(blind):  # 刀',
     '闸门少算真红那一侧 ⇒ 尺自陈计数与名单矛盾时不再响，"数一个说谎的数"会被读成通过'),
]


def read(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)


def run_roll(log):
    env = dict(os.environ)
    env.update(ENVS)
    with open(log, 'w', encoding='utf-8') as fh:
        proc = subprocess.run(CMD, cwd=TESTS, env=env,
                              stdout=fh, stderr=subprocess.STDOUT)
    return proc.returncode


ORIG = {p: read(p) for _, p, _, _, _ in KNIVES}
base_rc = run_roll('/tmp/r233_mutate_base.log')
if base_rc != 0:
    print('R233_MUTATE 基线就红 ⇒ 先修判据再下刀（不许在红树上记 CAUGHT）')
    sys.exit(1)

caught = escaped = not_run = 0
for kid, path, anchor, repl, why in KNIVES:
    original = read(path)
    hits = original.count(anchor)
    if hits != 1:
        print('%s NOT_RUN 锚点命中 %d 次（要恰好 1 次）｜%s' % (kid, hits, why))
        not_run += 1
        continue
    log = '/tmp/r233_mutate_%s.log' % kid
    write(path, original.replace(anchor, repl, 1))
    try:
        rc = run_roll(log)
    finally:
        write(path, original)
    restored = read(path) == original
    names, skipped = [], 0
    with open(log, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('FAIL:'):
                names.append(line.split('(')[-1].split(')')[0] if '(' in line else line.strip())
            if line.startswith('ERROR:'):
                names.append('ERROR ' + line.split('(')[-1].split(')')[0] if '(' in line else line.strip())
            if 'skipped' in line and ('FAIL:' not in line):
                skipped += 1
    if rc != 0 and names:
        caught += 1
        print('%s CAUGHT ｜ %s ｜ 红在：%s' % (kid, why, '、'.join(sorted(set(names)))))
    elif rc != 0:
        # 崩栈不是结论（R209/R212 那一族）：rc≠0 但一整卷没打出任何 `FAIL:`/`ERROR:` 行，
        # 说明这刀把文件弄到**导入不了**（语法错、收集期异常），它没有给任何一条判据作证。
        # 记成 NOT_RUN 并让整支出非 0 ⇒ 刀坏了就修刀，不许把"进程红了"抄成"判据红了"。
        not_run += 1
        print('%s NOT_RUN ⇒ rc=%d 但红没有名字（崩栈/收集错误不是证人，修刀）｜%s' % (kid, rc, why))
    else:
        escaped += 1
        print('%s ESCAPED ⇒ rc=%d（绿或 skip 都算逃）｜%s' % (kid, rc, why))
    if not restored:
        print('%s RESTORE_FAILED ⇒ 树是脏的，后面的读数都不算' % kid)
        sys.exit(1)

dirty = [p for p, text in ORIG.items() if read(p) != text]
clean = not dirty
print('R233_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d'
      % (len(KNIVES), caught, escaped, not_run))
print('RESTORE_CLEAN=%s%s' % ('yes' if clean else 'no', '' if clean else ' ｜还脏着：' + '、'.join(dirty)))
sys.exit(0 if (escaped == 0 and not_run == 0 and caught == len(KNIVES) and clean) else 1)
