#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R96 视觉腿：设置「隐私」分区，逐元素重判。

为什么是这一屏：阶段二的范围是"设置窗口每一个分区每一种控件"，而这一屏是
**唯一一屏同时有三种控件语法**的地方 —— 勾选框（五颗）、一列只读文本（默认排除名单）、
输入框 + 添加/移除按钮。R92 判过「数据」、R95 判过「快捷键」，这一屏还没被逐元素量过
（R35 只量了说明段的墨档，R13 只量了那颗"移除"按钮的按压档）。

三条读数：
 T1 五颗勾选框的**填充是否同一档**，以及"勾上"这件事在帧里到底改变了多少颗像素 ——
    如果勾上/不勾的差别只有一枚对勾，那两态的可辨性就等于那枚对勾的对比度。
 T2 勾上的那颗是**灰**的还是**强调蓝**的（色度 chroma）。系统复选框勾上应该是强调色。
    这一条只报读数不下结论：源码里这五颗都是裸 `Toggle`（没有任何自定义 toggleStyle），
    所以"灰"要么是非 key 窗口的系统画法、要么是通道伪影 —— **两种都不是产品选的颜色**，
    要判它得靠真机（已开 BACKLOG 139）。
 T3 默认排除那一列：左轴散布、行距、说明档对比度。

尺全部借 R92 / R95 那一支（`r92_data_visual`）。自检：T1 必须正好检出 5 颗框，
少一颗就是尺没压住（R95 在一颗借来的尺上已经犯过两次这个）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode
from r92_data_visual import (BG_TOL, boxes, chroma, column_split, dist, ink_of,
                             median_color_in, px, ratio)


def load(path):
    w, h, ch, rows = decode(path)
    return rows, ch, w, h


def row_bands(rows, ch, x0, x1, y0, y1, bg, gate=60, gap=6):
    """[y0,y1) 里有墨的行分成带（返回 (起, 止) 像素区间）。"""
    hits = [y for y in range(y0, y1)
            if any(dist(px(rows, ch, x, y), bg) >= gate for x in range(x0, x1))]
    bands, cur = [], []
    for y in hits:
        if cur and y - cur[-1] > gap:
            bands.append((cur[0], cur[-1]))
            cur = []
        cur.append(y)
    if cur:
        bands.append((cur[0], cur[-1]))
    return bands


def scan(shots, frame, label, lines):
    path = os.path.join(shots, frame)
    if not os.path.exists(path):
        lines.append('  %s NO-FRAME %s' % (label, frame))
        return
    rows, ch, w, h = load(path)
    m = re.search(r'-(\d+)x(\d+)-', frame)
    if not m:
        raise SystemExit('帧名里没有 WxH ⇒ 尺寸没有出处，别用猜的 scale')
    s = w / float(m.group(1))
    split = column_split(rows, ch, w, h)          # 像素
    page = median_color_in(rows, ch, split + 40, w - 40, 8, 40)
    cards = [b for b in boxes(rows, ch, split, w - 2, 0, h - 1, page)
             if (b[1] - b[0]) / s > 120 and (b[3] - b[2]) / s > 60]
    lines.append('  %s 尺寸=%dx%dpx(scale=%.3g) 页面底=%s 卡片=%d 张'
                 % (label, w, h, s, page, len(cards)))
    if not cards:
        raise SystemExit('一张卡片都没检出 ⇒ 尺没压住这一屏，读数作废')
    cx0, cx1, cy0, cy1 = max(cards, key=lambda b: b[1] - b[0])
    fill = median_color_in(rows, ch, cx0 + 6, cx1 - 6, cy0 + 6, cy0 + 40)
    lines.append('    卡片#1 框=(%.0f,%.0f)..(%.0f,%.0f)pt 填充=%s 对页面底对比=%.3f'
                 % (cx0 / s, cy0 / s, cx1 / s, cy1 / s, fill, ratio(fill, page)))
    # T1/T2：勾选框那一列（卡片左沿往里 8..30pt）
    box_x0, box_x1 = cx0 + int(8 * s), cx0 + int(30 * s)
    # 找框不能用"墨"的门槛（60）：那颗框自己的填充离卡片只有 24，
    # 于是未勾的框**整颗都不算墨**，只数得到边框上那十来颗深色像素 ——
    # 第一版因此只检出 3 颗（应有 5 颗），而"少检出的两颗"和"这一屏只有三颗框"
    # 在同一张报表上长得一模一样（R92 那一课，第三次）。改成按"离卡片填充够远"找带。
    bands = row_bands(rows, ch, box_x0, box_x1, cy0, cy1, fill, gate=15)
    boxes_found = []
    for (by0, by1) in bands:
        if (by1 - by0) / s < 10:
            continue
        bfill = median_color_in(rows, ch, box_x0 + 2, box_x1 - 2, by0 + 2, by1 - 2)
        # 真正的框有**自己的填充**（223 / 213，离卡片 247 有 24/34），而标题文字那两段的
        # "填充"就是卡片本身。用这一条把它们分开 —— 不是"我数到 7 颗，改成只取前 5 颗"，
        # 那等于拿期望值当判据。
        if dist(bfill, fill) < 8:
            continue
        ink, n, cr = ink_of(rows, ch, box_x0, box_x1, by0, by1, bfill)
        boxes_found.append((by0, by1, bfill, ink, n, cr))
    fills = set(b[2] for b in boxes_found)
    lines.append('    T1 勾选框检出 %d 颗（这一屏应有 5 颗：4 未勾 + 1 已勾）'
                 % len(boxes_found))
    for (by0, by1, bfill, ink, n, cr) in boxes_found:
        lines.append('      框 y=%.0f..%.0fpt 填充=%s 色度=%d 墨=%s 颗=%d 对填充对比=%.2f'
                     % (by0 / s, by1 / s, bfill, chroma(bfill), ink, n, cr))
    if len(boxes_found) != 5:
        lines.append('      SELF-CHECK FAIL 框数=%d ⇒ 尺没压住，本轮勾选那组读数不判'
                     % len(boxes_found))
    else:
        lines.append('      SELF-CHECK OK 填充档数=%d（>1 就说明勾上时框自己变了色）'
                     % len(fills))
    # T3：默认排除那一列（说明档）
    lefts, pitches, contrasts = [], [], []
    text_bands = row_bands(rows, ch, cx0 + int(5 * s), cx1 - int(5 * s), cy0, cy1, fill)
    prev = None
    for (by0, by1) in text_bands:
        if (by1 - by0) / s < 6 or (by1 - by0) / s > 20:
            continue
        xs = [x for y in range(by0, by1) for x in range(cx0, cx1)
              if dist(px(rows, ch, x, y), fill) >= 60]
        if not xs:
            continue
        lefts.append(min(xs))
        ink, n, cr = ink_of(rows, ch, min(xs), max(xs), by0, by1, fill)
        contrasts.append(cr)
        if prev is not None:
            pitches.append((by0 - prev) / s)
        prev = by1
    if lefts:
        lines.append('    T3 文字带 %d 段：左沿 min=%.1f 众数=%.1f 最大=%.1fpt；'
                     '行距中位=%.1fpt；对比 min=%.2f max=%.2f'
                     % (len(lefts), min(lefts) / s,
                        sorted(lefts)[len(lefts) // 2] / s, max(lefts) / s,
                        sorted(pitches)[len(pitches) // 2] if pitches else -1,
                        min(contrasts), max(contrasts)))


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r96_shots'
    lines = []
    for theme in ('light', 'dark'):
        lines.append('== 主题 %s' % theme)
        scan(shots, 'settings-privacy-720x540-%s.png' % theme, '隐私', lines)
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
