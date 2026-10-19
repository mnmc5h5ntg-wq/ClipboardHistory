#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R229 的"改前那一跑"：把本轮那一抬撤掉，用**同一批夹具、同一把尺**重跑捕获卷，留下盘上的证人。

为什么要单独跑这一遍（而不是抄台账里的旧数字）：
① 第一版台账引用过"改前 1.160:1"，但盘上那份捕获日志（`/tmp/r229_shots.log`）其实是
   **抬完之后**拍的（它打的是 `悬停药丸=232 比值=1.225`）—— 那句话没有证人，
   生成器的闸门因此当场拒绝（"改前亮档比值 1.225 并不低于地板 1.20"）；
② 正确形状不是"回到 HEAD"：HEAD 里根本没有 `row-favorite-*` 这两张夹具，回不去也量不到。
   本轮真正的反事实是**当前代码减去那一抬**，也就是变异刀 M768 的那一处替换；
③ 所以这一跑同时是两件事的证人：改前的读数（写进台账）+ "这一抬确实让判据从红变绿"的
   正对照（这一跑**必须红**，绿了说明本轮修的不是一个真问题）。

跑完逐字节还原并复核（RESTORE_CLEAN），日志与帧都落到新目录，不跨次复用。
"""
import hashlib
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
STYLE = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/PressableStyle.swift'
SHOTS = '/tmp/shots_r229pre'
LOG = '/tmp/r229_pre_lift.log'

NEEDLE = "        return isHovered ? hoverLevel + (dark ? 0 : VisualFillLift.hover) : 0"
REPL = "        return isHovered ? hoverLevel : 0"


def die(msg):
    print('PRE_LIFT_R229 refused: ' + msg)
    sys.exit(1)


path = os.path.join(ROOT, STYLE)
original = io.open(path, encoding='utf-8').read()
digest_before = hashlib.sha256(original.encode('utf-8')).hexdigest()
if original.count(NEEDLE) != 1:
    die('M768 那一处的整行锚点命中 %d 次（要 1）⇒ 反事实跑不了' % original.count(NEEDLE))

if os.path.exists(SHOTS) and os.listdir(SHOTS):
    die('帧目录已存在且非空：%s ⇒ 临时目录不许跨次复用（R91）' % SHOTS)
os.makedirs(SHOTS)

try:
    with io.open(path, 'w', encoding='utf-8') as h:
        h.write(original.replace(NEEDLE, REPL, 1))
    env = dict(os.environ, CLIPBOARD_HISTORY_UI_SHOTS=SHOTS)
    env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', 'UICaptureTests'],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
finally:
    with io.open(path, 'w', encoding='utf-8') as h:
        h.write(original)
    back = io.open(path, encoding='utf-8').read()
    if hashlib.sha256(back.encode('utf-8')).hexdigest() != digest_before:
        print('PRE_LIFT_R229 RESTORE_FAILED ⇒ 立刻停，别再跑任何东西')
        sys.exit(2)

with io.open(LOG, 'w', encoding='utf-8') as h:
    h.write(text)

readings = re.findall(r'HOVER_PILL_PROOF (light|dark) 空闲底=\d+ 空闲第二层像素=\d+ '
                      r'悬停底=\d+ 悬停药丸=(\d+) 药丸像素=(\d+) 比值=([\d.]+) 台阶=(\d+)', text)
pre = {tag: (int(grey), int(px), float(ratio)) for tag, grey, px, ratio, _step in readings}
if set(pre) != {'light', 'dark'}:
    die('这一跑没打齐两档读数 ⇒ 改前那句仍然没有证人；日志 ' + LOG)

mf = re.findall(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures?', text)
if not mf:
    die('捕获卷结论行读不到（日志 ' + LOG + '）')
# 每卷都有自己的 Executed 行，取格数最大的那条 = 整跑（和台账生成器同一口径，别在这儿发明第二种）
ran, skipped, fails = [int(x) for x in max(mf, key=lambda g: int(g[0]))]
# 正对照：这一跑**必须红**。绿了只有两种解释 —— 那一抬本来不影响任何判据，
# 或者地板根本没接上；两种都不允许本轮把 1.225 写成"修好了一个真问题"。
if fails == 0:
    die('撤掉那一抬之后捕获卷仍然全绿 ⇒ 「亮档淡到看不见」不是一条会红的病，本轮不能这么结案')

red_names = sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", text)))
print('PRE_LIFT light 悬停药丸=%d 药丸像素=%d 比值=%.3f ｜ dark 悬停药丸=%d 比值=%.3f'
      % (pre['light'][0], pre['light'][1], pre['light'][2], pre['dark'][0], pre['dark'][2]))
print('PRE_LIFT 捕获卷 Executed=%d skipped=%d failures=%d 红在=%s' % (ran, skipped, fails, ', '.join(red_names)))
print('PRE_LIFT 日志=%s 帧目录=%s PNG=%d' % (LOG, SHOTS, len([f for f in os.listdir(SHOTS) if f.endswith('.png')])))
print('PRE_LIFT RESTORE_CLEAN=yes 锚点=%s' % STYLE.split('/')[-1])
print('PRE_LIFT_OK')
