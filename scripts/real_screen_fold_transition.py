#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R552：真实窗口折叠过渡的**屏上**采样 —— 60fps 录屏 + 逐帧内容差（STATE R552 靶 ①）。

为什么不是 `screencapture -l` 循环：那条通道自己一次就要 100ms 上下，比被量的 16.7ms 慢一个量级
—— 拿它量「屏上帧间距 ≤20ms」是用一把比被量物更钝的尺，读出来的「间距」其实是截图耗时
（READOUT_BLIND 那一族）。ffmpeg 的 avfoundation 屏幕设备给的是**窗口服务合成之后**的帧流，
帧 PTS 就是屏上时序，所以间距只能从它算。

顺序（每一步读不到都有名字，不许把「没读到」写成「没卡顿」）：
  1. 先问显示器与辅助功能 —— 锁屏/休眠时 System Events 看不到窗口 ⇒ `NOT_RUN=display-channel`；
  2. 起被测物：`swift test --filter RealScreenFoldTransitionTests/...` + env 门 ⇒ 产品**自己那扇窗**
     摆上屏幕；存档是测试内的 `RecordingHistoryPersistence`（内存），**不碰用户真库、不截真实条目**；
  3. 矩形与屏幕 pt 尺寸都由被测物自己印（R143 的教训：python 手抄坐标，Swift 一改布局就截错态）；
  4. 录像先起，再 touch `go` 文件放行折叠/展开 ⇒ 事件一定落在录像窗口里；
  5. 逐帧算窗口矩形内的灰度指纹 ⇒ 变化帧之间的 PTS 差 = 屏上帧间距；
  6. 被测物另记一份 `(t_ms, 窗口宽, foldProgress, isCollapsed, 分栏各列宽)` CSV ——
     分栏列宽是「detail 还在不在树上」的现场证人，用来把「内容跳变」与「窗口变窄」分开。

退出码：0 = 读到数（读到的是缺陷也算读到）；1 = 通道读不到（具名 NOT_RUN）。
"""
import argparse
import os
import re
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from real_screen_sidebar_icons import display_channel_state, osascript  # noqa: E402

PKG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ClipboardHistory")
TEST_FILTER = "RealScreenFoldTransitionTests/testRecordRealWindowFoldTransition"
RECT_FILE = "/tmp/r552-fold-rect.txt"
TICKS_FILE = "/tmp/r552-fold-ticks.csv"
GO_FILE = "/tmp/r552-fold-go"
MOV_FILE = "/tmp/r552-fold.mov"
SEAM_PT = 280.0          # MainWindowCollapsePolicy.sidebarSeamWidth：detail 带的左界
FRAME_W = 360            # 逐帧指纹的横向采样宽（750pt 窗 ⇒ ≈2.1pt/列）
FRAME_H = 200
DIFF_EPS = 1.2           # 整帧平均灰度差超过它 = 这一帧屏上真的换了内容
COL_EPS = 8.0            # 单列平均差超过它 = 这一列换了内容
REF_FRAMES = 8


def log(line):
    sys.stdout.write(line + u"\n")
    sys.stdout.flush()


def not_run(cause, detail=u""):
    log(u"REALSCREEN_FOLD_NOT_RUN=%s %s ⇒ 这一格是没跑，不许读成「不卡」也不许读成「卡」" % (cause, detail))
    return 1


def screen_device():
    """挑屏幕采集设备。**按名字**给 avfoundation（本机现读：数字索引会 `Invalid device index`）。"""
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-f", "avfoundation",
                           "-list_devices", "true", "-i", ""],
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    # 设备表长这样：`[AVFoundation indev @ 0x…] [4] Capture screen 0`。
    # 只取 `[数字] 名称` 那一截 —— 早先按「最后一个 ] 之后」切，把 `[4] ` 一起抄进名字里，
    # avfoundation 认不出这个设备 ⇒ 录出一个空文件，而空文件长得像「屏幕上什么都没发生」。
    for idx, name in re.findall(r"\[\s*(\d+)\]\s+([^\n\r]*)", proc.stderr):
        if "screen" in name.lower() or u"屏幕" in name or u"显示器" in name:
            return name.strip()
    return None


def ffprobe_geometry(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "stream=width,height", "-of", "default=nw=1", path],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    vals = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k] = int(v)
    return vals.get("width"), vals.get("height")


def frame_pts(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "frame=pts_time", "-of", "csv=p=0", path],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip().strip(",")
        if not line:
            continue
        try:
            out.append(float(line))
        except ValueError:
            pass
    return out


def decode(path, crop_px):
    """把窗口矩形逐帧解成灰度小图（numpy 数组列表）。"""
    import numpy as np
    x, y, w, h = crop_px
    vf = "crop=%d:%d:%d:%d,scale=%d:%d" % (w, h, x, y, FRAME_W, FRAME_H)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", vf,
                             "-pix_fmt", "gray", "-f", "rawvideo", "-"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    blob = proc.stdout.read()
    proc.wait()
    stride = FRAME_W * FRAME_H
    n = len(blob) // stride
    arr = np.frombuffer(blob[:n * stride], dtype=np.uint8).reshape(n, FRAME_H, FRAME_W)
    return arr.astype(np.int32)


def bursts_of(diff):
    """连续「屏上换了内容」的帧归成一段；段间至少静默 3 帧。"""
    out, cur = [], []
    quiet = 0
    for i, d in enumerate(diff):
        if d > DIFF_EPS:
            cur.append(i)
            quiet = 0
        elif cur:
            quiet += 1
            if quiet >= 3:
                if cur:
                    out.append(cur)          # R552：一步切换在屏上就是**一帧**，单帧簇必须能报出来
                cur, quiet = [], 0
    if cur:
        out.append(cur)
    return out


def analyze(path, crop_px, width_pt, ticks_rows):
    import numpy as np
    frames = decode(path, crop_px)
    if len(frames) < 30:
        return not_run("few-frames", u"（只解出 %d 帧）" % len(frames))
    pts = frame_pts(path)
    if len(pts) < len(frames):
        pts = [i / 60.0 for i in range(len(frames))]
    pts = pts[:len(frames)]
    ref = np.median(frames[:REF_FRAMES], axis=0)
    diff = np.abs(frames.astype(np.float64) - ref).mean(axis=(1, 2))
    step = np.abs(np.diff(frames.astype(np.float64), axis=0)).mean(axis=(1, 2))
    step = np.concatenate(([0.0], step))
    bs = bursts_of(step[1:])
    log(u"REALSCREEN_FOLD file=%s 帧=%d 采样=%dx%d 窗口宽=%.0fpt 每列≈%.2fpt"
        % (os.path.basename(path), len(frames), FRAME_W, FRAME_H, width_pt, width_pt / FRAME_W))
    if not bs:
        log(u"REALSCREEN_FOLD_BURSTS=0 ⇒ 录像里一帧变化都没有 ⇒ 事件没落在录像窗口里（通道坏，不是产品绿）")
        return 1
    verdicts = []
    for n, b in enumerate(bs, 1):
        b = [i + 1 for i in b]
        gaps = [(pts[j] - pts[j - 1]) * 1000.0 for j in b[1:]] or [(pts[b[0]] - pts[b[0] - 1]) * 1000.0]
        # 一步切换 = 单帧簇：跨度记 0ms，间距记「这一帧距上一帧」，形状与多帧簇同一行可比。
        span = (pts[b[-1]] - pts[b[0]]) * 1000.0
        first = b[0]
        per_col = np.abs(frames[first] - ref).mean(axis=1)
        hit = np.nonzero(per_col > COL_EPS)[0]
        left_pt = (int(hit.min()) * width_pt / FRAME_W) if len(hit) else -1
        right_pt = (int(hit.max()) * width_pt / FRAME_W) if len(hit) else -1
        # 扫过的痕迹：变化带左界随帧号往左走的步数（>=3 步 = 有一条从右往左扫的边）
        sweep = []
        for j in b[:14]:
            pc = np.abs(frames[j] - ref).mean(axis=1)
            hh = np.nonzero(pc > COL_EPS)[0]
            sweep.append(int(hh.min()) * width_pt / FRAME_W if len(hh) else -1)
        steps = len({round(v / 20.0) for v in sweep if v >= 0})
        if len(b) == 1:
            verdict = u"一步切换（单帧到位，无中间态）"
        else:
            instant = left_pt >= 0 and left_pt < SEAM_PT + 20 and steps <= 2
            verdict = u"detail 当场消失" if instant else u"变化带随右缘扫过"
        verdicts.append(instant)
        log(u"REALSCREEN_FOLD_BURST id=%d 起=%.3fs 跨=%.0fms 变化帧=%d 间距max=%.1fms 中位=%.1fms "
            u"首帧变化带=[%.0f..%.0f]pt 扫过档数=%d ⇒ %s"
            % (n, pts[b[0]], span, len(b), max(gaps), statistics.median(gaps),
               left_pt, right_pt, steps, verdict))
        log(u"REALSCREEN_FOLD_SWEEP id=%d 左界序列=%s"
            % (n, u",".join(u"%.0f" % v for v in sweep)))
        # 右缘步进：整帧平均差对「一条边慢慢扫过」不敏感（每帧只改 2%% 的列），所以另起一把尺 ——
        # 逐列判「这一列还像过渡前吗」，取从左边连续成立的最右一列 = 这一帧的右缘。
        before = frames[b[0] - 1]
        edges = []
        for j in range(b[0] - 1, min(len(frames), b[-1] + 4)):
            like_before = (np.abs(frames[j] - before).mean(axis=0) < 6.0)
            edge = 0
            while edge < FRAME_W and like_before[edge]:
                edge += 1
            edges.append(edge * width_pt / FRAME_W)
        steps = len({round(v / 12.0) for v in edges})
        biggest = max([a - bb for a, bb in zip(edges, edges[1:])], default=0.0)
        log(u"REALSCREEN_FOLD_EDGE id=%d 右缘步进=%d 档 起点=%.0fpt 终点=%.0fpt 最大单步=%.0fpt 序列=%s"
            % (n, steps, edges[0], edges[-1], abs(biggest),
               u",".join(u"%.0f" % v for v in edges[:16])))
    if ticks_rows:
        widths = [r["width"] for r in ticks_rows]
        cols_present = [r["columns"] for r in ticks_rows]
        trans = [(r["t_ms"], r["width"], r["progress"], r["collapsed"], r["columns"]) for r in ticks_rows]
        log(u"REALSCREEN_FOLD_TICKS 行数=%d 宽档数=%d 分栏出现档数=%d"
            % (len(trans), len({round(w) for w in widths}), len({c for c in cols_present})))
        # detail 从树上消失的那一刻，窗口宽还剩多少？（离屏胶片答不了这一格）
        gone = [t for t in trans if t[4] == u"-"]
        if gone and trans:
            first_gone = gone[0]
            log(u"REALSCREEN_FOLD_LAYOUT 分栏消失@t=%dms 窗口宽=%.1fpt progress=%.3f 折叠=%d"
                % (first_gone[0], first_gone[1], first_gone[2], first_gone[3]))
        else:
            log(u"REALSCREEN_FOLD_LAYOUT 分栏全程在树上（或 CSV 空）⇒ 这一格读不到，不当作已证")
    return 0


def read_ticks(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as h:
        header = h.readline()
        for line in h:
            parts = line.rstrip("\n").split(",")
            if len(parts) < 5:
                continue
            try:
                rows.append({"t_ms": int(parts[0]), "width": float(parts[1]),
                             "progress": float(parts[2]), "collapsed": int(parts[3]),
                             "columns": parts[4]})
            except ValueError:
                continue
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mov", help="离线复量已有的录像（不重启被测物）")
    ap.add_argument("--keep-mov", action="store_true")
    ap.add_argument("--record-seconds", type=float, default=8.0)
    ap.add_argument("--test-timeout", type=float, default=420.0)
    args = ap.parse_args()

    try:
        import numpy  # noqa: F401
    except ImportError:
        return not_run("numpy", u"（没装 numpy ⇒ 量不了帧间距）")
    if subprocess.run(["which", "ffmpeg"], stdout=subprocess.DEVNULL).returncode != 0:
        return not_run("ffmpeg")

    if args.mov:
        if not os.path.exists(args.mov):
            return not_run("mov-missing", args.mov)
        # 离线复量：坐标与 pt 尺寸从旁边的 rect 文件读，读不到就不猜
        if not os.path.exists(RECT_FILE):
            return not_run("rect-missing", u"（离线模式要 %s 还在）" % RECT_FILE)
        rect_pt, screen_w = read_rect()
        rw, _ = ffprobe_geometry(args.mov)
        return analyze(args.mov, px_of(rect_pt, screen_w, rw), float(rect_pt[2]),
                       read_ticks(TICKS_FILE))

    alive, why = display_channel_state()
    if not alive:
        return not_run("display-channel", why)
    # 辅助功能**不是**这条通道的依赖：事件由被测物在进程内走产品自己的 `delegate.perform`，
    # 矩形也由被测物自己印，python 侧一次点击都不发。所以这里只报状态、不设门
    # （本机现读 `UI elements enabled=false`：拿它当门会把一格能量到的读数挡成没跑）。
    code, enabled = osascript('tell application "System Events" to return UI elements enabled')
    log(u"REALSCREEN_FOLD accessibility=%s（本通道不依赖它：不发点击、不读别人的窗口）"
        % (enabled if code == 0 else u"unknown"))
    device = screen_device()
    if not device:
        return not_run("avfoundation-device")

    for path in (RECT_FILE, TICKS_FILE, GO_FILE, MOV_FILE):
        if os.path.exists(path):
            os.remove(path)

    env = dict(os.environ, CLIPBOARD_HISTORY_REALSCREEN_FOLD="1",
               R552_RECT_FILE=RECT_FILE, R552_TICKS_FILE=TICKS_FILE, R552_GO_FILE=GO_FILE,
               PYTHONUTF8="1")
    env.pop("SDKROOT", None)
    log(u"REALSCREEN_FOLD step=起被测物 filter=%s" % TEST_FILTER)
    test = subprocess.Popen(["swift", "test", "--filter", TEST_FILTER], cwd=PKG, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        deadline = time.time() + args.test_timeout
        rect_pt = None
        screen_w = None
        while time.time() < deadline and rect_pt is None:
            time.sleep(0.5)
            if test.poll() is not None:
                return not_run("test-exited", u"（退出码 %s，窗口没摆上屏幕）" % test.poll())
            if os.path.exists(RECT_FILE):
                rect_pt, screen_w = read_rect()
        if rect_pt is None:
            return not_run("rect", u"（等 %ds 没拿到被测物自己印的矩形）" % args.test_timeout)

        rec = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error",
                                "-f", "avfoundation", "-framerate", "60",
                                "-capture_cursor", "0", "-i", "%s:none" % device,
                                "-t", "%.1f" % args.record_seconds, "-y", MOV_FILE],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)                     # 让录像真的开始写帧，再放行事件
        open(GO_FILE, "w").close()
        log(u"REALSCREEN_FOLD step=录像已起 device=%s 矩形=%s ⇒ 放行折叠/展开"
            % (device, u",".join(str(v) for v in rect_pt)))
        test_deadline = time.time() + 120
        while test.poll() is None and time.time() < test_deadline:
            time.sleep(0.5)
        rec.wait(timeout=60)
        if test.poll() not in (0, None):
            log(u"REALSCREEN_FOLD 被测物退出码=%s（过渡本身跑过了才有 CSV，见下）" % test.poll())
        if not os.path.exists(MOV_FILE) or os.path.getsize(MOV_FILE) < 10000:
            return not_run("mov-empty", u"（录屏没写出内容）")

        rw, rh = ffprobe_geometry(MOV_FILE)
        scale = rw / float(screen_w)
        px = [int(round(rect_pt[0] * scale)), int(round(rect_pt[1] * scale)),
              int(round(rect_pt[2] * scale)), int(round(rect_pt[3] * scale))]
        px = [px[0] + (px[0] % 2), px[1] + (px[1] % 2), px[2] - (px[2] % 2), px[3] - (px[3] % 2)]
        px[0] = max(0, min(px[0], rw - px[2]))
        px[1] = max(0, min(px[1], rh - px[3]))
        log(u"REALSCREEN_FOLD 录像=%dx%dpx 窗口矩形=%spx 屏幕=%.0fpt" % (rw, rh, px, screen_w))
        return analyze(MOV_FILE, px, float(rect_pt[2]), read_ticks(TICKS_FILE))
    finally:
        if test.poll() is None:
            test.terminate()
        if not args.keep_mov and os.path.exists(MOV_FILE):
            os.remove(MOV_FILE)      # 屏幕内容不进仓库、不留档，只留数值


def px_of(rect_pt, screen_w, recorded_w):
    """pt 矩形 → 录像里的像素矩形（偶数、且不越出画面）。"""
    scale = recorded_w / float(screen_w)
    x, y, w, h = [int(round(v * scale)) for v in rect_pt]
    x += x % 2
    y += y % 2
    w -= w % 2
    h -= h % 2
    return [max(0, x), max(0, y), w, h]


def read_rect():
    with open(RECT_FILE, encoding="utf-8") as h:
        lines = [l.strip() for l in h if l.strip()]
    if len(lines) < 2 or lines[0] in ("NO_SCREEN", "NO_WINDOW"):
        return None, None
    vals = [int(v) for v in re.findall(r"-?\d+", lines[0])]
    m = re.search(r"screen=(\d+)x(\d+)", lines[1])
    if len(vals) != 4 or not m:
        return None, None
    return vals, int(m.group(1))


if __name__ == "__main__":
    sys.exit(main())
