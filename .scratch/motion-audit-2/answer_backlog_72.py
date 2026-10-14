#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回答 BACKLOG 72：真胶片里"段内掉回地板以下"到底出现过没有。

R48 换尺时留了个口子：`contiguousChangedRuns`（连续段）与 `changedSpanElapsedMilliseconds`
（首尾跨度）在同一段数据上能差 3 倍，而其余调用点还在跨度上。理由是我怀疑**真胶片里
根本没有"两波之间掉回地板以下"这种形状** —— 那个形状只存在于 R2 的手工夹具
`coarseSampling = [0.11, 0.001, 0.10, 0, 0, 0]`。

这个脚本把判据搬到真读数上：日志里每条 `MOTION <场景> … 逐帧=[…]` 都按两把尺各读一遍，
数三件事：
  段数     = 连续段那把尺读出的变化段数量（>=2 就意味着"跨度"把两段并成了一段）
  段内低谷 = 跨度区间里掉到地板（峰值 × 0.15）以下的格子数
  两尺差   = 跨度时长 / 最长连续段时长（>1.5 才叫"差得有意义"）

尺子的形状必须与 Swift 那边一致：`minimumVisibleChange = 0.005`、`stepFloorRatio = 0.15`。
自检夹具就是 R2 那一条 —— 它必须读出"段数=2、两尺差≈3"，否则这个脚本在骗人。
"""
import io
import re
import sys

MIN_VISIBLE = 0.005
FLOOR_RATIO = 0.15

LINE = re.compile(r"^MOTION (\S+) frames=(\d+) 声明=(\d+)ms 整卷中位=(\d+)ms "
                  r"事件内最粗=(\S+)ms 变化段时长=(\S+)ms 过渡帧数=(\d+) "
                  r"时刻ms=\[([^\]]*)\] 逐帧=\[([^\]]*)\]")


def parse(log_path):
    films = []
    for line in io.open(log_path, encoding="utf-8", errors="replace").read().splitlines():
        m = LINE.match(line.strip())
        if not m:
            continue
        name = m.group(1)
        gaps = [int(x) for x in m.group(7).split()] if m.group(7).strip() else []
        fractions = [float(x) for x in m.group(8).split()] if m.group(8).strip() else []
        films.append((name, fractions, gaps))
    return films


def span_and_runs(fractions, gaps):
    """返回 (跨度ms, 段数, 最长连续段ms, 段内低谷格数)。"""
    peak = max(fractions) if fractions else 0.0
    if peak < MIN_VISIBLE:
        return None
    floor = peak * FLOOR_RATIO
    visible = [i for i, f in enumerate(fractions) if f >= MIN_VISIBLE]
    first, last = visible[0], visible[-1]
    low = sum(1 for i in range(first, last + 1) if fractions[i] < floor)
    # 时长用"格子之间"的间隔累加：stamps[i+1]-stamps[i] = gaps[i]
    def span_ms(a, b):                      # 从第 a 格到第 b 格之后那一次采样
        return sum(gaps[a:b + 1]) if b + 1 <= len(gaps) else sum(gaps[a:])
    span = span_ms(first, last)
    runs = []
    start = None
    for i in range(first, last + 2):
        moving = i <= last and fractions[i] >= floor
        if moving and start is None:
            start = i
        if not moving and start is not None:
            runs.append((start, i - 1))
            start = None
    longest = max((span_ms(a, b) for a, b in runs), default=0)
    return span, len(runs), longest, low


SELF_CHECK = [0.11, 0.001, 0.10, 0.0, 0.0, 0.0]


def main():
    log_path = sys.argv[1] if len(sys.argv) > 1 else None
    # ① 先自检尺子：R2 的手工夹具必须读出"段数=2、跨度是连续段的 ~3 倍"
    gaps = [45, 45, 45, 45, 45]
    got = span_and_runs(SELF_CHECK, gaps)
    span, runs, longest, low = got
    assert runs == 2, ("自检失败：夹具应读成两段，实读 %s" % (runs,))
    assert span / max(longest, 1) > 1.5, ("自检失败：两尺差应 >1.5，实读 %.2f" % (span / max(longest, 1)))
    print("SELF_CHECK OK 夹具=%s ⇒ 跨度=%dms 段数=%d 最长连续段=%dms 段内低谷=%d"
          % ("coarseSampling", span, runs, longest, low))
    if not log_path:
        print("（没给日志路径，只跑自检）")
        return
    films = parse(log_path)
    if not films:
        raise SystemExit("BACKLOG72_NO_FILM：日志里没有一条 `MOTION … 逐帧=[…]`，"
                         "这道题今天答不了（不是答『没有』）")
    print("\n%-26s %6s %5s %8s %8s %7s" % ("场景", "跨度ms", "段数", "最长段ms", "两尺差", "段内低谷"))
    multi = 0
    for name, fractions, gaps in films:
        got = span_and_runs(fractions, gaps)
        if got is None:
            print("%-26s  峰值低于 %.3f ⇒ 这一卷没有可判的变化" % (name, MIN_VISIBLE))
            continue
        span, runs, longest, low = got
        ratio = span / longest if longest else float("inf")
        if runs >= 2:
            multi += 1
        print("%-26s %6d %5d %8d %8s %7d"
              % (name, span, runs, longest, ("%.2f" % ratio if longest else "inf"), low))
    print("\n结论：真胶片里『一次变化被读成多段』出现的次数 = %d / %d 卷"
          % (multi, len(films)))
    print("  0 次 ⇒ R2 那个 coarseSampling 夹具是虚构的形状，BACKLOG 72 该按连续段重写；"
          "≥1 次 ⇒ 采样真的会漏，跨度才是对的。")


main()
