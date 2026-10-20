#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R241 的变异表（BACKLOG 273）：三把刀分别摘掉「两个口径会分开」「门槛真生效」「缺正对照要红」。

为什么这轮必须有三把刀：本轮改动**只有一支新判据卷**（`scripts/tests/test_hover_two_state_diff.py`），
它绿着跑完 16 格不说明任何事 —— 16 格可能全在量同一件事，也可能闸门是恒绿的摆设。
三把刀各摘掉一个声称：
  - M795 把逐通道门槛 `DELTA = 4` 抬到 100 ⇒ 合成帧里 80−30=50 的差就"没变"了。
    这一刀问的是：**门槛真在承重吗**（不承重的话"变化像素"只是个装饰计数）。
  - M796 把 `per_pixel` 的取值域从变化像素改成全体像素 ⇒ 稀释吞进控件局部口径。
    这一刀问的是 R239 那次差点改错产品的那句话：**两个口径是不是真的分得开**。
  - M797 把「没给 `--control`」那一支的 `rc = 1` 摘掉 ⇒ 尺会在没有参照的情况下宣布"可分辨"。
    这一刀问的是闸门：**它是闸门还是一行 print**。

needle 整行/整串字面、命中恰好一次（M796 的第一版就是被这条断言拦住的：`for n in changed]` 命中 3 次）；
跑完逐字节还原并复核。基线臂不可信 ⇒ 拒绝出表（exit 1）。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
RULER = 'scripts/hover_two_state_diff.py'
MODULE = 'scripts.tests.test_hover_two_state_diff'

ARMS = [
    ('M795', u'把逐通道门槛从 4 抬到 100（合成帧里 80−30=50 的差就"没变"）', RULER,
     'DELTA = 4',
     'DELTA = 100',
     'test_a_fully_changed_band_makes_the_two_estimators_agree'),
    ('M796', u'把 per_pixel 的取值域从变化像素换成全体像素（稀释吞掉控件局部口径）', RULER,
     'sum(pb[n]) / 3.0) for n in changed]',
     'sum(pb[n]) / 3.0) for n in range(len(pa))]',
     'test_unchanged_pixels_dilute_band_mean_but_not_per_pixel'),
    ('M797', u'摘掉「没给 --control」那一支的 rc = 1（闸门退化成一行 print）', RULER,
     "        rc = 1\n    else:\n        a, b = args.control.split(',', 1)",
     "        pass\n    else:\n        a, b = args.control.split(',', 1)",
     'test_missing_positive_control_cannot_announce_resolvability'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, s):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(s)


def run_guard():
    """跑整支判据卷，再从 -v 输出里点名**那一格**是不是 FAIL（只认退出码会把别的格算成本刀的结论）。"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    env.pop('CLIPBOARD_HISTORY_UI_SHOTS', None)      # 表在两台上都要同形：真帧那一格走有名字的 skip
    proc = subprocess.run([sys.executable, '-m', 'unittest', '-v', MODULE],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode('utf-8', 'replace')


def red_names(out):
    names = set(re.findall(r'^FAIL: (\S+)', out, re.M))
    names |= set(re.findall(r'^(\S+).* \.\.\. FAIL', out, re.M))
    return sorted(n for n in names if n.startswith('test_'))


base = run_guard()
io.open('/tmp/r241_mutate_base.log', 'w', encoding='utf-8').write(base)
base_reds = red_names(base)
if 'Ran ' not in base or not base.rstrip().splitlines()[-1].startswith('OK') or base_reds:
    print('R241_MUTATE_REFUSED 基线臂不可信 ran=%s 结尾OK=%s 红名=%s'
          % ('Ran ' in base, base.rstrip().splitlines()[-1].startswith('OK'), ','.join(base_reds) or '无'))
    sys.exit(1)

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
    io.open('/tmp/r241_%s.log' % mid, 'w', encoding='utf-8').write(out)
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

print('R241 变异表（对象=尺自己，产品 0 文件）')
print('%-6s %-14s %-46s %-56s %s' % ('刀号', '结论', '红名', '期望那一格', '还原'))
for r in rows:
    print('%-6s %-14s %-46s %-56s %s' % (r[0], r[1], r[2][:46], r[3][:56], r[4]))
print('R241_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d 抓错格=%d RESTORE_CLEAN=%s'
      % (len(ARMS), caught, escaped, not_run, other,
         'yes' if all(r[4] == 'yes' for r in rows) else 'NO'))
sys.exit(0 if (caught == len(ARMS) and escaped == 0 and not_run == 0 and other == 0) else 1)
