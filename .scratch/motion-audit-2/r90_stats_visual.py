#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R90 的看图仪器（设置窗口「统计」分区 = 阶段一那个新功能的落点）。

为什么这一轮要量而不是看：这一屏是热图本尊，而热图的**全部信息都在颜色里**。
"看起来挺清楚"在这种屏上是最坏的评价方式 —— 档位之间差 3/255 与差 30/255 用眼睛看
都可能"有深浅"，但只有前者是读不出来的。⇒ 每档分别取出色号、含墨像素数、与**局部**背景的
距离，并且**把相邻档位的差打出来**（差=0 的两档在画面上是同一个东西）。

三处口径（都是上一轮栽过的位置）：
 · 参照点用**网格内部的局部背景**（直方图里最大的那簇近灰），不用整页中位数：
   实测这两个数在这张帧上差 3（252 与 255），拿整页当参照会把"格子比卡片深多少"读少。
 · 距离用**逐通道最大绝对差**（切比雪夫），不用"最大通道减背景"：后者对蓝色格恒等于
   255-255≈0 —— 蓝格的蓝通道本来就接近 255，那个量法会把最显眼的东西读成看不见。
 · 灰与蓝分开报：色相（蓝−另两通道）才是分得开"淡蓝"与"浅灰"的那条轴（R54 / U-80）。

三条自检（仪器自己没验过的读数不算读数）：
 ① 正对照：空态帧（`heatmap-empty-*`）里**必须量不到蓝色格**，否则检测器在拿噪声当信号。
 ② 区域不是猜的：每个横向色带（网格 / 图例）的 y 范围由检出的蓝像素算出来并打成 pt 坐标。
 ③ 反对照：同一套函数跑在**暗色**帧上必须给出色号完全不同的一批簇；若两色模式报出同一批
    色号 ⇒ 帧没切主题，读数作废（脚本末尾的 CROSS_MODE_SAME_CLUSTERS 行）。
 ④ 格式串 arity：所有 print 走 F()，占位符个数与参数个数不等就直接抛，不允许半截读数落盘。

跑法：
    PYTHONUTF8=1 python3 .scratch/motion-audit-2/r90_stats_visual.py /tmp/r90_shots
输出同时写 `.scratch/motion-audit-2/r90_stats_readings.log`。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode                   # 同一个 PNG 解码器，不引第三方依赖
# 侧栏那一列**不**复用 R88 的 `r88_sidebar_icons`：它只认比背景亮的墨，
# 在暗色帧上黑字一颗带都切不出来（本轮实测 `文字带=0/1 个`），所以那边"亮色侧栏没问题"
# 其实是"没量到"。本轮自带双边判据（`sidebar_rows`），并把符号打出来。

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r90_stats_readings.log')

BLUE_CHROMA = 25        # 蓝 − max(红,绿)：判"这是色还是灰"
BLUE_MIN = 80
MIN_CLUSTER = 300       # 一格在 2x 帧里约 26x26=676px，300 是"确实有一批格子"的下限
SPEC = re.compile(r'%[-+ #0]*[\d.]*[sdrfx%]')


def F(template, *args):
    """带 arity 自检的格式化：占位符数 ≠ 参数数就抛，别把半截读数写进台账。"""
    n = len([m for m in SPEC.finditer(template) if m.group() != '%%'])
    if n != len(args):
        raise AssertionError('FORMAT_ARITY 占位符=%d 参数=%d :: %s' % (n, len(args), template))
    return template % args


def px(rows, ch, x, y):
    line = rows[y]
    o = x * ch
    return line[o], line[o + 1], line[o + 2]


def maxc(p):
    return max(p[0], p[1], p[2])


def chroma(p):
    return p[2] - max(p[0], p[1])


def is_blue(p):
    return chroma(p) >= BLUE_CHROMA and p[2] >= BLUE_MIN


def dist(p, ref):
    """与参照色的逐通道最大绝对差（切比雪夫）。参照色是 RGB 三元组。"""
    return max(abs(p[0] - ref[0]), abs(p[1] - ref[1]), abs(p[2] - ref[2]))


def page_bg(rows, ch, w, h):
    """整页背景：右下角那块谁都不写的空白里取中位数（不是角点 —— 角点是窗口圆角/阴影）。"""
    vals = []
    for y in range(int(h * 0.72), int(h * 0.95), 5):
        for x in range(int(w * 0.55), int(w * 0.95), 5):
            vals.append(maxc(px(rows, ch, x, y)))
    vals.sort()
    return vals[len(vals) // 2]


def strip_median(rows, ch, x0, x1, y0, y1):
    """一条窄带里逐通道的中位数颜色 —— 用作"卡片底"，因为它按结构一定不是格子。"""
    rs, gs, bs = [], [], []
    for y in range(y0, y1 + 1, 2):
        for x in range(x0, x1):
            p = px(rows, ch, x, y)
            rs.append(p[0]); gs.append(p[1]); bs.append(p[2])
    if not rs:
        return (0, 0, 0)
    rs.sort(); gs.sort(); bs.sort()
    m = len(rs) // 2
    return (rs[m], gs[m], bs[m])


def blue_rows(rows, ch, w, h):
    """逐行蓝像素计数：用来把"网格"与"图例"这两个横向色带分开（不猜 y 坐标）。"""
    prof = []
    for y in range(int(h * 0.10), int(h * 0.62)):
        n = 0
        for x in range(int(w * 0.28), w - 4, 2):
            if is_blue(px(rows, ch, x, y)):
                n += 1
        prof.append((y, n))
    return prof


def runs(prof, min_n=3, gap=6):
    """把逐行计数切成连续色带：≥min_n 的行连成一段，中间允许 gap 行的空隙。"""
    out, start, last = [], None, None
    for y, n in prof:
        if n >= min_n:
            if start is None:
                start, last = y, y
            elif y - last <= gap:
                last = y
            else:
                out.append((start, last))
                start, last = y, y
    if start is not None:
        out.append((start, last))
    return out


def clusters(rows, ch, box):
    """盒内色号直方图（4 阶量化，吸收抗锯齿），只保留够大的簇。"""
    x0, x1, y0, y1 = box
    hist = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = px(rows, ch, x, y)
            key = (p[0] // 4 * 4, p[1] // 4 * 4, p[2] // 4 * 4)
            hist[key] = hist.get(key, 0) + 1
    return sorted(((c, n) for c, n in hist.items() if n >= MIN_CLUSTER), key=lambda t: -t[1])


def band_ink(rows, ch, w, h, ref, x0, x1, y0, y1, delta=40):
    """一个矩形带里有多少含墨像素、以及最远那一点与参照的距离（文字可读性的量法）。"""
    ink, peak = 0, 0
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            d = dist(px(rows, ch, x, y), ref)
            if d >= delta:
                ink += 1
                peak = max(peak, d)
    return ink, peak


def ink_cols(rows, ch, x0, x1, y0, y1, bgp, delta=40):
    """一段水平区间里每列的含墨行数 —— 用来**扫出**列位置，而不是记在常量里。"""
    return [sum(1 for y in range(y0, y1) if dist(px(rows, ch, x, y), bgp) >= delta)
            for x in range(x0, x1)]


def segments(counts, x0, min_n=1):
    """把非零列切成连续段 [(x0,x1,最大覆盖)]。"""
    out, start, last, peak = [], None, None, 0
    for i, n in enumerate(counts):
        x = x0 + i
        if n >= min_n:
            if start is None:
                start, peak = x, n
            else:
                peak = max(peak, n)
            last = x
        elif start is not None:
            out.append((start, last, peak))
            start = None
    if start is not None:
        out.append((start, last, peak))
    return out


def divider_x(rows, ch, w, h, bgp):
    """侧栏与内容区之间那条竖线：在 150..600 里**纵向覆盖最高**的那一列。
    列位置全部由它推出来 —— R88 把图标框写成 88–150、文字框写成 170–420，
    本轮实测这一列的真实位置是图标 35–68 / 标签 79–153 / 分隔线 296，
    也就是说它那个"文字框"整个落在**内容区**里。⇒ 不再抄常量。

    阈值分档试：暗档那条线只有 ~10/255，用 40 扫不出来（本轮实测覆盖=48 ⇒ NOT-RUN）。
    用了哪一档必须打出来 —— 门槛越低，"找到了"这句话越弱。
    """
    for delta in (40, 16, 8):
        cols = ink_cols(rows, ch, 150, min(600, w), 0, h, bgp, delta)
        if not cols:
            continue
        best = max(range(len(cols)), key=lambda i: cols[i])
        if cols[best] > h * 0.7:
            return (150 + best, cols[best], h, delta)
    return None


def sidebar_bands(rows, ch, w, h, bgp, x0, x1, delta=40):
    """按"这一行在标签列里有没有墨"切水平带（双边：墨可以比背景暗）。"""
    ink = []
    for y in range(h):
        n = sum(1 for x in range(x0, x1) if dist(px(rows, ch, x, y), bgp) >= delta)
        ink.append(n)
    out, start = [], None
    for y, n in enumerate(ink):
        if n >= 2 and start is None:
            start = y
        elif n < 2 and start is not None:
            if y - start >= 3:
                out.append([start, y])
            start = None
    if start is not None:
        out.append([start, h])
    merged = []
    for b in out:
        if merged and b[0] - merged[-1][1] <= 12:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    return [tuple(m) for m in merged]


def sidebar_report(shots, name, labels=('快捷键', '通用', '隐私', '推荐', '数据', '统计')):
    """侧栏每一行分别量图标框与文字框：'整行淡'（行被禁用）与'只有图标淡'是两种病。"""
    path = os.path.join(shots, name)
    if not os.path.exists(path):
        print(F('MISSING=%s', path))
        return
    w, h, ch, rows = decode(path)
    # 侧栏背景：图标列左边那条一定没字的窄带
    vals = [px(rows, ch, x, y) for y in range(int(h * 0.10), int(h * 0.90), 7) for x in range(20, 32)]
    vals.sort(key=maxc)
    bgp = vals[len(vals) // 2]
    dv = divider_x(rows, ch, w, h, bgp)
    if dv is None:
        print(F('--- %s  分隔线没扫出来（连 8/255 那一档都没有纵向 >70%% 的列）'
                '⇒ 列位置无从推导，这张帧的侧栏读数 NOT-RUN', name))
        return
    dx, delta = dv[0], dv[3]
    segs = [s for s in segments(ink_cols(rows, ch, 24, dx - 3, int(h * 0.10), int(h * 0.92), bgp, delta),
                                24) if s[1] - s[0] >= 6]
    print(F('--- %s  %dx%d 侧栏底=rgb(%d,%d,%d) 分隔线 x=%d（覆盖 %d/%d，门槛=%d/255）列段=%s',
            name, w, h, bgp[0], bgp[1], bgp[2], dx, dv[1], h, delta,
            ' '.join('x=%d-%d' % (s[0], s[1]) for s in segs)))
    if len(segs) < 2:
        print(F('    COLUMN_SEGMENTS=%d ⇒ 扫不出"图标列 + 标签列"两段，下面的数不许引用', len(segs)))
        return
    icon_box, label_box = (segs[0][0], segs[0][1] + 1), (segs[1][0], segs[1][1] + 1)
    bs = sidebar_bands(rows, ch, w, h, bgp, *label_box, delta=delta)
    print(F('    图标框 x=%d-%d 标签框 x=%d-%d 文字带=%d 个（期望 %d）',
            icon_box[0], icon_box[1], label_box[0], label_box[1], len(bs), len(labels)))
    if len(bs) != len(labels):
        print(F('    BAND_COUNT_MISMATCH=%d ⇒ 带切法在这张图上不成立，下面的数不许引用', len(bs)))
        return
    for name_row, b in zip(labels, bs):
        ic, ic_far, ic_p = row_profile(rows, ch, b, icon_box, bgp)
        tx, tx_far, tx_p = row_profile(rows, ch, b, label_box, bgp)
        print(F('    ROW %-4s 带y=%d-%d（pt y=%.0f-%.0f） 图标 ≥2:%-5d ≥8:%-5d ≥16:%-5d ≥40:%-5d'
                ' 最远=%-4d rgb(%d,%d,%d) | 标签 ≥2:%-6d ≥8:%-6d ≥16:%-6d ≥40:%-6d 最远=%-4d rgb(%d,%d,%d)',
                name_row, b[0], b[1], b[0] / 2.0, b[1] / 2.0,
                ic[2], ic[8], ic[16], ic[40], ic_far, ic_p[0], ic_p[1], ic_p[2],
                tx[2], tx[8], tx[16], tx[40], tx_far, tx_p[0], tx_p[1], tx_p[2]))


def row_profile(rows, ch, band, box, bgp):
    """一个带 × 一个水平框，按**四档阈值**分别数含墨像素，并报最大偏离与它的色号。

    为什么要四档而不是一个阈值：本轮第一次量到"亮色帧里侧栏图标 0 颗像素偏离 ≥40"，
    这句话有两种完全不同的解释 —— 图标**根本没画**（整列恰好等于背景），
    或画了但只有 15/255（着色解析错）。两者要修的东西不是一回事。⇒ 把 2/8/16/40 都数出来。
    """
    x0, x1 = box
    y0, y1 = band
    pad = 6
    counts = {t: 0 for t in (2, 8, 16, 40)}
    far, farp = 0, (0, 0, 0)
    for y in range(max(0, y0 - pad), min(len(rows), y1 + pad)):
        for x in range(x0, min(x1, len(rows[y]) // ch)):
            p = px(rows, ch, x, y)
            d = dist(p, bgp)
            for t in counts:
                if d >= t:
                    counts[t] += 1
            if d > far:
                far, farp = d, p
    return counts, far, farp


def text_bands(rows, ch, w, h, bg_global):
    """文字带的可读性：标题 / 副标题（或空态那一句）/ 底部两段注释。

    放在**有没有蓝色格之前**跑：空态帧里没有格子，但那句"还没有可统计的记录"照样要被判。
    """
    ref_gray = (bg_global, bg_global, bg_global)
    for label, band in (('标题「每日复制」', (int(h * 0.13), int(h * 0.175))),
                        ('副标题 / 空态那一句', (int(h * 0.17), int(h * 0.245))),
                        ('注释段（这张图怎么读…）', (int(h * 0.52), int(h * 0.72)))):
        ink, peak = band_ink(rows, ch, w, h, ref_gray, int(w * 0.30), w - 4, band[0], band[1])
        print(F('    %-22s px y=%d-%d（pt y=%.0f-%.0f）含墨像素=%-6d 峰值距=%-4d %s',
                label, band[0], band[1], band[0] / 2.0, band[1] / 2.0, ink, peak,
                '' if ink > 150 else '⇒ 这个带几乎没字，读数可疑'))


def report(shots, name, scale=2.0):
    path = os.path.join(shots, name)
    if not os.path.exists(path):
        print(F('MISSING=%s', path))
        return None
    w, h, ch, rows = decode(path)
    bg_global = page_bg(rows, ch, w, h)
    print(F('=== %s  %dx%d px（%.0fpt 宽）整页背景最大通道=%d', name, w, h, w / scale, bg_global))
    if w >= 1400:
        text_bands(rows, ch, w, h, bg_global)
    prof = blue_rows(rows, ch, w, h)
    bands = runs(prof)
    if not bands:
        print('    NO_BLUE_CELLS ⇒ 这张帧里没有蓝色格（空态帧应当走到这里）')
        return []
    results = []
    for bi, (ry0, ry1) in enumerate(bands):
        x0 = x1 = None
        for y in range(ry0, ry1 + 1):
            for x in range(int(w * 0.28), w - 4):
                if is_blue(px(rows, ch, x, y)):
                    x0 = x if x0 is None else min(x0, x)
                    x1 = x if x1 is None else max(x1, x)
                    break
            for x in range(w - 5, int(w * 0.28), -1):
                if is_blue(px(rows, ch, x, y)):
                    x1 = x if x1 is None else max(x1, x)
                    break
        box = (x0, x1, ry0, ry1)
        cl = clusters(rows, ch, box)
        # 参照点用**结构**而不是亮度：网格左边那条窄带一定是卡片底（不是格子），
        # 拿它当背景，才不会出现"0 计数格恰好是最大簇时被当成背景"那种自我循环。
        card = strip_median(rows, ch, max(0, x0 - 44), max(1, x0 - 10), ry0, ry1)
        ref = card
        label = '网格' if bi == 0 else '色带%d' % (bi + 1)
        contaminated = is_blue(card)
        print(F('  [%s] px x=%d-%d y=%d-%d（pt x=%.0f-%.0f y=%.0f-%.0f）卡片底=rgb(%d,%d,%d)%s',
                label, x0, x1, ry0, ry1, x0 / scale, x1 / scale, ry0 / scale, ry1 / scale,
                ref[0], ref[1], ref[2],
                '  CARD_SAMPLE_CONTAMINATED ⇒ 参照点取到了别处的蓝，这一带的"距卡片底"不许引用'
                if contaminated else ''))
        blues, band_grays = [], []
        for c, cnt in cl:
            tag = '蓝' if is_blue(c) else '灰'
            print(F('      簇 rgb=(%3d,%3d,%3d) %-2s 像素=%-6d 距卡片底=%-4d 色相=%+d',
                    c[0], c[1], c[2], tag, cnt, dist(c, ref), chroma(c)))
            if tag == '蓝':
                blues.append((c, cnt))
            else:
                results.append(('gray', c, cnt, dist(c, ref)))
                band_grays.append(('gray', c, cnt, dist(c, ref)))
        blues.sort(key=lambda t: chroma(t[0]))
        print(F('      蓝色档位数=%d（按色相深度排序；相邻差=0 ⇒ 画面上是同一个东西）', len(blues)))
        prev = None
        for c, cnt in blues:
            gap = '' if prev is None else F('  与上一档差=%+d', chroma(c) - prev)
            print(F('        档 rgb(%3d,%3d,%3d) 像素=%-6d 距卡片底=%-4d 色相=%+d%s',
                    c[0], c[1], c[2], cnt, dist(c, ref), chroma(c), gap))
            prev = chroma(c)
            results.append(('blue', c, cnt, chroma(c)))
        # 只看**这一带**的灰簇：`results` 是跨带累加的，拿它找"最近的灰"会让上一带的数冒充这一带的。
        pale = [g for g in band_grays if g[3] >= 2]
        if pale:
            near = min(pale, key=lambda g: g[3])
            print(F('      0 计数格（离卡片底最近的非蓝簇）rgb(%d,%d,%d) 像素=%d 距卡片底=%d ⇒ %s',
                    near[1][0], near[1][1], near[1][2], near[2], near[3],
                    '可辨' if near[3] >= 8 else '与卡片底几乎同色'))
        else:
            print(F('      盒内除卡片底外没有 ≥%d 像素的灰簇 ⇒ 0 计数格与卡片底同色（量不出差）', MIN_CLUSTER))
    return results


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r90_shots'

    class Tee(object):
        def __init__(self, *sinks):
            self.sinks = sinks

        def write(self, s):
            for sink in self.sinks:
                sink.write(s)

        def flush(self):
            for sink in self.sinks:
                try:
                    sink.flush()
                except Exception:
                    pass

    console = sys.stdout
    frames = ('heatmap-empty-430x150-light.png', 'heatmap-empty-430x150-dark.png',
              'settings-stats-720x540-light.png', 'settings-stats-720x540-dark.png',
              'settings-stats-populated-720x540-light.png',
              'settings-stats-populated-720x540-dark.png')
    with open(OUT, 'w', encoding='utf-8') as log:
        sys.stdout = Tee(console, log)
        try:
            print(F('shots=%s', shots))
            collected = {}
            for f in frames:
                collected[f] = report(shots, f)
            print()
            print('--- 侧栏逐行（双边判据：墨可以比背景暗，负号就是"比底还暗"）')
            for f in ('settings-stats-720x540-light.png', 'settings-stats-populated-720x540-light.png',
                      'settings-stats-720x540-dark.png', 'settings-stats-populated-720x540-dark.png'):
                sidebar_report(shots, f)
            # ③ 反对照：两色模式若报出同一批色号 ⇒ 帧没切主题。
            li = set(c[1] for c in (collected.get(frames[4]) or []))
            da = set(c[1] for c in (collected.get(frames[5]) or []))
            both = li & da
            print(F('CROSS_MODE light簇=%d dark簇=%d 交集=%d %s',
                    len(li), len(da), len(both),
                    '⇒ 交集过大，怀疑帧没切主题，本轮色号读数作废' if len(both) > max(2, min(len(li), len(da)) // 3)
                    else '⇒ 两色模式色号基本不重叠，主题确实切了'))
        finally:
            sys.stdout = console
    print(F('WROTE=%s', OUT))


if __name__ == '__main__':
    main()
