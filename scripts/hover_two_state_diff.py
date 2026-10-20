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
import re
import statistics
import sys

from PIL import Image, ImageChops

DELTA = 4          # 逐通道差大于该值才算"这个像素变了"（与 frame_audit 同一门槛）
MIN_CHANGED = 50   # 正对照至少要看到这么多变化像素，否则算"尺读不到变化"
# 仓库自己的可见性地板（`UICaptureHarness` 里 R220 骨架条带 / R225 浮层悬停 / R229 小控件三处沿用）。
# **这两条是 WCAG 线性口径的数** —— 只有 `per_pixel_wcag` 那一列有资格和它们比（D-229）。
FLOOR_LIGHT, FLOOR_DARK = 1.20, 1.10
# 底"平涂"的判据：静置帧在变化带里众数占到这个比例以上，才认为那一块底是平的。
# 为什么要有这一格：R242 在同一次 CI 里看到 runner 的 `空闲=236 点亮=204`、本机 `255→220`
# —— runner 那片底被抖成许多小格子。底不平涂时"对底比值"没有单一的底可对，
# 那种格子只能报读数，不能拿去判过线/不过线（否则又造一次跨机假红）。
FLAT_SHARE = 0.70
# 门槛是量出来的，不是拍的（R244）：本机 162 帧里六对真帧的底众数占比 = 0.962 / 0.955 / 0.931 / 0.892 / 0.828 / 0.827（真帧的底上有字形，所以到不了 1.0）；棋盘抖动对照 = 0.500；runner 那片被抖成许多小格子的底（R242：空闲=236 而本机=255）会更低。取 0.70 = 最低真帧读数（0.827）之下留 0.13 余量、又在抖动对照之上留四成空间。注：第一版这条占比算在了**点亮那帧**上（measure 的 a 是 hover、b 是 idle，我用错了 pa），于是真帧读数全被压到 0.741~0.957 且合成棋盘格被判成平涂 —— 是合成对照格把它红出来的。

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
    # 底平不平涂：静置帧在变化带里，众数灰阶占多少颗。不平涂 ⇒ 地板判定没有对象，只报读数。
    # 「底」取的是**变化像素在静置帧上的那些值** —— 不是整个包围盒：
    # 包围盒把字形与四周都算进来，那里永远不平涂（第一版就是这么把六对全判成"底不平涂"的）。
    greys = [int(round(sum(pb[n]) / 3.0)) for n in changed]
    mode_grey = max(set(greys), key=greys.count)
    base_share = greys.count(mode_grey) / float(len(greys))
    flat = base_share >= FLAT_SHARE
    med_wcag = statistics.median(per_wcag)
    floor = FLOOR_LIGHT if 'light' in b_name else FLOOR_DARK
    verdict = ('只报读数（底不平涂）' if not flat
               else ('过线' if med_wcag >= floor else '低于地板'))
    return {'changed': len(changed), 'share': 100.0 * len(changed) / total,
            'band_mean': round(_ratio(means[0], means[1]), 3),
            'per_pixel': round(statistics.median(per), 3),
            'per_pixel_wcag': round(med_wcag, 3), 'bbox': bbox,
            'idle_flat': flat, 'base_share': round(base_share, 3), 'floor': floor, 'verdict': verdict}


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


def rung_from_readings(text, machine):
    """305 的尺：相邻两档（悬停↔按下）的台阶，从**判据自己印的灰阶**里算，不去重扫 PNG。

    为什么读日志而不是读帧：灰阶众数那一步住在 Swift 的 `pillReading` 里，在 python 再写一份
    就是第二个定义处（R229/R230 那一族：两份定义会各自算出两个数还互相掩盖）。这里只借用
    本文件已有的 `_ratio_wcag`，输入是判据印出来的三个灰阶 ⇒ 两台机器走同一条代码，地板才推得出来。

    校准是这条尺的**正对照**：用判据自印的灰阶重算"悬停对底""按下对底"两个比值，
    必须复现判据自己印的那两个数（误差 ≤0.002）。复现不了就是两把尺在读不同对象，
    台阶数一律不算。返回 (行列表, 退出码)。
    """
    rows, rc = [], 0
    pat = re.compile(
        r'PRESS_LADDER_PROOF (light|dark) 底 idle=(\d+) hover=(\d+) press=(\d+)'
        r'｜药丸 idle=(\d+) hover=(\d+) press=(\d+)'
        r'｜比值 ([\d.]+) → ([\d.]+)')
    found = pat.findall(text)
    if not found:
        return (['RUNG_STEP_EMPTY=1 日志里一行 PRESS_LADDER_PROOF 都没有 ⇒ 这台机器没量到按下档，'
                 '不许在空名单上给绿（R99）'], 1)
    seen = set()
    for tag, _bi, _bh, _bp, _pi, hover, press, r0, r1 in found:
        seen.add(tag)
        # 底：三个 idle/hover/press 的底是同一片纸，取判据印的 hover 那一格
        bg = int(re.search(r'PRESS_LADDER_PROOF ' + tag + r' 底 idle=(\d+)', text).group(1))
        mine0, mine1 = _ratio_wcag(bg, int(hover)), _ratio_wcag(bg, int(press))
        step = _ratio_wcag(int(hover), int(press))
        calib_ok = abs(mine0 - float(r0)) <= 0.002 and abs(mine1 - float(r1)) <= 0.002
        if not calib_ok:
            rc = 1
            rows.append('RUNG_STEP_CALIB=BAD %s 用判据自印的灰阶重算得 %.3f/%.3f，而它印的是 %s/%s'
                        ' ⇒ 两把尺在读不同对象，台阶数不算' % (tag, mine0, mine1, r0, r1))
            continue
        rows.append('RUNG_STEP %s %s 悬停=%s 按下=%s 底=%s｜悬停→按下台阶(WCAG)=%.3f'
                    '｜悬停对底=%s 按下对底=%s｜判定=只印不判（305：地板要两机各读一次才推）'
                    % (machine, tag, hover, press, bg, step, r0, r1))
    for need in ('light', 'dark'):
        if need not in seen:
            rc = 1
            rows.append('RUNG_STEP_INCOMPLETE %s 档没有按下态读数 ⇒ 两档对照不存在，不许只按有读数的那档下结论'
                        % need)
    return rows, rc


def main():
    ap = argparse.ArgumentParser(description='两态差尺（带内均值 + 变化像素逐点中位数）')
    ap.add_argument('--shots', help='帧目录（默认取 CLIPBOARD_HISTORY_UI_SHOTS）')
    ap.add_argument('--min-pairs', type=int, default=1, help='至少要配到几对（覆盖率地板，本机实测 2）')
    ap.add_argument('--control', help='正对照：a,b 两个帧名（不含 .png），必须已知有变化')
    ap.add_argument('--readings', help='305 的尺：从判据自己印的日志算「相邻两档台阶」，不重扫帧')
    ap.add_argument('--machine', default='', help='读数归属的机器键（喂 runner 日志时要显式写，别默认成本机）')
    args = ap.parse_args()
    machine = args.machine or ('local:' + (os.uname().nodename if hasattr(os, 'uname') else 'unknown'))
    if args.readings:
        try:
            with open(args.readings, encoding='utf-8', errors='replace') as f:
                text = f.read()
        except OSError as e:
            print('RUNG_STEP_REFUSED 读不到日志 %s（%s）' % (args.readings, e))
            return 2
        rows, rc = rung_from_readings(text, machine)
        for row in rows:
            print(row)
        print('RUNG_STEP 行数=%d 机器=%s 退出=%d' % (len(rows), machine, rc))
        return rc
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
              '变化像素逐点中位(WCAG口径=%s) 地板=%s 底平涂=%s 判定=%s '
              '⇒ 只有 WCAG 那一列可以拿去和地板比（D-229）' % (
                  app, hover, idle, m['bbox'], m['share'], m['band_mean'],
                  m['per_pixel'], m['per_pixel_wcag'], m['floor'],
                  '是' if m['idle_flat'] else '否', m['verdict']))
        print(u'HOVER_DIFF_BASE %s 底众数占比=%s（平涂线 %s）' % (app, m['base_share'], FLAT_SHARE))
        if m['verdict'] == u'低于地板':
            print('HOVER_DIFF_FLOOR_RED=1 %s 的悬停在 WCAG 口径下只有 %s（地板 %s）⇒ 这一档反馈淡到没有读者'
                  % (hover, m['per_pixel_wcag'], m['floor']))
            rc = 1
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
