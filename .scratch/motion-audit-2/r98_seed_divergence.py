#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R98 / BACKLOG 141：同一份夹具声明，两套测试各拍出什么。

R97 记下的那句话是"两条读图通道给出不同的卡片边界"（TIFF 回路 vs python 直接解 PNG）。
R98 的第一条读数把它**证伪**了：同一张帧，两条通道逐段一致（`CARD_CHANNEL_SUMMARY 不一致=0`）。
真正不一致的是**两张不同的文件** —— 卡片节奏那条判据自己重渲染的 `settings-privacy-excluded`
与捕获卷交付的那一张，字节不同（319980 vs 333059），而 settings 族其余 9 对逐字节相同。

这个脚本只问一件事：**差在哪一段像素上**。
不猜机制，先把分歧的位置量出来，再拿位置去对夹具声明里唯一一处特殊的东西（`seed:`）。

输出两条读数：
 D1 逐行"该像素与页面底/卡片填充的距离"指纹，找出**第一处分歧的行**与分歧行的分布；
 D2 分歧带里两边的"墨行数"——如果一边有字一边没字，就是内容不同；
     如果两边都有字但字不一样，也是内容不同。两种都指向夹具没被同一份数据喂饱。
自检：两帧尺寸必须一致（不一致就先报"不是同一种帧"，别把尺寸差当成分歧）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode
from r92_data_visual import dist, px

CAP = "/tmp/r97_shots"
RHY = "/tmp/r98_scratch"


def load(path):
    w, h, ch, rows = decode(path)
    return {"w": w, "h": h, "ch": ch, "rows": rows, "path": path}


def row_fingerprint(img, x0, x1):
    """每行一个数：该行里"离页面底最远"的那个像素的距离（只看带宽内）。"""
    rows, ch = img["rows"], img["ch"]
    page = median_page(img, x0, x1)
    out = []
    for y in range(0, img["h"]):
        best = 0
        for x in range(x0, x1, 2):
            best = max(best, dist(px(rows, ch, x, y), page))
        out.append(best)
    return out, page


def median_page(img, x0, x1):
    """页面底 = 窗口最上面那一条的众数（与 Swift 判据取法一致：那里不可能有卡片）。"""
    from collections import Counter
    c = Counter()
    for y in range(int(4 * img["h"] / 1040.0), int(12 * img["h"] / 1040.0)):
        for x in range(x0, x1, 3):
            c[px(img["rows"], img["ch"], x, y)] += 1
    return c.most_common(1)[0][0]


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else \
        "settings-privacy-excluded-720x1040-light.png"
    a = load(os.path.join(RHY, name))
    b = load(os.path.join(CAP, name))
    print("D0 尺寸 本用例=%dx%d 捕获卷=%dx%d" % (a["w"], a["h"], b["w"], b["h"]))
    if (a["w"], a["h"]) != (b["w"], b["h"]):
        print("D0 不是同一种帧 ⇒ 后面的逐行比较没有对象")
        return 2
    scale = a["w"] / 720.0
    x0, x1 = int(155 * scale), int(715 * scale)
    fa, page_a = row_fingerprint(a, x0, x1)
    fb, page_b = row_fingerprint(b, x0, x1)
    print("D0 页面底 本用例=%s 捕获卷=%s" % (page_a, page_b))
    diff = [y for y in range(a["h"]) if fa[y] != fb[y]]
    print("D1 逐行指纹不同的行数=%d / %d" % (len(diff), a["h"]))
    if not diff:
        print("D1 两帧在带宽内逐行指纹**完全一致** ⇒ 分歧在颜色不在几何，见 D3")
    else:
        # 分歧行切成带
        bands = []
        start = prev = diff[0]
        for y in diff[1:]:
            if y > prev + 8:
                bands.append((start, prev))
                start = y
            prev = y
        bands.append((start, prev))
        print("D1 分歧带（pt）：%s" %
              ", ".join("%.1f..%.1f" % (s / scale, (e + 1) / scale) for s, e in bands[:12]))
        print("D1 第一处分歧在 %.1fpt，最大带 %dpx" %
              (diff[0] / scale, max(e - s for s, e in bands)))
        print("D2 每条带的墨行数（≥120 距离算墨）：")
        for s, e in bands[:12]:
            ia = sum(1 for y in range(s, e + 1) if fa[y] >= 120)
            ib = sum(1 for y in range(s, e + 1) if fb[y] >= 120)
            print("   %.1f..%.1fpt  本用例=%d 捕获卷=%d  %s" %
                  (s / scale, (e + 1) / scale, ia, ib,
                   "一边有字一边没字 ⇒ 内容不同" if (ia == 0) != (ib == 0) else
                   "两边都有字 ⇒ 字的种类/数量不同"))
    # D3：逐像素不同的总数量与位置（不看几何，看颜色）
    n = 0
    first = None
    for y in range(a["h"]):
        for x in range(x0, x1):
            if px(a["rows"], a["ch"], x, y) != px(b["rows"], b["ch"], x, y):
                n += 1
                if first is None:
                    first = (x, y)
    print("D3 带宽内逐像素不同=%d 第一处=(%.1f, %.1f)pt"
          % (n, (first[0] / scale if first else -1), (first[1] / scale if first else -1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
