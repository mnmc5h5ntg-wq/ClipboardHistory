#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R230 的"改前那一读"：用**与仓库那颗尺同一个算法**重读盘上留下的改前帧。

为什么不重建一次改前的产品：改前 = 玻璃圆那一层自绘且夹在 `.compositingGroup()` 里、
段按钮两层叠加、样式那一层还带着 R229 留下的 0.025 幽灵层。把这三处照抄回去的一次构建，
只要有一处没抄准，台账里的"改前"就成了假话 —— 而本轮要的不是一个历史数值，
是"同一档墨在两条画法下读得出差别"这一句，它有更干净的形状：**同名义值、同一片底、两态对照**。

两组证人各自来自哪一次捕获（都留在盘上，路径写在输出里）：
① `SHOTS_B`（`/tmp/shots_r230b`，玻璃圆仍自绘、且那一档**已经**按 R230 抬到 0.105）：
   亮档必须**低于**地板 1.20，暗档必须**不低于** 1.10
   ⇒ 同一名义值、同一片底，画法不同就差 0.045 比值；HEAD 那一版还没抬（0.08），
     而比值随 alpha 单调 ⇒ 0.08 在组内只会比 1.175 更淡（这一句是**推论**，不是读数）。
② `SHOTS_A`（`/tmp/shots_r230`，样式那一层还没让位）：
   亮档**选中那一段**空闲与悬停两帧的众数必须**不相等**（幽灵层被画上了），
   暗档那一段必须相等 ⇒ 幽灵只长在亮档，成因就是那一抬，不是别的东西。
"""
import os
import sys
from collections import Counter

SHOTS_A = '/tmp/shots_r230'    # 幽灵层在场
SHOTS_B = '/tmp/shots_r230b'   # 玻璃圆那一层还在 compositingGroup 里
FLOOR = {'light': 1.20, 'dark': 1.10}
# 与 UICaptureHarness 的 segmentRectLeft / segmentRectRight / circleColumnRect 一一对应。
SEG_L, SEG_R = (8, 35, 92, 57), (108, 35, 192, 57)
CIRCLE = (38, 40, 82, 225)


def channel(v):
    c = v / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def contrast_ratio(a, b):
    la, lb = channel(a) + 0.05, channel(b) + 0.05
    return max(la, lb) / min(la, lb)


def band_modal(px, rect, scale, w, h):
    x0, y0, x1, y1 = rect
    x0, x1 = max(0, int(round(x0 * scale))), min(w, int(round(x1 * scale)))
    y0, y1 = max(0, int(round(y0 * scale))), min(h, int(round(y1 * scale)))
    if x1 <= x0 or y1 <= y0:
        return -1, 0
    hist = Counter(int(round(0.2126 * px[x, y][0] + 0.7152 * px[x, y][1] + 0.0722 * px[x, y][2]))
                   for y in range(y0, y1) for x in range(x0, x1))
    grey, cnt = max(hist.items(), key=lambda kv: kv[1])
    return grey, cnt


def read_pair(shots, label, pt_w, idle_pat, hov_pat, rect, tag):
    from PIL import Image
    fp, gp = os.path.join(shots, idle_pat % tag), os.path.join(shots, hov_pat % tag)
    if not (os.path.exists(fp) and os.path.exists(gp)):
        return None, '%s %s NOT-RUN 缺帧 %s / %s' % (label, tag, fp, gp)
    a, b = Image.open(fp).convert('RGB'), Image.open(gp).convert('RGB')
    if a.size != b.size:
        return None, '%s %s 两态尺寸不一致（%s vs %s）⇒ 不是同一块' % (label, tag, a.size, b.size)
    scale = a.size[0] / float(pt_w)
    ig, _ = band_modal(a.load(), rect, scale, a.size[0], a.size[1])
    hg, hc = band_modal(b.load(), rect, scale, a.size[0], a.size[1])
    line = ('%s %s 空闲=%d 悬停=%d 比值=%.3f 像素=%d 地板=%.2f'
            % (label, tag, ig, hg, contrast_ratio(ig, hg), hc, FLOOR[tag]))
    return (ig, hg, contrast_ratio(ig, hg), hc), line


def main():
    for d in (SHOTS_A, SHOTS_B):
        if not os.path.isdir(d) or not [f for f in os.listdir(d) if f.endswith('.png')]:
            print('PRE_READ_R230 NOT-RUN：%s 没有帧 ⇒ /tmp 会被清，空对账不许读成"改前没问题"' % d)
            return 3
    fails = []
    G = ('玻璃圆(组内自绘·已抬一档)', 120, 'glass-pill-states-120x232-%s.png',
         'glass-pill-hover-120x232-%s.png', CIRCLE)
    S = ('段按钮(样式那一层未让位)', 200, 'segmented-filter-idle-200x60-%s.png',
         'segmented-filter-hover-200x60-%s.png', None)
    for tag in ('light', 'dark'):
        label, pt_w, ip, hp, rect = G
        res, line = read_pair(SHOTS_B, label, pt_w, ip, hp, rect, tag)
        if res is None:
            fails.append(line)
            print('PRE_READ ' + line)
            continue
        print('PRE_READ %s ⇒ %s' % (line, 'BELOW_FLOOR' if res[2] < FLOOR[tag] else 'AT_OR_ABOVE'))
        if tag == 'light' and res[2] >= FLOOR[tag]:
            fails.append('玻璃圆亮档在组内也已经过线 ⇒ 「画法把这档画淡了」这句话没有证人')
        if tag == 'dark' and res[2] < FLOOR[tag]:
            fails.append('玻璃圆暗档不过线 ⇒ 暗档也得改，本轮"暗档一字未动"是假话')
        label, pt_w, ip, hp, _ = S
        for rect_i, name, is_selected in ((SEG_L, '选中段', True), (SEG_R, '未选中段', False)):
            res2, line2 = read_pair(SHOTS_A, label + ' ' + name, pt_w, ip, hp, rect_i, tag)
            if res2 is None:
                fails.append(line2)
                print('PRE_READ ' + line2)
                continue
            changed = res2[0] != res2[1]
            print('PRE_READ %s ⇒ %s' % (line2,
                  (('GHOST' if changed else 'CLEAN') if is_selected
                   else ('CHANGED' if changed else 'NO_LAYER'))))
            if is_selected:   # 选中段：亮档该有幽灵、暗档不该
                if tag == 'light' and not changed:
                    fails.append('亮档选中段没有幽灵层 ⇒ `level == 0` 那一格本轮没有证人')
                if tag == 'dark' and changed:
                    fails.append('暗档选中段也被改了 ⇒ 成因不是那一抬，得另找')
    print('PRE_READ_R230 证人目录 %s(PNG=%d) %s(PNG=%d)'
          % (SHOTS_A, len(os.listdir(SHOTS_A)), SHOTS_B, len(os.listdir(SHOTS_B))))
    for f in fails:
        print('PRE_READ_R230 refused: ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
