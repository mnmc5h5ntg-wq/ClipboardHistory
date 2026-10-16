#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R92 的看图仪器：设置窗口「数据」分区（历史记录存储 / 导出与导入 / 清空）。

为什么这一屏要量而不是看：它整屏都是**容器**（一张卡片、几条分隔线、三颗按钮、一颗选中胶囊），
容器类缺陷用眼睛最容易糊过去 —— "有底色、有线、能点"看着都对。四个问题各配一条读数：

 Q1 分组语言是不是混用：同一段内容既被卡片底色圈起来、又被分隔线切开来 ⇒ 两套分组在说同一件事。
 Q2 破坏性那颗按钮有没有被区分：「清空」删的是全部未收藏记录，而它和「导出历史…」看着同级。
    ⇒ 量两颗按钮的填充色、文字色、两者之差，以及**红分量是否占优**（destructive 走的通道是红）。
 Q3 暗档选中胶囊里的字读不读得出来：胶囊是系统蓝，标签也是蓝 ⇒ 报 WCAG 对比度。
 Q4 内容最低到哪儿（下方那片空要不要动，是一条判断，不是缺陷）。

检测器的形状（第一版栽过，记在这里免得再写错）：**不能按"整行中位色"找盒子**。
按钮只占内容列宽度的两三成，那一行的中位数仍然是页面底色 ⇒ 中位色判据会把两颗按钮整批漏掉，
而"漏掉"在报表上和"这一屏没有按钮"长得一模一样。现在走的是"与底色不同的像素 → 横向段 →
跨行合并成矩形"，卡片与按钮同一把尺，分类只看高宽。

三条自检（仪器自己没验过的读数不算读数）：
 ① 尺不瞎：两档都必须检出侧栏那颗选中胶囊，且它的色相必须是**这一列里最大的**（相对判据，
    不是抄来的常数 —— 抄 R90 的"色相 ≥25"时两档都差 3 没检出，见下面 Q3 那段注释）。
 ② 同一套函数跑在「通用」分区上必须也检出 ≥1 张全宽卡片；只认「数据」页那一张 = 在背位置。
 ③ CROSS_MODE：亮暗两档的页面底色必须差 ≥100，否则帧根本没切主题，本轮所有读数作废。
 ④ 所有输出走 F()：占位符数 ≠ 参数数直接抛，不允许半截读数落盘。

跑法：
    PYTHONUTF8=1 python3 .scratch/motion-audit-2/r92_data_visual.py /tmp/r92_shots
读数写 `.scratch/motion-audit-2/r92_data_readings.log`。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r86_heatmap_legend import decode

SCALE = 2.0                                  # 720x540 的 pt 空间，帧是 1440x1080
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r92_data_readings.log')
SPEC = re.compile(r'%[-+ #0]*[\d.]*[sdrfx%]')
BG_TOL = 4                                   # 与页面底色差这么多才算"不是背景"
INK_MIN = 40                                 # 与所在填充差这么多才算"墨"
MIN_RUN_PX = 18                              # 横向段至少 9pt 宽才可能是容器


def F(template, *args):
    n = len([m for m in SPEC.finditer(template) if m.group() != '%%'])
    if n != len(args):
        raise AssertionError('FORMAT_ARITY 占位符=%d 参数=%d :: %s' % (n, len(args), template))
    return template % args


def px(rows, ch, x, y):
    line = rows[y]
    o = x * ch
    return line[o], line[o + 1], line[o + 2]


def dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def chroma(p):
    return p[2] - max(p[0], p[1])


def red_dominant(p):
    return p[0] - max(p[1], p[2])


def lum(p):
    def chan(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(p[0]) + 0.7152 * chan(p[1]) + 0.0722 * chan(p[2])


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def median(vals):
    s = sorted(vals)
    return s[len(s) // 2] if s else None


def pt(v):
    return v / SCALE


def median_color_in(rows, ch, x0, x1, y0, y1):
    rs, gs, bs = [], [], []
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            p = px(rows, ch, x, y)
            rs.append(p[0]); gs.append(p[1]); bs.append(p[2])
    if not rs:
        return None
    return median(rs), median(gs), median(bs)


def page_bg(rows, ch, w, h, x0, x1):
    """内容列**最低那一段**里的中位数：那里谁都不写。不取角点（角点是窗口圆角/阴影）。"""
    vals = []
    for y in range(int(h * 0.86), int(h * 0.97), 3):
        for x in range(x0, x1, 7):
            vals.append(px(rows, ch, x, y))
    return (median([v[0] for v in vals]), median([v[1] for v in vals]), median([v[2] for v in vals]))


def column_split(rows, ch, w, h):
    """内容列的左边界 = 那条贯穿大半屏高、与左右两侧都不同色的竖线。"""
    best = None
    for x in range(int(w * 0.15), int(w * 0.45)):
        mid = int(h * 0.5)
        left = px(rows, ch, x - 6, mid)
        right = px(rows, ch, x + 6, mid)
        if dist(left, right) < 3:
            continue
        hits = sum(1 for y in range(int(h * 0.12), int(h * 0.9), 11)
                   if dist(px(rows, ch, x, y), px(rows, ch, x - 6, y)) >= 2)
        if best is None or hits > best[1]:
            best = (x, hits)
    if not best:
        raise AssertionError('SPLIT_NOT_FOUND 内容列左边界没找到 ⇒ 后面的读数都没有坐标')
    return best[0]


def row_runs(rows, ch, x0, x1, y, bg):
    """这一行里所有"不是背景"的横向段。"""
    segs, cur = [], None
    for x in range(x0, x1):
        hit = dist(px(rows, ch, x, y), bg) >= BG_TOL
        if hit and cur is None:
            cur = [x, x]
        elif hit:
            cur[1] = x
        elif cur is not None:
            if cur[1] - cur[0] + 1 >= MIN_RUN_PX:
                segs.append((cur[0], cur[1]))
            cur = None
    if cur is not None and cur[1] - cur[0] + 1 >= MIN_RUN_PX:
        segs.append((cur[0], cur[1]))
    return segs


def boxes(rows, ch, x0, x1, y0, y1, bg):
    """跨行合并：把同一列上连续几行的同位置段缝成矩形（够宽够高的才算容器，字被自然滤掉）。"""
    active, done = [], []
    for y in range(y0, y1):
        for (rx0, rx1) in row_runs(rows, ch, x0, x1, y, bg):
            host = None
            for a in active:
                if a[3] >= y - 3 and not (rx1 < a[0] - 3 or rx0 > a[1] + 3):
                    host = a
                    break
            if host is None:
                active.append([rx0, rx1, y, y])
            else:
                host[0] = min(host[0], rx0)
                host[1] = max(host[1], rx1)
                host[3] = y
        for a in list(active):
            if a[3] < y - 3:
                active.remove(a)
                done.append(tuple(a))
    done.extend(tuple(a) for a in active)
    return done


def ink_of(rows, ch, x0, x1, y0, y1, fill):
    core = []
    for y in range(y0 + 2, y1 - 2, 2):
        for x in range(x0 + 2, x1 - 2, 2):
            p = px(rows, ch, x, y)
            if dist(p, fill) >= INK_MIN:
                core.append(p)
    if not core:
        return None, 0, 0.0
    med = (median([p[0] for p in core]), median([p[1] for p in core]), median([p[2] for p in core]))
    return med, len(core), ratio(med, fill)


def premise(shots):
    """捕获通道的前提：这台机器上窗口是不是 key、App 是不是 active。

    为什么这条决定 Q2/Q3 能不能判：`.borderedProminent + .tint(.red)` 与侧栏选中胶囊
    都是从**系统 accent** 派生的颜色，而 AppKit 在非 key 窗口里会把 accent 去饱和成灰。
    本机这份读数就是 `面板key=false appActive=false` ⇒
    "那颗破坏性按钮没红" / "那颗胶囊里的蓝字对比度 3.5" 这两句话在这条通道上
    **量的是通道，不是产品**（R91 的焦点环零蓝像素是同一族）。所以这里把它们降级成 NOT-RUN，
    只保留几何与灰度那几条能判的读数。
    """
    path = os.path.join(shots, 'capture-readings.log')
    if not os.path.exists(path):
        return 'unknown'
    with open(path, encoding='utf-8', errors='replace') as handle:
        text = handle.read()
    if '面板key=false' in text or 'appActive=false' in text:
        return 'non-key'
    return 'key'


def inner_dividers(rows, ch, card, fill):
    """卡片**内部**有没有分隔线：只找"与卡片底色不同、横跨卡片九成宽、高 ≤3px"的行。

    为什么单独一条：内容列那把尺是拿"页面底色"当参照的，卡片内部的线比的是卡片底色，
    用页面底色当参照会把整张卡片读成一整块 ⇒ "其余四个分区 0 条分隔线"就成了假证据。
    """
    x0, x1, y0, y1 = card[:4]
    hits = []
    # 卡片自己的描边/渐变会在边缘 1~3px 处触发"整行都不同色"，那不是分隔线
    #（本机第一版就被隐私页的顶边骗出过一条 y=34pt 的"内线"，而那张卡片从 32pt 开始）。
    # 所以两边各让开 8pt，并且要求**同一方向**偏离：一条线是整行比底色暗（或亮），
    # 而抗锯齿边是混着来的。
    pad = int(13 * SCALE)
    for y in range(y0 + pad, y1 - pad):
        below = above = total = 0
        for x in range(x0 + 6, x1 - 6, 3):
            p, d = px(rows, ch, x, y), fill
            total += 1
            if max(p) - max(d) <= -4 or (sum(p) - sum(d)) <= -12:
                below += 1
            elif (sum(p) - sum(d)) >= 12:
                above += 1
        if total and max(below, above) / float(total) >= 0.9:
            hits.append(y)
    # 连续行合并成"一条线"
    lines, run = [], []
    for y in hits:
        if run and y != run[-1] + 1:
            lines.append(run[0]); run = [y]
        else:
            run.append(y)
    if run:
        lines.append(run[0])
    return [pt(y) for y in lines if len([h for h in hits if abs(h - y) < 3]) <= 3]


def scan(shots, frame, label, lines, accent='key'):
    path = os.path.join(shots, frame)
    if not os.path.exists(path):
        lines.append(F('NOT_RUN=%s 帧不存在 %s', label, frame))
        return None
    w, h, ch, rows = decode(path)
    cx = column_split(rows, ch, w, h)
    content = (cx + 20, w - 20)
    sidebar = (int(w * 0.02), cx - 4)
    bg = page_bg(rows, ch, w, h, content[0], content[1])
    sbg = page_bg(rows, ch, w, h, sidebar[0] + 8, sidebar[1])
    width_pt = pt(content[1] - content[0])
    lines.append(F('%s 帧=%dx%d 内容列左边界 x=%.0fpt（宽 %.0fpt）页面底色=rgb%s 侧栏底色=rgb%s',
                   label, w, h, pt(cx), width_pt, bg, sbg))

    cards, dividers, buttons = [], [], []
    for (x0, x1, y0, y1) in boxes(rows, ch, content[0], content[1],
                                  int(h * 0.06), int(h * 0.86), bg):
        bw, bh = (x1 - x0 + 1) / SCALE, (y1 - y0 + 1) / SCALE
        fill = median_color_in(rows, ch, x0, x1, y0, y1)
        if fill is None:
            continue
        if bh <= 3 and bw > width_pt * 0.9:
            dividers.append((y0, fill))
        elif bw > width_pt * 0.9 and bh >= 20:
            cards.append((x0, x1, y0, y1, fill))
        elif 30 <= bw <= 160 and 16 <= bh <= 60:
            buttons.append((x0, x1, y0, y1, fill))
    for i, (x0, x1, y0, y1, fill) in enumerate(cards):
        med, n, r = ink_of(rows, ch, x0, x1, y0, y1, fill)
        inner = inner_dividers(rows, ch, (x0, x1, y0, y1), fill)
        lines.append(F('  卡片#%d 框=(%.0f,%.0f)..(%.0f,%.0f)pt 填充=rgb%s 内墨=%s 颗=%d 对比=%.2f'
                       ' 内部线=%s',
                       i + 1, pt(x0), pt(y0), pt(x1), pt(y1), fill, med, n, r,
                       ' '.join('%.0fpt' % y for y in inner) or '无'))
    lines.append(F('  分隔线=%d 条 y=%s', len(dividers),
                   ' '.join('%.0fpt' % pt(y) for y, _f in dividers) or '无'))
    for (y, fill) in dividers:
        for (cx0, cx1, cy0, cy1, cfill) in cards:
            gap = min(abs(y - cy0), abs(y - cy1)) / SCALE
            if gap <= 6:
                lines.append(F('  Q1 分隔线 y=%.0fpt 距卡片(y=%.0f..%.0fpt) 边缘 %.1fpt ⇒ 同一层分组说了两遍'
                               '（卡片底色已经把它和上一段分开了）',
                               pt(y), pt(cy0), pt(cy1), gap))
    # 按钮：按"填充盒子"找（宽度 < 内容列九成、高度 16~60pt）。
    # R92 改完「数据」页之后这里必须换参照：三颗按钮从"压在页面底色上"变成"压在卡片底色上"，
    # 只拿页面底色当参照会把它们整批漏掉 —— 而"漏掉"在报表上长得和"这一屏没有按钮"一模一样
    #（本机第一版就是这么把它读成 NOT_RUN 的）。所以卡片外面按页面底色找，
    # 卡片里面再拿**卡片底色**找一遍，两批合并。
    candidates = list(buttons)
    for (cx0, cx1, cy0, cy1, cfill) in cards:
        for (x0, x1, y0, y1) in boxes(rows, ch, cx0 + 4, cx1 - 4, cy0 + 4, cy1 - 4, cfill):
            if 30 <= (x1 - x0 + 1) / SCALE <= 160 and 16 <= (y1 - y0 + 1) / SCALE <= 60:
                # 填充取**这个盒子自己**的中位色，不取卡片色：
                # 拿卡片色当填充会把按钮的灰底（235）算进"墨"里，报出"按钮填充=247"这种假读数。
                own = median_color_in(rows, ch, x0, x1, y0, y1)
                candidates.append((x0, x1, y0, y1, own if own else cfill))
    named = []
    seen = set()
    for (x0, x1, y0, y1, fill) in sorted(candidates, key=lambda b: (b[2], b[0])):
        if (x0, x1, y0, y1) in seen:
            continue
        seen.add((x0, x1, y0, y1))
        med, n, r = ink_of(rows, ch, x0, x1, y0, y1, fill)
        named.append((x0, x1, y0, y1, fill, med, n, r))
        lines.append(F('  按钮 框=(%.0f,%.0f)..(%.0f,%.0f)pt 填充=rgb%s 文字=%s 颗=%d 对比=%.2f 红占优=%s',
                       pt(x0), pt(y0), pt(x1), pt(y1), fill, med, n, r,
                       ('%d' % red_dominant(med)) if med else '无墨'))
    if len(named) >= 2:
        a, b = named[0], named[-1]
        same = dist(a[4], b[4]) <= 6 and (not a[5] or not b[5] or dist(a[5], b[5]) <= 12)
        head = F('  Q2 最左 vs 最右按钮：填充差=%d 文字差=%s ⇒ ',
                 dist(a[4], b[4]), dist(a[5], b[5]) if a[5] and b[5] else '量不到墨')
        if accent == 'non-key':
            # 产品里那颗是 `Button(role:.destructive).buttonStyle(.borderedProminent).tint(.red)`
            # （SettingsView.swift:658-660），而这条通道是非 key 窗口 ⇒ AppKit 把 accent 去饱和成灰。
            # ⇒ "两颗同填充"这句话今天**不能**读成"破坏性那颗没被区分"，只能读成"这条通道判不了颜色"。
            lines.append(head + 'NOT-RUN=ACCENT_IN_NON_KEY_CHANNEL（两颗填充确实相同，'
                                '但红色那一档来自 accent，非 key 窗口下系统会去饱和 ⇒ '
                                '"有没有被区分"这一格没判，见 PREMISE 行）')
        else:
            lines.append(head + ('同一套样式（破坏性那颗没有被区分）' if same else '两颗不同级'))
    else:
        lines.append(F('  Q2 NOT_RUN 只检出 %d 颗按钮填充 ⇒ 这一格没判', len(named)))

    pill = None
    sb_boxes = []
    for (x0, x1, y0, y1) in boxes(rows, ch, sidebar[0], sidebar[1],
                                  int(h * 0.06), int(h * 0.86), sbg):
        fill = median_color_in(rows, ch, x0, x1, y0, y1)
        if fill is None:
            continue
        sb_boxes.append((x0, x1, y0, y1, fill))
    # 判"这是那颗选中胶囊"用的是**相对**判据，不是绝对色相阈值。理由（本轮当场踩的）：
    # 早先这里抄了 R90 热图那格的 `色相 ≥25`，而实测这颗胶囊是
    # 亮 rgb(217,229,251) 色相=22 / 暗 rgb(28,43,64) 色相=21 —— 两档都差 3 就"没检出"，
    # 于是 Q3 被读成"今天没判"。给没量过的色号写阈值，就会把量到的东西读没。
    # 现在：色相 ≥12（淡蓝的下限）+ 与侧栏底色差 ≥12 + 高 ≥14pt + 宽 ≥ 侧栏六成，
    # 并且必须比这一列里**其它任何**盒子更蓝（正对照：拿它和未选中行比，而不是和一个常数比）。
    others = [chroma(b[4]) for b in sb_boxes]
    for (x0, x1, y0, y1, fill) in sb_boxes:
        if (chroma(fill) >= 12 and dist(fill, sbg) >= 12
                and (y1 - y0 + 1) / SCALE >= 14
                and (x1 - x0) > (sidebar[1] - sidebar[0]) * 0.6
                and chroma(fill) == max(others)):
            pill = (x0, x1, y0, y1, fill)
    if pill is None:
        lines.append('  Q3 NOT_RUN=SIDEBAR_PILL_NOT_FOUND 侧栏没检出蓝色胶囊 ⇒ 尺不瞎这条没过，'
                     '"胶囊里的字读不出来"这一格今天没判，不许读成没问题')
    else:
        x0, x1, y0, y1, fill = pill
        med, n, r = ink_of(rows, ch, x0, x1, y0, y1, fill)
        lines.append(F('  Q3 选中胶囊 框=(%.0f,%.0f)..(%.0f,%.0f)pt 填充=rgb%s 色相=%d（这一列最大色相=%d）'
                       ' 内墨=%s 颗=%d 对比=%.2f',
                       pt(x0), pt(y0), pt(x1), pt(y1), fill, chroma(fill), max(others), med, n, r))
        if accent == 'non-key':
            lines.append('  Q3 结论=NOT-RUN=ACCENT_IN_NON_KEY_CHANNEL 胶囊底色与标签蓝都从 accent 派生，'
                         '非 key 窗口下系统会去饱和 ⇒ 这个 3.5 是**通道**的读数，不是产品给人的对比度；'
                         '真机 key 窗口那一档没判（BACKLOG 130）')
        else:
            lines.append(F('  Q3 结论=%s', '对比 <4.5 ⇒ 正文级不达标' if r < 4.5 else '达标'))
    lowest = max([c[3] for c in cards] + [b[3] for b in buttons] + [d[0] for d in dividers])
    lines.append(F('  Q4 内容最低到 y=%.0fpt（帧高 %.0fpt）⇒ 下方空 %.0fpt',
                   pt(lowest), pt(h), pt(h) - pt(lowest)))
    return bg


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r92_shots'
    lines, got = [], {}
    accent = premise(shots)
    lines.append('PREMISE 通道=%s（%s）⇒ accent 派生的颜色那一档 %s'
                 % (accent, 'capture-readings.log 里的 面板key/appActive',
                    '判不了，Q2/Q3 记 NOT-RUN' if accent == 'non-key' else '可以判'))
    for mode in ('light', 'dark'):
        got[mode] = scan(shots, 'settings-data-720x540-%s.png' % mode, 'DATA ' + mode, lines, accent)
    probe = []
    scan(shots, 'settings-general-720x540-light.png', 'CONTROL general light', probe, accent)
    lines.append('CONTROL_GENERAL 卡片检出=%s' % ('是' if any('卡片#' in l for l in probe) else '否'))
    lines.extend('  | ' + l for l in probe if '卡片#' in l or '按钮' in l)
    # 跨分区对账：分组语言是"一张卡片包全部"还是"卡片 + 外面的分隔线"
    for page in ('settings-general', 'settings-shortcuts', 'settings-privacy',
                 'settings-stats-populated'):
        one = []
        scan(shots, '%s-720x540-light.png' % page, page, one, accent)
        cards = sum(1 for l in one if '卡片#' in l)
        outer = [l for l in one if l.strip().startswith('分隔线=')]
        inner = [l.split('内部线=')[1].strip() for l in one if '内部线=' in l]
        lines.append(F('GROUPING %s 卡片=%d %s 卡片内线=%s', page, cards,
                       outer[0].strip() if outer else '分隔线=?', ';'.join(inner) or '无'))
    if got.get('light') and got.get('dark'):
        d = dist(got['light'], got['dark'])
        lines.append(F('CROSS_MODE 页面底色差=%d %s', d,
                       'OK（帧确实切了主题）' if d >= 100 else '⇒ 差 <100，两帧可能同一主题，本轮读数作废'))
    text = '\n'.join(lines) + '\n'
    with open(OUT, 'w', encoding='utf-8') as handle:
        handle.write(text)
    print(text, end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
