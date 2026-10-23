# -*- coding: utf-8 -*-
u"""R315：逐分区量「底部留白比例」+ 分辨「贴边」的两种成因（滚动折 vs 文字被裁）。

为什么要这一支：R314 的看图腿判出「统计页空态下半屏 53% 是空白」，并据此开了一张单（371）。
当时缺的不是理由而是**对照** —— 没有其余分区的同一个数，"53%" 就还是形容词。
R315 开场查重把 371 撤了（那是 R9 的决定且已有判据钉着），但撤销当时只有理由没有数；
这一支就是补上那五个数，并且顺手把「墨带末行压在最后一行像素」这一格分辨清楚：

  · `距底=0` 本身**不判**任何东西 —— 两种成因判法相反：
      (a) ScrollView 的折：内容在折处被切开，用户滚动即可看全 ⇒ 不是缺陷；
      (b) 文字被裁：一行的下半截没了 ⇒ 是缺陷（R28 快捷键说明被截断那一族）。
  · 分辨用的是**行剖面**：健康形状是"最后一行文字之下还有一段空白"（对照臂
    `settings-recommendations` 实测 14 像素），被切的那一行则收口到帧底（实测 231→44→28）。

只读不改；帧是夹具造的，不含用户内容。
用法：python3 .scratch/motion-audit-2/measure_pane_whitespace_r315.py [帧目录]
结论行：
  `PANE_INK <帧名> 尺寸=WxH 底部留白比例=.. 距底=..`
  `PANE_EDGE <帧名> 末三行=.. 健康对照=.. 判=scroll-fold|complete|no-ink`
  `PANE_INK_DONE 页=.. 贴边=.. 对照余量=..`
"""
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure_empty_states_r314 import ink_band, mode_background, THRESHOLD  # noqa: E402
from PIL import Image  # noqa: E402

# 「健康」的下沿余量下限（像素）：低于这个值就按"贴边"处理，交给行剖面去分辨。
EDGE_EPS = 1
# 收口形状：文字行被切时，末几行的墨像素数会**单调下降但不归零**；
# 完整行的下面应当出现一段近零行（帧底留白）。
TAIL_BLANK = 6


def tail_rows(path, n=3):
    u"""取墨带末尾 n 行的墨像素数（自顶向下）。"""
    img = Image.open(path).convert(u"RGB")
    w, h = img.size
    px = img.load()
    bg = mode_background(px, w, h)
    _w, _h, y0, y1, _k = ink_band(path)
    if y1 is None:
        return []
    out = []
    for y in range(max(0, y1 - n + 1), y1 + 1):
        hit = 0
        for x in range(w):
            q = px[x, y]
            if max(abs(q[0] - bg[0]), abs(q[1] - bg[1]), abs(q[2] - bg[2])) > THRESHOLD:
                hit += 1
        out.append(hit)
    return out


def blank_below(path):
    u"""墨带末行之下还有几行近零行（>= 阈值以下的行）。"""
    img = Image.open(path).convert(u"RGB")
    w, h = img.size
    px = img.load()
    bg = mode_background(px, w, h)
    _w, _h, y0, y1, _k = ink_band(path)
    if y1 is None:
        return h
    k = 0
    for y in range(y1 + 1, h):
        hit = 0
        for x in range(w):
            q = px[x, y]
            if max(abs(q[0] - bg[0]), abs(q[1] - bg[1]), abs(q[2] - bg[2])) > THRESHOLD:
                hit += 1
        if hit >= 3:
            break
        k += 1
    return k


def main(directory):
    pats = [os.path.join(directory, u"settings-*-*.png")]
    names = sorted({p for g in pats for p in glob.glob(g)})
    if not names:
        print(u"PANE_INK_NO_FRAMES 目录=%s 里没有 settings 帧" % directory)
        return 1
    edge = 0
    control = None
    for p in names:
        n = os.path.basename(p)
        w, h, y0, y1, _k = ink_band(p)
        if y1 is None:
            print(u"PANE_INK %s 尺寸=%dx%d 墨带=无" % (n, w, h))
            continue
        bottom = 1.0 - (y1 + 1) / float(h)
        gap = h - 1 - y1
        print(u"PANE_INK %s 尺寸=%dx%d 底部留白比例=%.3f 距底=%d" % (n, w, h, bottom, gap))
        if gap <= EDGE_EPS:
            edge += 1
            t = tail_rows(p)
            b = blank_below(p)
            verdict = u"scroll-fold" if b < TAIL_BLANK else u"complete"
            print(u"PANE_EDGE %s 末三行=%s 下余=%d 判=%s" % (n, t, b, verdict))
        elif control is None and u"recommendations" in n:
            control = blank_below(p)
    print(u"PANE_INK_DONE 页=%d 贴边=%d 健康对照余量=%s 阈值=%d"
          % (len(names), edge, u"没读到" if control is None else control, THRESHOLD))
    return 0


if __name__ == u"__main__":
    d = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith(u"-") else u"/tmp/r314_shots"
    sys.exit(main(d))
