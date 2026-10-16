#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R94 视觉腿：菜单栏面板（MenuBarExtra 的内容视图）逐元素重判。

为什么是这三屏：阶段二的范围里"菜单栏（MenuBarExtra 与状态菜单）"从 R9 到现在**一次都没有
被逐元素量过**（R9–R93 量的是主窗口、设置各分区、热图、浮层）。帧一直有：
`menubar-{empty,refreshing,recommendations}-*-{light,dark}.png`，共 6 张，但从没被读过。

判什么（每条都要能被打红，且给出 pt 坐标）：
  层级   标题 / 小标题 / 正文 / 说明四档的字身高与对比度，是否各自成档
  对齐   文字带共用同一条左轴？行内 label 与 reason 的 y 中心差（firstTextBaseline 承诺过的事）
  边界   右边缘留白：任何一条文字带不许贴到 320pt 的边上
  分隔线 数量、是否齐宽、是否与文字的左轴一致
  两态   empty 与 refreshing 必须**真的有两态**（R76 那条：两态对照必须真的有两态）
  颜色   「都不是我想要的」那行 —— 在非 key 通道里 .blue 会被去饱和 ⇒ 前提闸门判 NOT-RUN，
        但它与相邻说明文字的**亮度差**照量（那才是这条通道里真看得见的东西）

不做的事：不据此改产品。本轮先给出读数与"该不该加动效/hover"的判断依据；
每一格的处置写进 AGENT_UI_AUDIT 第 96 轮。
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode           # PNG 解码（无 PIL 的本机）
from r92_data_visual import chroma, lum, median, ratio   # 同一颗尺，别造第二把

LOGICAL_W = 320.0


def L(p):
    """0..255 的亮度。`r92_data_visual.lum()` 返回的是 **WCAG 相对亮度 Y ∈ [0,1]**
    （实测：lum((39,39,39)) = 0.0203），所以把它的输出直接跟 12、25 这种"255 尺度"的阈值
    比，结果是这颗尺**永远读 0 个墨点** —— 第一次跑就是六张帧全部"带数=0"。
    这正是账本里那条「量纲/坐标约定要实测，别把抄来的阈值当同一种单位」。
    """
    return lum(p) * 255.0


# 墨的判据改用 **对比度比值**（与主题无关），不用 ΔL：
# 同一根原生 `Divider()` 在两个主题里都是 ≈1.25:1，可 ΔL 却是 亮档 53.2 / 暗档 5.4 ——
# WCAG 的 Y 在高端近乎线性、在低端被压扁，于是"固定 ΔL 门槛"这一颗尺
# **在暗档读不到、在亮档读得到**（第一次跑就是：亮色报 3 条分隔线、暗色报 0 条，
# 而那 0 其实是"我的门槛"，不是"画面上没有"）。与 R90 那条"量不到 ≠ 没问题"同一族。
INK_FLOOR = 1.15


def is_ink(p, bg):
    return ratio(p, bg) >= INK_FLOOR


def load(path):
    # `decode()` 的形状是 (w, h, ch, rows) —— 第一次我按 (rows, ch, w, h) 解，
    # 于是 `h` 成了一行列，`h // 40` 直接 TypeError。
    # 这把尺的坐标约定必须实测（R90 那条：抄来的签名会把"量错对象"伪装成"量到了"）。
    w, h, ch, rows = decode(path)
    return rows, ch, w, h


def pt_scale(w):
    """像素宽 ÷ 夹具的逻辑宽 ⇒ 这台机器的 scale。量出来，别假设。"""
    return w / LOGICAL_W


def bg_of(rows, ch, w, h):
    """面板底色：取四角之外、整幅中位数（R92 的教训：参照点不能拿角点，角上是描边）。"""
    vals = []
    for y in range(0, h, max(1, h // 40)):
        vals.append([tuple(rows[y][x * ch:x * ch + ch][:3]) for x in range(0, w, max(1, w // 60))])
    flat = [p for row in vals for p in row]
    return tuple(int(median([p[i] for p in flat])) for i in range(3))


def ink_rows(rows, ch, y, w, bg):
    """这一行里与底色差得足够的像素列号（亮度轴，暗底亮字/亮底暗字都算墨）。"""
    out = []
    for x in range(w):
        p = tuple(rows[y][x * ch:x * ch + ch][:3])
        if is_ink(p, bg):
            out.append(x)
    return out


def bands(rows, ch, w, h, bg):
    """把连续的有墨行合成带；返回 [(y0,y1,x0,x1)]，单位像素。"""
    res = []
    run = None
    for y in range(h):
        cols = ink_rows(rows, ch, y, w, bg)
        if cols:
            if run is None:
                run = [y, y, min(cols), max(cols)]
            else:
                run[1] = y
                run[2] = min(run[2], min(cols))
                run[3] = max(run[3], max(cols))
        else:
            if run is not None:
                res.append(run)
                run = None
    if run is not None:
        res.append(run)
    return [r for r in res if (r[1] - r[0]) >= 1]


def ink_color(rows, ch, b, bg, w):
    """这一条带里对比度最高的那 8% 像素的均色 —— 抗锯齿不会把墨色拉偏。"""
    px = []
    y0, y1, x0, x1 = b
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = tuple(rows[y][x * ch:x * ch + ch][:3])
            r = ratio(p, bg)
            if r >= 1.6:
                px.append((r, p))
    if not px:
        return None
    px.sort(reverse=True)
    take = px[:max(1, len(px) // 12)]
    return tuple(int(median([t[1][i] for t in take])) for i in range(3))


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:12]


def premise(shots):
    """非 key 通道 ⇒ .blue 这类强调色被 AppKit 去饱和，那条问题今天不能判（同 R92 / BACKLOG 130）。"""
    path = os.path.join(shots, 'capture-readings.log')
    if not os.path.exists(path):
        return 'no-readings-log', []
    lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    key = any('面板key=true' in l for l in lines)
    active = any('appActive=true' in l for l in lines)
    return ('key' if key else 'non-key') + ('/active' if active else '/inactive'), lines


def report(shots, theme):
    print('== 主题 %s @ %s' % (theme, shots))
    frames = [('empty', 'menubar-empty-320x120-%s.png' % theme, 120.0),
              ('refreshing', 'menubar-refreshing-320x120-%s.png' % theme, 120.0),
              ('recommendations', 'menubar-recommendations-320x320-%s.png' % theme, 320.0)]
    cache = {}
    for name, fn, logical_h in frames:
        path = os.path.join(shots, fn)
        if not os.path.exists(path):
            print('  %s NO-FRAME %s' % (name, fn))
            continue
        rows, ch, w, h = load(path)
        s = pt_scale(w)
        bg = bg_of(rows, ch, w, h)
        bs = bands(rows, ch, w, h, bg)
        print('  %-16s 尺寸=%dx%dpx(scale=%.3g) 底色=%s 带数=%d sha=%s'
              % (name, w, h, s, bg, len(bs), sha(path)))
        dividers = []
        for b in bs:
            y0, x0, x1 = b[0], b[2], b[3]
            height_pt = (b[1] - b[0] + 1) / s
            span_pt = (x1 - x0 + 1) / s
            full = span_pt > (LOGICAL_W * 0.92)
            if height_pt <= 3.0 and full:
                # 分隔线的档差 ≈1.25:1，而文字最低那档 ≈3.5:1 ⇒ 用"高度 + 齐宽"分类，
                # 不用颜色分类：R89 那次就是让 Divider() 混进了文字带名单（左边距 0 的假结论）。
                dividers.append((round(y0 / s, 1), round(x0 / s, 1), round(x1 / s, 1)))
                continue
            col = ink_color(rows, ch, b, bg, w)
            cr = ratio(col, bg) if col else None
            print('     带 y=%5.1f..%5.1f高=%3.1fpt 左=%5.1f 右=%5.1f 右留白=%4.1f 墨=%s 对比=%s'
                  % (y0 / s, b[1] / s, height_pt, x0 / s, x1 / s,
                     LOGICAL_W - x1 / s, col, ('%.2f' % cr) if cr else 'n/a'))
        print('     分隔线 %d 条：' % len(dividers) + ' '.join('y=%.1f[%.1f..%.1f]' % d for d in dividers))
        cache[name] = {'rows': rows, 'ch': ch, 'w': w, 'h': h, 'scale': s,
                       'bg': bg, 'bands': bs, 'path': path, 'dividers': dividers}
    return cache


def two_state_check(caches):
    """empty vs refreshing：两态必须真的有两态，而且不许是同一张。"""
    for theme, cache in caches.items():
        a, b = cache.get('empty'), cache.get('refreshing')
        if not a or not b:
            print('  [%s] 两态对照 NOT-RUN=缺帧' % theme)
            continue
        same_size = (a['w'], a['h']) == (b['w'], b['h'])
        identical = sha(a['path']) == sha(b['path'])
        sa, sb = a['scale'], b['scale']
        diff = ([('%.1f..%.1f' % (x[0] / sa, x[1] / sa)) for x in a['bands']
                 if x not in [y for y in b['bands']]]) if len(a['bands']) == len(b['bands']) else []
        print('  [%s] EMPTY_VS_REFRESHING 同尺寸=%s 像素完全相同=%s 带数=%d/%d 只在空态出现的带=%s'
              % (theme, same_size, identical, len(a['bands']), len(b['bands']), diff or '(逐带相同)'))
        if identical:
            print('     DEFECT=NAME_LIES 这一帧叫「正在整理」却与「暂无推荐」逐字节相同')


def recommendations_check(caches, theme):
    """三条推荐行：左轴、行内 label/reason 基线、右留白、蓝色那行的亮度差。"""
    cache = caches[theme].get('recommendations')
    if not cache:
        print('  recommendations NOT-RUN=缺帧')
        return
    rows, ch, w, h, s, bg, bs = (cache['rows'], cache['ch'], cache['w'], cache['h'],
                                 cache['scale'], cache['bg'], cache['bands'])
    div = {(d[0]) for d in cache['dividers']}
    text = [b for b in bs if (round(b[0] / s, 1) not in div)]
    if not text:
        # 「一把尺读不到东西」与「画面上真的没东西」是两件事，必须能分开（R78 那一族）。
        print('  recommendations NO-BANDS：文字带 0 条 ⇒ 判据没电，不是产品没问题')
        return
    lefts = [b[2] / s for b in text]
    rights = [LOGICAL_W - b[3] / s for b in text]
    print('  左轴：min=%.1f max=%.1f 散布=%.1fpt（>1.5pt 就是没共用一条轴）'
          % (min(lefts), max(lefts), max(lefts) - min(lefts)))
    print('  右留白：min=%.1f max=%.1fpt（<4pt 就是贴边）' % (min(rights), max(rights)))
    heights = {}
    for b in text:
        key = round(b[0] / s, 1)
        col = ink_color(rows, ch, b, bg, w) or (0, 0, 0)
        heights[key] = (round((b[1] - b[0] + 1) / s, 1), round(ratio(col, bg), 2), col)
    print('  逐带 字身高/对比：' + ' '.join('y=%.1f:%.1fpt/%.2f' % (k, v[0], v[1]) for k, v in sorted(heights.items())))
    below = [(k, v) for k, v in sorted(heights.items()) if v[1] < 4.5]
    if below:
        print('  低于 4.5 档的文字带：%s（这条档来自说明段那四条地板；能不能算产品缺陷要看表面）'
              % ['y=%.1fpt %.2f:1 墨=%s' % (k, v[1], v[2]) for k, v in below])
    last = text[-1]
    prev = text[-2] if len(text) > 1 else None
    c1 = ink_color(rows, ch, last, bg, w)
    c2 = ink_color(rows, ch, prev, bg, w) if prev else None
    if c1 and c2:
        print('  末行(应为蓝色动作) 墨=%s 上一行 墨=%s 亮度差=%.1f/255 色度差=%.1f'
              % (c1, c2, abs(L(c1) - L(c2)), abs(chroma(c1) - chroma(c2))))


def topology_check(caches):
    """正对照：同一件产品、两个主题 ⇒ **结构必须同形**（带数、带的 y、分隔线数）。
    不同形就只有两种解释：①产品在某档真的少画了东西；②我这颗尺在一档上量不到。
    上一版用固定 ΔL 门槛时，这里就是亮的 3 条 / 暗的 0 条 —— 被读成"暗档没有分隔线"，
    而实测（同一行取中位色算 WCAG）两个档都是 ≈1.25:1。⇒ 那次是②，尺的错。
    """
    for name in ('empty', 'refreshing', 'recommendations'):
        a = caches['light'].get(name)
        b = caches['dark'].get(name)
        if not a or not b:
            print('  %-16s TOPOLOGY NOT-RUN=缺帧' % name)
            continue
        ya = [round(x[0] / a['scale'], 1) for x in a['bands']]
        yb = [round(x[0] / b['scale'], 1) for x in b['bands']]
        # **容差 1.0pt**：两档实测差 0.5pt（亮 74.0 / 暗 73.5、亮 144.0 / 暗 143.5、亮 174.5 / 暗 174.0），
        # 那是抗锯齿落在哪一行像素上，不是"少了一条带"。第一版用逐点相等 ⇒ 三帧全报"不同形"，
        # 一把只会报假的尺比一把没做的尺更贵（R83 那条：贴边假峰躲过 4pt 是同一个形状的反面）。
        tol = 1.0
        dev = (max((abs(x - y) for x, y in zip(ya, yb)), default=0.0)
               if len(ya) == len(yb) else float('inf'))
        same = (dev <= tol) and (len(a['dividers']) == len(b['dividers']))
        print('  %-16s TOPOLOGY 同形=%s 带=%d/%d 分隔线=%d/%d 最大y偏差=%.1fpt 带=%s'
              % (name, same, len(a['bands']), len(b['bands']),
                 len(a['dividers']), len(b['dividers']), dev, ya))
        if not same:
            print('     DEFECT_OR_RULER 结构在两档不同 ⇒ 先判是产品少画了还是尺量不到（别直接写进台账结论）')


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r94_shots'
    pr, _ = premise(shots)
    print('CAPTURE_CHANNEL premise=%s（非 key ⇒ 强调色那条判 NOT-RUN）' % pr)
    caches = {}
    for theme in ('light', 'dark'):
        caches[theme] = report(shots, theme)
    topology_check(caches)
    two_state_check(caches)
    for theme in ('light', 'dark'):
        recommendations_check(caches, theme)
    return 0


if __name__ == '__main__':
    sys.exit(main())
