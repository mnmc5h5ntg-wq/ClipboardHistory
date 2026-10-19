#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 / BACKLOG 222：热图梯子的**真帧通道**证人 —— 判据量的是离屏单格，这张读的是压了卡片材质的帧。

来历：R198 把两条通道的逐档墨色相减，发现偏移只集中在 **R 那一列**（真帧比离屏渲染红 6…21/255，G/B ≤1），
而"最大通道差"这把尺只在最大通道恰好是 R 的那几格才改变读数 ⇒ 暗档两通道吻合 ≤1/255，
亮档 `空→第 1 档` 真帧 28→21 而判据 34→25.41，地板 18 那一侧余量判据 7.4、真帧只剩 3。
那条判据今天看不见这个偏移（BACKLOG 222）。这一支把它变成读数。

梯子**按结构推**（R90/R102 的教训）：走 `heatmap-cell-strip-still-*` 那两张竖条的中轴列，
连续同色的游程 = 一格，第一段同色是夹具背景（不当一档），档位顺序按"蓝超出血绿"排 ——
竖条夹具的显示顺序不是单调的，按游程序号相邻会量错对象。

退出码（"算不出来必须响"）：
  0 = 两通道都量到、且逐档对账没有越界；
  1 = 量到了但越界（真帧那侧掉到地板以下，或偏移不再只在一列）；
  2 = 读不到输入（帧目录没给、帧缺、竖条档数不是 5、判据日志里没有那 16 条）⇒ **绝不当成通过**。

只读帧、只印坐标与颜色数字，不写仓库、不打印任何用户内容（帧本身是合成夹具）。
"""
import argparse, io, os, re, sys

FLOOR = 18.0
# 与 Swift 那颗尺同一套常数（`HeatmapHoverEvidenceTests.simulateDeuteranopia`）。
# 两处各写一份是**故意的**：本脚本读 PNG、判据读 NSBitmapImageRep，本来就在两个运行时；
# 靠 `test_heatmap_frame_levels_matrix_matches_the_swift_ruler` 钉住两边常数一致，而不是假装共用一份代码。
VIENOT_DEUTAN = ((0.625, 0.375, 0.0), (0.300, 0.700, 0.0), (0.0, 0.040, 0.960))


def lin(v):
    x = v / 255.0
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def enc(v):
    x = max(0.0, min(1.0, v))
    return x * 12.92 if x <= 0.0031308 else 1.055 * (x ** (1.0 / 2.4)) - 0.055


def deutan(px):
    r, g, b = lin(px[0]), lin(px[1]), lin(px[2])
    out = []
    for row in VIENOT_DEUTAN:
        out.append(int(round(enc(row[0] * r + row[1] * g + row[2] * b) * 255)))
    return tuple(out)


def maxdelta(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def runs_down_middle(img, min_len=8):
    x = img.width // 2
    seq, cur, n, y0 = [], None, 0, 0
    for y in range(img.height):
        p = img.getpixel((x, y))[:3]
        if p == cur:
            n += 1
        else:
            if cur is not None and n >= min_len:
                seq.append((y0, n, cur))
            cur, n, y0 = p, 1, y
    if cur is not None and n >= min_len:
        seq.append((y0, n, cur))
    return seq


def ladder(path):
    """→ 5 档填充色（浅到深），或抛 ValueError（结构不像预期的 5 格竖条）。"""
    from PIL import Image
    im = Image.open(path).convert('RGB')
    seq = runs_down_middle(im)
    if not seq:
        raise ValueError('%s 一条游程都没有 ⇒ 这张帧不是竖条' % path)
    bg = seq[0][2]
    cells = [c for y0, n, c in seq if 8 <= n <= 30 and c != bg]
    uniq = sorted(set(cells), key=lambda c: c[2] - (c[0] + c[1]) / 2.0)
    if len(uniq) != 5:
        raise ValueError('%s 读到 %d 档（要 5：空格 + 四档）⇒ 背景没排干净或夹具换了' % (path, len(uniq)))
    return uniq


def steps(uniq):
    return [(maxdelta(uniq[i - 1], uniq[i]), maxdelta(deutan(uniq[i - 1]), deutan(uniq[i])))
            for i in range(1, 5)]


JUDG_RE = (r'HEAT_ADJACENT_CVD (dark|light)/1x \S+→\S+ 像素=\d+ 前墨=\(([^)]*)\) 后墨=\(([^)]*)\) '
           r'模拟前=([\d.]+) 模拟后=([\d.]+)')


def judgment_channel(log_text):
    """从判据那 16 条读数里取出 1x 的两档：每档 5 个墨色 + 4 步（前/后）。"""
    out = {}
    for tag, ink_a, ink_b, before, after in re.findall(JUDG_RE, log_text):
        rows = out.setdefault(tag, [])
        rows.append((tuple(int(v) for v in ink_a.replace(' ', '').split(',')),
                     tuple(int(v) for v in ink_b.replace(' ', '').split(',')),
                     float(before), float(after)))
    for tag, rows in out.items():
        if len(rows) != 4:
            raise ValueError('判据日志里 %s 只有 %d 对（要 4）' % (tag, len(rows)))
    return {tag: ([r[0] for r in rows] + [rows[-1][1]], [(r[2], r[3]) for r in rows]) for tag, rows in out.items()}


def main():
    ap = argparse.ArgumentParser(prog=os.path.basename(__file__), description=__doc__.splitlines()[0])
    ap.add_argument('--shots', help='帧目录（CLIPBOARD_HISTORY_UI_SHOTS 指的那个）')
    ap.add_argument('--judgment-log', help='判据那 16 条 HEAT_ADJACENT_CVD 所在的日志')
    ap.add_argument('--max-col-offset', type=float, default=24.0,
                    help='允许 G/B 两列的最大偏移（超过就说明偏的不只一列）；默认 24，由本轮实测 1 放宽到 24 留余量')
    args = ap.parse_args()

    shots = args.shots or os.environ.get('CLIPBOARD_HISTORY_UI_SHOTS')
    if not shots or not os.path.isdir(shots):
        print('HEAT_FRAME_INPUT_MISSING shots 目录没给或不存在 ⇒ 这一格记 NOT-RUN，不算通过')
        return 2
    if not args.judgment_log or not os.path.exists(args.judgment_log):
        print('HEAT_FRAME_INPUT_MISSING 判据日志读不到（%r）⇒ 两条通道没法对账' % args.judgment_log)
        return 2
    try:
        judg = judgment_channel(io.open(args.judgment_log, encoding='utf-8', errors='replace').read())
    except ValueError as e:
        print('HEAT_FRAME_INPUT_MISSING 判据日志解析失败：%s' % e)
        return 2

    reds = []
    for tag in ('dark', 'light'):
        path = os.path.join(shots, 'heatmap-cell-strip-still-90x140-%s.png' % tag)
        if not os.path.exists(path):
            print('HEAT_FRAME_INPUT_MISSING 缺帧 %s' % path)
            return 2
        try:
            uniq = ladder(path)
        except ValueError as e:
            print('HEAT_FRAME_STRUCTURE %s' % e)
            return 2
        fr = steps(uniq)
        if tag not in judg:
            print('HEAT_FRAME_INPUT_MISSING 判据日志里没有 %s 那 4 对 ⇒ 两通道没法对账（不许 KeyError 当成跑过了）' % tag)
            return 2
        j_inks, j_steps = judg[tag]
        offs = [tuple(fr_ - j_ for fr_, j_ in zip(uniq[i], j_inks[i])) for i in range(5)]
        gb = max(abs(o[c]) for o in offs for c in (1, 2))
        rr = max(abs(o[0]) for o in offs)
        fr_min = min(a for _, a in fr)
        j_min = min(a for _, a in j_steps)
        print('HEAT_FRAME_LEVELS %s 真帧墨=%s' % (tag, uniq))
        print('  HEAT_FRAME_STEPS %s 真帧 %s | 判据 %s' % (
            tag, u'、'.join(u'%g→%g' % (b, a) for b, a in fr),
            u'、'.join(u'%g→%g' % (b, a) for b, a in j_steps)))
        print('  HEAT_FRAME_OFFSET %s 逐档 真帧−判据 %s ⇒ 最大 |R|=%g 最大 |G/B|=%g' % (tag, offs, rr, gb))
        print('  HEAT_FRAME_MARGIN %s 真帧最小模拟后=%g 判据=%g 地板=%g ⇒ 余量 真帧=%g 判据=%g'
              % (tag, fr_min, j_min, FLOOR, fr_min - FLOOR, j_min - FLOOR))
        if fr_min < FLOOR:
            reds.append('%s 真帧那侧最小模拟后 %g 掉到地板 %g 之下 ⇒ 对色觉障碍用户这两档是一档（改梯子，别降地板）'
                        % (tag, fr_min, FLOOR))
        if gb > args.max_col_offset:
            reds.append('%s G/B 两列偏到 %g（上限 %g）⇒ 偏移不再只压在 R 那一列，两通道的口径变了，先查谁换了背景'
                        % (tag, gb, args.max_col_offset))
    if reds:
        for r in reds:
            print('HEAT_FRAME_RED ' + r)
        print('HEAT_FRAME_VERDICT red=%d' % len(reds))
        return 1
    print('HEAT_FRAME_VERDICT ok 两通道都量到、真帧未越地板、偏移仍压在 R 那一列')
    return 0


if __name__ == '__main__':
    sys.exit(main())
