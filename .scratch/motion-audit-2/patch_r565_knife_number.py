#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R565 补正笔第三格：把「M1468 是空刀 / 下一轮从 M1468 起」这一族互斥说法改齐。

形状（现读名册为准）：
- `mutate_needle_precheck.py` 的 TABLES 里 r565 那一批是 **M1466/M1467/M1468/M1469 四把真刀**（全 CAUGHT），
  现读最高号 = **M1469** ⇒ 下一轮从 M1470 起。
- 那把试完就撤的空刀**从来没占过号**：它的草稿临时借过 `mutate_r565_m1468.py` 这个名字，
  而同一轮 B 笔把 M1468 登记成了路径卫生守卫的真刀（`020cef3`）⇒ 借用的号作废。
- 台账笔写 U-2443 / D-565 ③ / CHANGELOG / ITERATION / STATE 补记 ④ 的时候 B 笔**早已落盘**，
  却照抄了 A 笔草稿的措辞 ⇒ 同一轮里两处互斥地说 M1468（第三次犯，与 R563 的 636、R564 的读单同族）。

这是**改账、不是改门**：没撤判据、没降地板、没改期望、没加豁免，也没有新增/删除任何一把刀。
'''
import io
import sys


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, t):
    io.open(p, 'w', encoding='utf-8').write(t)


def once(t, old, new, label):
    if t.count(old) != 1:
        sys.stderr.write('ANCHOR_BAD %s 命中=%d\n' % (label, t.count(old)))
        sys.exit(1)
    if t.count(new) == 1 and old not in t:
        sys.stderr.write('ALREADY_PATCHED %s\n' % label)
        sys.exit(1)
    return t.replace(old, new, 1)


EMPTY_NEW = '''**一把空刀试落即撤、不登记、不占号**（它的草稿临时借过 `mutate_r565_m1468` 这个名字，而同一轮 B 笔把 M1468 登记成了下面那支路径卫生守卫的真刀 ⇒ 借用的号作废，这一格由补正笔改齐）：把"字芯"从偏差前 5% 改成**全部偏差像素** ⇒ 读数 6.01/9.16:1 仍 ≥4.5 ⇒ 判据 PASSED ⇒ 按 R560/R562 的规矩那是**空刀**（变化量没出得了判据自己的容差），撤掉并照实写。四张表登记进 `mutate_needle_precheck.TABLES`（M1466/M1467/M1468/M1469，现读最高 M1469 ⇒ **下一轮从 M1470 起**）。'''

CHECK = '--check' in sys.argv
n = 0

# ---- AGENT_UI_AUDIT.md：U-2443 那一格 ----
p = 'AGENT_UI_AUDIT.md'
t = rd(p)
t = once(t, '''**M1468 试落即撤、不登记、不占号**：把"字芯"从偏差前 5% 改成**全部偏差像素** ⇒ 读数 6.01/9.16:1 仍 ≥4.5 ⇒ 判据 PASSED ⇒ 按 R560/R562 的规矩那是**空刀**（变化量没出得了判据自己的容差），撤掉并照实写 ⇒ **下一轮仍从 M1468 起**（现读已登记最高 M1467）。两张表已登记进 `mutate_needle_precheck.TABLES`。''',
         EMPTY_NEW, 'ui-empty-knife')
if not CHECK:
    wr(p, t)
n += 1

# ---- AGENT_DECISIONS.md：D-565 ③ ----
p = 'AGENT_DECISIONS.md'
t = rd(p)
t = once(t, '''③ **空刀不占号。** M1468（把字芯从"偏差前 5%"改成"全部偏差像素"）落下去判据仍 PASSED ⇒ 撤掉、不登记、写进账，下一轮仍从 M1468 起。''',
         '''③ **空刀不占号 —— 也不许借号。** 那把空刀（把字芯从"偏差前 5%"改成"全部偏差像素"）落下去判据仍 PASSED ⇒ 撤掉、不登记、写进账；它的草稿临时借过 M1468 这个名字，而同一轮 B 笔把 **M1468/M1469 登记成了路径卫生守卫的两把真刀** ⇒ 借用的号作废，账里不能再写「下一轮从 M1468 起」。现读名册最高 **M1469** ⇒ 下一轮从 **M1470** 起。''',
         'dec-empty-knife')
if not CHECK:
    wr(p, t)
n += 1

# ---- CHANGELOG.md ----
p = 'CHANGELOG.md'
t = rd(p)
t = once(t, '''M1468 试落即撤 —— 把字芯从"偏差前 5%"改成"全部偏差像素"后读数 6.01/9.16 仍过地板 ⇒ 空刀，不登记不占号，下一轮仍从 M1468 起。''',
         '''那把空刀试落即撤（草稿临时借过 M1468 这个名字，随后被 B 笔的刀 M1468 用掉 ⇒ 借用作废）：把字芯从"偏差前 5%"改成"全部偏差像素"后读数 6.01/9.16 仍过地板 ⇒ 判据 PASSED ⇒ 不登记、不占号；名册现读最高 M1469 ⇒ 下一轮从 M1470 起。''',
         'changelog-empty-knife')
if not CHECK:
    wr(p, t)
n += 1

# ---- AGENT_VISUAL_ITERATION.md：正文 + 七维表 ----
p = 'AGENT_VISUAL_ITERATION.md'
t = rd(p)
t = once(t, '''一把试完就撤（M1468 把字芯从"偏差前 5%"改成"全部偏差像素"，读数 6.01/9.16 仍过地板 ⇒ 判据 PASSED ⇒ 空刀，不登记不占号）。''',
         '''一把试完就撤（把字芯从"偏差前 5%"改成"全部偏差像素"，读数 6.01/9.16 仍过地板 ⇒ 判据 PASSED ⇒ 空刀，不登记不占号 —— 它草稿借过的 M1468 已被同一轮 B 笔的真刀用掉 ⇒ 借用的号作废，名册现读最高 M1469）。''',
         'iter-body-empty-knife')
t = once(t, '''空刀 M1468 试完就撤、不登记不占号；''',
         '''空刀试完就撤、不登记不占号（草稿借过的 M1468 由同一轮 B 笔用掉 ⇒ 借用作废，这一格是补正笔改齐的）；''',
         'iter-dim-empty-knife')
if not CHECK:
    wr(p, t)
n += 1

# ---- AGENT_STATE.md：补记 ④ 与 ⑥④ ----
p = 'AGENT_STATE.md'
t = rd(p)
t = once(t, '''刀号 **M1468 起且未使用**（现读最高 M1467；M1468 试落即撤 ⇒ 不占号）''',
         '''刀号现读最高 **M1469**（M1466-M1469 四把都已登记且 CAUGHT；从前这一格写「M1468 起且未使用」抄的是 A 笔草稿的临时借号，而 B 笔早已把 M1468/M1469 登记成真刀 ⇒ 由补正笔改齐，R566 从 **M1470** 起）''',
         'state-addendum-4-knife')
t = once(t, '''④ **M1468 是空刀**：把"字芯"从偏差前 5% 改成全部偏差像素，读数 6.01/9.16:1 仍过 4.5 地板 ⇒ 判据 PASSED ⇒ 撤掉、不登记、不占号（与 R560 的 M1455、R562 的两把同族）。''',
         '''④ **一把空刀试完就撤**（把"字芯"从偏差前 5% 改成全部偏差像素，读数 6.01/9.16:1 仍过 4.5 地板 ⇒ 判据 PASSED ⇒ 撤掉、不登记、不占号；与 R560 的 M1455、R562 的两把同族）。**账从前把它写成「M1468 是空刀」是同一轮里第三处互斥说法** —— 它的草稿临时借过 M1468 这个名字，而 B 笔 `020cef3` 早已把 M1468/M1469 登记成路径卫生守卫的两把真刀（名册现读最高 M1469 ⇒ R566 从 M1470 起）；台账笔抄了 A 笔的措辞、没跟同一轮已落盘的 B 笔交叉核对 ⇒ 本补正笔改齐（改账不改门）。⑦ **这一族第三次犯的机械形状**：改账的时机都是「补记/台账笔沿用前一笔的草稿措辞」，而同一轮里已经有一笔把那个号用掉了 —— 下一次落刀之前先 `grep` 一遍名册，别信自己上一笔写的「未使用」。''',
         'state-selfinjury-4-knife')
if not CHECK:
    wr(p, t)
n += 1

print('KNIFE_NUMBER_CORRECTION books=%d check=%d' % (n, 1 if CHECK else 0))
