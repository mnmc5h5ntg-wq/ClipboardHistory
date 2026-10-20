#!/usr/bin/env python3
"""两态差尺：把「悬停那一档在产物像素上到底存不存在、多强」变成可复算的两个口径。

为什么要有这把尺（R240 / BACKLOG 272）：R239 量 251 的两处悬停位点时用的是一把临时尺，
它给出"带内均值比"这一个数，而那个数与历史账里"控件局部对比度"不是同一个估计量 ⇒ 不配给产品定罪。
本文件把两种口径**同时**交出来，谁也不许冒充谁：

  band_mean   —— 变化带（Δ>4 的像素包围盒）内**全部**像素的均值比。未变像素进分母，会被稀释。
  per_pixel   —— 只取**变化了**的像素，逐点算两态对比度后取中位数。这才是"控件局部"那一档。

配对按帧名推，不猜坐标：`X-hover-<尺寸>-<档>.png` 的静置态是 `X-<尺寸>-<档>.png` 或 `X-idle-<尺寸>-<档>.png`。
帧是 @2x，所以本尺**只用逐像素差**，不接受任何点坐标 —— R239 就是按点坐标取样把四个框全读成平涂背景的。

对照两把（缺任何一把都 exit 1，不许静默给绿）：
  负对照  任一帧 ↔ 自身 ⇒ 变化像素必须恰为 0
  正对照  名里给的一对**已知有变化**的帧 ⇒ 变化像素必须 > 0，且它的 per_pixel 就是"可分辨"的参照

名单为空 = 红（R99）：一个配对都没找到时不许打印"没有缺陷"。
用法：CLIPBOARD_HISTORY_UI_SHOTS=<目录> python3 scripts/hover_two_state_diff.py
  或 python3 scripts/hover_two_state_diff.py --shots <目录> --control modechip-hover-idle-200x60-dark,modechip-hover-lit-200x60-dark
"""
import argparse
import os
import statistics
import sys

from PIL import Image, ImageChops

DELTA = 4          # 逐通道差大于该值才算"这个像素变了"（与 frame_audit 同一门槛）
MIN_CHANGED = 50   # 正对照至少要看到这么多变化像素，否则算"尺读不到变化"

# ── 口径对账（R243 / D-229）─────────────────────────────────────────────────
# 仓库里的亮/暗地板（1.20 / 1.10）是 **WCAG 线性口径**：`UICaptureHarness.contrastRatio` 对每个
# 通道做 `c<=0.03928 ? c/12.92 : ((c+0.055)/1.055)**2.4` 再加 0.05 取比值。本尺原来的 `_ratio`
# 走的是**码值口径**（c/255 直接加 0.05）。两者在同一对像素上给的数不同：白底上 alpha=0.085 的
# 悬停层，码值口径读 1.09、WCAG 口径读 1.22 —— 拿 1.09 去比 1.20 那条地板会**造出一个假缺陷**
# （R240/D-225 拦下过一次改档，这次是同一个坑的第二种形状：不是估计量不同，是线性化不同）。
# 所以这把尺现在把两个口径一起交出来，谁也不许冒充谁，也不许拿一个去比另一个的地板。
def _lum(p):
    return (p / 255.0)


def _wcag_lum(p):
    c = p / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _ratio(a, b):
    hi, lo = (max(a, b), min(a, b))
    return (_lum(hi) + 0.05) / (_lum(lo) + 0.05)


def _ratio_wcag(a, b):
    hi, lo = (max(a, b), min(a, b))
    return (_wcag_lum(hi) + 0.05) / (_wcag_lum(lo) + 0.05)


def _open(path):
    return Image.open(path).convert('RGB')


def measure(dirpath, a_name, b_name):
    """返回 (两态差的两个口径 + 面积占比)。形状不一致或缺帧 ⇒ None（调用方点名）。"""
    fa, fb = os.path.join(dirpath, a_name + '.png'), os.path.join(dirpath, b_name + '.png')
    if not (os.path.exists(fa) and os.path.exists(fb)):
        return None
    ia, ib = _open(fa), _open(fb)
    if ia.size != ib.size:
        return None
    diff = ImageChops.difference(ia, ib)
    pa, pb = list(ia.getdata()), list(ib.getdata())
    changed = [n for n, d in enumerate(diff.getdata()) if max(d) > DELTA]
    total = ia.size[0] * ia.size[1]
    if not changed:
        return {'changed': 0, 'share': 0.0, 'band_mean': None, 'per_pixel': None, 'bbox': None}
    xs = [n % ia.size[0] for n in changed]
    ys = [n // ia.size[0] for n in changed]
    bbox = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    box = ia.crop(bbox), ib.crop(bbox)
    means = []
    for im in box:
        data = list(im.getdata())
        means.append(sum(sum(p) for p in data) / (3.0 * len(data)))
    per = [_ratio(sum(pa[n]) / 3.0, sum(pb[n]) / 3.0) for n in changed]
    per_wcag = [_ratio_wcag(sum(pa[n]) / 3.0, sum(pb[n]) / 3.0) for n in changed]
    return {'changed': len(changed), 'share': 100.0 * len(changed) / total,
            'band_mean': round(_ratio(means[0], means[1]), 3),
            'per_pixel': round(statistics.median(per), 3),
            'per_pixel_wcag': round(statistics.median(per_wcag), 3), 'bbox': bbox}


def find_pairs(dirpath):
    """按帧名配对：X-hover-… ↔ X-… / X-idle-…，返回 [(档, hover名, 静置名)]。"""
    names = sorted(f[:-4] for f in os.listdir(dirpath) if f.endswith('.png'))
    pairs, unpaired = [], []
    for n in names:
        if '-hover' not in n:
            continue
        ap = n[n.rfind('-'):]
        stem = n[:n.rfind('-')]
        base = stem.replace('-hover', '')
        for cand in (base + ap,                                   # glass-pill-120x232
                     stem.replace('-hover', '-idle') + ap,        # segmented-filter-idle-200x60
                     stem + '-idle' + ap):                        # X-hover-…-idle（少见形）
            if cand in names:
                pairs.append((ap, n, cand))
                break
        else:
            unpaired.append(n)
    return pairs, unpaired


def main():
    ap = argparse.ArgumentParser(description='两态差尺（带内均值 + 变化像素逐点中位数）')
    ap.add_argument('--shots', help='帧目录（默认取 CLIPBOARD_HISTORY_UI_SHOTS）')
    ap.add_argument('--min-pairs', type=int, default=1, help='至少要配到几对（覆盖率地板，本机实测 2）')
    ap.add_argument('--control', help='正对照：a,b 两个帧名（不含 .png），必须已知有变化')
    args = ap.parse_args()
    shots = args.shots or os.environ.get('CLIPBOARD_HISTORY_UI_SHOTS')
    if not shots or not os.path.isdir(shots):
        print('HOVER_DIFF_REFUSED 帧目录不可用（要 --shots 或 CLIPBOARD_HISTORY_UI_SHOTS）：%s' % shots)
        return 2
    rc = 0
    pairs, unpaired = find_pairs(shots)
    for n in unpaired:
        print('HOVER_DIFF 无静置态 %s ⇒ 这一位的两态对照不存在（251 的欠账形状）' % n)
    if not pairs:
        print('HOVER_DIFF_EMPTY=1 一个「悬停↔静置」配对都没找到 ⇒ 要么帧名形状漂了、要么两态帧不存在。这一支不许在空名单上给绿（R99）')
        return 1
    for app, hover, idle in pairs:
        m = measure(shots, hover, idle)
        if m is None:
            print('HOVER_DIFF 缺帧/尺寸不符 %s ↔ %s' % (hover, idle))
            rc = 1
            continue
        print('HOVER_DIFF %s 对=%s↔%s 带=%s 变化=%.1f%% 带内均值(码值)=%s 变化像素逐点中位(码值)=%s '
              '变化像素逐点中位(WCAG口径=%s，仓库的 1.20/1.10 地板是这个口径) '
              '⇒ 只有最后一列可以拿去和地板比' % (
                  app, hover, idle, m['bbox'], m['share'], m['band_mean'],
                  m['per_pixel'], m['per_pixel_wcag']))
    neg = measure(shots, pairs[0][1], pairs[0][1])
    if neg is None or neg['changed'] != 0:
        print('HOVER_DIFF_NEG_CONTROL=BAD 帧↔自身应当 0 个变化像素，读到 %s ⇒ 尺坏了，上面的数一律不算' % (
            None if neg is None else neg['changed']))
        rc = 1
    else:
        print('HOVER_DIFF_NEG_CONTROL=OK 帧↔自身 变化像素=0')
    if not args.control:
        print('HOVER_DIFF_POS_CONTROL=MISSING 没给 --control ⇒ 不许宣布"可分辨/不可分辨"，只报读数')
        rc = 1
    else:
        a, b = args.control.split(',', 1)
        pos = measure(shots, a, b)
        if pos is None or pos['changed'] < MIN_CHANGED:
            print('HOVER_DIFF_POS_CONTROL=BAD %s ↔ %s 变化像素=%s（要 ≥%d）⇒ 尺读不到已知变化' % (
                a, b, None if pos is None else pos['changed'], MIN_CHANGED))
            rc = 1
        else:
            print('HOVER_DIFF_POS_CONTROL=OK %s ↔ %s 变化=%.1f%% 带内均值=%s 逐点中位=%s' % (
                a, b, pos['share'], pos['band_mean'], pos['per_pixel']))
    if len(pairs) < args.min_pairs:
        print('HOVER_DIFF 配对=%d 低于 --min-pairs=%d ⇒ 覆盖率本身要红（不许只数"出现过"）' % (len(pairs), args.min_pairs))
        rc = 1
    print('HOVER_DIFF 配对=%d 无静置态=%d 目录=%s 退出=%d' % (len(pairs), len(unpaired), shots, rc))
    return rc


if __name__ == '__main__':
    sys.exit(main())
