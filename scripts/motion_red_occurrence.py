#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""627/622 的出现率读数：从 CI 日志里把 copy receipt、fold 采样、帧多段分开数。

为什么要有它（R540 现读）：
- 627 的两种红不能缝成一种：copy receipt 是 Motion filmstrip 的「1x 只有 1 个过渡帧」，
  fold 是 Swift tests 的「foldProgress 中间帧 [0,0,0,0.993,0.993]」。两者发生在不同的卷、
  不同的断言，只有分别数出现率，才知道该登记还是该改产品。
- 622 的 frame 半不能只看一个 worst：同一次跑里 `PROBE_FPS` 同时给出 baseline/off/loaded
  三段 p95、比值、n、worst 与超锚点颗数；把它们放在同一行，才能判「1–2 颗离群」还是「整段慢」。

口径（两条，缺一条这张表就会骗人）：
① **skip 不是红，也不是执行过**：copy receipt 在 Swift tests 里被 skip（env 门）不算红；
   fold 的 skipped 不进 executed 分母。
② **copy receipt 的通过不落 CI 日志**：Motion filmstrip 只打印失败用例，所以它的分母
   写 `filmstrip-failures-only`，不许拿日志条数冒充通过数。fold 的 passed/failed 都打印，
   分母可数。

用法：`python3 scripts/motion_red_occurrence.py <log> [<log> ...]`
退出码：0 = 读完（有红也退 0，这是读数不是闸门）；2 = 一份日志都没读到。
"""
import io
import os
import re
import sys

COPY = "testCopyReceiptAppearsAndDismissesWithAVisibleProcess"
FOLD = "testCollapseWidthIsMeasuredFrameByFrame"


def scan(text):
    """把一份日志归约成四个读数：copy / fold / motion floor / 帧多段。"""
    copy_red = bool(re.search(r"MotionFilmstripTests %s'?\]' failed" % COPY, text))
    copy_skip = bool(re.search(r"%s'?\]' skipped" % COPY, text))
    fold = "ABSENT"
    for m in re.finditer(r"Test Case '-\[[^]]*\.MainWindowFoldMotionTests %s\]' (passed|failed|skipped)" % FOLD, text):
        st = m.group(1)
        if st == "failed":
            fold = "RED"
            break
        if st == "passed" and fold != "RED":
            fold = "PASS"
        if st == "skipped" and fold == "ABSENT":
            fold = "SKIP"
    judged = None
    m = re.search(r"MOTION_FLOOR_FACTS judged=(\d+)/(\d+) executed=(\d+) not-run=(\S+)[^\n]*?红的用例=(\S*)", text)
    if m:
        judged = (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), m.group(5))
    frame = None
    f = re.search(
        r"PROBE_FPS .*?baseline_p95=([0-9.]+) off_p95=([0-9.]+) loaded_p95=([0-9.]+) "
        r"比值=([0-9.]+) .*?n=(\d+) worst=([0-9.]+)ms 超锚点帧=(\d+)", text)
    if f:
        frame = tuple(f.groups())
    # copy receipt 的通过不落日志；Swift 卷的 skip 只是另一卷没跑，不能读成 filmstrip 的结论。
    copy = "RED" if copy_red else "NOT_PRINTED"
    return {"copy": copy, "fold": fold, "judged": judged, "frame": frame,
            "copy_swift_skip": copy_skip}


def summarize(items):
    copy_red = sum(1 for x in items if x["copy"] == "RED")
    fold_exec = sum(1 for x in items if x["fold"] in ("PASS", "RED"))
    fold_red = sum(1 for x in items if x["fold"] == "RED")
    markdown_red = sum(1 for x in items
                       if x["judged"] is not None
                       and "testMarkdownModeLabelChangeIsAVisibleProcess" in x["judged"][4].split(","))
    frames = [x["frame"] for x in items if x["frame"] is not None]
    return {"copy_red": copy_red, "fold_red": fold_red, "markdown_red": markdown_red,
            "fold_exec": fold_exec, "logs": len(items), "frames": frames}


def read(path):
    if not os.path.exists(path):
        return None
    return io.open(path, encoding="utf-8", errors="replace").read()


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    items = []
    for path in args:
        text = read(path)
        if text is None:
            print("OCCURRENCE_UNREADABLE %s（读不到不等于没有红）" % path)
            continue
        s = scan(text)
        items.append(s)
        j = "-" if s["judged"] is None else "%d/%d executed=%d not-run=%s red=%s" % s["judged"]
        fr = "-" if s["frame"] is None else "/".join(s["frame"])
        print("LOG %s copy=%s fold=%s motion=%s frame=%s"
              % (os.path.basename(path), s["copy"], s["fold"], j, fr))
    if not items:
        return 2
    z = summarize(items)
    print("OCCURRENCE copy_receipt reds=%d logs=%d denominator=filmstrip-failures-only"
          % (z["copy_red"], z["logs"]))
    print("OCCURRENCE fold reds=%d executed=%d logs=%d"
          % (z["fold_red"], z["fold_exec"], z["logs"]))
    print("OCCURRENCE markdown reds=%d logs=%d denominator=motion-floor-runs"
          % (z["markdown_red"], z["logs"]))
    if z["frames"]:
        worst = max(float(f[5]) for f in z["frames"])
        over = max(int(f[6]) for f in z["frames"])
        loaded = max(float(f[2]) for f in z["frames"])
        ratios = [float(f[3]) for f in z["frames"]]
        over_runs = sum(1 for f in z["frames"] if int(f[6]) > 0)
        print("FRAME_MULTI logs=%d with=%d worst_max=%.1f over_max=%d over_runs=%d "
              "loaded_p95_max=%.2f ratio_min=%.3f ratio_max=%.3f"
              % (z["logs"], len(z["frames"]), worst, over, over_runs,
                 loaded, min(ratios), max(ratios)))
    else:
        print("FRAME_MULTI logs=%d with=0 ⇒ NOT_RUN" % z["logs"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
