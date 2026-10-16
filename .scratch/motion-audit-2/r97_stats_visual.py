#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R97 的看图仪器（第一腿）：**"卡片填充"这个概念在帧里到底是怎么被认出来的**。

起因是 R96 的两条 declined 读数互相说不通：
    settings-stats            未判原因=整带没有卡片（全是页面底）
    settings-stats-populated  未判原因=卡片里没有一行被判成墨 ⇒ 尺没压住字
而源码里「统计」这一屏**根本没有 `GroupBox`**（`SettingsView.statsSection` 直接放
`DailyCopyStatsSection`）。

我先假设是"热图那块有底色的区域被认成卡片"，**这个假设被这一支自己否掉了**：
逐行众数扫下来，热图那些格子的行众数**全都等于页面底**（格子只占一行宽度的两三成，
众数仍是白），一整块 ≥8pt 的候选带一个都没有。

真正的机制只有一格那么小：`cardRowKinds` 里
    fill = modals.first(where: { abs($0 - pageLuma) > 3 })
"第一行离页面底 >3 就算卡片填充" —— 而在「统计」这一屏，**第一行满足条件的是那条 1pt 的
`Divider()`**（实测 y=271.0 与 271.5 两行，众数 228，占该行 1048/1120 个像素）。
于是填充=线的颜色，而下一格又把"众数==页面底"的行一律判成 `.outside` ⇒
带子里所有**文字行**（众数都是页面底）连参加墨计数的资格都没有 ⇒ `墨行=0`。
一条 1pt 的横线当上了"卡片"，然后这张"卡片"里当然没有字。

这一支就把这件事量出来并钉成正对照：
  ① 真卡片（`settings-shortcuts` / `settings-data`）：`fill` 那一行必须属于一段 ≥40pt 的稳定带；
  ② `settings-stats-populated`：`fill` 必须落在一段 ≤2px 的带上（就是那条线）；
  ③ `settings-stats`（空态）：一条候选都没有（与 R96 的"整带没有卡片"同形）。
三条里任何一条反了 ⇒ 是本仪器错了，不是产品错了。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/r97_stats_visual.py <帧目录>
退出码：0 = 三条自检全过；1 = 有自检不过。
"""
import os
import sys

from PIL import Image

BAND_X0, BAND_X1 = 155.0, 715.0     # 内容列（pt）：与判据同一条带
BAND_Y0 = 60.0                      # 判据的带上沿（写死的那一格，R97 要改的就是它）
STEP = 8                            # 色档宽度，与判据里的 `/ 8` 一致
GATE = 3                            # "离页面底多远算不是页面底"，与判据里的 >3 一致


def row_modal(px, y, x0, x1):
    hist = {}
    for x in range(x0, x1):
        r, g, b = px[x, y]
        k = int(0.2126 * r + 0.7152 * g + 0.0722 * b) // STEP
        hist[k] = hist.get(k, 0) + 1
    key, count = max(hist.items(), key=lambda kv: kv[1])
    return key * STEP + STEP // 2, count


def scan(path):
    """返回 (页面底, 逐行众数列表, 第一格候选所属的连续带)。"""
    img = Image.open(path).convert('RGB')
    w, h = img.size
    scale = float(w) / 720.0
    px = img.load()
    x0, x1 = int(BAND_X0 * scale), int(min(w, BAND_X1 * scale))
    y0, y1 = int(BAND_Y0 * scale), h
    page, _ = row_modal(px, int((BAND_Y0 - 52) * scale), x0, x1)   # 窗口最上面那一条
    modals = [row_modal(px, y, x0, x1)[0] for y in range(y0, y1)]
    widths = [row_modal(px, y, x0, x1)[1] for y in range(y0, y1)]
    first = None
    for i, m in enumerate(modals):
        if abs(m - page) > GATE:
            first = i
            break
    if first is None:
        return page, scale, None, 0
    fill = modals[first]
    a = first
    while a > 0 and abs(modals[a - 1] - fill) <= GATE:
        a -= 1
    b = first
    while b < len(modals) - 1 and abs(modals[b + 1] - fill) <= GATE:
        b += 1
    # **连续带高**不够用：正对照自己就不够 —— 快捷键那张真卡片的连续带只有 34.5pt，
    # 因为卡片里字多的行会把众数顶到别的档上（实测 69px 就断）。
    # 所以再量一格"整条带里有多少行的众数落在这个档上"（不要求连续）：
    # 卡片会被字打断但仍然到处是它自己的底色，而一条线只有它自己那 2px。
    total = sum(1 for m in modals if abs(m - fill) <= GATE)
    return page, scale, dict(row=first, fill=fill, top_pt=BAND_Y0 + a / scale,
                             height_pt=(b - a + 1) / scale,
                             total_pt=total / scale,
                             share=float(widths[first]) / max(1, x1 - x0)), b - a + 1


def main():
    shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r96_shots'
    cases = [('settings-shortcuts', '真卡片(快捷键)', 'card'),
             ('settings-data', '真卡片(数据)', 'card'),
             ('settings-stats-populated', '热图那一屏(有数据)', 'line'),
             ('settings-stats', '热图那一屏(空态)', 'none')]
    problems, table = [], []
    for name, label, expect in cases:
        for tag in ('light', 'dark'):
            path = os.path.join(shots, '%s-720x540-%s.png' % (name, tag))
            if not os.path.exists(path):
                problems.append(u'缺帧 %s' % path)
                continue
            page, scale, cand, rows = scan(path)
            kind = (u'卡片(整带 %dpx 里 %dpx 是它)' % (int(440 * scale), int(cand['total_pt'] * scale))) \
                if (cand and cand['total_pt'] >= 40) \
                else (u'%dpx 的一条线(占行 %.2f)' % (rows, cand['share']) if cand else u'无候选')
            print(u'%-22s %-6s 页底=%-3d 候选填充=%-3s 起于 y=%-6s 连续=%-6s 总高=%-6s ⇒ %s'
                  % (label, tag, page,
                     cand['fill'] if cand else '-',
                     ('%.1f' % cand['top_pt']) if cand else '-',
                     ('%.1fpt' % cand['height_pt']) if cand else '-',
                     ('%.1fpt' % cand['total_pt']) if cand else '-',
                     kind))
            got = 'none' if cand is None else ('card' if cand['total_pt'] >= 40 else 'line')
            table.append((name, tag, expect, got, cand))
            if got != expect:
                problems.append(u'%s/%s 期望=%s 实得=%s ⇒ 假设或仪器错了' % (name, tag, expect, got))
    print(u'\n== 自检（三条都要过：真卡片=高带、统计页=1pt 的线、空态=无候选）')
    for p in problems:
        print(u'  SELF-CHECK FAIL %s' % p)
    print(u'  形状统计=%s' % u' '.join(u'%s/%s:%s' % (n, t, g) for n, t, _, g, _ in table))
    print(u'  SELF-CHECK %s' % ('OK' if not problems else 'FAIL'))
    if not problems:
        print(u'\n结论：`fill` 的"第一行离页面底>3"这条定义会让一条 1pt 的 `Divider()` 当上卡片，'
              u'而下一格"众数==页面底 ⇒ .outside"又把带子里所有文字行挡在墨计数之外 ⇒ '
              u'`墨行=0` 与"这一屏没有卡片"其实是同一件事的两种说法。'
              u'\n修法（门槛从上面那组数里取，不是拍的）：卡片填充要按**整带里有多少行落在这个档上**判，'
              u'实测真卡片是 176.5–217.0pt（带子总共 440pt），而那条线是 1.0pt ⇒ '
              u'地板取 20pt：离两边都远，且给"只有一行的卡片"（如「通用」）留了余量。'
              u'\n注意**不能**用"连续带高"当判据：快捷键那张真卡片的连续带只有 34.5pt'
              u'（卡片里字多的行会把众数顶到别的档上），正对照当场就不绿了。')
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
