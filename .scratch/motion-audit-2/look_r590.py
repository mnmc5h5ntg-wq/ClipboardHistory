# -*- coding: utf-8 -*-
"""R590 看图那一腿：**本轮产品 0 文件**，所以"看"的对象不是新界面，而是"同一台机器、同一份产品，
两批帧到底一不一样"。这与 659 那条形状规矩同族：像素尺必须先证明它看得见差量，再报 0。

三格读数（顺序不许换）：
  ① 逐字节同一：`/tmp/r590/frames` vs `/tmp/r589/frames` 全 356 张 —— 产品未动 ⇒ 期望"全同"；
     有任何一张不同就是**现场读数**，要么写进漂移、要么承认捕获不可重复（两者都是本轮的账）。
  ② 差量可见性正对照（659 那一族）：`getbbox()` 在 RGBA 差值图上会**恒报 None**，所以先 `convert("L")`
     再取框；正对照用"同一张自己 vs 点亮一块的副本"，必须给非零包围盒与非零差量像素数。
     没有这一格，①的那个"全同"分不清"没有差"与"尺看不见差"。
  ③ 本轮门里那 16 张变帧：逐张给包围盒 + 差量像素数 + 尺寸 + 色档（同尺寸同色档才算同一个对象）。

用法：python3 .scratch/motion-audit-2/look_r590.py > /tmp/r590/look.txt
"""
import hashlib
import io
import os
import re
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NOW = "/tmp/r590/frames"
PREV = "/tmp/r589/frames"
THRESH = 8          # 与既有像素尺同一口径：>8/255 才算差量
MIN_CHANGED = 1     # 差量像素数下界（0 就是"看不见"）


def names(d):
    return sorted([f for f in os.listdir(d) if f.endswith(".png")])


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_measure(a, b):
    """返回 (包围盒, 差量像素数, 尺寸是否同一)。灰度上量（659：RGBA 差值图的 getbbox 恒 None）。"""
    ia, ib = Image.open(a), Image.open(b)
    if ia.size != ib.size:
        return None, -1, False
    g = ImageChops.difference(ia.convert("L"), ib.convert("L"))
    box = g.getbbox()
    px = 0
    if box:
        w, h = g.size
        data = g.crop(box).tobytes()
        px = len([1 for v in data if v > THRESH])
    return box, px, True


def tier_of(name):
    m = re.search(r"-(dark|light)\.png$", name)
    return m.group(1) if m else "（无档位词）"


def main():
    out = []
    now, prev = names(NOW), names(PREV)
    out.append(u"LOOK_SCOPE 本轮帧=%d 上一轮帧=%d 名字集合相同=%s"
               % (len(now), len(prev), set(now) == set(prev)))

    same, differ, absent = [], [], []
    for n in now:
        p = os.path.join(PREV, n)
        if not os.path.exists(p):
            absent.append(n)
        elif md5(os.path.join(NOW, n)) == md5(p):
            same.append(n)
        else:
            differ.append(n)
    out.append(u"LOOK_BYTE_IDENTICAL 逐字节同一=%d 不同=%d 上一轮没有这张=%d"
               % (len(same), len(differ), len(absent)))

    # ② 正对照：尺必须看得见它声称能看见的那种差
    ctl = "/tmp/r590/look_ctl"
    if not os.path.isdir(ctl):
        os.mkdir(ctl)
    src = os.path.join(NOW, now[0])
    im = Image.open(src).convert("RGB")
    w, h = im.size
    for x in range(w // 4, w // 4 + 60):
        for y in range(h // 4, h // 4 + 40):
            im.putpixel((x, y), (255, 255, 255))
    ctl_b = os.path.join(ctl, "lit.png")
    im.save(ctl_b)
    box, px, ok_size = diff_measure(src, ctl_b)
    out.append(u"LOOK_POSITIVE_CONTROL 包围盒=%s 差量像素=%d 同尺寸=%s ⇒ 尺%s"
               % (box, px, ok_size, u"看得见差量" if (box and px >= MIN_CHANGED) else u"**看不见差量（坏）**"))
    if not (box and px >= MIN_CHANGED):
        raise SystemExit(u"正对照无效 ⇒ ①那个『全同』不许读成『没有差』")
    # 同尺寸同色档的"自己 vs 自己"必须读 0（否则尺在假红）
    box0, px0, _ = diff_measure(src, src)
    out.append(u"LOOK_SELF_ZERO 自己vs自己 包围盒=%s 差量像素=%d ⇒ 尺没有假红" % (box0, px0))

    for n in differ:
        box, px, ok_size = diff_measure(os.path.join(NOW, n), os.path.join(PREV, n))
        out.append(u"  不同 %s 档=%s 包围盒=%s 差量像素=%d 同尺寸=%s"
                   % (n, tier_of(n), box, px, ok_size))

    # ③ 门里那 16 张变帧（与基线不同、已登记漂移）：现读门的 changed 名单
    gate = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "frame_baseline.py"),
                           "compare", NOW, "--against", "working"],
                          cwd=ROOT, capture_output=True, text=True).stdout
    changed = re.findall(u"^  changed  (\\S+\\.png)$", gate, re.M)
    out.append(u"LOOK_GATE_CHANGED 门报变帧=%d（本轮与 R589 之间没有一张变帧重复出现在差集里=%s）"
               % (len(changed), not (set(changed) & set(differ))))
    # 变帧是"这一轮 vs 基线"，基线是 R586 之前烤的那一份；逐张给包围盒与差量像素
    baseline_dir = os.path.join(ROOT, "docs", "frame_baselines")
    latest = sorted(os.listdir(baseline_dir)) if os.path.isdir(baseline_dir) else []
    out.append(u"LOOK_BASELINE_DIR 目录=%s 条目=%d 取最新一份=%s"
               % (baseline_dir, len(latest), latest[-1] if latest else u"（无）"))
    if latest:
        bd = os.path.join(baseline_dir, latest[-1])
        for n in changed[:20]:
            p = os.path.join(bd, n)
            if not os.path.exists(p):
                out.append(u"  变帧 %s 基线那一份不在（%s）⇒ 只能报本轮，不硬判" % (n, latest[-1]))
                continue
            box, px, ok_size = diff_measure(os.path.join(NOW, n), p)
            out.append(u"  变帧 %s 档=%s 包围盒=%s 差量像素=%d 同尺寸=%s"
                       % (n, tier_of(n), box, px, ok_size))
    out.append(u"LOOK_WHOLE_FRAMES_TO_OPEN " + u" ".join(now[:2]) )
    text = u"\n".join(out)
    io.open(u"/tmp/r590/look.txt", u"w", encoding=u"utf-8").write(text + u"\n")
    print(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
