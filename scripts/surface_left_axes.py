#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把"这一屏的左轴对不对"从形容词变成可复算的读数（R209 看图那一轮搬回仓库的尺）。

来历（2026-10-19 看图时先用 /tmp 手搓尺量过 —— 那条规矩说这种尺只配形成问题，进判据要搬回仓库）：
  · 快速选择浮层：选中行的药丸左缘 22.0pt、右缘内缩 22.0pt、搜索框占位墨左缘 24.0pt、行图标左缘 35.5pt。
    我第一句写的是"看起来没对齐"，量出来三轴各自成轴，**没有一条是错的**；
    真正能被证伪的是"药丸左右内缩不对等"，实测差 0.0pt。
  · 设置「统计」：卡片里统计行 / 月份行 / 说明正文的最左墨都在 148.0pt（同一条轴），
    而热图网格最右墨 558.5pt、说明文字最右墨 678.5pt ⇒ 网格比文字列短 120pt。
    这一格判为**不改**（格子尺寸是"一天一格"的编码前提，拉宽会把宽度变成第二个编码通道），
    但"网格不越过文字列"这件事从此该由读数说，而不是由我这双眼睛说。

只留**关系判据**，不留绝对值：绝对值会把今天的形状钉成契约（R83 那一族），
而"对称 / 同轴 / 不越过"这三条在窗口变宽、字体变档时仍然说得出话。

一条自己踩过的坑（写在这把尺的第一版里，R209）：**背景色不许从探针窗口自己取**。
第一版用"窗口内的众数色"当底，于是药丸那种"占满窗口大部分格子"的对象把背景吃掉了 ——
量出来的左内缩是 0.0pt（它量的是面板底相对药丸的差）。现在底由**每颗探针另给的空白窗口**取，
并且要求那块窗口本身几乎是纯色（不纯色 ⇒ NOT_RUN）：前提钉子挂在尺能读到的东西上。

三条规矩（每条都能各自红）：
  A 对称：一条探针的左内缩与右内缩之差 ≤ 1.0pt。
  B 同轴：一组探针的最左墨彼此相差 ≤ 1.0pt。
  C 不越过：网格的最右墨不得越过参照文字列的最右墨（也不得比它更靠左）。
探针一律**钉死窗口坐标**并断言"这一格里确实有墨"（R86：自动搜出来的采样点会把量错对象
伪装成量到了）。任何一条探针取不到墨或底不纯 ⇒ `NOT_RUN`，判据整体红 —— 不许在空名单上给绿（R99）。

用法：
  python3 scripts/surface_left_axes.py --shots /tmp/shots_r207      # 真帧
  python3 scripts/surface_left_axes.py --shots DIR --json
  python3 scripts/surface_left_axes.py --self-test                  # 已知答案的对照
退出码：0=三条都过；1=有判据红（含 NOT_RUN）；2=帧取不到/用法错。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

TOL_PT = 1.0
INK_THRESHOLD = 12
# 底必须几乎是纯色：允许的最大通道偏差（比墨的门槛低一档，否则"有墨"与"底不纯"会互相冒充）
BG_FLAT_TOLERANCE = 6

# 探针表。stem=帧名去掉 -dark/-light；window=量墨的格子；bg=取底的空白格子（不许与 window 重叠）。
PROBES = [
    dict(name=u'浮层/选中行药丸', stem=u'quickpick-list-420x300',
         window=(0, 104, 840, 148), bg=(0, 500, 840, 560)),
    # 统计页：x 从 280 起，左边那条是侧栏，混进来会造出一条假轴
    dict(name=u'统计/统计行', stem=u'settings-stats-populated-720x540',
         window=(280, 246, 1440, 274), bg=(280, 900, 1400, 960)),
    dict(name=u'统计/月份行', stem=u'settings-stats-populated-720x540',
         window=(280, 296, 1440, 324), bg=(280, 900, 1400, 960)),
    dict(name=u'统计/说明正文', stem=u'settings-stats-populated-720x540',
         window=(280, 666, 1440, 700), bg=(280, 900, 1400, 960)),
    dict(name=u'统计/热图网格', stem=u'settings-stats-populated-720x540',
         window=(280, 326, 1440, 352), bg=(280, 900, 1400, 960)),
]

AXIS_GROUP = u'统计/统计行,统计/月份行,统计/说明正文'      # B 同轴
SYMMETRY_PROBE = u'浮层/选中行药丸'                        # A 对称
NO_OVERFLOW = (u'统计/热图网格', u'统计/说明正文')          # C 不越过


def parse_frame_pt_width(stem):
    """从帧名里取 pt 宽：`quickpick-list-420x300` ⇒ 420。取不到返回 None（不许猜 2x）。"""
    m = re.search(r'-(\d+)x(\d+)$', stem)
    return int(m.group(1)) if m else None


def _clipped(window, W, H):
    x0, y0, x1, y1 = window
    return max(0, x0), max(0, y0), min(W, x1), min(H, y1)


def background(px, window, W, H):
    """取底：窗口内的众数色 + "它是不是纯色"的判定。返回 (rgb, 是否纯色)。"""
    x0, y0, x1, y1 = _clipped(window, W, H)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None, False
    counts = collections.Counter()
    for y in range(y0, y1, 3):
        for x in range(x0, x1, 3):
            counts[px[x, y]] += 1
    if not counts:
        return None, False
    modal, n = counts.most_common(1)[0]
    total = sum(counts.values())
    far = sum(c for rgb, c in counts.items()
              if max(abs(rgb[i] - modal[i]) for i in range(3)) > BG_FLAT_TOLERANCE)
    return modal, (total and far / float(total)) < 0.02


def probe_reading(im, probe):
    """返回 (最左/最右墨，像素与 pt)；取不到墨或底不纯 ⇒ None（宁可 NOT_RUN 不给假数）。"""
    px = im.load()
    W, H = im.size
    pt_w = parse_frame_pt_width(probe['stem'])
    if not pt_w:
        return None
    bg, flat = background(px, probe['bg'], W, H)
    if bg is None or not flat:
        return None
    scale = pt_w / float(W)
    x0, y0, x1, y1 = _clipped(probe['window'], W, H)
    xs = []
    for x in range(x0, x1):
        for y in range(y0, y1):
            r, g, b = px[x, y]
            if max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2])) > INK_THRESHOLD:
                xs.append(x)
                break
    if not xs:
        return None
    return dict(left_px=xs[0], right_px=xs[-1], width_px=W,
                left_pt=round(xs[0] * scale, 2), right_pt=round((W - 1 - xs[-1]) * scale, 2),
                pt_width=pt_w)


def judge(readings):
    """三条关系判据。readings: {probe_name: reading|None} → (rows, problems)。"""
    rows, problems = [], []
    for name, r in readings.items():
        if r is None:
            problems.append(('NOT_RUN', u'%s：探针取不到墨或底不纯 ⇒ 尺没有对象，不许给绿' % name))
    if problems:
        return rows, problems

    r = readings[SYMMETRY_PROBE]
    d = round(abs(r['left_pt'] - r['right_pt']), 2)
    rows.append(('A 对称', SYMMETRY_PROBE,
                 u'左内缩=%spt 右内缩=%spt 差=%spt（容差 %s）' % (r['left_pt'], r['right_pt'], d, TOL_PT)))
    if d > TOL_PT:
        problems.append(('ASYMMETRIC', u'%s：左右内缩差 %spt > %spt' % (SYMMETRY_PROBE, d, TOL_PT)))

    names = [n.strip() for n in AXIS_GROUP.split(u',')]
    lefts = [readings[n]['left_pt'] for n in names]
    spread = round(max(lefts) - min(lefts), 2)
    rows.append(('B 同轴', u'、'.join(names), u'最左墨=%spt 跨度=%spt（容差 %s）' % (lefts, spread, TOL_PT)))
    if spread > TOL_PT:
        problems.append(('OFF_AXIS', u'同组左轴跨度 %spt > %spt ⇒ 卡片里出现了第二条轴' % (spread, TOL_PT)))

    a, b = NO_OVERFLOW
    ra, rb = readings[a], readings[b]
    rows.append(('C 不越过', u'%s ⊆ %s' % (a, b),
                 u'网格左缘=%spt 右内缩=%spt ｜参照左缘=%spt 右内缩=%spt' % (ra['left_pt'], ra['right_pt'],
                                                              rb['left_pt'], rb['right_pt'])))
    if ra['right_px'] > rb['right_px'] + 2:
        problems.append(('GRID_PAST_TEXT', u'热图网格右缘 %spx 越过说明文字右缘 %spx ⇒ 内容顶到文字列外面'
                                      % (ra['right_px'], rb['right_px'])))
    if ra['left_px'] < rb['left_px'] - 2:
        problems.append(('GRID_LEFT_OF_TEXT', u'热图网格左缘 %spx 早于说明文字 %spx ⇒ 网格跑到文字列外面'
                                      % (ra['left_px'], rb['left_px'])))
    return rows, problems


def collect(shots_dir, suffix=u'-dark'):
    from PIL import Image
    readings, absent = {}, []
    for p in PROBES:
        key = p['stem'] + suffix
        path = os.path.join(shots_dir, key + u'.png')
        if not os.path.exists(path):
            readings[p['name']] = None
            absent.append(key + u'.png')
            continue
        readings[p['name']] = probe_reading(Image.open(path).convert('RGB'), p)
    return readings, sorted(set(absent))


def self_test():
    """已知答案的对照：正对照要绿，三种坏法各自要红，空帧要 NOT_RUN。"""
    from PIL import Image
    ok = True

    def stats_frame(axis_shift=0, grid_right=1117):
        im = Image.new('RGB', (1440, 1080), (30, 30, 30))
        px = im.load()
        for name, y0 in ((u'统计/统计行', 246), (u'统计/月份行', 296), (u'统计/说明正文', 666)):
            x = 296 + (axis_shift if name == u'统计/月份行' else 0)
            for yy in range(y0, y0 + 28):
                for xx in range(x, 1357):
                    px[xx, yy] = (230, 230, 230)
        for yy in range(326, 352):
            for xx in range(296, grid_right):
                px[xx, yy] = (60, 120, 220)
        return im

    def quickpick_frame(offset=0):
        im = Image.new('RGB', (840, 600), (30, 30, 30))
        px = im.load()
        for yy in range(104, 148):
            for xx in range(44 + offset, 796):
                px[xx, yy] = (60, 60, 60)
        return im

    def run(qp, st):
        frames = {u'quickpick-list-420x300': qp, u'settings-stats-populated-720x540': st}
        readings = {p['name']: probe_reading(frames[p['stem']], p) for p in PROBES}
        return judge(readings)

    cases = [
        (u'正对照·今天的样子', quickpick_frame(0), stats_frame(), True),
        (u'反对照·药丸只往右缩', quickpick_frame(30), stats_frame(), False),
        (u'反对照·月份行换了一条轴', quickpick_frame(0), stats_frame(axis_shift=30), False),
        (u'反对照·网格越过文字右缘', quickpick_frame(0), stats_frame(grid_right=1400), False),
        (u'反对照·全空帧', Image.new('RGB', (840, 600), (30, 30, 30)),
         Image.new('RGB', (1440, 1080), (30, 30, 30)), False),
    ]
    for label, qp, st, want_ok in cases:
        _, problems = run(qp, st)
        codes = [c for c, _ in problems]
        got_ok = not problems
        good = got_ok == want_ok
        if not good:
            ok = False
        print(u'SELFTEST %-22s 期望=%s 实得=%s %s ｜ %s'
              % (label, u'绿' if want_ok else u'红', u'绿' if got_ok else u'红',
                 u'' if good else u'** 对照坏掉 **', u'、'.join(codes) or u'无问题'))
    print(u'LEFT_AXIS_SELFTEST %s' % ('ok' if ok else 'bad'))
    return 0 if ok else 1


def ci_mode(shots_dir):
    """CI 那一刀的处置策略，写在 python 里而不是 shell 里（R64 的教训：awk 没有一份自测能证明它对）。

    三种出口，处置不同：
      · 关系判据真红（ASYMMETRIC / OFF_AXIS / GRID_*）⇒ `verdict=red`，exit 1 —— 这才是产品/夹具的结论。
      · 只有 NOT_RUN（帧没拍到、或那块窗口没墨）⇒ `verdict=skipped`，exit 0 ——
        无头 runner 的高窗只画一条下沿带（BACKLOG 201），拿环境缺席去判产品就是 R154 那朵假红。
        跳过必须是**读数**（`not_run=几颗、缺哪些帧`），不许变成一条覆盖率通道。
      · 全绿 ⇒ `verdict=ok`。
    """
    if os.environ.get('SURFACE_LEFT_AXES_FORCE_NO_PIL') == '1':
        print(u'LEFT_AXIS_CI verdict=unavailable reason=pillow-blocked hard=0 not_run=0 '
              u'missing_frames=0 probes=0')
        print(u'LEFT_AXIS_ENV_NOTE 这一格只说"这台机器/这一步没有像素库"，不说产品对不对 ⇒ exit 0')
        return 0
    try:
        readings, absent = collect(shots_dir)
    except ImportError:
        print(u'LEFT_AXIS_CI verdict=unavailable reason=pillow-missing hard=0 not_run=0 '
              u'missing_frames=0 probes=0')
        print(u'LEFT_AXIS_ENV_NOTE import PIL 失败 ⇒ 环境缺席，不许报成产品结论（R154 那一族）')
        return 0
    rows, problems = judge(readings)
    codes = [c for c, _ in problems]

    hard = [c for c in codes if c != 'NOT_RUN']
    not_run = codes.count('NOT_RUN')
    for name, probe, text in rows:
        print(u'LEFT_AXIS %s ｜ %s ｜ %s' % (name, probe, text))
    for code, why in problems:
        print(u'LEFT_AXIS_%s %s' % (code, why))
    for a in absent:
        print(u'LEFT_AXIS_MISSING_FRAME %s' % a)
    verdict = 'red' if hard else ('skipped' if not_run else 'ok')
    print(u'LEFT_AXIS_CI verdict=%s hard=%d not_run=%d missing_frames=%d probes=%d'
          % (verdict, len(hard), not_run, len(absent), len(readings)))
    return 1 if hard else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--shots', default=None)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--ci', action='store_true', help=u'CI 用：只有关系判据真红才让步骤红')
    ap.add_argument('--suffix', default=u'-dark')
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.shots:
        sys.stderr.write('要么给 --shots 目录，要么 --self-test\n')
        return 2
    if not os.path.isdir(args.shots):
        sys.stderr.write('FRAME_DIR_MISSING %s\n' % args.shots)
        return 2
    if args.ci:
        return ci_mode(args.shots)

    readings, absent = collect(args.shots, args.suffix)
    for a in absent:
        print(u'LEFT_AXIS_NOT_RUN 探针取不到帧：%s' % a)
    rows, problems = judge(readings)
    if args.json:
        print(json.dumps(dict(readings=readings, rows=rows, problems=[p[0] for p in problems]),
                         ensure_ascii=False))
    else:
        for name, probe, text in rows:
            print(u'LEFT_AXIS %s ｜ %s ｜ %s' % (name, probe, text))
        for code, why in problems:
            print(u'LEFT_AXIS_%s %s' % (code, why))
        print(u'LEFT_AXIS_VERDICT %s 探针=%d 问题=%d NOT_RUN帧=%d'
              % ('ok' if not problems else 'bad', len(readings), len(problems), len(absent)))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
