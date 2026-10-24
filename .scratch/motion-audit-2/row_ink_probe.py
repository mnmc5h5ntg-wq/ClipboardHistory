#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R337 看图腿用的一把一次性尺：同一张帧里，**列表那一行**与**详情区同一条记录**的墨量对照。

它不是门（不 exit 1、不接进电池），它只把"选中行看着是纯黑"这句形容词变成两个数。
来历：R337 回顾时逐张看已提交的帧，`content-with-history-750x560-dark.png` 里
被选中的那一行整块是黑的（BACKLOG 229 的形状），而详情区把同一条记录画得清清楚楚。
要判"是没内容"还是"内容没画出来"，得在同一张帧里拿两个区域对照 ⇒ 这一把。

规矩（写在这里免得下一次拿它当门用）：
① 区域由**这份文件自己打印**，不许在台账里手填坐标；
② 它同时打印"邻居行"的读数 —— 只有两行同一次运行、同一颗尺，差才说明东西；
③ 它**不**回答"真机上是不是这样"（那是 229/373 欠的真机眼，离屏通道判不了选中强调色）。

跑法：python3 .scratch/motion-audit-2/row_ink_probe.py [帧路径]
"""
from __future__ import annotations

import io
import os
import statistics
import sys


DEFAULT = u"/tmp/r336c_rv/frames/content-with-history-750x560-%s.png"
# 左列文字带（px，@2x）：x 从行首图标之后到列表右边界
X0, X1 = 150, 520
INK_FLOOR = 90          # ≥90 才算"有墨"（背景 28、纯黑块 0，两边都离得很远）
SIDE_DELTA = 8          # 离背景众数 ≥8 才算"有东西"，两个方向各数一次
BOXES = [(u"行1文字", 190, 380, 530, 470),
         (u"行2文字", 190, 490, 400, 575),
         (u"选中块内", 190, 794, 530, 926),
         (u"详情头", 600, 140, 1300, 200),
         (u"页面底对照", 190, 300, 530, 360)]


def both_sides(path, y0, y1, x0, x1):
    u"""同一块区域**两个方向**各数一次：比底亮的墨、比底暗的墨。

    只数"比背景亮"是 U-203 记过的那一族（暗档黑字切不出带）。这一把尺量的是
    "这一行有没有字"，而字可以是白底黑字，也可以是黑底黑字 —— 后者恰恰是问题所在，
    所以两个方向必须一起报，不许只报一个。
    """
    from PIL import Image
    im = Image.open(path).convert(u"L")
    px = im.load()
    vals = [px[x, y] for y in range(y0, y1) for x in range(x0, x1)]
    bg = statistics.mode(vals)
    light = [v for v in vals if v >= bg + SIDE_DELTA]
    dark = [v for v in vals if v <= bg - SIDE_DELTA]
    def ratio(a, b):
        def lin(v):
            c = v / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        la, lb = lin(a), lin(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
    return dict(n=len(vals), bg=bg, light=len(light), dark=len(dark),
                darkest=min(dark) if dark else None, brightest=max(light) if light else None,
                ratio_dark=ratio(min(dark), bg) if dark else 0.0,
                ratio_light=ratio(max(light), bg) if light else 0.0)


def band(profile, y0, y1):
    """返回 (带高, 中位电平的最小值, 每行墨像素的最大值, 有墨的行数)。"""
    part = [r for r in profile if y0 <= r[0] < y1]
    if not part:
        return (0, 0, 0, 0)
    return (len(part), min(r[1] for r in part), max(r[2] for r in part),
            sum(1 for r in part if r[2] > 0))


def find_dark_block(profile):
    """自动找那段"整行中位电平 ≤8"的连续带 —— 块的位置不许手填（①）。"""
    runs, cur = [], None
    for y, med, _ink in profile:
        if med <= 8:
            cur = (y, y) if cur is None else (cur[0], y)
        else:
            if cur and cur[1] - cur[0] > 40:
                runs.append(cur)
            cur = None
    if cur and cur[1] - cur[0] > 40:
        runs.append(cur)
    return runs


def main(argv):
    tiers = argv[1:] or [u"dark", u"light"]
    rc = 0
    for tier in tiers:
        path = DEFAULT % tier
        if not os.path.exists(path):
            sys.stdout.write(u"ROW_INK_NOT_RUN %s 帧不在盘上：%s\n" % (tier, path))
            rc = 2
            continue
        for name, x0, y0, x1, y1 in BOXES:
            r = both_sides(path, y0, y1, x0, x1)
            sys.stdout.write(
                u"ROW_INK %s %-8s 底=%3d 亮墨=%5d(最亮 %s, 比 %.2f:1) "
                u"暗墨=%5d(最暗 %s, 比 %.2f:1)\n"
                % (tier, name, r[u"bg"], r[u"light"], r[u"brightest"], r[u"ratio_light"],
                   r[u"dark"], r[u"darkest"], r[u"ratio_dark"]))
    sys.stdout.write(u"ROW_INK_NOTE 两个方向都报：只数「比底亮」的墨会把暗档黑字读成「没有字」"
                     u"（U-203 那一族）。这一把不判产品，也不判通道 —— 它只给数。\n")
    return rc




if __name__ == u"__main__":
    sys.exit(main(sys.argv))
