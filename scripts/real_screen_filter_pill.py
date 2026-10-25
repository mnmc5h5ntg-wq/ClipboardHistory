#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真机那一层的「筛选胶囊比轨道亮还是暗」量尺 —— BACKLOG 377 的判据通道（R330 真机普查第一格）。

为什么要有它：377 的全部证据来自**离屏合成**（`filter-pill-slide` 那卷胶片与
`sidebar-history-300x520-dark.png`），现读 轨道 51.9 / 药丸 36.0 / 页底 30 ⇒ 在离屏通道里
"选中"是轨道上挖出来的一个**暗洞**。而 macOS 分段控件的惯例是选中那颗**更亮**。
这两件事只有一种解释方式能分开：屏幕上到底画的哪一面 —— 离屏通道对材质本来就有盲区
（D-090 / 126 / 130 / 172 那一族），R172 就是靠 `real_screen_sidebar_icons.py` 结的案。

它做什么（顺序不许换，每一步的"读不到"都有名字）：
  1. 先问显示器（电源日志 + 一小块探针截图），再碰窗口 —— 屏幕关掉时辅助功能看不到别的 App 的窗口，
     把那种"读不到"记成产品缺陷是这仓库烧过好几轮的错法（R141 / U-476）；
  2. **绝不碰用户的真存档**：用 `CLIPBOARD_HISTORY_DATA_DIR` / `CLIPBOARD_HISTORY_LOG_DIR`
     指向 /tmp 下的隔离目录启动一份，里面是空库（不是复制真库）；
  3. 走产品自己的入口让主窗口出现（`open -a` 触发 `applicationShouldHandleReopen` → `showMainWindow`），
     窗口矩形**由 System Events 现读**，不写死坐标；
  4. 只截那一扇窗口的矩形（`screencapture -R`），并且只量侧栏顶部那条"分段控件带"；
  5. 只打坐标、电平、段宽这类数，**绝不打窗口里的任何文字**。

判法（预先登记，两档之间留第三个出口，不许四舍五入到任一侧）：
  显示器关了 / 锁屏         ⇒ `REALSCREEN_NOT_RUN display_channel`：辅助功能看不到窗口，这一格是没跑
  有实例在跑                ⇒ `REALSCREEN_NOT_RUN already_running`：不替你关窗（那可能是你的真存档）
  起了进程没有窗口          ⇒ `REALSCREEN_NOT_RUN no_window`
  截到未绘制/动画中的帧     ⇒ `REALSCREEN_NOT_RUN frame_not_rendered`（要连续两帧指纹相同才算稳）
  控件上下两条参照带不同档  ⇒ `reference_unstable`：参照物自己不可信 ⇒ 不许往下判
  找不到候选带              ⇒ `no_band`：这一格没跑（窗口没出现 / 侧栏不在预期位置）
  |药丸 − 轨道| < 8          ⇒ `indistinguishable`：这台机器上两档分不开 ⇒ 只配记成通道限制
  药丸比轨道**亮** ≥ 8       ⇒ `pill_lighter`：屏幕上是原生那一面 ⇒ 377 是**离屏通道的锅**（不是产品缺陷）
  药丸比轨道**暗** ≥ 8       ⇒ `pill_darker`：屏幕上也是暗洞 ⇒ 377 是**产品缺陷**，开修

退出码：0 = 判到了（两种结论都算判到）；1 = 这一格没跑 / 参照不可信。

用法：
  PYTHONUTF8=1 python3 scripts/real_screen_filter_pill.py [--keep-png] [--timeout 20]
  # 离线复量已有的帧（不启动 App）：读数要能离开现场复查
  PYTHONUTF8=1 python3 scripts/real_screen_filter_pill.py --png /tmp/…/pill.png --width-pt 750
"""
import argparse
import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from real_screen_sidebar_icons import (  # noqa: E402  同一套通道 plumbing，单一真相
    appearance_of, display_channel_state, osascript, parse_bounds,
)

APP_PATH = "/Applications/时间剪史.app"
BIN_NAME = "ClipboardHistoryApp"
SIDEBAR_W_PT = 320          # 侧栏宽度（pt，窗口内）；与夹具的 sidebar-* 同一族
SCAN_Y = (28, 170)          # 分段控件住在窗口顶部这一段（pt）
MIN_RUN_PT = 40             # 短于此的连续段不算那颗胶囊（图标、分隔线都会更窄）
MIN_CONTAINER_PT = 100      # 轨道本身要横跨这么宽才配当"一条控件"（R330 的第一把闸）
MIN_SOLIDITY = 0.20         # 轨道的纵向实心度地板：把"一片填充"与"几笔字"分开（见 track_solidity）
DELTA = 8.0                 # 与胶片那把尺同一个 delta（分箱/分离都按它算）
APP_PROCESS = u"ClipboardHistoryApp"    # System Events 的**进程名**（= 可执行名，不是显示名「时间剪史」）


def capture_identity(frontmost, target=APP_PROCESS):
    u"""这一帧要拍的**对象**是不是它 —— 前台进程必须是目标进程。

    R341 当场撞的：`frame_ready` 只问「这帧画完了没有」（≥3 档电平各占 ≥2%），它答不了「这帧是谁」。
    屏幕解锁后同一条调用链拍到的是 Numbers 的保存对话框（用户的表格），背景中位 247、电平 26 档 ⇒
    放行，接着尺报 `no_band`（侧栏没有控件）—— 一个关于**产品**的假结论，而产品窗口根本不在前台。
    这是「尺读的不是它声称的对象」那一族第四次（D-090 / 176 / 372 之后）：闸门要问对象，不是像素多不多。

    三态，`ok` 之外都自带名字：
      `ok`                      前台就是目标进程 ⇒ 这一帧可以是它的
      `occluded_not_frontmost`  前台是别人 ⇒ 拍到的像素属于别人，这一格没跑
      `frontmost_unknown`       System Events 答不出前台 ⇒ 连对象都问不到，这一格没跑
    """
    if not frontmost:
        return u"frontmost_unknown"
    if frontmost == target:
        return u"ok"
    return u"occluded_not_frontmost"


def frontmost_name():
    rc, out = osascript(u'tell application "System Events" to get name of first application process '
                        u'whose frontmost is true')
    return out if rc == 0 and out else None


def activate_and_wait(pid, timeout=6.0):
    u"""把目标进程推到前台并**等它真的变成前台**；返回最后一次读到的前台名。

    `open -a` 起得来的进程不一定被激活，而 `screencapture -R` 拍的是**屏幕**、不是窗口 ——
    不在前台就拍到别人的窗口。所以这里不是「叫一声就完」，而是「叫到读数为准」。
    """
    deadline = time.time() + timeout
    name = frontmost_name()
    while time.time() < deadline and name != APP_PROCESS:
        osascript(u'tell application "System Events" to set frontmost of '
                  u'(first process whose unix id is %d) to true' % pid)
        time.sleep(0.4)
        name = frontmost_name()
    return name


def already_running():
    """有没有**别人的**实例在跑。有就绝不动它：那是用户自己那一份，可能带着真存档。"""
    out = subprocess.run(["pgrep", "-f", os.path.join(APP_PATH, "Contents", "MacOS", BIN_NAME)],
                         capture_output=True, text=True)
    pids = [int(s) for s in out.stdout.split() if s.strip().isdigit()]
    return pids


def launch_isolated(workdir, logdir, via_open=True):
    """用隔离目录启动一份，返回 pid（拿不到返回 None）。空库 ⇒ 截图里不可能出现用户的真实条目。

    两条启动路径，先走 `open --env`（R330 现读的教训）：
      · 直接 exec 二进制**不一定会被激活**，而这个产品的主窗口是
        `applicationDidBecomeActive → restoreMainWindowIfNeeded` 才出现的
        （`WindowManager.showMainWindow` 只 present 已存在的窗口，从不新建）——
        本机实测：同一份二进制，前两趟 exec 拿到了窗口，后两趟 `count of windows = 0`；
      · `open -a --env` 走 LaunchServices，会正常激活，且 `--env` 能把隔离目录带进去
        （macOS 27 的 `open` 支持 `--env`，本机现读 `open --help` 抄来的，不是记的）。
    """
    exe = os.path.join(APP_PATH, "Contents", "MacOS", BIN_NAME)
    if not os.path.exists(exe):
        return None
    if already_running():
        return None
    if via_open:
        subprocess.run(["open", "-a", APP_PATH,
                        "--env", "CLIPBOARD_HISTORY_DATA_DIR=" + workdir,
                        "--env", "CLIPBOARD_HISTORY_LOG_DIR=" + logdir],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 12.0
        while time.time() < deadline:
            pids = already_running()
            if pids:
                return pids[0]
            time.sleep(0.4)
        return None
    env = dict(os.environ)
    env["CLIPBOARD_HISTORY_DATA_DIR"] = workdir
    env["CLIPBOARD_HISTORY_LOG_DIR"] = logdir
    proc = subprocess.Popen([exe], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.pid


def window_bounds(pid, timeout):
    """等主窗口出现并现读它的矩形（写死坐标会把"截到哪一态"变成运气）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, text = osascript(
            'tell application "System Events" to tell (first process whose unix id is %d)\n'
            '  if (count of windows) is 0 then return "NO_WINDOW"\n'
            '  set p to position of window 1\n'
            '  set s to size of window 1\n'
            '  return (item 1 of p) & "," & (item 2 of p) & "," & (item 1 of s) & "," & (item 2 of s)\n'
            'end tell' % pid)
        bounds = parse_bounds(text)
        if bounds and code == 0:
            return bounds
        time.sleep(0.5)
    return None


def capture(bounds, path):
    x, y, w, h = bounds
    proc = subprocess.run(["screencapture", "-x", "-R%d,%d,%d,%d" % (x, y, w, h), path],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.returncode == 0 and os.path.exists(path)


def column_levels(px, y0, y1, x0, x1, stride_px):
    """逐列电平 = 该列在这一行带内的**中位数**（不是最大值）。

    为什么这一格要写死成中位：R330 第一版用了 `max()`，于是"时间剪史 / 0 条记录"那一条
    **文字行**被读成了胶囊（轨道档 137.0 = 字那一档，药丸档 58.6 = 页底），差 -78.4 级。
    max 把字墨当成了控件的一部分；中位在一行带里字只占少数列时把字洗掉。
    """
    out = []
    for x in range(x0, x1, stride_px):
        vals = sorted(max(px[x, y]) for y in range(y0, y1))
        out.append((x, vals[len(vals) // 2]))
    return out


def mode_level(profile, delta):
    """页底 = 这一行里**住得最密**的那一档（按 delta 量化后取众数）。

    不用 90 分位：R326/R330 两次踩过同一个坑——分位数是"取第几名"，不是"哪一档人多"，
    一行里只要有一小撮亮像素（图标、字、控件右边距）就能把分位数抬到别的档上去。
    """
    if not profile:
        return 0.0
    bins = {}
    for _x, v in profile:
        bins[int(round(v / delta))] = bins.get(int(round(v / delta)), 0) + 1
    top = max(bins.items(), key=lambda kv: (kv[1], -kv[0]))
    vals = sorted(v for _x, v in profile if int(round(v / delta)) == top[0])
    return vals[len(vals) // 2]


def contiguous_runs(flags):
    """[(起点索引, 终点索引+1)]：flags 里连续的 True 段。"""
    out, start = [], -1
    for i, flag in enumerate(flags):
        if flag and start < 0:
            start = i
        elif not flag and start >= 0:
            out.append((start, i))
            start = -1
    if start >= 0:
        out.append((start, len(flags)))
    return out


def measure_row(profile, page, stride_px, scale, delta):
    """把一行读成"轨道 + 洞里那颗胶囊"；读不出这个形状就返回 None（不是返回 0）。

    `page` 由**外面**给（见 `reference_outside`）：行内众数在两半区各占一半时会翻，
    一翻就把同一个缺陷报成反向结论（R330 臂 B 实测翻过一次，页底被读成 80 ⇒ 差 +31.0）。

    四道形状闸（R330，每一道都被前一版的假阳性喂过）：
      1. 轨道要**横跨够宽**：`MIN_CONTAINER_PT`；
      2. 轨道要**与页底差够一档**：|差| ≥ delta —— 否则"轨道"只是噪声；
      3. 轨道范围内要有一段 ≥ `MIN_RUN_PT` 的**与页底同档**的连续段 —— 那才是胶囊；
      4. 轨道要**纵向实心**（`MIN_SOLIDITY`，见 `track_solidity`）—— 前三道只管横向，
         一条两头各有一块字的标题行能把前三道全过掉（本机实测过掉，差 -99.0 级）。
    """
    if not profile or page is None:
        return None
    differs = [abs(v - page) >= delta for _x, v in profile]
    if not any(differs):
        return None
    first = differs.index(True)
    last = len(differs) - 1 - differs[::-1].index(True)
    extent = profile[first:last + 1]
    track_w_pt = (last - first + 1) * stride_px / scale
    track_vals = sorted(v for _x, v in extent if abs(v - page) >= delta)
    track = track_vals[len(track_vals) // 2]
    if track_w_pt < MIN_CONTAINER_PT or abs(track - page) < delta:
        return None
    hole = [abs(v - page) < delta for _x, v in extent]
    runs = [(a, b) for a, b in contiguous_runs(hole) if (b - a) * stride_px / scale >= MIN_RUN_PT]
    if not runs:
        return None
    a, b = max(runs, key=lambda r: r[1] - r[0])
    seg = sorted(v for i, (_x, v) in enumerate(extent) if a <= i < b)
    return {
        "page": page,
        "page_mode_in_row": mode_level(profile, delta),
        "track": track,
        "pill": seg[len(seg) // 2],
        "extent_pt": track_w_pt,
        "extent_x0": first * stride_px / scale,
        "hole_pt": (b - a) * stride_px / scale,
        "hole_x0": (first + a) * stride_px / scale,
        "hole_x1": (first + b) * stride_px / scale,
        "hole_share": (b - a) / float(len(extent)),
    }


def pair_split(profile, page, stride_px, scale, delta, gap=2):
    u"""两段式控件的第二形状：一个控件、左右两半，选中段在**左**。

    为什么要有它（R341 真机现读）：R339 把选中那颗抬到轨道**之上**以后，屏幕上是
    `左=107 / 右=80 / 页底=43`；而 `measure_row` 把「胶囊」定义成「容器里与页底同档的那一段」，
    修好之后那一段根本不存在 ⇒ 尺报 `no_band`（侧栏没有控件）。**修好了的产品被判成没有控件**，
    比不量更坏：它把人引回去改产品。

    形状只说产品本来的样子：侧栏那行是**一个控件、两段**；选中段是左边那一段
    （产品打开时选中「全部」—— 这是输入，不是从像素里猜的；换选另一段时本形状不适用）。
    两半按控件宽度中点切开，切口左右各让 `gap` 个采样点，免得把接缝读进任何一半。
    返回 None 的每种条件都写成可数的：不够宽 / 切不开 / 两半差不到一档。

    为了不出现两套下游口径，这里把「选中段」直接写成 `pill`、把「未选段」写成 `track`，
    `report()` 那一段一字不动 —— 换形状不换量纲。
    """
    if not profile or page is None:
        return None
    differs = [abs(v - page) >= delta for _x, v in profile]
    if not any(differs):
        return None
    first = differs.index(True)
    last = len(differs) - 1 - differs[::-1].index(True)
    extent = profile[first:last + 1]
    width_pt = (last - first + 1) * stride_px / scale
    if width_pt < MIN_CONTAINER_PT:
        return None
    mid = len(extent) // 2
    if mid - gap <= 0 or mid + gap >= len(extent):
        return None
    left = sorted(v for _x, v in extent[:mid - gap])
    right = sorted(v for _x, v in extent[mid + gap:])
    lvl_l, lvl_r = left[len(left) // 2], right[len(right) // 2]
    if abs(lvl_l - lvl_r) < delta:
        return None
    return {
        "pair": True,
        "page": page,
        "page_mode_in_row": mode_level(profile, delta),
        "pill": lvl_l,
        "track": lvl_r,
        "left_x0": first * stride_px / scale,
        "left_x1": (first + mid - gap) * stride_px / scale,
        "extent_pt": width_pt,
        "extent_x0": first * stride_px / scale,
        "hole_pt": (mid - gap) * stride_px / scale,
        "hole_x0": first * stride_px / scale,
        "hole_x1": (first + mid - gap) * stride_px / scale,
        "hole_share": (mid - gap) / float(len(extent)),
    }


def prefer_shape(rows):
    u"""两种形状都在时选哪一种：**有胶囊形状就先用它**，只有一行都读不出胶囊时才退到两段形状。

    顺序是承重的：胶囊形状是 377 结案的原始台阶；两种都能读时不许换尺，
    否则同一台机器上前后的读数就不再是同一个量。返回 `(kind, best)` 或 `(None, None)`。
    """
    pills = [g for g in rows if not g.get(u"pair")]
    pairs = [g for g in rows if g.get(u"pair")]
    if pills:
        return u"pill", max(pills, key=lambda g: (g["extent_pt"], g["hole_pt"]))
    if pairs:
        return u"pair", max(pairs, key=lambda g: (g["extent_pt"], g["solidity"]))
    return None, None


def track_solidity(px, y_center_pt, x0_pt, x1_pt, track, scale, delta, height_pt=12):
    """轨道是**铺满的一片**还是**几笔字**：12pt 高的窗口里，每列有多少行停在轨道档上。

    为什么必须有这道闸（R330 第二版自曝）：前三道闸只判"水平方向够不够宽、够不够亮"，
    而"时间剪史 / 0 条记录"那一行**横向跨度也是 320pt、也比页底亮 99 级**——它是两头各一块字。
    区分"控件的填充"与"文字的笔画"的唯一形状量是**纵向实心度**：
    本机现读三个数（地板就按这三个定）：真机控件带 0.445（过闸行里最低 0.32）/
    真机文字行 0.017 / 合成帧里那条**更密**的文字行 0.169。地板取 0.20：
    它把两种文字行都挡在外面（0.017 与 0.169），又给真控件留着 1.6 倍的余量。
    上一版取 0.15 时，那条 0.169 的合成密集文字行**过了闸** —— 是判据卷把它抓出来的。
    """
    ys = range(int((y_center_pt - height_pt / 2.0) * scale),
               int((y_center_pt + height_pt / 2.0) * scale))
    if not ys:
        return 0.0
    tot = hits = 0.0
    for x in range(int(x0_pt * scale), int(x1_pt * scale), max(2, int(scale))):
        col = sum(1 for y in ys if abs(max(px[x, y]) - track) < delta) / float(len(list(ys)) or 1)
        tot += 1.0
        hits += col
    return hits / tot if tot else 0.0


def frame_ready(png, min_bins=3, min_share=0.02):
    """这一帧**画完了没有**：整帧的电平里至少有 `min_bins` 档各占 ≥2%。

    为什么必须有它（R330 当场撞的）：`window_bounds` 只要 System Events 报得出矩形就返回，
    而 AppKit 的第一次绘制在这之后。第二趟我跳过了前面的探针截图、直接截屏，
    拿到的是 1500x1120 的**纯白未绘制表面**（p50=255），于是尺报 `no_band`——
    那是"没跑到"，不是"侧栏没有控件"。把未绘制的帧当成一次判定，是这仓库最贵的一类错。
    """
    from PIL import Image
    im = Image.open(png).convert("RGB")
    pw, ph = im.size
    px = im.load()
    bins = {}
    total = 0
    for x in range(0, pw, 6):
        for y in range(0, ph, 6):
            bins[int(max(px[x, y]) // DELTA)] = bins.get(int(max(px[x, y]) // DELTA), 0) + 1
            total += 1
    if not total:
        return False, 0, 0.0
    good = [n for n in bins.values() if n >= max(2, int(min_share * total))]
    return len(good) >= min_bins, len(bins), len(good)


def frame_fingerprint(png, step=8):
    """把一帧压成"每 8px 一档量化电平"的串，用来判**布局稳了没有**。"""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    pw, ph = im.size
    px = im.load()
    return "%dx%d:" % (pw, ph) + "".join(
        chr(48 + min(31, int(max(px[x, y]) // DELTA)))
        for x in range(0, pw, step) for y in range(0, ph, step))


def wait_for_rendered_frame(bounds, png, timeout):
    """反复截，直到拿到**画完且稳住**的那一帧；等不到就返回 False（⇒ NOT_RUN，不许往下判）。

    两道而不是一道（R330 第二趟撞的）：`frame_ready` 只保证"这一帧有内容"，
    而窗口刚出现时截到的是**布局动画中间那一帧**——侧栏只有 70pt 宽、控件被裁在左边缘，
    有内容、有对比，却不是被测对象（它把臂 A 判成了 `no_band`）。
    所以要连续两帧指纹相同，才叫"稳了"。
    """
    deadline = time.time() + timeout
    tries = 0
    prev = None
    while time.time() < deadline:
        tries += 1
        if not capture(bounds, png):
            time.sleep(0.4)
            prev = None
            continue
        ok, _n, _good = frame_ready(png)
        fp = frame_fingerprint(png) if ok else None
        if ok and fp == prev:
            return True, tries
        prev = fp
        time.sleep(0.5)
    return False, tries


def scan(png, width_pt, band_pt=6, step_pt=2):
    """扫侧栏顶部，返回（候选行列表, 通道自证行）。找不到候选 ⇒ 空列表。

    两趟，顺序是承重的（R330 第三趟之后改的）：
      趟 1 用**行内众数**当临时页底，只为把"控件住在哪几行"圈出来（ymin..ymax）；
      趟 2 到控件**外面**（ymin 之上、ymax 之下各一条带）读真正的页底，再回来重量。
    为什么不能一趟：页底参照如果从控件自己那一行里取，两半区各占一半时它就是掷硬币；
    而上下两条带是同一个背景，控件盖不到它们。参照带自己不同档 ⇒ `ref_stable=False`，
    由 `report()` 判成 `reference_unstable`，不许往下判。
    """
    from PIL import Image
    im = Image.open(png).convert("RGB")
    pw, ph = im.size
    scale = pw / float(width_pt)
    px = im.load()
    vals = sorted(max(px[x, y]) for x in range(0, pw, 8) for y in range(0, ph, 8))
    bg = vals[len(vals) // 2]
    side_w = int(min(SIDEBAR_W_PT, width_pt) * scale)
    stride = max(2, int(2 * scale))

    rows = []
    for y_pt in range(SCAN_Y[0], SCAN_Y[1], step_pt):
        y0, y1 = int(y_pt * scale), int((y_pt + band_pt) * scale)
        if y1 > ph:
            break
        rows.append((y_pt, column_levels(px, y0, y1, 0, side_w, stride)))
    provisional = []
    for y_pt, profile in rows:
        row_page = mode_level(profile, DELTA)
        got = measure_row(profile, row_page, stride, scale, DELTA) \
            or pair_split(profile, row_page, stride, scale, DELTA)
        if got:
            provisional.append(y_pt)
    if not provisional:
        return [], (pw, ph, scale, appearance_of(bg), bg)
    ymin, ymax = min(provisional), max(provisional) + band_pt

    page, ref_stable = reference_outside(px, ymin, ymax, side_w, stride, scale, DELTA)
    found = []
    for y_pt, profile in rows:
        got = measure_row(profile, page, stride, scale, DELTA)
        if not got:
            got = pair_split(profile, page, stride, scale, DELTA)
        if not got:
            continue
        got["ref_stable"] = ref_stable
        if got.get(u"pair"):
            got["solidity"] = track_solidity(px, y_pt + band_pt / 2.0, got["left_x0"],
                                             got["left_x1"], got["pill"], scale, DELTA)
        else:
            got["solidity"] = track_solidity(px, y_pt + band_pt / 2.0, 0.0,
                                             min(SIDEBAR_W_PT, width_pt), got["track"], scale, DELTA)
        if got["solidity"] >= MIN_SOLIDITY:
            got["y"] = y_pt
            found.append(got)
    return found, (pw, ph, scale, appearance_of(bg), bg)


def reference_outside(px, ymin, ymax, x1_px, stride_px, scale, delta, gap_pt=8.0, band_pt=4):
    """控件外面读页底：上带贴在 ymin 之上、下带贴在 ymax 之下，两带必须同档才算可信。"""
    per = []
    for y in (ymin - gap_pt - band_pt, ymax + gap_pt):
        if y < 2:
            continue
        y0, y1 = int(y * scale), int((y + band_pt) * scale)
        prof = column_levels(px, y0, y1, 0, x1_px, stride_px)
        if prof:
            per.append(mode_level(prof, delta))
    if not per:
        return None, False
    page = mode_level([(i, v) for i, v in enumerate(per)], delta)
    return page, (max(per) - min(per)) < delta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-png", action="store_true", help="把截图留在 /tmp（默认测完删掉）")
    ap.add_argument("--timeout", type=int, default=20, help="等主窗口出现的秒数")
    ap.add_argument("--png", default=None,
                    help="离线复量一张已有的截图（不启动 App、不截屏）：尺的读数要能离开现场复查")
    ap.add_argument("--width-pt", type=int, default=750, help="--png 模式下这扇窗的宽度（pt）")
    args = ap.parse_args()

    if args.png:
        found, meta = scan(args.png, args.width_pt)
        print("OFFLINE png=%s FRAME %dx%d scale=%.2f 外观=%s（背景中位=%.1f）"
              % (args.png, meta[0], meta[1], meta[2], meta[3], meta[4]))
        return report(found)

    alive, why = display_channel_state()
    print("DISPLAY_CHANNEL 可判=%d 成因=%s" % (1 if alive else 0, why))
    if not alive:
        print("REALSCREEN_NOT_RUN display_channel（%s）⇒ 这一格是没跑，不是通过" % why)
        return 1

    workdir = "/tmp/r330_real/data"
    logdir = "/tmp/r330_real/log"
    png = "/tmp/r330_real/pill.png"
    for d in (workdir, logdir):
        os.makedirs(d, exist_ok=True)
    if os.path.exists(png):
        os.remove(png)

    if already_running():
        print("REALSCREEN_NOT_RUN already_running（有实例在跑，可能是你自己那一份真存档；"
              "先退出它再跑这一格，尺不替你关窗）")
        return 1
    pid = launch_isolated(workdir, logdir)
    if pid is None:
        print("REALSCREEN_NOT_RUN no_executable_or_launch_failed（%s 不在盘上，或 open 没起得来）" % APP_PATH)
        return 1
    print("PID=%d 数据目录=%s（空库，不是复制真存档）" % (pid, workdir))
    try:
        bounds = window_bounds(pid, args.timeout)
        if not bounds:
            osascript('tell application "System Events" to tell (first process whose unix id is %d) '
                      'to perform action "AXPress" of menu bar item 1 of menu bar 2' % pid)
            bounds = window_bounds(pid, max(4, args.timeout // 2))
        if not bounds:
            print("REALSCREEN_NOT_RUN no_window（起了进程但 System Events 看不到窗口）")
            return 1
        print("WINDOW x=%d y=%d w=%d h=%d" % bounds)
        who = activate_and_wait(pid, max(4.0, args.timeout * 0.3))
        gate = capture_identity(who)
        print("CAPTURE_IDENTITY 前台=%s 目标=%s 判=%s" % (who, APP_PROCESS, gate))
        if gate != u"ok":
            print("REALSCREEN_NOT_RUN %s（前台是 %r，不是目标窗口 ⇒ 拍到的像素属于别人；"
                  "尺子不猜像素属于谁 —— 这一格是没跑，不是「侧栏没有控件」）" % (gate, who))
            return 1
        ok, tries = wait_for_rendered_frame(bounds, png, max(6.0, args.timeout * 0.6))
        print("RENDER 画完=%d 截了=%d 次" % (1 if ok else 0, tries))
        if not ok:
            print("REALSCREEN_NOT_RUN frame_not_rendered（截到的是未绘制的表面，不是「侧栏没有控件」）")
            return 1
        who2 = frontmost_name()
        gate2 = capture_identity(who2)
        print("CAPTURE_IDENTITY_AFTER 前台=%s 判=%s" % (who2, gate2))
        if gate2 != u"ok":
            print("REALSCREEN_NOT_RUN %s（拍照这一段时间里前台换成了 %r ⇒ 这一帧作废）" % (gate2, who2))
            return 1
        found, meta = scan(png, bounds[2])
        print("FRAME %dx%d scale=%.2f 外观=%s（背景中位=%.1f）" % (meta[0], meta[1], meta[2], meta[3], meta[4]))
        return report(found)
    finally:
        quit_isolated(pid)
        if not args.keep_png:
            if os.path.exists(png):
                os.remove(png)


def quit_isolated(pid):
    """只关**这一趟自己起的那一个** pid；不 pkill、不按名字杀（那会连别人的实例一起带走）。"""
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def report(found):
    """把候选行打印出来并判 377。两半（屏幕上是亮面 / 是暗洞）之外只留"没跑到"。"""
    if not found:
        print("REALSCREEN_VERDICT=no_band 侧栏顶部 %d..%dpt 里没有一行过四道形状闸"
              "（轨道 ≥%dpt 且比页底亮 ≥%.0f 级、洞 ≥%dpt、纵向实心度 ≥%.2f）"
              % (SCAN_Y[0], SCAN_Y[1], MIN_CONTAINER_PT, DELTA, MIN_RUN_PT, MIN_SOLIDITY))
        return 1
    stable = [g for g in found if g.get("ref_stable")]
    if not stable:
        print("REALSCREEN_VERDICT=reference_unstable 控件上下两条参照带**不同档** ⇒ 参照物不可信，"
              "这一格不许判（读不到背景 ≠ 背景没有）")
        return 1
    kind, best = prefer_shape(stable)
    if best is None:
        print(u"REALSCREEN_VERDICT=no_band 有 %d 行过了参照门，但两种形状都读不出来" % len(stable))
        return 1
    print(u"PILL_SHAPE=%s（pill=容器里与页底同档的那一段；pair=一个控件两段、选中段在左）" % kind)
    for g in sorted(stable, key=lambda g: g["y"])[:6]:
        print("  候选 y=%3dpt 轨道宽=%3.0fpt 洞宽=%3.0fpt 页底=%4.1f(行内众数会读成 %4.1f) "
              "轨道=%4.1f 药丸=%4.1f 实心=%.2f"
              % (g["y"], g["extent_pt"], g["hole_pt"], g["page"], g["page_mode_in_row"],
                 g["track"], g["pill"], g["solidity"]))
    if len(stable) > 6:
        print("  …共 %d 行过闸" % len(stable))
    diff = best["pill"] - best["track"]
    print("PILL_ROW y=%dpt 轨道宽=%.0fpt(x%.0f起) 洞宽=%.0fpt(x%.0f..%.0f, 占 %.0f%%) "
          "页底=%.1f 轨道档=%.1f 药丸档=%.1f 差=%+.1f 实心=%.2f"
          % (best["y"], best["extent_pt"], best["extent_x0"],
             best["hole_pt"], best["hole_x0"], best["hole_x1"], best["hole_share"] * 100.0,
             best["page"], best["track"], best["pill"], diff, best["solidity"]))
    if abs(diff) < DELTA:
        print("REALSCREEN_VERDICT=indistinguishable 两档差 %.1f < %.0f ⇒ 这台机器上分不开，"
              "只配记成通道限制（377 不据此结案）" % (abs(diff), DELTA))
        return 1
    if diff > 0:
        print("REALSCREEN_VERDICT=pill_lighter 屏幕上选中那颗比轨道**亮** %.1f 级 ⇒ 377 的暗洞是"
              "**离屏合成**的产物，不是产品缺陷（胶片那卷读的是通道）" % diff)
    else:
        print("REALSCREEN_VERDICT=pill_darker 屏幕上选中那颗比轨道**暗** %.1f 级 ⇒ 377 是真缺陷："
              "选中态在屏幕上读起来像轨道上挖出的洞" % abs(diff))
    return 0


if __name__ == "__main__":
    sys.exit(main())
