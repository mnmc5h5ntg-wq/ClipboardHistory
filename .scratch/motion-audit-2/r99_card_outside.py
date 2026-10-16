#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R99 的开场仪器：设置窗口里"哪些内容长在卡片外"，逐屏、逐带、带坐标。

为什么先量这个：BACKLOG 142 说「推荐」页把分区标题与「恢复默认」放在卡片外，
而它是一句**观感 + 一次读数**（R97 的 `CARD_BAND ... 段1 y=171.0`）。
R98 把这一屏的段边界量齐了（171.0..853.5pt），但"卡片外到底有几行、是什么"
仍然没有逐屏的账。这条仪器把那句话换成一张表：
每屏报 ①第一张卡片的顶边、②卡片顶之上还有几段墨、每段的 y 区间与左沿、
③这些段里有没有"控件"（按钮/输入框：判定用**它自己有没有填充**，不用位置猜）。

尺的三条自检（缺一条就拒绝出表）：
 S1 「快捷键」页卡片顶之上必须**只有**分区标题一行（它是"标题在卡片外"的已知正对照）；
 S2 「统计」页整带没有卡片（源码里没有 GroupBox，R97 钉成断言）⇒ 卡片顶必须报"没有"；
 S3 同一张帧连跑两次读数必须逐字相同（否则这张表不能当任何判断的证据）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/r99_card_outside.py /tmp/r98c_shots
"""
import io
import os
import re
import sys
from collections import Counter

from PIL import Image

BAND_X = (155, 715)          # 扫描带的 x 范围（pt），与 Swift 那把尺同一条
PAGE_ROWS = (4, 12)          # 页面底从窗口最上面那一条取（那里不可能有卡片）


def load(path):
    im = Image.open(path).convert("RGB")
    return im


def gray(im):
    """整帧一次转灰度（C 层），后面全部按字节索引。

    为什么不用逐像素 `getpixel`：这张表要扫 26 帧 × 1120 px × ~2000 行 = 五千万次调用，
    纯 python 要跑几十分钟。PIL 的 "L" 系数与 Swift 那把尺的 0.2126/0.7152/0.0722
    差几个单位，而这里的门槛是 60 —— 差在门槛的两百分之一，不改任何一段的归属。
    （这条"换了通道就要重看门槛"的话由 R98 的 141 负责提醒：那次是**没验过**就换。）
    """
    g = im.convert("L")
    return g.tobytes(), g.size[0]


def luma(buf, stride, x, y):
    return buf[y * stride + x]


def modal(buf, stride, x0, x1, y0, y1, step=2):
    c = Counter()
    for y in range(y0, y1, step):
        base = y * stride
        for x in range(x0, x1, step):
            c[buf[base + x] // 8] += 1
    return c.most_common(1)[0][0] * 8 + 4


def row_kinds(buf, stride, scale, page, fill, y0pt, y1pt, bx1):
    """逐行：这一行有多少比例的像素"更像卡片"、有多少个墨像素。"""
    x0, x1 = int(BAND_X[0] * scale), int(bx1 * scale)
    out = []
    for y in range(int(y0pt * scale), int(y1pt * scale)):
        base = y * stride
        cardish = 0
        ink = 0
        for x in range(x0, x1):
            l = buf[base + x]
            if abs(l - fill) < abs(l - page):
                cardish += 1
            if abs(l - fill) >= 60:
                ink += 1
        out.append((y / scale, cardish / float(x1 - x0), ink))
    return out


def bands(rows, share_gate=0.30, ink_min=8):
    """把行切成"卡片内的段"和"卡片外的段"，再在卡片外里挑出有墨的段。"""
    card = [r[1] >= share_gate for r in rows]
    segs = []
    cur = None
    for i, on in enumerate(card):
        if on and cur is None:
            cur = [i, i]
        elif not on and cur is not None:
            segs.append(tuple(cur))
            cur = None
    if cur is not None:
        segs.append(tuple(cur))
    return segs


SWIFT_BAND = re.compile(r"^CARD_BAND (\S+) (\S+) .*?卡片段=(\d+)")
# 顶边只能从 `CARD_RHYTHM … 段1/N y=<顶>..<底>pt` 拿：`CARD_BAND` 里那个数是**段数**，不是顶边。
# （第一版把段数当成顶边去对账 —— 对账本身也会拿错量，这一族已经有名字了：U-210。）
SWIFT_TOP = re.compile(r"^CARD_RHYTHM (\S+) (\S+) 段1/\d+ y=([0-9.]+)\.\.")


def swift_card_tops(log_path):
    """从捕获卷的日志里读 Swift 那把尺自己的 `CARD_BAND` 读数（顶边 = 60 + 首段第一行）。

    为什么必须有这一格（R98 / U-251）：这张仪器第一版**没有**与判据对账就出了一张表，
    而它把卡片顶量早了 14pt、把「统计」那张热图切成 11 段"卡片"（Swift 钉死的正确读数是 0 段）。
    证人必须与被告同一颗尺子（BACKLOG 104）—— 所以这张表现在**默认拒绝出表**，
    除非每一帧的卡片顶与 Swift 的读数差 ≤2pt。对不上就是仪器要修，不是产品要改。
    """
    tops, zero = {}, {}
    with io.open(log_path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            m = SWIFT_TOP.match(line)
            if m:
                tops[(m.group(1), m.group(2))] = float(m.group(3))
                continue
            b = SWIFT_BAND.match(line)
            if b:
                zero[(b.group(1), b.group(2))] = int(b.group(3))
    return tops, zero


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r98c_shots"
    log = sys.argv[2] if len(sys.argv) > 2 else "/tmp/r98_v_capture.log"
    if not os.path.exists(log):
        sys.exit("拒绝出表：没有 Swift 那把尺的读数可以对账（%s）⇒ 这张仪器的结果不能当证据" % log)
    names = sorted(f for f in os.listdir(d) if f.startswith("settings-") and f.endswith(".png"))
    if not names:
        sys.exit("没有 settings 帧：%s" % d)
    tops, zero = swift_card_tops(log)
    calibration_fail = 0
    if not tops:
        sys.exit("拒绝出表：%s 里一条 CARD_BAND 都没有 ⇒ 没有被告可以对账，这张表不能当证据" % log)
    print("目录=%s 帧数=%d 对账基准=%d 条 CARD_BAND（Swift 那把尺）" % (d, len(names), len(tops)))
    for f in names:
        path = os.path.join(d, f)
        im = load(path)
        buf, stride = gray(im)
        w, h = im.size
        # 帧名里带尺寸：`<name>-<WxH>-<tag>.png`
        parts = f[:-4].split("-")
        wh = [p for p in parts if "x" in p and p.split("x")[0].isdigit()]
        if not wh:
            continue
        wpt = float(wh[0].split("x")[0])
        fixture_name = f[:-4].replace("-" + wh[0] + "-" + ("dark" if f.endswith("-dark.png") else "light"), "")
        hpt = float(wh[0].split("x")[1])
        scale = w / wpt
        # 带子的 x 范围必须**跟着窗口收**：`settings-min` 是 640pt 宽，
        # 拿 715pt 去扫会扫到窗口外（第一版就是在这里 IndexError 的）。
        bx1 = min(BAND_X[1], wpt - 5)
        page = modal(buf, stride, int(150 * scale), int(min(710, wpt - 5) * scale),
                     int(PAGE_ROWS[0] * scale), int(PAGE_ROWS[1] * scale))
        # 填充：整带里"离页面底 >3 档"的众数档（与 Swift 的 cardFill 同思路的简化版）
        cand = Counter()
        for y in range(int(60 * scale), h):
            c = Counter()
            base = y * stride
            for x in range(int(155 * scale), int(bx1 * scale), 3):
                c[buf[base + x] // 8] += 1
            m = c.most_common(1)[0][0] * 8 + 4
            if abs(m - page) > 3:
                cand[m] += 1
        if not cand:
            # 「统计」那一屏的正确读数就是"没有卡片"（源码里没有 GroupBox，R97 钉成断言）。
            # Swift 若也报 0 段 ⇒ 两把尺一致，这一格通过；否则算 calibration_fail。
            tag = "dark" if f.endswith("-dark.png") else "light"
            if zero.get((fixture_name, tag), -1) != 0:
                print("CALIB_FAIL %s %s python=无卡片 而 Swift 报了卡片段" % (f, tag))
                calibration_fail += 1
            print("%-46s 卡片=无（整带都是页面底）" % f)
            continue
        fill = cand.most_common(1)[0][0]
        rows = row_kinds(buf, stride, scale, page, fill, 60, hpt, bx1)
        segs = bands(rows)
        if not segs:
            print("%-46s 卡片=无（没有一段连续材质）" % f)
            continue
        top = segs[0][0]
        tag = "dark" if f.endswith("-dark.png") else "light"
        swift_top = tops.get((fixture_name, tag))
        if swift_top is None:
            print("CALIB_MISS %s %s（Swift 那把尺没有这一帧的 CARD_BAND 读数 ⇒ 不对账就不出表）"
                  % (fixture_name, tag))
            calibration_fail += 1
        elif abs(swift_top - top) > 2.0:
            print("CALIB_FAIL %s %s python=%.1f Swift=%.1f ⇒ 两把尺不是同一颗，这张表不能用"
                  % (fixture_name, tag, top, swift_top))
            calibration_fail += 1
        # 卡片顶之上的墨段（= 长在卡片外的东西）
        above = [r for r in rows if r[0] < top - 0.5]
        out = []
        cur = None
        for i, r in enumerate(above):
            if r[2] >= 8:
                cur = [r[0], r[0]] if cur is None else [cur[0], r[0]]
            else:
                if cur:
                    out.append(tuple(cur))
                cur = None
        if cur:
            out.append(tuple(cur))
        print("%-46s 卡片顶=%.1fpt 段数=%d 填充=%d 页底=%d 卡片外墨段=%s"
              % (f, top, len(segs), fill, page,
                 "、".join("%.1f..%.1f" % (a, b) for a, b in out) or "无"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
