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
  两尺差   = 跨度时长 / 含峰那一段的时长

**两把尺都得先与 Swift 那边对账**，否则这只是另一份"我用 python 重算了一遍"的猜测：
日志里同一行自带 Swift 算出来的 `变化段时长=` 与 `事件内最粗=`，脚本把它们与本文件的
实现逐场景比一遍（`RULER_AGREEMENT`）。任何一格不一致就中止 ——
第一版就是因为分组下标数错（`过渡帧数` 被当成 `时刻ms`）而把 182ms 读成 3ms，
这道对账就是它自己的解药（"计数命令本身没证伪"那一族）。

尺子的形状必须与 Swift 一致：`minimumVisibleChange = 0.005`、`stepFloorRatio = 0.15`。
"""
import io
import re
import sys

MIN_VISIBLE = 0.005
FLOOR_RATIO = 0.15

LINE = re.compile(r"^MOTION (\S+) frames=(\d+) 声明=(\d+)ms 整卷中位=(\d+)ms "
                  r"事件内最粗=(\S+)ms 变化段时长=(\S+)ms 过渡帧数=(\d+) "
                  r"时刻ms=\[([^\]]*)\] 逐帧=\[([^\]]*)\]")

SELF_CHECK_FRACTIONS = [0.11, 0.001, 0.10, 0.0, 0.0, 0.0]
SELF_CHECK_GAPS = [45, 45, 45, 45, 45]


def parse(log_path):
    films = []
    for line in io.open(log_path, encoding="utf-8", errors="replace").read().splitlines():
        m = LINE.match(line.strip())
        if not m:
            continue
        name = m.group(1)
        declared = int(m.group(3))
        worst_logged = None if m.group(5) == "无" else float(m.group(5))
        span_logged = None if m.group(6) == "无" else float(m.group(6))
        gaps = [int(x) for x in m.group(8).split()]
        fractions = [float(x) for x in m.group(9).split()]
        films.append(dict(name=name, declared=declared, gaps=gaps, fractions=fractions,
                          worst_logged=worst_logged, span_logged=span_logged))
    return films


def span_ms(gaps, a, b):
    """第 a 格到"第 b 格之后的那次采样"之间经过了多少毫秒。"""
    return sum(gaps[a:b + 1]) if b + 1 <= len(gaps) else sum(gaps[a:])


def read(fractions, gaps):
    """返回 (跨度ms, 段数, 含峰那一段的 (起, 止, 时长, 段内最粗), 段内低谷格数)。"""
    peak = max(fractions) if fractions else 0.0
    if peak < MIN_VISIBLE:
        return None
    floor = peak * FLOOR_RATIO
    visible = [i for i, f in enumerate(fractions) if f >= MIN_VISIBLE]
    first, last = visible[0], visible[-1]
    low = sum(1 for i in range(first, last + 1) if fractions[i] < floor)
    runs = []
    start = None
    for i in range(first, last + 2):
        moving = i <= last and fractions[i] >= floor
        if moving and start is None:
            start = i
        if not moving and start is not None:
            runs.append((start, i - 1))
            start = None
    peak_run = next(((a, b) for a, b in runs if a <= fractions.index(peak) <= b), runs[0])
    a, b = peak_run
    # 与 Swift 一致：`worstIntervalInsideRun` 取的是"这一段里相邻两次采样的最大间隔"，
    # 下标从 a 到 b（`gaps[i] = stamps[i+1] - stamps[i]`），不多取段尾之后的那一格。
    worst = max((gaps[k] for k in range(a, min(b + 1, len(gaps)))), default=0)
    return span_ms(gaps, first, last), len(runs), (a, b, span_ms(gaps, a, b), worst), low


def self_check():
    """① 夹具必须读出"段数=2、跨度是含峰段的 ~3 倍"；② 解析器必须读得动一行真日志。"""
    span, runs, (a, b, longest, worst), low = read(SELF_CHECK_FRACTIONS, SELF_CHECK_GAPS)
    assert runs == 2, ("自检失败：夹具应读成两段，实读 %s" % (runs,))
    assert span / max(longest, 1) > 1.5, ("自检失败：两尺差应 >1.5，实读 %.2f" % (span / max(longest, 1)))
    print("SELF_CHECK 夹具 OK ⇒ 跨度=%dms 段数=%d 含峰段=%dms 段内低谷=%d"
          % (span, runs, longest, low))
    sample = ("MOTION unit-fixture frames=27 声明=160ms 整卷中位=44ms 事件内最粗=96ms "
              "变化段时长=182ms 过渡帧数=3 时刻ms=[66 96 43 43 44] 逐帧=[0.000 0.213 0.117 0.042 0.000 0.000]")
    m = LINE.match(sample)
    assert m, "自检失败：正则读不动一行真格式的 MOTION 行"
    assert m.group(7) == "3" and m.group(8) == "66 96 43 43 44" and m.group(9).startswith("0.000 0.213"), \
        ("自检失败：分组下标错位", m.group(7), m.group(8), m.group(9))
    print("SELF_CHECK 解析器 OK ⇒ 过渡帧数=%s 时刻ms=[%s] 逐帧=[%s…]"
          % (m.group(7), m.group(8), m.group(9)[:18]))


def main():
    self_check()
    log_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not log_path:
        print("（没给日志路径，只跑自检）")
        return
    films = parse(log_path)
    if not films:
        raise SystemExit("BACKLOG72_NO_FILM：日志里没有一条 `MOTION … 逐帧=[…]`，"
                         "这道题今天答不了（不是答『没有』）")

    print("\n=== 与 Swift 那把尺对账（同一行里它自己打的数）===")
    disagreements = 0
    for film in films:
        got = read(film["fractions"], film["gaps"])
        if got is None:
            print("  %-24s 峰值低于 %.3f ⇒ 无变化段可比" % (film["name"], MIN_VISIBLE))
            continue
        _, _, (_, _, longest, worst), _ = got
        ok_span = film["span_logged"] is not None and abs(longest - film["span_logged"]) <= 1
        ok_worst = film["worst_logged"] is not None and abs(worst - film["worst_logged"]) <= 1
        if not (ok_span and ok_worst):
            disagreements += 1
        print("  %-24s 含峰段 %6.0f vs Swift %6s  段内最粗 %5.0f vs Swift %5s  ⇒ %s"
              % (film["name"], longest,
                 "-" if film["span_logged"] is None else "%.0f" % film["span_logged"],
                 worst,
                 "-" if film["worst_logged"] is None else "%.0f" % film["worst_logged"],
                 "一致" if (ok_span and ok_worst) else "不一致"))
    if disagreements:
        raise SystemExit("RULER_AGREEMENT=failed：%d 个场景与 Swift 的读数不一致 ⇒ "
                         "下面那张表的结论不能算数（先修解析器/尺子）" % disagreements)
    print("RULER_AGREEMENT=ok（%d 卷全部一致）" % len(films))

    print("\n%-24s %7s %5s %8s %7s %8s" % ("场景", "跨度ms", "段数", "含峰段ms", "两尺差", "段内低谷"))
    multi = 0
    for film in films:
        span, runs, (a, b, longest, worst), low = read(film["fractions"], film["gaps"])
        if runs >= 2:
            multi += 1
        ratio = span / longest if longest else float("inf")
        print("%-24s %7d %5d %8d %7s %8d"
              % (film["name"], span, runs, longest, "%.2f" % ratio, low))
    print("\n结论：真胶片里『一次变化被读成多段』出现的次数 = %d / %d 卷"
          % (multi, len(films)))
    print("  0 次 ⇒ R2 那个 coarseSampling 夹具是虚构的形状，BACKLOG 72 该按连续段重写；"
          "≥1 次 ⇒ 采样真的会漏，跨度才是对的。")


main()
