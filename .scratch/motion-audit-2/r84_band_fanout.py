#!/usr/bin/env python3
'''BACKLOG 117 的量：骨架扫光的亮带到底是"一块光穿过整组条带"，还是"每根条各扫各的"。

输入是判据自己画出来的逐帧条带图（`MotionFilmstripTests.testSkeletonSweepActuallySweeps`
里的 `writeStrip("skeleton-sweep", …)`），不是产品截图，也不含任何用户内容。

方法（每一步都留了对照）：
  1. 一格里按行均值找出那三根条的 y 带（三根，间距 10pt）。
  2. 每根条沿 x 求亮度剖面，取"高于本行中位数 + 1"的那一段的**质心**当亮斑中心。
  3. 判据：
     * 假设 A（整组一条带）⇒ 三根条的亮斑**绝对** x 相同；
     * 假设 B（每根条自己的单位空间）⇒ 绝对 x 与条宽成正比，即 x_i / w_i 相同。
     条宽由 `SkeletonMotion.barFractions = [0.42, 0.86, 0.64]` 与格宽 420pt 推出：176.4 / 361.2 / 268.8。
  4. 正对照：同一根条在不同帧上的归一化位置必须**不同**（否则量的是静止画面）。

用法：
  sips -s format bmp <strip.png> --out /tmp/r82/strip.bmp
  python3 .scratch/motion-audit-2/r83_band_fanout.py /tmp/r82/strip.bmp
'''
import struct
import sys

COLS, ROWS = 6, 4
BAR_FRACTIONS = [0.42, 0.86, 0.64]


def load(path):
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    assert abs(h) % ROWS == 0 and w % COLS == 0, '条带图不是 %d 列 × %d 行' % (COLS, ROWS)
    return d, off, w, abs(h)


def main(path):
    d, off, w, h = load(path)
    CW, CH = w // COLS, h // ROWS
    pt = CW / 420.0          # 条带图按 1× 画的（writeStrip 里 first.width/2）

    def lum(cx, cy, x, y):
        i = off + ((cy * CH + y) * w + (cx * CW + x)) * 4
        return (d[i] + d[i + 1] + d[i + 2]) / 3.0

    def bars(cx, cy):
        prof = [(y, sum(lum(cx, cy, x, y) for x in range(0, CW, 4)) / (CW // 4))
                for y in range(CH)]
        base = sorted(v for _, v in prof)[len(prof) // 2]
        bands, cur = [], None
        for y, v in prof:
            if v > base + 1.0:
                cur = (y, y) if cur is None else (cur[0], y)
            else:
                if cur and cur[1] - cur[0] >= 3:
                    bands.append(cur)
                cur = None
        return bands[:3], base

    def centroid(cx, cy, y0, y1, bar_w):
        """亮斑中心，**只在这根条自己的 x 区间 [0, bar_w) 里量**。

        两个坑都在这一步（都是本轮现场踩的）：
        1. 第一版用"高于本行中位数 + 1"当亮带 ⇒ 量到的是整根条（条带底色本来就比窗口背景亮），
           于是第一根条的质心恒等于它的中点 88.0pt，24 帧一个数都不动。
           换成行内相对极值（最亮与最暗的中点以上）之后，量到的才是亮带。
        2. 剖面必须在**条内**取，且极大值必须贴在条内部：亮带还没扫进来或已经扫出去的那一帧，
           条内剖面是单调斜坡，"半程以上"的质心退化成条的中点 —— 那是个与相位无关的假数
           （最后一帧就是这么来的：0.505 / 0.952 / 0.504，散布 0.448 全是它贡献的）。
        返回 (质心 px, 峰谷差, 亮带在不在条内)。
        """
        hi_x = int(round(bar_w * pt))
        vals = [sum(lum(cx, cy, x, y) for y in range(y0, y1 + 1)) / (y1 - y0 + 1)
                for x in range(hi_x)]
        if not vals:
            return -1.0, 0.0, False
        lo, hi = min(vals), max(vals)
        thr = lo + 0.5 * (hi - lo)
        xs = [i for i, v in enumerate(vals) if v >= thr]
        # R84 把估计量从『高于半程的那段质心』换成**峰值列本身**（argmax）：
        # 质心会被条端切掉的那一半拉走（亮带扫过短条右端时残差 10pt），而峰值列不会 ——
        # 仓库里那把尺（`MotionFilmstripTests.bandFramePeaks`）用的就是 argmax，
        # 两份实现要能对上，估计量必须先统一。
        peak = max(range(len(vals)), key=lambda i: vals[i])
        cen = float(peak)
        inside = 10 < peak < hi_x - 10
        return cen, hi - lo, inside

    widths = [f * 420.0 * pt for f in BAR_FRACTIONS]
    print('条带宽（pt）= %s（由 barFractions × 格宽 420pt 推出，量出来的 y 带与它一致）'
          % ['%.1f' % v for v in widths])
    max_norm_spread, max_abs_spread = 0.0, 0.0
    seen = set()
    used = rejected = 0
    amp_floor = 5.0        # 灰阶：亮带扫过一根条时该行峰谷差实测 23–26，没扫过时 ~2
    for (cx, cy) in [(c, r) for r in range(ROWS) for c in range(COLS)]:
        bands, _ = bars(cx, cy)
        if len(bands) < 3:
            continue
        # 幅度地板：亮带没扫到某一根条的那一帧，那一根条的剖面里只有底色，
        # "半程以上"就退化成"整根条"⇒ 质心变成条的中点（一个与相位无关的假数）。
        # 所以这种帧必须**丢掉并数出来**，不许让它进散布。
        read = [centroid(cx, cy, y0, y1, wd) for (y0, y1), wd in zip(bands, widths)]
        amps = [a for _, a, _ in read]
        if min(amps) < amp_floor or not all(f for _, _, f in read):
            rejected += 1
            continue
        cents = [c / pt for c, _, _ in read]
        norms = [c / wd for c, wd in zip(cents, widths)]
        # **同一帧内**三根条之间的散布才是这题的判据（跨帧的散布量的是"带走了多远"，那是正对照）
        spread_norm = max(norms) - min(norms)
        spread_abs = max(cents) - min(cents)
        max_norm_spread = max(max_norm_spread, spread_norm)
        max_abs_spread = max(max_abs_spread, spread_abs)
        seen.add(round(norms[0], 2))
        used += 1
        if (cx + cy) % 3 == 0:
            print('  帧(%d,%d) 绝对中心=%s pt  归一化=%s' % (
                cx, cy, ['%.1f' % v for v in cents], ['%.3f' % v for v in norms]))
    print('用了 %d 帧，丢掉 %d 帧（亮带没扫到全部三根条：幅度低于 %.0f 灰阶，或剖面是单调斜坡=极大值贴在边上）'
          % (used, rejected, amp_floor))
    print('结论：**同一帧内**三根条的绝对中心最大相差 %.0f pt，而归一化中心最大只差 %.3f（=%.0f pt 在最宽那根上）'
          % (max_abs_spread, max_norm_spread, max_norm_spread * widths[1]))
    print('正对照（同一根条跨帧必须移动）：不同帧上第一根条的归一化中心共 %d 个不同取值 %s'
          % (len(seen), sorted(seen)[:12]))
    verdict = ('B（每根条各扫各的）' if max_norm_spread < 0.02 and max_abs_spread > 20
               else 'A（整组一条带）' if max_abs_spread < 8 else '分不开')
    print('⇒ 支持假设 %s；地板：归一化散布 < 0.02 判 B、绝对散布 < 8pt 判 A' % verdict)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/r82/strip.bmp')
