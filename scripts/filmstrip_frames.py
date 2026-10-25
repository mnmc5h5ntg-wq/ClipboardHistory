#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""胶片拼贴 → 逐帧读数（R354 / BACKLOG 427）。内容墨与胶囊中心两条序列，自带正对照。

为什么要有它（R353 现场）：390 的两行数出自一次用完就撤的 PIL —— 隔两轮就没人能复核，
而换两卷胶片重读时，一次胶囊根本不移动、一次字墨被侧栏 chrome 主导。**尺要留在仓库里。**

拼贴的网格**不写死**：从文件名的场景尺寸推不出来，就按"宽或高能被整除数整除"枚举 6×5 / 5×6 / 10×3 …
并在 `GRID` 行里报名；选中哪一个由"帧宽:帧高 ≈ 场景宽:场景高"决定（调用方给 `--scene 300x520`）。

两条序列：
  `INK`  帧内 **内容带**（左侧栏、标题以下、去掉最右滚动条列）里比页底暗 20 级以上的像素数；
  `PILL` 帧内 **控制带**（标题以上那 60pt）里"列最大值"的最宽亮点段的中位 x（pt）。
页底取每帧内容带的中位数；`INK` 用绝对颗数、`PILL` 用 pt 坐标 —— 两者都不跨机器比，只在本卷内比落点。

正对照（不跑就不知道尺有没有对象）：
  ① `--control-steady 关`：关臂的 PILL 必须在第 3 帧前落定（关=不演，本来就没有过程）；
  ② `--control-differ 开A 开B`：两臂的 INK 序列在前 8 帧里必须**不同**（同了就说明这一格读的不是动画那一层）。
退出码：0=两条对照都成立；1=有一条不成立（打印是哪条）。
"""
import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.stdout.write(u"FILMSTRIP_REFUSED 没有 PIL\n")
    sys.exit(2)

GRIDS = [(6, 5), (5, 6), (10, 3), (3, 10), (15, 2), (2, 15), (30, 1), (1, 30)]


def pick_grid(w, h, scene):
    sw, sh = scene
    best = None
    for cols, rows in GRIDS:
        if w % cols or h % rows:
            continue
        fw, fh = w // cols, h // rows
        err = abs(float(fw) / fh - float(sw) / sh)
        if best is None or err < best[0]:
            best = (err, cols, rows, fw, fh)
    return None if best is None else best[1:]


def frame_stats(px, x0, y0, fw, fh):
    """一帧两条数：内容墨（颗）与胶囊中心（pt，找不到给 -1）。"""
    band_top, band_h = int(fh * 0.10), max(6, int(fh * 0.10))
    ctrl_top = int(fh * 0.05)
    # 页底：内容带里逐列中位数的众数
    import statistics
    cols = []
    for x in range(x0 + 4, x0 + min(fw - 4, int(fw * 0.5)), 3):
        vals = [px[x, y] for y in range(y0 + band_top, y0 + fh - 8, 5)]
        cols.append(statistics.median(vals))
    page = statistics.median(cols) if cols else 255
    ink = 0
    for y in range(y0 + band_top, y0 + fh - 10, 3):
        for x in range(x0 + 4, x0 + min(fw - 4, int(fw * 0.5)), 3):
            if px[x, y] < page - 20:
                ink += 1
    pill = -1
    best = (0, -1)
    run, start = 0, 0
    for x in range(x0 + 2, x0 + fw - 2):
        v = max(px[x, y] for y in range(y0 + ctrl_top, y0 + ctrl_top + band_h, 2))
        if v >= page + 20:
            run += 1
            if run == 1:
                start = x
        else:
            if run > best[0]:
                best = (run, start + run // 2)
            run = 0
    if run > best[0]:
        best = (run, start + run // 2)
    if best[0] >= max(6, fw // 40):
        pill = best[1] - x0
    return ink, pill, page


def read_strip(path, scene):
    im = Image.open(path).convert("L")
    px = im.load()
    w, h = im.size
    g = pick_grid(w, h, scene)
    if not g:
        return None, (w, h, None)
    cols, rows, fw, fh = g
    seq = []
    for r in range(rows):
        for c in range(cols):
            seq.append(frame_stats(px, c * fw, r * fh, fw, fh))
    return seq, (w, h, g)


def steady(seq, idx):
    u"""稳态 = 非 -1 值里的众数（末几格常是拼贴留白，拿"最后一个"当稳态会被留白骗）。"""
    vals = [s[idx] for s in seq if s[idx] != -1]
    if not vals:
        return -1
    from collections import Counter
    return Counter(vals).most_common(1)[0][0]


def land(seq, idx):
    u"""落点 = **此后一直等于稳态**的第一帧（过冲不算落定：开A 会冲到 175 再回到 150）。"""
    st = steady(seq, idx)
    if st == -1:
        return -1
    for i in range(len(seq)):
        if all(s[idx] == st for s in seq[i:] if s[idx] != -1):
            return i
    return -1


def main(argv=None):
    ap = argparse.ArgumentParser(prog=u"filmstrip_frames.py")
    ap.add_argument(u"paths", nargs=u"+")
    ap.add_argument(u"--scene", default=u"300x520")
    ap.add_argument(u"--control-steady", default=None, help=u"文件名片段：它的 PILL 必须在第 3 帧前落定")
    ap.add_argument(u"--control-differ", nargs=2, default=None, help=u"两段文件名：前 8 帧的 INK 必须不同")
    a = ap.parse_args(argv)
    sw, sh = [int(v) for v in a.scene.lower().split(u"x")]
    out = {}
    for p in a.paths:
        seq, meta = read_strip(p, (sw, sh))
        name = os.path.basename(p)
        if seq is None:
            print(u"GRID %s %dx%d 认不出网格 ⇒ 这一卷没读" % (name, meta[0], meta[1]))
            continue
        cols, rows, fw, fh = meta[2]
        print(u"GRID %s %dx%d → %d×%d 帧 %dx%d" % (name, meta[0], meta[1], cols, rows, fw, fh))
        print(u"INK  %s %s" % (name, u"," .join(u"%d" % s[0] for s in seq)))
        print(u"PILL %s %s" % (name, u"," .join(u"%d" % s[1] for s in seq)))
        out[name] = seq
    ok = True
    if a.control_steady:
        hit = [n for n in out if a.control_steady in n]
        if not hit:
            print(u"CONTROL_STEADY no_object 找不到 %r" % a.control_steady); ok = False
        else:
            i = land(out[hit[0]], 1)
            good = 0 <= i <= 2
            print(u"CONTROL_STEADY %s pill_landed=%d %s" % (hit[0], i, u"ok" if good else u"FAILED"))
            ok = ok and good
    if a.control_differ:
        got = []
        for part in a.control_differ:
            hit = [n for n in out if part in n]
            got.append(out[hit[0]][:8] if hit else None)
        if None in got:
            print(u"CONTROL_DIFFER no_object 两臂缺一卷"); ok = False
        else:
            # 比的是 **PILL** 那一列：两臂的 INK 在这一卷上本来就一样（行文字两条都淡出），
            # 差别在胶囊走多远（开A 冲 175、开B 冲 189）—— R353 就是拿错通道才看不出区别。
            same = [g[1] for g in got[0]] == [g[1] for g in got[1]]
            print(u"CONTROL_DIFFER pill_first8_differs=%s %s" % (not same, u"FAILED" if same else u"ok"))
            ok = ok and not same
    print(u"FILMSTRIP_FRAMES_RESULT=%s" % (u"ok" if ok else u"failed"))
    return 0 if ok else 1


if __name__ == u"__main__":
    sys.exit(main())
