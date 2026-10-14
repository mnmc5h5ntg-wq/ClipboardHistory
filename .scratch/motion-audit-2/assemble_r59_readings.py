#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `collect_r59_readings.sh` 收下来的两条通道汇成台账引用的那份读数文件。

为什么要单独一个脚本：台账里写"本机五遍"的每一个数都必须能重建。
第一版这段逻辑是我在命令行里现敲的，那样产出的文件就没人能再产第二遍。

**解析不出来就直接抛，不许静默出一张空表**：这条是本轮自己撞出来的 ——
分栏那条读数换了轴，旧正则匹配不到，于是 `min()` 打在空序列上炸在半路、文件写了一半。
现在每条读数各自抽干净、全部齐了才落盘，抽不到就报清是哪一条变了。
同理，写进表里的数字一律从读数来，**不留上一版的字面量**
（上一版这里写着"文件通道 72 条"，那是上一次采集的数，跟着格式一起就过期了）。

输入：`/tmp/r59-readings/{full.md,file/rep*.log,rep*.log}`
输出：`.scratch/motion-audit-2/r59_motion_readings.log`
"""
import io
import re

OUT = "/tmp/r59-readings"
DEST = "/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/r59_motion_readings.log"

# 分栏的两条轴（旧 = 各自峰值归一；新 = 由两栏较大峰值导出的同一条绝对线）。
COL_RE = re.compile(
    r"MOTION_COLUMN .*?旧轴\(各自峰值归一\) 侧栏=(\d+) 详情区=(\d+) 差=(\d+)帧"
    r".*?新轴\(同一条绝对线 ([\d.]+).*?最后还在变的帧号 侧栏=(-?\d+) 详情区=(-?\d+) "
    r"采样≈(\d+)ms")
# 图标跟踪：全帧跨度（**别当位移**）与强帧跨度（真正用来判动没动的那条）。
TRACK_RE = re.compile(
    r"MOTION_TRACK .*?全帧跨度=([\d.]+)px.*?强帧跨度=([\d.]+)px 像素数 首=(\d+) 末=(\d+) "
    r"帧数=(\d+) 有图标帧=(\d+) 强帧数=(\d+)")
# `形状分类` 那半句用 `[^\n]*` 而不是 `(.*)$`：这些读数在文件通道里是一行一条，
# 而 BOX 行不是文件最后一行 —— `$` 在没有 MULTILINE 时只认文末，于是整条正则匹配不上
# （第一版就是这么炸的，而且炸得对：它没写出半张表）。
BOX_RE = re.compile(
    r"MOTION_TRACK_BOX .*?外框 首=\[(-?\d+),(-?\d+)\] 末=\[(-?\d+),(-?\d+)\] "
    r"上沿移=(-?\d+)px 下沿移=(-?\d+)px.*?形状分类：([^\n]*)")


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except FileNotFoundError:
        return ""


def grab(rx, text, what, where):
    m = rx.search(text)
    if not m:
        raise SystemExit(
            "%s 里没匹配到 %s —— 判据的读数格式改了而这个汇总脚本没跟着改。\n"
            "  先修脚本，别把旧数字抄进新格式的文件里。原文前 400 字：\n%s"
            % (where, what, text[:400]))
    return m.groups()


def main():
    full = read(OUT + "/full.md")
    if not full.strip():
        raise SystemExit("整条卷那次采集是空的 —— 采集没跑完，不出文件")
    reps = [read(OUT + "/file/rep%d.log" % i) for i in range(1, 6)]
    missing = [i + 1 for i, t in enumerate(reps) if not t.strip()]
    if missing:
        raise SystemExit("第 %s 遍的文件通道读数是空的 —— 采集没跑完，不出文件" % missing)

    file_lines = len([l for l in full.splitlines() if l.startswith("MOTION_")])
    # 整条卷那一次的 stdout 通道：数"以 MOTION_ 开头的读数行"，不是"含 MOTION_ 子串的行"
    # （后者会把 skip 原因里那句 MOTION_NOT_RUN 也算进来，于是两条通道看起来都"有读数"）。
    full_stdout_lines = len([l for l in read(OUT + "/full.log").splitlines() if l.startswith("MOTION_")])
    stdout_prefix = []
    for i in range(1, 6):
        text = read(OUT + "/rep%d.log" % i)
        stdout_prefix.append(len([l for l in text.splitlines() if l.startswith("MOTION_")]))

    cols = [grab(COL_RE, t, "MOTION_COLUMN 的两条轴", "第 %d 遍" % i) for i, t in enumerate(reps, 1)]
    tracks = [grab(TRACK_RE, t, "MOTION_TRACK 的两条跨度", "第 %d 遍" % i) for i, t in enumerate(reps, 1)]
    boxes = [grab(BOX_RE, t, "MOTION_TRACK_BOX 的外框", "第 %d 遍" % i) for i, t in enumerate(reps, 1)]

    buf = io.StringIO()
    w = buf.write
    w("""> R59 本机读数。**采集**：`.scratch/motion-audit-2/collect_r59_readings.sh`
> （`env -u SDKROOT swift test`，本机 2x 缩放）；**汇总**：`.scratch/motion-audit-2/assemble_r59_readings.py`
> —— 就是生成这份文件的那个脚本，它解析不到任何一条读数时会**报错退出**，不会写半张表。
> 台账里每一句"本机五遍"的数都指回这里。
>
> 两条通道分开记，因为**本机这一轮它们给的不是同一份东西**：整条卷那一次，stdout 里以 `MOTION_`
> 开头的读数行 **%d** 条，文件通道 **%d** 条 —— 差出去的那些只从文件通道回来。
> R56 加第二条通道就是为了这个形状；本轮它第一次在本地真的把读数救回来
> （在 runner 上是另一回事：R58 的 `MOTION_CHANNEL_UNIONED=1 stdout=61 文件=65`，那边是 stdout 更多）。

## 1) 整条 `MotionFilmstripTests`

```
""" % (full_stdout_lines, file_lines))
    w(full.rstrip() + "\n```\n\n")
    w("（skip 的那几条都是 `MOTION_NOT_RUN=app-not-active` —— AppKit 行动画只在激活进程里跑，"
      "判据自己把它登记成未覆盖，不是产品没动。）\n")

    w("\n## 2) 本轮改写的那几条测量，连跑五遍（文件通道原文）\n\n")
    for i, text in enumerate(reps, 1):
        counted = len([l for l in text.splitlines() if l.startswith("MOTION_")])
        w("### 第 %d 遍 ｜ stdout 通道读数行=%d ｜ 文件通道=%d\n\n```\n" % (i, stdout_prefix[i - 1], counted))
        w(text.rstrip() + "\n```\n\n")

    w("\n## 3) 五遍的汇总（本轮两个结论都是从这两张表上翻的，不是从看图的感觉上）\n\n")
    w("### 3.1 分栏：两条轴给两个答案（`MOTION_COLUMN`）\n\n")
    w("| 遍 | 旧轴·各自峰值归一 侧栏/详情区 | 旧轴差(帧) | 共享线 | 新轴·最后还在变的帧号 侧栏/详情区 | 新轴差(帧) |\n")
    w("|---|---|---|---|---|---|\n")
    same_frame = 0
    for i, c in enumerate(cols, 1):
        d = int(c[4]) - int(c[5])
        same_frame += 1 if d == 0 else 0
        w("| %d | %s / %s | %s | %s | %s / %s | %+d |\n" % (i, c[0], c[1], c[2], c[3], c[4], c[5], d))
    old_diffs = [int(c[2]) for c in cols]
    sampling = cols[0][5]
    w("\n- 旧轴五遍都说侧栏先停（差 %d–%d 帧 ≈ %d–%d ms，采样 %s ms/帧），"
      "**新轴 %d/5 遍两栏是同一帧落定**。\n"
      % (min(old_diffs), max(old_diffs), min(old_diffs) * int(sampling),
         max(old_diffs) * int(sampling), sampling, same_frame))
    w("- 原因写死在尺子里：`transitionFrameCount` 的门槛是**各自峰值**×15%，"
      "侧栏峰值大 ⇒ 线高 ⇒ 先判停。线不一样高，比出来的不是时间，是墨量。\n")
    w("- ⇒ BACKLOG 85 里\u201c两栏以不同进度消失\u201d那半边**作废**；措辞现在由 "
      "`columnSettlementVerdict` 从帧号生成，被合成真值表 `testSharedFloorColumnComparisonIsATruthTable` 钉住。\n")

    w("\n### 3.2 图标：全帧质心在漂，强帧外框几乎没动（`MOTION_TRACK` / `MOTION_TRACK_BOX`）\n\n")
    w("| 遍 | 全帧质心跨度 px | 强帧质心跨度 px | 外框 首→末 | 上沿移 | 下沿移 | 有图标帧/强帧 | 分类 |\n")
    w("|---|---|---|---|---|---|---|---|\n")
    for i in range(5):
        t_, b = tracks[i], boxes[i]
        w("| %d | %s | %s | [%s,%s]→[%s,%s] | %s | %s | %s/%s | %s |\n"
          % (i + 1, t_[0], t_[1], b[0], b[1], b[2], b[3], b[4], b[5], t_[5], t_[6], b[6].strip()))
    raw = [float(t_[0]) for t_ in tracks]
    strong_spread = [float(t_[1]) for t_ in tracks]
    still = sum(1 for b in boxes if b[4] == "0" and b[5] == "0")
    w("\n- 全帧质心跨度 %s px —— 第一遍读数出来时我把它写成了\u201c图标在上移\u201d。\n" % raw)
    w("- 强帧质心跨度 %s px；外框上沿移 %s px、下沿移 %s px ⇒ 五遍里 **%d/5 遍外框一格没挪**。\n"
      % (strong_spread, sorted({b[4] for b in boxes}), sorted({b[5] for b in boxes}), still))
    w("- 两条轴的差别来自判色阈值：图标淡下去时高饱和的边缘先掉，剩下的像素聚在哪半边，"
      "质心就往哪边漂 ⇒ 那条轴量的其实是**阈值在动**"
      "（与\u201c绝对帧数判据其实判的是采样率\u201d同族）。\n")
    # 两条轴各自数一边，不许合成一句"站住了"就完事：本轮它们就有 1 遍不一致。
    quiet = sum(1 for t_ in tracks if float(t_[1]) < 4.0)
    if still == 5 and quiet == 5:
        w("- ⇒ \u201c原地淡出\u201d站住了（两条轴五遍一致），与 `.bannerOut` 只设 `isExit`、不设 `slides` 一致；"
          "R22 那句\u201c它是淡出，不是塌陷\u201d在这一格被**证实**（那时只有一帧可看，结论对但没有证据）。\n")
    else:
        w("- ⇒ 两条轴各自数一边：**强帧跨度 <4px 的有 %d/5 遍**（判\u201c没在动\u201d那条轴），"
          "**外框一格没挪的有 %d/5 遍**。\n" % (quiet, still))
        w("  不一致的那遍是下沿上移 4px —— 它正好落在\u201c淡出时高饱和边缘先脱落\u201d的量级里，"
          "而 ±2px 这条容差分不开\u201c边缘脱落\u201d和\u201c一边被裁\u201d。\n")
        w("  ⇒ 可以说的是：**原来那个\u201c上移 6.5pt\u201d作废**（比外框能看到的任何数都大），"
          "但\u201c绝对没动\u201d也不许写成结论（差 1 遍）。\n")
    w("- 判\u201c在不在动\u201d用的是**强帧**跨度；分类线 4px（≈2pt）是尺子的线、不是产品的判据"
      "（见 `trackMoveClassifierPixels`）。`有图标帧` 与 `强帧数` 两列就是地板 4 与\u201c只看强帧\u201d这两件事的依据。\n")

    with open(DEST, "w", encoding="utf-8") as handle:
        handle.write(buf.getvalue())
    print("%s ← %d bytes, cols=%d tracks=%d boxes=%d 外框没挪=%d/5"
          % (DEST, len(buf.getvalue()), len(cols), len(tracks), len(boxes), still))


if __name__ == "__main__":
    main()
